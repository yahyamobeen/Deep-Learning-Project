"""Train flan-T5-small with a hand-rolled torch loop.
No transformers.Trainer / no accelerate — sidesteps DLL fights on Windows.
"""
import os, sys, random, gc, traceback, time
print("STEP 0: script started", flush=True)

BASE   = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
HF_ORG = "sign-lang"
os.environ.setdefault("HF_TOKEN",
    os.environ.get("HF_TOKEN") or "hf_paste_your_token_here")

os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import warnings
warnings.filterwarnings("ignore")

print("STEP 1: importing torch", flush=True)
import torch
print(f"STEP 2: torch {torch.__version__}", flush=True)
DEV = "cuda" if torch.cuda.is_available() else "cpu"
print(f"STEP 3: device = {DEV}", flush=True)

print("STEP 4: importing transformers", flush=True)
from transformers import AutoTokenizer, T5ForConditionalGeneration
print("STEP 5: transformers imported", flush=True)

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
] * 200

MODEL_NAME = "google/flan-t5-small"


def train_one(direction):
    print(f"\n=== {direction} ===", flush=True)
    out_dir = f"{BASE}/models/" + ("t5_text2gloss" if direction == "text2gloss" else "gloss2text")
    os.makedirs(out_dir, exist_ok=True)

    print("  loading tokenizer ...", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("  loading model ...", flush=True)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEV)
    print(f"  model params: {sum(p.numel() for p in model.parameters())/1e6:.1f}M", flush=True)

    if direction == "text2gloss":
        prefix = "translate English to ASL gloss: "
        pairs = [(prefix + e, g) for e, g in SEED_PAIRS]
    else:
        prefix = "translate ASL gloss to English: "
        pairs = [(prefix + g, e) for e, g in SEED_PAIRS]

    random.seed(42); random.shuffle(pairs)
    cut = int(0.95 * len(pairs))
    train_pairs, val_pairs = pairs[:cut], pairs[cut:]
    print(f"  train={len(train_pairs)}  val={len(val_pairs)}", flush=True)

    def encode_batch(batch_pairs):
        srcs = [p[0] for p in batch_pairs]
        tgts = [p[1] for p in batch_pairs]
        s = tok(srcs, max_length=32, padding="max_length", truncation=True, return_tensors="pt")
        with tok.as_target_tokenizer():
            t = tok(tgts, max_length=32, padding="max_length", truncation=True, return_tensors="pt")
        labels = t["input_ids"].clone()
        labels[labels == tok.pad_token_id] = -100
        return s["input_ids"].to(DEV), s["attention_mask"].to(DEV), labels.to(DEV)

    BATCH    = 4
    EPOCHS   = 2
    LR       = 3e-4
    ACCUM    = 4    # effective batch 16
    LOG_EVERY = 25

    opt    = torch.optim.AdamW(model.parameters(), lr=LR)
    n_steps = (len(train_pairs) // (BATCH * ACCUM)) * EPOCHS
    sched   = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(n_steps, 1))

    step = 0
    t_start = time.time()
    for epoch in range(EPOCHS):
        random.shuffle(train_pairs)
        opt.zero_grad()
        running = 0.0
        for i in range(0, len(train_pairs), BATCH):
            batch = train_pairs[i:i + BATCH]
            if len(batch) == 0:
                continue
            ids, mask, labels = encode_batch(batch)
            out = model(input_ids=ids, attention_mask=mask, labels=labels)
            loss = out.loss / ACCUM
            loss.backward()
            running += loss.item() * ACCUM

            if (i // BATCH + 1) % ACCUM == 0:
                opt.step()
                sched.step()
                opt.zero_grad()
                step += 1
                if step % LOG_EVERY == 0:
                    avg = running / (LOG_EVERY * ACCUM)
                    elapsed = time.time() - t_start
                    print(f"  epoch {epoch} step {step}/{n_steps} loss={avg:.3f}  ({elapsed:.0f}s)", flush=True)
                    running = 0.0

        # Eval at end of epoch
        model.eval()
        v_loss = 0.0; v_n = 0
        with torch.no_grad():
            for j in range(0, len(val_pairs), BATCH):
                vb = val_pairs[j:j + BATCH]
                if not vb: continue
                ids, mask, labels = encode_batch(vb)
                out = model(input_ids=ids, attention_mask=mask, labels=labels)
                v_loss += out.loss.item() * len(vb); v_n += len(vb)
        model.train()
        print(f"  epoch {epoch} done  val_loss={v_loss/max(v_n,1):.3f}", flush=True)

    print(f"  saving to {out_dir} ...", flush=True)
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    print(f"  saved -> {out_dir}", flush=True)

    # Quick generation test
    model.eval()
    test_inputs = pairs[:3]
    for src, ref in test_inputs:
        ids = tok(src, return_tensors="pt").input_ids.to(DEV)
        with torch.no_grad():
            gen = model.generate(ids, max_length=48, num_beams=4)
        print(f"    SRC: {src!r}", flush=True)
        print(f"    REF: {ref!r}", flush=True)
        print(f"    PRD: {tok.decode(gen[0], skip_special_tokens=True)!r}", flush=True)

    del model; gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()


directions = sys.argv[1:] if len(sys.argv) > 1 else ["text2gloss", "gloss2text"]
print(f"STEP 6: directions = {directions}", flush=True)

for d in directions:
    try:
        train_one(d)
    except Exception as e:
        print(f"FATAL in {d}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

print("STEP 7: all done", flush=True)
