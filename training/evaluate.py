"""Evaluate everything and write local_runs/docs/RESULTS.md.

- ST-GCN: Top-1 / Top-5 on WLASL-Top-300 test split
- flan-T5 text->gloss: BLEU-4 on a held-out slice of SEED_PAIRS
- flan-T5 gloss->text: BLEU-4
- ST-GCN CPU latency (p50 / p95 / p99)
"""
import os, json, time, random, datetime
import numpy as np
print("STEP 0: started", flush=True)

BASE = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
os.makedirs(f"{BASE}/docs", exist_ok=True)
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
import warnings; warnings.filterwarnings("ignore")

import torch
DEV = "cuda" if torch.cuda.is_available() else "cpu"
print(f"STEP 1: device = {DEV}", flush=True)

results = {}


# ---- ST-GCN test accuracy ---------------------------------------------------
CACHE = f"{BASE}/data/wlasl_top300_landmarks_npz"
OUT   = f"{BASE}/models/sthgcn_wlasl300"
te_path = f"{CACHE}/test.npz"

print("STEP 2: ST-GCN test eval", flush=True)
if os.path.exists(te_path) and os.path.exists(f"{OUT}/model.ts"):
    te = np.load(te_path); Xt = te["X"]; yt = te["y"]
    m = torch.jit.load(f"{OUT}/model.ts", map_location=DEV).eval()
    top1 = top5 = 0
    with torch.no_grad():
        for i in range(0, len(Xt), 32):
            xb = torch.from_numpy(Xt[i:i+32].astype(np.float32)).to(DEV)
            top = m(xb).topk(5, dim=-1).indices.cpu().numpy()
            for r in range(top.shape[0]):
                top1 += int(top[r, 0] == yt[i+r])
                top5 += int(yt[i+r] in top[r])
    results["sthgcn_top1"] = top1 / len(yt)
    results["sthgcn_top5"] = top5 / len(yt)
    results["sthgcn_n"]    = int(len(yt))
    print(f"  Top-1={results['sthgcn_top1']:.3f}  Top-5={results['sthgcn_top5']:.3f}  N={results['sthgcn_n']}", flush=True)
else:
    print("  skipped — model.ts or test.npz missing", flush=True)
    results["sthgcn_top1"] = results["sthgcn_top5"] = None
    results["sthgcn_n"] = 0


# ---- T5 BLEU ---------------------------------------------------------------
SEED_PAIRS = [
    ("hello how are you",          "HELLO HOW YOU"),
    ("my name is sara",            "MY NAME S-A-R-A"),
    ("i am hungry",                "I HUNGRY"),
    ("what time is it",            "TIME WHAT"),
    ("thank you very much",        "THANK-YOU VERY MUCH"),
    ("where is the bathroom",      "BATHROOM WHERE"),
    ("i love you",                 "I LOVE YOU"),
    ("i need help",                "HELP NEED I"),
    ("how much does this cost",    "COST HOW-MUCH THIS"),
    ("i do not understand",        "UNDERSTAND I NOT"),
    ("please speak slowly",        "PLEASE SPEAK SLOW"),
    ("i am a student",             "I STUDENT"),
    ("see you tomorrow",           "SEE YOU TOMORROW"),
    ("what is your name",          "YOUR NAME WHAT"),
    ("i am happy",                 "I HAPPY"),
    ("i am tired",                 "I TIRED"),
    ("do you have water",          "YOU HAVE WATER"),
    ("where do you live",          "YOU LIVE WHERE"),
    ("i want to learn sign",       "I WANT LEARN SIGN"),
    ("this is my friend",          "MY FRIEND THIS"),
    ("good morning",               "MORNING GOOD"),
    ("good night",                 "NIGHT GOOD"),
    ("nice to meet you",           "MEET YOU NICE"),
    ("i am sorry",                 "I SORRY"),
    ("excuse me",                  "EXCUSE-ME"),
    ("yes please",                 "YES PLEASE"),
    ("no thank you",               "NO THANK-YOU"),
    ("i need to go home",          "HOME I GO NEED"),
    ("can you help me",            "YOU HELP ME CAN"),
    ("i feel sick",                "I SICK FEEL"),
]
random.seed(42)
eval_pairs = random.sample(SEED_PAIRS, len(SEED_PAIRS))   # all 30, deterministic order

