"""Pull trained weights from HuggingFace into ./models/.

Run after the Victus has pushed each notebook's output. Idempotent — repeats
skip already-downloaded files. Set HF_ORG env var if you used the fallback
namespace (e.g. your username instead of the team org).

Usage:
    $env:HF_ORG = "sign-lang"          # or "YahyaMobeen" if fallback
    $env:HF_TOKEN = "hf_..."           # if not already a User env var
    python pull_weights.py
"""
import os
import shutil

from huggingface_hub import snapshot_download

ORG = os.environ.get("HF_ORG", "sign-lang")
TOKEN = os.environ.get("HF_TOKEN")

os.makedirs("models", exist_ok=True)

REPOS = [
    (f"{ORG}/sthgcn-wlasl300", "sthgcn_wlasl300"),
    (f"{ORG}/t5-text2gloss",   "t5_text2gloss"),
    (f"{ORG}/t5-gloss2text",   "gloss2text"),
    (f"{ORG}/sign-tutor-refs", "refs"),
]

for repo, sub in REPOS:
    dest = f"models/{sub}"
    print(f"Pulling {repo} -> {dest}")
    try:
        snapshot_download(
            repo_id=repo,
            local_dir=dest,
            local_dir_use_symlinks=False,
            token=TOKEN,
        )
        print(f"  OK")
    except Exception as e:
        print(f"  skipped ({type(e).__name__}: {e})")

# Promote reference_signs.json so tutor_scorer.py finds it.
refs_src = "models/refs/reference_signs.json"
if os.path.exists(refs_src):
    shutil.copy(refs_src, "models/reference_signs.json")
    print("copied reference_signs.json into models/")

print("\nDone. Restart uvicorn and you should see real backends loaded:")
print("  [SignRecognizer] mode=ensemble active=['pose']")
print("  [TextToGloss] backend = pytorch")
print("  [GlossToText] backend = pytorch")
