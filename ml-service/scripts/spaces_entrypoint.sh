#!/usr/bin/env bash
# Entrypoint for the Hugging Face Spaces container.
# Pulls checkpoints from the project HF org (if HF_REPO_* env vars are set)
# and then starts uvicorn on the port HF Spaces expects.
set -euo pipefail

MODELS_DIR=/app/models
mkdir -p "$MODELS_DIR"

pull() {
  local repo="$1"; local target="$2"
  if [ -z "$repo" ]; then return 0; fi
  if [ -d "$target" ] && [ -n "$(ls -A "$target" 2>/dev/null || true)" ]; then
    echo "[entrypoint] $target already populated; skipping $repo."
    return 0
  fi
  echo "[entrypoint] downloading $repo -> $target"
  python - <<PY
from huggingface_hub import snapshot_download
import os
snapshot_download(repo_id="${repo}", local_dir="${target}",
                  local_dir_use_symlinks=False,
                  token=os.environ.get("HF_TOKEN"))
PY
}

# Optional repos (set as Space secrets/env). Leave unset to skip and run DUMMY.
pull "${HF_REPO_STHGCN:-}"   "$MODELS_DIR/sthgcn_wlasl300"
pull "${HF_REPO_MOVINET:-}"  "$MODELS_DIR/movinet_a0_wlasl300"
pull "${HF_REPO_T5_T2G:-}"   "$MODELS_DIR/t5_text2gloss"
pull "${HF_REPO_T5_G2T:-}"   "$MODELS_DIR/gloss2text"
pull "${HF_REPO_REFS:-}"     "$MODELS_DIR/refs"
if [ -f "$MODELS_DIR/refs/reference_signs.json" ]; then
  cp "$MODELS_DIR/refs/reference_signs.json" "$MODELS_DIR/reference_signs.json"
fi

PORT="${PORT:-7860}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