print("STEP 3: T5 BLEU eval", flush=True)
try:
    import sacrebleu
    from transformers import AutoTokenizer, T5ForConditionalGeneration

    def bleu(direction):
        out_dir = f"{BASE}/models/" + ("t5_text2gloss" if direction == "text2gloss" else "gloss2text")
        if not os.path.exists(f"{out_dir}/config.json"):
            return None
        tok = AutoTokenizer.from_pretrained(out_dir)
        m   = T5ForConditionalGeneration.from_pretrained(out_dir).eval().to(DEV)
        prefix = "translate English to ASL gloss: " if direction == "text2gloss" else "translate ASL gloss to English: "
        preds, refs = [], []
        for en, gl in eval_pairs:
            src, tgt = (en, gl) if direction == "text2gloss" else (gl, en)
            ids = tok(prefix + src, return_tensors="pt", truncation=True, max_length=64).input_ids.to(DEV)
            with torch.no_grad():
                out = m.generate(ids, max_length=64, num_beams=4)
            preds.append(tok.decode(out[0], skip_special_tokens=True))
            refs.append(tgt)
        return sacrebleu.corpus_bleu(preds, [refs]).score

    results["bleu_text2gloss"] = bleu("text2gloss")
    results["bleu_gloss2text"] = bleu("gloss2text")
    print(f"  BLEU text->gloss: {results['bleu_text2gloss']}", flush=True)
    print(f"  BLEU gloss->text: {results['bleu_gloss2text']}", flush=True)
except Exception as e:
    print(f"  T5 eval failed: {e}", flush=True)
    results["bleu_text2gloss"] = results["bleu_gloss2text"] = None


# ---- ST-GCN CPU latency -----------------------------------------------------
print("STEP 4: ST-GCN CPU latency benchmark", flush=True)
ts_path = f"{OUT}/model.ts"
if os.path.exists(ts_path):
    m_cpu = torch.jit.load(ts_path, map_location="cpu").eval()
    rng = np.random.default_rng(0)
    clips = [torch.from_numpy(rng.standard_normal((1, 32, 1629)).astype(np.float32)) for _ in range(50)]
    for _ in range(3): m_cpu(clips[0])  # warm-up
    times = []
    for c in clips:
        t0 = time.perf_counter(); m_cpu(c); times.append((time.perf_counter() - t0) * 1000)
    arr = np.asarray(times)
    results["latency_p50"] = float(np.percentile(arr, 50))
    results["latency_p95"] = float(np.percentile(arr, 95))
    results["latency_p99"] = float(np.percentile(arr, 99))
    print(f"  p50={results['latency_p50']:.1f}ms  p95={results['latency_p95']:.1f}ms  p99={results['latency_p99']:.1f}ms", flush=True)
else:
    print("  skipped — model.ts missing", flush=True)
    results["latency_p50"] = results["latency_p95"] = results["latency_p99"] = None


# ---- write report -----------------------------------------------------------
print("STEP 5: writing RESULTS.md", flush=True)
md = []
md.append("# Project Results\n")
md.append(f"_Generated: {datetime.datetime.now().isoformat(timespec='minutes')}_\n\n")

md.append("## Isolated sign recognition (ST-GCN, WLASL-Top-300)\n\n")
if results["sthgcn_top1"] is not None:
    md.append(f"- Top-1 accuracy: **{results['sthgcn_top1']*100:.1f}%**\n")
    md.append(f"- Top-5 accuracy: **{results['sthgcn_top5']*100:.1f}%**\n")
    md.append(f"- Test clips: {results['sthgcn_n']}\n\n")
else:
    md.append("- *(not computed — ST-GCN model or test cache missing)*\n\n")

md.append("## Text ↔ Gloss (flan-T5-small)\n\n")
if results["bleu_text2gloss"] is not None:
    md.append(f"- BLEU-4 text → gloss: **{results['bleu_text2gloss']:.2f}**\n")
if results["bleu_gloss2text"] is not None:
    md.append(f"- BLEU-4 gloss → text: **{results['bleu_gloss2text']:.2f}**\n")
md.append("\n")

md.append("## CPU latency (ST-GCN, single clip, 32 frames)\n\n")
if results["latency_p50"] is not None:
    md.append(f"- p50: **{results['latency_p50']:.1f} ms**\n")
    md.append(f"- p95: **{results['latency_p95']:.1f} ms**\n")
    md.append(f"- p99: **{results['latency_p99']:.1f} ms**\n")
    md.append(f"- SLO (< 350 ms p95): **{'PASS' if results['latency_p95'] < 350 else 'FAIL'}**\n\n")
else:
    md.append("- *(skipped)*\n\n")

report = "".join(md)
out_file = f"{BASE}/docs/RESULTS.md"
open(out_file, "w").write(report)
print(report)
print(f"saved -> {out_file}", flush=True)
