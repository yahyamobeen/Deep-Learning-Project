# Compute Playbook (Free-tier survival)

We have **no personal GPU**. Every GPU minute lives on a free cloud tier. This
playbook tells you which tier to use, in what order, and how to recover when
one fails.

## 1. The compute ladder

| Tier | Free quota | Session length | Use it for |
|---|---|---|---|
| **Colab Free** (T4) | ~12 h/day soft cap | up to 12 h, can disconnect | Default for jobs <2 h |
| **Kaggle Notebooks** (P100 / T4 ×2) | **30 GPU h/week** | 9 h hard, no random disconnects | Any job >2 h, especially overnight |
| **Lightning AI Studio** (T4) | 22 GPU h/month | persistent storage | Long fine-tunes when Colab T4 is busy |
| **HuggingFace AutoTrain** | small free quota | managed | No-code fallback |
| **Google Cloud free trial** | $300 / 90 days | flexible | **Last resort** |

**Single-account budget:** 1 Google account (~12 h/day Colab T4 soft cap) + 1 Kaggle account (30 GPU h/week, 9-h sessions). That is enough for the full pipeline if you follow §4 (every notebook checkpoints per epoch and pushes to HF, so a kernel death never wipes a run).

## 2. Decision tree

```
Need to train?
│
├── ETA < 1 h?       → Colab Free.
│                      If "no GPU available" → switch to Kaggle.
├── ETA 1–3 h?       → Kaggle (no disconnects).
│                      If quota empty → Lightning AI.
├── ETA > 3 h?       → Either split into <2 h resumable chunks on Colab,
│                      OR run as one 9-h Kaggle session overnight.
└── Won't fit on T4? → You picked the wrong model. Do not pay for GPU.
```

## 3. Day-0 account checklist (week 1)

- [ ] **One** Google account → Colab Free
- [ ] **One** Kaggle account, phone-verified → 30 GPU h/week (backup for jobs > 2 h)
- [ ] HuggingFace account → create org `uet-signlang` (all weights + datasets push here)
- [ ] HuggingFace token (write access) — https://huggingface.co/settings/tokens
- [ ] Lightning AI free account (optional fallback)
- [ ] GitHub Student Developer Pack — apply with `.edu` email (3–5 days)
- [ ] Render, Vercel, Neon, Firebase, UptimeRobot
- [ ] Android Studio + Flutter SDK on the laptop you'll build the APK from

## 4. Single-account scheduling (week-by-week)

Because you have only **one** Colab + **one** Kaggle account, plan training across days
so you never burn both quotas in 24 h:

| Day | Notebook | Where | Time | Rationale |
|---|---|---|---|---|
| Mon | `01_load_dataset.ipynb`            | Colab CPU         | ~10 min | No GPU needed |
| Tue | `02_build_tutor_references.ipynb`  | Colab T4          | ~15 min | Short, fits Colab daily cap |
| Wed | `03_finetune_sthgcn.ipynb`         | Colab T4          | ~45 min | One run, save Kaggle for the long jobs |
| Fri | `05_finetune_flan_t5_text2gloss.ipynb` | **Kaggle** P100/T4×2 | ~60 min | 9-h hard limit, no random disconnects |
| Sat | `06_evaluate.ipynb`                | Colab T4          | ~20 min | Final numbers, then push results |

If Colab gives you "no GPU available" today, **switch the same notebook to Kaggle** —
the code is identical, only the first cell (Drive mount) needs to change to use
`/kaggle/working/` instead.

## 5. Colab survival rules

Write these into the **first cell** of every notebook:

1. Mount Drive, `cd /content/drive/MyDrive/dl_project`. Never write to `/content/` — dies with kernel.
2. `save_strategy='epoch'`, `save_total_limit=2`, `load_best_model_at_end=True`.
3. End every training cell with `trainer.train(resume_from_checkpoint=True)` (works even on first run).
4. After each epoch, `huggingface_hub.upload_folder(...)` — your real backup.
5. `fp16=True` on T4. Never `bf16`.
6. Effective batch via accumulation: real batch 4 × `gradient_accumulation_steps=8`.
7. `seed=42` so resumes are deterministic.

## 6. Kaggle quick-start

1. kaggle.com → New Notebook → Settings → Accelerator: **GPU T4 ×2** → Internet: **On**.
2. Import the same `.ipynb` from `training/`.
3. Add Drive mounting alternative: `/kaggle/working/` is the persistent path; the equivalent of HF push is identical.
4. Run; the 9-hour hard limit is plenty for any single notebook.

## 7. When everything is down

- **Mid-training**: every notebook checkpoints to Drive AND pushes to HF after each epoch. Resume tomorrow.
- **Demo day**: pre-recorded **2-min screen video** of the working app on a USB stick.
- **HF Spaces sleeping**: UptimeRobot ping `/health` every 5 minutes for 24 h before viva.

## 8. What never to do

- Do **not** pay for Colab Pro. The free tier is enough if you follow §4.
- Do **not** train on a CPU. If GPU is unavailable today, wait.
- Do **not** push checkpoints over 1 GB to HF — quantize / export ONNX first.
- Do **not** keep weights on Drive only — Drive 15 GB fills fast; HF org is unlimited storage for model repos.
