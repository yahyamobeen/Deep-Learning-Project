"""Push trained ST-GCN to HuggingFace.

Uploads only: model.ts, encoder.onnx, labels.json
Skips Trainer-state files.
Falls back to personal namespace on 403.
"""
import os, sys

BASE   = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
HF_ORG = "sign-lang"
os.environ.setdefault("HF_TOKEN",
    os.environ.get("HF_TOKEN") or "hf_paste_your_token_here")

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import warnings; warnings.filterwarnings("ignore")

from huggingface_hub import HfApi, create_repo, login, whoami
from huggingface_hub.utils import HfHubHTTPError

login(token=os.environ["HF_TOKEN"], add_to_git_credential=False)
ME = whoami(token=os.environ["HF_TOKEN"])["name"]
print(f"Logged in as: {ME}", flush=True)

api = HfApi()
FOLDER = f"{BASE}/models/sthgcn_wlasl300"
SLUG   = "sthgcn-wlasl300"

def push(org):
    repo = f"{org}/{SLUG}"
    print(f"Pushing {FOLDER} -> {repo}", flush=True)
    create_repo(repo, repo_type="model", private=True, exist_ok=True,
                token=os.environ["HF_TOKEN"])
    api.upload_folder(
        folder_path=FOLDER, repo_id=repo, repo_type="model",
        allow_patterns=["model.ts", "encoder.onnx", "labels.json"],
        token=os.environ["HF_TOKEN"],
    )
    print(f"  pushed -> {repo}", flush=True)

# Sanity check
needed = ["model.ts", "encoder.onnx", "labels.json"]
missing = [f for f in needed if not os.path.exists(f"{FOLDER}/{f}")]
if missing:
    print(f"FATAL: missing files in {FOLDER}: {missing}", flush=True)
    sys.exit(1)

try:
    push(HF_ORG)
except HfHubHTTPError as e:
    code = e.response.status_code if e.response is not None else None
    if code in (401, 403):
        print(f"  cannot push to {HF_ORG} ({code}); falling back to {ME}", flush=True)
        push(ME)
    else:
        raise
print("all done", flush=True)
