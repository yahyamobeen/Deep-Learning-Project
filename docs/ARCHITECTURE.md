# System Architecture

```
┌────────────────────┐  HTTPS/WS  ┌────────────────────┐  HTTP   ┌────────────────────┐
│  Frontend (Next.js)│ ─────────► │ Gateway (Node/Expr)│ ──────► │ ML Service (FastAPI│
│  • Webcam          │            │  • Auth (JWT)      │         │  • ST-GCN sign rec.│
│  • 3D avatar       │ ◄───────── │  • Lessons/progress│ ◄────── │  • flan-T5 text↔gl │
│  • Lessons UI      │            │  • Proxy to ML     │         │  • Whisper-base.en │
└────────────────────┘            └────────────────────┘         │  • DTW tutor scorer│
                                          │                      └────────────────────┘
┌────────────────────┐                    │                              │
│  Mobile (Flutter)  │ ───────────────────┘                              ▼
│  • Camera/audio    │                                          ┌────────────────────┐
│  • Same REST API   │                                   ┌──────│  Model artefacts   │
└────────────────────┘                                   │      │  pulled at startup │
                                                         │      │  from HF org       │
                                          ┌──────────────┘      └────────────────────┘
                                          ▼
                                   ┌──────────┐
                                   │ Postgres │
                                   │  users   │
                                   │ progress │
                                   └──────────┘
```

## Request flows

### Sign → English Text
1. Browser / phone captures a 3-second clip (WebM / MP4).
2. POST `/api/translate/sign-to-text` → gateway → FastAPI.
3. FastAPI samples 32 frames, extracts MediaPipe landmarks, runs ST-GCN.
4. The predicted gloss is fed into `gloss_to_text` (flan-T5 or rule-based) to
   produce a natural English sentence.
5. Returns `{gloss, sentence, confidence, top5}`.

### English Text → Sign
1. POST `/api/translate/text-to-sign` with `{text}`.
2. FastAPI runs `text_to_gloss` (flan-T5 or rule-based) → gloss tokens.
3. Returns gloss tokens + clip URLs for the playback library.
4. Client either plays the clips or animates the 3D avatar.

### English Speech → Sign
1. Mic audio → Whisper-base.en (in FastAPI) → English text → Text→Sign pipeline.

### Tutor scoring
1. User watches the reference video → records own attempt.
2. POST `/api/tutor/score` → FastAPI extracts MediaPipe landmarks.
3. Score = 0.6 · DTW-channel + 0.4 · ST-GCN-encoder cosine. Falls back to
   pure DTW if the encoder isn't loaded.
4. Returns `{score, hint, passed}`.

## Two-stage Sign Recognizer

`ml-service/app/inference/sign_recognizer.py` runs the pose stream first; if
its top-1 confidence is below `POSE_CONFIDENCE_THRESHOLD` (default 0.6) **or**
fewer than 8 hand landmarks were detected, it falls back to the MoViNet RGB
path. Mode is controlled by `SIGN_RECOGNIZER_MODE = pose | rgb | ensemble`.

## Where things run

| Component | Local dev | Production |
|---|---|---|
| Training | n/a (CPU laptops) | **Google Colab Free** (T4) + **Kaggle** backup |
| ML inference | `uvicorn` on laptop | **Hugging Face Spaces** (CPU 16 GB) |
| Gateway | `npm run dev` | **Render** Web Service |
| Frontend | `npm run dev` | **Vercel** |
| Database | local Postgres / Docker | **Neon** |
| Mobile | Android emulator / USB phone | **Firebase App Distribution** APK |

## Foolproof defaults

Every inference module supports a **DUMMY mode** when its checkpoint folder is
empty — it returns a stable shape so the UI and mobile app can be developed
against an empty `models/` directory. The `pytest tests/test_dummy_mode.py`
suite locks the contract.
