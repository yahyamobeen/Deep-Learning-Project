# Deployment (Free-tier)

Same architecture as local dev, just split across free tiers:

| Component | Hosted on | Free-tier limit | Sleeps? |
|---|---|---|---|
| `ml-service` (FastAPI) | **Hugging Face Spaces** (Docker, CPU 16 GB) | 50 GB disk | After 48 h idle |
| `gateway` (Node/Express) | **Render** Web Service | 512 MB RAM | After 15 min idle |
| `frontend` (Next.js) | **Vercel** | unlimited static | No |
| Postgres | **Neon** | 0.5 GB | No |
| Mobile distribution | **Firebase App Distribution** | 100 testers | n/a |
| Uptime pings | **UptimeRobot** | 50 monitors free | n/a |

## 0. Before you start

- Push the repo to GitHub (one shared repo for the whole team).
- Have an HF org (`sign-lang`) with the trained-weight repos already pushed (see notebooks 03 + 05).

## 1. Deploy `ml-service` to Hugging Face Spaces

1. **Create the Space**
   - https://huggingface.co/new-space
   - Owner: `sign-lang` (the org). Name: `ml`. SDK: **Docker**.
   - Hardware: `cpu-basic` (free, 16 GB).
2. **Push the contents of `ml-service/` to the Space repo.** Two ways:
   - **Sync from GitHub**: Space → Settings → "Linked repository" → connect your GitHub repo, set the subdirectory to `ml-service`. Then add `Dockerfile.spaces` as the active Dockerfile by copying it to `Dockerfile` in the linked branch — or set the build to use it explicitly.
   - **Manual push**:
     ```
     git clone https://huggingface.co/spaces/sign-lang/ml hf-ml
     cp -r ml-service/* hf-ml/
     cp ml-service/Dockerfile.spaces hf-ml/Dockerfile
     cd hf-ml && git add . && git commit -m "Initial deploy" && git push
     ```
3. **Set Space secrets** (Settings → Variables and secrets):
   ```
   HF_TOKEN         = hf_xxx        # your write-enabled HF token
   HF_REPO_STHGCN   = sign-lang/sthgcn-wlasl300
   HF_REPO_T5_T2G   = sign-lang/t5-text2gloss
   HF_REPO_T5_G2T   = sign-lang/t5-gloss2text
   HF_REPO_REFS     = sign-lang/sign-tutor-refs
   ALLOWED_ORIGINS  = https://your-frontend.vercel.app,https://your-gateway.onrender.com
   ```
   Optional: `HF_REPO_MOVINET` for the RGB fallback.
4. **Wait for the build** (~5 min). When it goes green, hit:
   `curl https://sign-lang-ml.hf.space/health` → `{"status":"ok"}`.

## 2. Deploy `gateway` to Render

1. https://render.com → New → Web Service → connect GitHub repo → root `gateway/`.
2. Build command: `npm install`. Start command: `npm start`.
3. Env:
   ```
   JWT_SECRET     = <openssl rand -hex 32>
   DATABASE_URL   = postgres://... (from Neon)
   ML_SERVICE_URL = https://sign-lang-ml.hf.space
   PORT           = 4000
   ```
4. After it goes green, hit `https://your-gateway.onrender.com/health`.

## 3. Deploy `frontend` to Vercel

1. https://vercel.com → New Project → import GitHub repo → root `frontend/`.
2. Vercel auto-detects Next.js. No build overrides needed.
3. Env:
   ```
   NEXT_PUBLIC_GATEWAY_URL = https://your-gateway.onrender.com
   ```

## 4. Provision Postgres on Neon

1. https://neon.tech → New Project → copy the **pooled** connection string.
2. Paste it into Render env (`DATABASE_URL`). Restart the gateway.

## 5. Wire mobile to the deployed gateway

Edit `mobile/.env`:
```
GATEWAY_URL=https://your-gateway.onrender.com
```
Rebuild APK (`flutter build apk --release`) and redistribute via Firebase
(see `docs/MOBILE_RELEASE.md`).

## 6. Keep things awake (UptimeRobot)

1. https://uptimerobot.com → free account.
2. Create 3 HTTP monitors, each pinging `/health`:
   - `https://sign-lang-ml.hf.space/health` (every 5 min)
   - `https://your-gateway.onrender.com/health` (every 5 min)
   - `https://your-frontend.vercel.app/` (every 30 min — unimportant, doesn't sleep)
3. Email yourself on downtime.

**Demo-day rule:** turn the pings ON 24 h before viva. Cold-start after a 48 h
sleep is ~30 s on HF Spaces — you do not want that mid-presentation.

## 7. Smoke tests after deployment

```
curl https://sign-lang-ml.hf.space/health
curl https://your-gateway.onrender.com/health
curl -X POST https://your-gateway.onrender.com/api/translate/text-to-sign \
     -H 'Content-Type: application/json' \
     -d '{"text":"i am hungry"}'
```
Expected response: `{"gloss":["I","HUNGRY"], "clips":[...]}`.

## 8. Rollback

- HF Spaces and Render both keep deploy history. Promote a previous commit
  via the dashboard. No CLI surgery needed.
- Mobile: keep the previous APK around. Redistribute via Firebase if the
  current build is broken.
