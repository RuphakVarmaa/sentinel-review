# Sentinel Review

LLM-powered code review platform. GitHub App + CI pipeline + public web dashboard.

**Live demo:** https://sentinel-review.vercel.app  
**API:** https://sentinel-review-api.railway.app/api/docs

---

## What it does

- **Public diff reviewer** — paste any unified diff at `/review`, get AI analysis in ~8 seconds
- **GitHub App** — installs on any repo, reviews every PR automatically with inline comments
- **CI integration** — GitHub Actions workflow that fails builds on critical findings
- **5 parallel LLM agents** — Security, Logic, Performance, Style, Maintainability
- **Shareable results** — every review gets a `/review/{share_id}` link (7 days)

---

## Quick start: CI integration

Add `.github/workflows/sentinel-review.yml` to your repo:

```yaml
name: Sentinel AI Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Get PR diff
        run: git diff origin/${{ github.base_ref }}...HEAD > pr.diff
      - name: Run Sentinel Review
        id: review
        env:
          SENTINEL_API_KEY: ${{ secrets.SENTINEL_API_KEY }}
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          PAYLOAD=$(jq -n --rawfile diff pr.diff --arg context "$PR_TITLE" --arg source "ci" \
            '{diff: $diff, context: $context, source: $source}')
          RESPONSE=$(curl -s -X POST \
            -H "Authorization: Bearer $SENTINEL_API_KEY" \
            -H "Content-Type: application/json" \
            -d "$PAYLOAD" \
            https://sentinel-review-api.railway.app/v1/review)
          echo "severity=$(echo $RESPONSE | jq -r .overall_severity)" >> $GITHUB_OUTPUT
          echo "critical=$(echo $RESPONSE | jq -r .finding_counts.critical)" >> $GITHUB_OUTPUT
      - name: Fail on critical findings
        if: steps.review.outputs.critical > 0
        run: exit 1
```

Set `SENTINEL_API_KEY` in your repo secrets (get one at `/dashboard`).

---

## GitHub App install

1. Go to https://github.com/apps/sentinel-review-app/installations/new
2. Select repositories to review
3. Open or update any PR — Sentinel posts a review automatically

---

## API

Base URL: `https://sentinel-review-api.railway.app`

```bash
# Submit a diff for review
curl -X POST https://sentinel-review-api.railway.app/v1/review \
  -H "Content-Type: application/json" \
  -d '{"diff": "...", "context": "Add OAuth login", "source": "api"}'

# Stream results via SSE
curl -X POST https://sentinel-review-api.railway.app/v1/review/stream \
  -H "Content-Type: application/json" \
  -d '{"diff": "..."}'
```

Interactive docs at `/api/docs`.

---

## Self-hosting

### Backend (Railway / Docker)

```bash
cd backend
cp .env.example .env
# Fill in OPENAI_API_KEY, DATABASE_URL, REDIS_URL, GITHUB_APP_* values

docker build -t sentinel-backend .
docker run -p 8000:8000 --env-file .env sentinel-backend
```

#### Required env vars

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` | GPT-4o access |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key (PEM) |
| `GITHUB_WEBHOOK_SECRET` | Webhook HMAC secret |
| `GITHUB_CLIENT_ID` | OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | OAuth app client secret |
| `JWT_SECRET` | Min 32 chars |

#### Database setup

```bash
psql $DATABASE_URL < backend/migrations/001_init.sql
```

### Frontend (Vercel)

```bash
cd frontend
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL to your backend URL

npm install
npm run dev
```

Deploy to Vercel:
```bash
vercel --prod
```

Set `NEXT_PUBLIC_API_URL` environment variable in Vercel project settings.

---

## GitHub App setup

1. Create a GitHub App at https://github.com/settings/apps/new
2. Set webhook URL to `https://your-backend.railway.app/webhook/github`
3. Subscribe to events: `Pull requests`
4. Set permissions: `Pull requests: Read & Write`
5. Generate and download a private key
6. Copy App ID and private key to your `.env`

---

## Architecture

```
┌──────────────────┐     ┌─────────────────────┐     ┌──────────────┐
│  Next.js 14      │────▶│  FastAPI Backend     │────▶│  GPT-4o      │
│  (Vercel)        │◀────│  (Railway)           │     │  (5 agents)  │
└──────────────────┘     └─────────────────────┘     └──────────────┘
                               │          │
                         ┌─────▼──┐  ┌───▼────┐
                         │ Postgres│  │ Redis  │
                         │ +pgvec  │  │ cache  │
                         └────────┘  └────────┘
```

Review pipeline:
1. Parse unified diff → structured hunks
2. Run 5 parallel LLM agents (asyncio.gather)
3. Deduplicate findings by title similarity
4. Stream results via SSE as each agent completes
5. Post inline GitHub PR comments (GitHub App path)
