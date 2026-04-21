# ClipForge — Video Content Pipeline

Upload a video → get transcript, Twitter thread, LinkedIn post, blog, and auto-cut shorts.

## Run locally (dev)

```bash
# 1. Copy env and fill in your keys
cp .env.example .env

# 2. Start everything
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
```

Required keys in `.env`:

- `AI_PROVIDER` — `anthropic` or `openai`
- `ANTHROPIC_API_KEY` — required when `AI_PROVIDER=anthropic`
- `OPENAI_API_KEY` — required when `AI_PROVIDER=openai`
- `ASSEMBLYAI_API_KEY` — transcription (free tier: 100 hours)
- `POSTGRES_PASSWORD` — any string (local only)

## Investor demo (easiest)

Use the built-in Cloudflare Quick Tunnel flow if you just need a temporary public demo link.

Prerequisites:

- Docker Desktop is running
- `.env` contains either `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, based on `AI_PROVIDER`
- `.env` contains `ASSEMBLYAI_API_KEY`

Start the demo:

```powershell
.\scripts\start-investor-demo.ps1
```

The script will:

- start the full app stack
- start a temporary Cloudflare tunnel
- stream the `cloudflared` logs until the public `https://...trycloudflare.com` URL appears

Stop the demo:

```powershell
.\scripts\stop-investor-demo.ps1
```

Notes:

- The tunnel URL changes every time you restart the demo.
- This is for short-lived demos only, not production hosting.
- The frontend now uses same-origin `/api` requests, so only the frontend needs to be exposed publicly for the investor demo.

## Deploy to a VPS (production)

```bash
# 1. SSH into your VPS (Ubuntu 22.04 recommended)
# 2. Install Docker + Docker Compose
# 3. Clone repo and fill in .env
git clone <repo>
cp .env.example .env
# Edit .env: set real keys, DOMAIN=yourdomain.com, STORAGE_TYPE=r2

# 4. Set your email in traefik/traefik.yml for Let's Encrypt

# 5. Start
docker-compose up -d --build
```

That's it. Traefik auto-issues SSL for your domain.

## Deploy to Railway (free demo)

Railway services do not share the `./storage` volume that Docker Compose uses locally.
For the free school-project deployment, use Postgres-backed storage instead of `local`
or R2:

- `clipforge-backend` — root directory `backend`, Dockerfile `backend/Dockerfile`
- `clipforge-worker` — same source as backend, with `SERVICE_TYPE=worker`
- `clipforge-frontend` — root directory `frontend`, Dockerfile `frontend/Dockerfile`
- `clipforge-db` — Railway Postgres
- `Redis` — Railway Redis

Set these variables on both backend and worker:

```env
STORAGE_TYPE=db
DATABASE_URL=${{clipforge-db.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
ASSEMBLYAI_API_KEY=...
SHOTSTACK_ENV=stage
MAX_FILE_SIZE_MB=50
MAX_SHORTS=3
```

To keep using Anthropic instead, set `AI_PROVIDER=anthropic` and
`ANTHROPIC_API_KEY=...` on both backend and worker.

Set this only on the backend:

```env
PORT=8000
```

Set this only on the worker:

```env
SERVICE_TYPE=worker
CELERY_CONCURRENCY=1
```

Set these on the frontend:

```env
NEXT_PUBLIC_API_URL=/api
INTERNAL_API_URL=http://${{clipforge-backend.RAILWAY_PRIVATE_DOMAIN}}:${{clipforge-backend.PORT}}
```

`NEXT_PUBLIC_API_URL=/api` keeps browser requests same-origin. The Next.js API and
storage route handlers proxy to `INTERNAL_API_URL` at runtime, so the frontend does
not need the public backend URL baked into the Docker image.

Railway troubleshooting:

- Job stuck at `queued`: the worker is not running, or backend and worker do not
  share the same `REDIS_URL`.
- Job fails before `cutting`: check the job error and backend/worker logs for
  missing `ASSEMBLYAI_API_KEY`, `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`, or storage
  misconfiguration.
- Job completes with no shorts: redeploy this version and inspect the job error.
  Shorts design provider failures are surfaced as processing errors instead of
  being hidden as an empty shorts list.
- Shorts exist but videos do not play: ensure backend and worker both use
  `STORAGE_TYPE=db`, and the frontend has `NEXT_PUBLIC_API_URL=/api` plus
  `INTERNAL_API_URL` pointing at the backend private domain.

## Deploy to Render

This repo is ready for Render deployment with production services for the frontend, backend, worker, database, and Redis.

Use the `render.yaml` blueprint in this repo to deploy:

- `clipforge-backend` — FastAPI backend web service
- `clipforge-worker` — Celery worker service
- `clipforge-frontend` — Next.js frontend web service
- `clipforge-db` — Render Postgres database
- `clipforge-redis` — Render Key Value (Redis-compatible) service

During deployment, set these secret environment variables in Render:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY` if `AI_PROVIDER=openai`
- `ASSEMBLYAI_API_KEY`
- `SHOTSTACK_API_KEY`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`

For production storage, keep these values:

- `STORAGE_TYPE=r2`
- `R2_BUCKET=video-pipeline`
- `R2_PUBLIC_URL=https://pub-xxx.r2.dev`

On Render, the frontend expects the backend API to be available at:

- `https://clipforge-backend.onrender.com/api`

## Switch to Cloudflare R2 (production storage)

In `.env`:

```
STORAGE_TYPE=r2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_key
R2_SECRET_ACCESS_KEY=your_secret
R2_BUCKET=video-pipeline
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

## AWS deployment with S3 storage

If you deploy on AWS, use S3 for file storage by setting:

```
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=video-pipeline
AWS_REGION=us-east-1
AWS_S3_PUBLIC_URL=https://video-pipeline.s3.amazonaws.com
```

`AWS_S3_PUBLIC_URL` is optional when your bucket is publicly accessible.

## Pipeline

```
Upload → Transcribe (AssemblyAI) → Generate posts (configured AI provider) → Score + cut shorts (FFmpeg)
```

Each step runs in a Celery worker. The frontend polls `/api/jobs/{id}` every 2.5s for status.
