# Sign Language Translator & Tutor (English ASL)

Pretrained-first deep-learning project — **bi-directional ASL ↔ English translation
(Sign ↔ Text ↔ Speech)** plus an interactive sign-language tutor. Web app + Flutter
mobile app, all on free-tier infrastructure (no personal GPU required).

## Repository layout

```
dl project/
├── training/        # Colab notebooks — fine-tuning recipes (run on free T4 / Kaggle)
├── ml-service/      # FastAPI inference service (Python) — deploys to HF Spaces
├── gateway/         # Node.js + Express API gateway (auth, sessions, lessons)
├── frontend/        # Next.js web app (webcam, 3D avatar, lessons)
├── mobile/          # Flutter mobile app (Android first, iOS optional)
├── docs/            # Architecture, deployment, mobile release, compute playbook
├── .github/workflows/ # Free GitHub Actions CI
└── docker-compose.yml
```

## Three flows + tutor

| Flow | Pipeline |
|---|---|
| **Sign → English Text** | webcam clip → MediaPipe landmarks → ST-GCN → gloss → flan-T5 → English sentence |
| **English Text → Sign** | text → flan-T5 (or rule-based fallback) → gloss → clip library / 3D avatar |
| **English Speech → Sign** | mic → Whisper-base.en → text → Text→Sign pipeline |
| **Tutor** | record sign → MediaPipe + ST-GCN encoder → DTW + cosine vs reference → 0–100 + hint |

## Pretrained backbones (no model trained from scratch)

| Module | Backbone | Where it's fine-tuned | Final size |
|---|---|---|---|
| Sign → Gloss (pose) | OpenHands ST-GCN (pre-trained on WLASL2000) | WLASL-Top-300 | ~3 MB |
| Sign → Gloss (RGB fallback, optional) | MoViNet-A0 (Kinetics-600) | WLASL-Top-300 via LoRA | ~12 MB |
| Text ↔ Gloss | google/flan-t5-small | ASLG-PC12 → How2Sign CSV (int8 ONNX) | ~60 MB |
| Speech → Text | openai/whisper-base.en | _(no fine-tune)_ | ~290 MB |

Total shipped weight footprint **~360 MB** — fits HF Spaces free CPU 16 GB.

## Where things run (free tier)

| Component | Hosted on | Notes |
|---|---|---|
| ML service | **Hugging Face Spaces** (Docker, CPU 16 GB) | sleeps after 48 h — UptimeRobot ping keeps it warm |
| Gateway | **Render** Web Service | sleeps after 15 min |
| Web frontend | **Vercel** | static + serverless, no sleep |
| Postgres | **Neon** | 0.5 GB free, no sleep |
| Mobile distribution | **Firebase App Distribution** | up to 100 testers free |
| Training | **Google Colab Free** + **Kaggle Notebooks** (30 GPU h/wk) | see `docs/COMPUTE_PLAYBOOK.md` |

## Quick start (local dev)

### 1. Backend
```
cd ml-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # DUMMY mode if no models present
```

### 2. Gateway + frontend
```
cd gateway   && npm install && npm run dev   # port 4000
cd frontend  && npm install && npm run dev   # port 3000
```

Or `docker-compose up` for all three.

### 3. Mobile (Flutter)
```
cd mobile
copy .env.example .env       # edit GATEWAY_URL
flutter pub get
flutter run                  # picks up an emulator or USB phone
```

## Running the training pipeline

You have **two equivalent paths** — pick whichever fits your machine:

### Option A — Colab Free notebooks (no local GPU)
Open each `.ipynb` in https://colab.research.google.com → Runtime: T4 GPU.
1. `01_load_dataset.ipynb` (WLASL top-300, ~10 min CPU)
2. `02_build_tutor_references.ipynb` (~15 min T4)
3. `03_finetune_sthgcn.ipynb` (~45 min T4)
4. `04_finetune_movinet_lora.ipynb` *(optional)*
5. `05_finetune_flan_t5_text2gloss.ipynb` (~60 min T4)
6. `06_evaluate.ipynb` (~20 min T4 — produces `docs/RESULTS.md`)

### Option B — Standalone Python scripts (local NVIDIA GPU)
Run from PowerShell with the venv active, inside `training/`:
```
python extract_landmarks.py        # ~3 h CPU — caches MediaPipe landmarks
python train_sthgcn.py             # ~45 min on RTX 4050 — trains sign recognizer
python push_sthgcn.py              # uploads to HF org
python train_t5_manual.py          # ~10 min — text↔gloss (avoids Trainer DLL issues)
python push_t5.py                  # uploads
python build_references.py         # ~5 min — tutor references
python evaluate.py                 # ~5 min — writes docs/RESULTS.md
```

After training, all weights are pushed to your HF org. The HF Spaces container
pulls them at startup via `ml-service/scripts/spaces_entrypoint.sh`. The dev
laptop pulls them via `python ml-service/pull_weights.py`.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system diagram + request flows
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — step-by-step free-tier deployment
- [`docs/MOBILE_RELEASE.md`](docs/MOBILE_RELEASE.md) — Flutter → APK → Firebase
- [`docs/COMPUTE_PLAYBOOK.md`](docs/COMPUTE_PLAYBOOK.md) — Colab/Kaggle survival
- [`docs/RESULTS.md`](docs/RESULTS.md) — eval numbers (auto-filled by notebook 06)
- [`docs/POSTGRES_SETUP.md`](docs/POSTGRES_SETUP.md) — local Postgres / Neon
- [`mobile/README.md`](mobile/README.md) — Flutter dev workflow
- [`training/README.md`](training/README.md) — model lineage, notebook order

## Group

- BSDSF23A019 — Osairum Ahmad Khan
- BSDSF23A026 — Mujtaba Asad
- BSDSF23A036 — Abdul Muneeb Khurrum
- BSDSF23A039 — Yahya Mobeen

Instructor: Prof. Dr. Kamran Malik
