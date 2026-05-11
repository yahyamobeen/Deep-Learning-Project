"""flan-T5-small trainer with verbose step logging + 6GB-friendly defaults."""
import os, sys, random, gc, traceback
print("STEP 0: script started", flush=True)

BASE   = r"C:\Users\Maleeha\Desktop\dl-project\local_runs"
HF_ORG = "sign-lang"
os.environ.setdefault("HF_TOKEN",
    os.environ.get("HF_TOKEN") or "hf_paste_your_token_here")

os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import warnings
warnings.filterwarnings("ignore")

print("STEP 1: imports starting", flush=True)
import torch
print("STEP 2: torch imported", flush=True)

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print(f"STEP 3: Device: {DEV}", flush=True)
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}  VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB", flush=True)

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


def train_direction(direction, pairs):
    print(f"  [td-1] entered train_direction({direction!r})", flush=True)

    from transformers import (AutoTokenizer, T5ForConditionalGeneration,
                              Seq2SeqTrainer, Seq2SeqTrainingArguments,
                              DataCollatorForSeq2Seq)
    from datasets import Dataset
    print(f"  [td-2] transformers imported", flush=True)

    out_dir = f"{BASE}/models/" + ("t5_text2gloss" if direction == "text2gloss" else "gloss2text")
    os.makedirs(out_dir, exist_ok=True)
    print(f"  [td-3] out_dir={out_dir}", flush=True)

    if direction == "text2gloss":
        prefix = "translate English to ASL gloss: "
        rows = [{"src": prefix + e, "tgt": g} for e, g in pairs]
    else:
        prefix = "translate ASL gloss to English: "
        rows = [{"src": prefix + g, "tgt": e} for e, g in pairs]

    random.seed(42)
    random.shuffle(rows)
    cut = int(0.95 * len(rows))
    train_ds = Dataset.from_list(rows[:cut])
    val_ds   = Dataset.from_list(rows[cut:])
    print(f"  [td-4] datasets built: train={len(train_ds)} val={len(val_ds)}", flush=True)

    MODEL = "google/flan-t5-small"
    print(f"  [td-5] loading tokenizer {MODEL} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    print(f"  [td-6] tokenizer ready", flush=True)

    def tokenize(b):
        s = tok(b["src"], max_length=32, padding="max_length", truncation=True)
        with tok.as_target_tokenizer():
            t = tok(b["tgt"], max_length=32, padding="max_length", truncation=True)
        s["labels"] = [
            [(x if x != tok.pad_token_id else -100) for x in seq]
            for seq in t["input_ids"]
        ]
        return s

    train_ds = train_ds.map(tokenize, batched=True, remove_columns=["src", "tgt"])
    val_ds   = val_ds.map(tokenize,   batched=True, remove_columns=["src", "tgt"])
    print(f"  [td-7] tokenization done", flush=True)

    print(f"  [td-8] loading model ...", flush=True)
    model = T5ForConditionalGeneration.from_pretrained(MODEL)
    print(f"  [td-9] model loaded, params={sum(p.numel() for p in model.parameters())/1e6:.1f}M", flush=True)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        before = torch.cuda.memory_allocated() / 1e6
        print(f"  [td-10] VRAM before train: {before:.0f} MB", flush=True)

    # 6GB-friendly config: batch 2 + accum 8, max_len 32, fp16 OFF (fp32 sidesteps a known T5 fp16 nan bug)
    args = Seq2SeqTrainingArguments(
        output_dir                  = out_dir,
        num_train_epochs            = 2,
        per_device_train_batch_size = 2,
        per_device_eval_batch_size  = 2,
        gradient_accumulation_steps = 8,
        learning_rate               = 3e-4,
        warmup_ratio                = 0.05,
        lr_scheduler_type           = "cosine",
        fp16                        = False,          # T5 + fp16 sometimes NaNs on small GPUs
        eval_strategy               = "epoch",
        save_strategy               = "epoch",
        save_total_limit            = 1,
        load_best_model_at_end      = True,
        predict_with_generate       = True,
        logging_steps               = 25,
        report_to                   = "none",
        seed                        = 42,
        dataloader_pin_memory       = False,
    )
    print(f"  [td-11] TrainingArguments built", flush=True)

    collator = DataCollatorForSeq2Seq(tok, model=model)
    trainer = Seq2SeqTrainer(
        model=model, args=args,
        train_dataset=train_ds, eval_dataset=val_ds,
        data_collator=collator, tokenizer=tok,
    )
    print(f"  [td-12] Trainer built. starting trainer.train() ...", flush=True)

    try:
        trainer.train()
    except Exception as e:
        print(f"  [td-ERR] trainer.train() raised: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        raise

    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)
    print(f"  [td-13] saved -> {out_dir}", flush=True)

    del model, trainer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


print("STEP 4: pair count =", len(SEED_PAIRS), flush=True)
DIRECTIONS = sys.argv[1:] if len(sys.argv) > 1 else ["text2gloss", "gloss2text"]
print(f"STEP 5: directions = {DIRECTIONS}", flush=True)

for _d in DIRECTIONS:
    print(f"STEP 6: starting {_d}", flush=True)
    try:
        train_direction(_d, SEED_PAIRS)
    except Exception as e:
        print(f"FATAL in {_d}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

print("STEP 7: all done", flush=True)
