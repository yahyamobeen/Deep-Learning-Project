"""Train tiny ST-GCN on pre-extracted WLASL-Top-300 landmarks.

Reads from .../local_runs/data/wlasl_top300_landmarks_npz/{train,val,test}.npz
Writes to  .../local_runs/models/sthgcn_wlasl300/{model.ts, encoder.onnx, labels.json}

Resumable: per-epoch checkpoint to last.pt; re-running picks up where it left off.
"""
import os, sys, json, time, gc, traceback
print("STEP 0: started", flush=True)

BASE  = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
CACHE = f"{BASE}/data/wlasl_top300_landmarks_npz"
OUT   = f"{BASE}/models/sthgcn_wlasl300"

os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
import warnings; warnings.filterwarnings("ignore")

print("STEP 1: importing torch + numpy", flush=True)
import torch
import torch.nn as nn
import numpy as np
print(f"STEP 2: torch {torch.__version__}", flush=True)

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print(f"STEP 3: device = {DEV}", flush=True)
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}", flush=True)


# ---- load data --------------------------------------------------------------
print("STEP 4: loading cached landmarks", flush=True)
tr = np.load(f"{CACHE}/train.npz"); X_tr, y_tr = tr["X"], tr["y"]
va = np.load(f"{CACHE}/val.npz")   if os.path.exists(f"{CACHE}/val.npz")   else None
te = np.load(f"{CACHE}/test.npz")  if os.path.exists(f"{CACHE}/test.npz")  else None
print(f"  train {X_tr.shape}  y {y_tr.shape}", flush=True)
if va is not None: print(f"  val   {va['X'].shape}", flush=True)
if te is not None: print(f"  test  {te['X'].shape}", flush=True)

gloss2id = json.load(open(f"{BASE}/models/gloss_vocab.json"))
NUM_LABELS = len(gloss2id)
id2gloss = {i: g for g, i in gloss2id.items()}
print(f"  classes: {NUM_LABELS}", flush=True)


# ---- model ------------------------------------------------------------------
class TempBlock(nn.Module):
    def __init__(self, c_in, c_out, k=5):
        super().__init__()
        self.conv = nn.Conv1d(c_in, c_out, k, padding=k // 2)
        self.bn   = nn.BatchNorm1d(c_out)
        self.act  = nn.GELU()
    def forward(self, x): return self.act(self.bn(self.conv(x)))

class STGCNTiny(nn.Module):
    def __init__(self, num_labels):
        super().__init__()
        self.proj = nn.Linear(1629, 128)
        self.t1   = TempBlock(128, 128)
        self.t2   = TempBlock(128, 256)
        self.t3   = TempBlock(256, 256)
        self.head = nn.Linear(256, num_labels)
    def encode(self, x):
        h = self.proj(x).transpose(1, 2)
        h = self.t1(h); h = self.t2(h); h = self.t3(h)
        return h.mean(-1)
    def forward(self, x):
        return self.head(self.encode(x))


# ---- train ------------------------------------------------------------------
os.makedirs(OUT, exist_ok=True)
BATCH = 32
EPOCHS = 15
LR = 1e-3

from torch.utils.data import TensorDataset, DataLoader

def make_loader(X, y, shuffle):
    return DataLoader(
        TensorDataset(torch.from_numpy(X.astype(np.float32)),
                      torch.from_numpy(y.astype(np.int64))),
        batch_size=BATCH, shuffle=shuffle, num_workers=0, pin_memory=False)

tr_loader = make_loader(X_tr, y_tr, shuffle=True)
va_loader = make_loader(va["X"], va["y"], shuffle=False) if va is not None else None

model = STGCNTiny(NUM_LABELS).to(DEV)
print(f"STEP 5: model params = {sum(p.numel() for p in model.parameters())/1e6:.2f}M", flush=True)

opt   = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)

best = 0.0
ckpt = f"{OUT}/last.pt"
start_epoch = 0
RANDOM_BASELINE = 1.0 / NUM_LABELS   # what random guessing scores

