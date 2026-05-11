# Training Notebooks (Colab Free / Kaggle)

English-only ASL pipeline. **Pretrained-first**, fine-tuned with parameter-efficient
recipes that fit a single T4 (16 GB) on the free tier.

## Model lineage (post-rewrite)

| Module | Backbone | Fine-tune target | Notebook |
|---|---|---|---|
| Sign → Gloss (pose) | OpenHands ST-GCN (WLASL2000-pretrained) | WLASL-Top-300 head | `03_finetune_sthgcn.ipynb` |
| Sign → Gloss (RGB fallback, optional) | MoViNet-A0 (Kinetics-600) | WLASL-Top-300 via LoRA | `04_finetune_movinet_lora.ipynb` |
| Text ↔ Gloss | flan-T5-small | ASLG-PC12 → How2Sign CSV | `05_finetune_flan_t5_text2gloss.ipynb` |
| Speech → Text | `openai/whisper-base.en` | _(no fine-tune)_ | n/a |

## Open in Colab

1. https://colab.research.google.com → File → Upload notebook → pick the `.ipynb`
2. Runtime → Change runtime type → **T4 GPU**
3. The first cell mounts Google Drive — all artefacts persist in `/content/drive/MyDrive/dl_project/`.
4. After each successful epoch the notebook also pushes to your private HF org
   so a Colab disconnect never wipes a run.

## Run order

| # | Notebook | GPU? | Wall-time on T4 | Output |
|---|---|---|---|---|
| 1 | `01_load_dataset.ipynb`                  | No     | ~10 min  | `wlasl_top300_*` splits, `gloss_vocab.json` |
| 2 | `02_build_tutor_references.ipynb`        | T4     | ~15 min  | `reference_signs.json` (landmarks **+** ST-GCN embeddings) |
| 3 | `03_finetune_sthgcn.ipynb`               | **T4** | ~45 min  | `sthgcn_wlasl300/` (model.ts + encoder.onnx + labels.json) |
| 4 | `04_finetune_movinet_lora.ipynb` *(opt)* | T4     | ~90 min  | `movinet_a0_wlasl300/` |
| 5 | `05_finetune_flan_t5_text2gloss.ipynb`   | T4     | ~60 min  | `t5_text2gloss/` + `gloss2text/` (with int8 ONNX) |
| 6 | `06_evaluate.ipynb`                      | T4     | ~20 min  | `docs/RESULTS.md` |

## Pull the trained weights into `ml-service/models/`

The deployed `ml-service` (HF Spaces) calls the `spaces_entrypoint.sh` script
to fetch the following repos at container start. Set them as Space secrets:

```
HF_REPO_STHGCN  = uet-signlang/sthgcn-wlasl300
HF_REPO_MOVINET = uet-signlang/movinet-a0-wlasl300   # optional
HF_REPO_T5_T2G  = uet-signlang/t5-text2gloss
HF_REPO_T5_G2T  = uet-signlang/t5-gloss2text
HF_REPO_REFS    = uet-signlang/sign-tutor-refs
HF_TOKEN        = hf_xxx
```

For local dev, just download these folders manually into `ml-service/models/`
or run `python -c "from huggingface_hub import snapshot_download; ..."`.

## Compute survival rules (Colab Free)

1. Always mount Drive first; `cd /content/drive/MyDrive/dl_project/`.
2. `save_strategy='epoch'` + `save_total_limit=2` + `load_best_model_at_end=True`.
3. Add `trainer.train(resume_from_checkpoint=True)` so reconnects pick up where they left off.
4. After each epoch, `huggingface_hub.upload_folder(...)` the output dir.
5. `fp16=True`, never `bf16` (T4 doesn't support it).
6. `seed=42` so resumes are deterministic.

If Colab is unavailable, switch to **Kaggle Notebooks** (30 GPU h/week,
no random disconnects) — same code, just upload the `.ipynb` and add a
Kaggle "Internet On" + "GPU" runtime. Use Kaggle for the longest job (notebook 5).

## Required env

- `HF_TOKEN` — https://huggingface.co/settings/tokens (needs `write` to push).
