"""Push the two trained flan-T5 directories to HuggingFace.

Run from PowerShell with the venv active, in the training/ folder:

    python push_t5.py                # pushes both directions
    python push_t5.py text2gloss     # only one
    python push_t5.py gloss2text

Tries the `sign-lang` org first; if the token can't push there, falls back
to your personal namespace automatically.
"""
import os, sys

BASE   = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
HF_ORG = "sign-lang"

os.environ.setdefault("HF_TOKEN",
    os.environ.get("HF_TOKEN") or "hf_paste_your_token_here")

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import warnings
warnings.filterwarnings("ignore")

from huggingface_hub import HfApi, create_repo, login, whoami
from huggingface_hub.utils import HfHubHTTPError

login(token=os.environ["HF_TOKEN"], add_to_git_credential=False)
ME = whoami(token=os.environ["HF_TOKEN"])["name"]
print(f"Logged in as: {ME}", flush=True)

api = HfApi()


def push(folder, slug, org):
    repo = f"{org}/{slug}"
    print(f"Pushing {folder} -> {repo}", flush=True)
    create_repo(repo, repo_type="model", private=True, exist_ok=True,
                token=os.environ["HF_TOKEN"])
    api.upload_folder(
        folder_path=folder, repo_id=repo, repo_type="model",
        ignore_patterns=["checkpoint-*", "*.bin.index.json", "optimizer.pt", "scheduler.pt"],
        token=os.environ["HF_TOKEN"],
    )
    print(f"  pushed -> {repo}", flush=True)
    return repo


def push_with_fallback(folder, slug):
    if not os.path.isdir(folder) or not os.path.exists(f"{folder}/config.json"):
        print(f"  SKIP {folder}: not a trained model dir (config.json missing)", flush=True)
        return None
    try:
        return push(folder, slug, HF_ORG)
    except HfHubHTTPError as e:
        code = e.response.status_code if e.response is not None else None
        if code in (401, 403):
            print(f"  cannot push to {HF_ORG} ({code}); falling back to {ME}", flush=True)
            return push(folder, slug, ME)
        raise


SLUG = {
    "text2gloss": ("t5_text2gloss",  "t5-text2gloss"),
    "gloss2text": ("gloss2text",     "t5-gloss2text"),
}

if __name__ == "__main__":
    directions = sys.argv[1:] if len(sys.argv) > 1 else ["text2gloss", "gloss2text"]
    for d in directions:
        if d not in SLUG:
            print(f"unknown direction: {d}", flush=True); continue
        local_subdir, repo_slug = SLUG[d]
        push_with_fallback(f"{BASE}/models/{local_subdir}", repo_slug)
    print("all done", flush=True)