if os.path.exists(ckpt):
    sd = torch.load(ckpt, map_location=DEV)
    saved_epoch = sd["epoch"]
    saved_best  = sd.get("best", 0.0)
    saved_at_end = saved_epoch >= EPOCHS - 1
    looks_random = saved_best < RANDOM_BASELINE * 3   # 3x random = not learning

    if saved_at_end and looks_random:
        print(f"STEP 6: stale checkpoint detected (epoch {saved_epoch}, best={saved_best:.3f} "
              f"~ random {RANDOM_BASELINE:.3f}). Discarding and starting fresh.", flush=True)
        for f in ("last.pt", "best.pt"):
            try:
                os.remove(f"{OUT}/{f}")
                print(f"  removed {f}", flush=True)
            except FileNotFoundError:
                pass
    else:
        model.load_state_dict(sd["model"])
        opt.load_state_dict(sd["opt"])
        start_epoch = saved_epoch + 1
        best = saved_best
        print(f"STEP 6: resuming at epoch {start_epoch}, best={best:.3f}", flush=True)

if not os.path.exists(ckpt):
    print("STEP 6: fresh training run", flush=True)

t_total = time.time()
for epoch in range(start_epoch, EPOCHS):
    t_ep = time.time()
    model.train()
    running = 0.0; n = 0
    for i, (X, y) in enumerate(tr_loader):
        X, y = X.to(DEV), y.to(DEV)
        loss = loss_fn(model(X), y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        running += loss.item() * len(y); n += len(y)
        if (i + 1) % 50 == 0:
            print(f"  ep{epoch} step{i+1}/{len(tr_loader)} loss={running/n:.3f}", flush=True)
    sched.step()

    val_acc = float("nan")
    if va_loader is not None:
        model.eval(); c = nn_ = 0
        with torch.no_grad():
            for X, y in va_loader:
                pred = model(X.to(DEV)).argmax(-1).cpu().numpy()
                c += (pred == y.numpy()).sum(); nn_ += len(y)
        val_acc = c / max(nn_, 1)
        if val_acc > best:
            best = val_acc
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                        "epoch": epoch, "best": best}, f"{OUT}/best.pt")

    torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                "epoch": epoch, "best": best}, ckpt)
    print(f"epoch {epoch}: val_acc={val_acc:.3f} best={best:.3f}  ({time.time()-t_ep:.0f}s)", flush=True)

print(f"STEP 7: training done in {time.time()-t_total:.0f}s, best val acc = {best:.3f}", flush=True)


# ---- evaluate test ----------------------------------------------------------
if te is not None and os.path.exists(f"{OUT}/best.pt"):
    print("STEP 8: evaluating on test split", flush=True)
    sd = torch.load(f"{OUT}/best.pt", map_location=DEV)["model"]
    model.load_state_dict(sd); model.eval()
    Xt = torch.from_numpy(te["X"].astype(np.float32))
    yt = te["y"]
    top1 = top5 = 0
    with torch.no_grad():
        for i in range(0, len(Xt), BATCH):
            logits = model(Xt[i:i+BATCH].to(DEV))
            top = logits.topk(5, dim=-1).indices.cpu().numpy()
            for r in range(top.shape[0]):
                top1 += int(top[r, 0] == yt[i+r])
                top5 += int(yt[i+r] in top[r])
    print(f"  Top-1 = {top1/len(yt):.3f}   Top-5 = {top5/len(yt):.3f}   N={len(yt)}", flush=True)


# ---- export TorchScript + ONNX encoder + labels -----------------------------
print("STEP 9: exporting model.ts, encoder.onnx, labels.json", flush=True)
model.eval()
example = torch.zeros(1, 32, 1629, dtype=torch.float32).to(DEV)

ts = torch.jit.trace(model, example)
ts.save(f"{OUT}/model.ts")

class Enc(nn.Module):
    def __init__(self, m): super().__init__(); self.m = m
    def forward(self, x): return self.m.encode(x)

torch.onnx.export(
    Enc(model), example, f"{OUT}/encoder.onnx",
    input_names=["x"], output_names=["emb"], opset_version=17,
    dynamic_axes={"x": {0: "B", 1: "T"}, "emb": {0: "B"}},
)
json.dump({i: id2gloss[i] for i in range(NUM_LABELS)}, open(f"{OUT}/labels.json", "w"))
print(f"  exported to {OUT}", flush=True)
print("STEP 10: all done", flush=True)
