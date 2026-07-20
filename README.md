# Sentinel Review

LLM-powered code review platform. GitHub App + CI pipeline + public web dashboard.

---

## Live URLs

| Surface | URL | Status |
|---------|-----|--------|
| **Sentinel Review (Dashboard)** | https://frontend-nu-three-92.vercel.app | ✅ Live |
| **Sentinel Review (stable alias)** | https://frontend-ruphakvarmaas-projects.vercel.app | ✅ Live |
| **GitHub Repo** | https://github.com/RuphakVarmaa/sentinel-review | ✅ Public |
| **Backend API** | Deploy needed (see below) | ⏳ Pending |

### Other projects also on Vercel

| Project | URL |
|---------|-----|
| CV Analytics Platform | https://cv-analytics-platform.vercel.app |
| StyleHub Fashion | https://stylehub-fashion.vercel.app |
| Trendwear Fashion | https://trendwear-fashion.vercel.app |
| Shopify Store | https://shopify-store-six-rho.vercel.app |
| AI Cybersec SOC | https://ai-cybersec-soc.vercel.app |
| Axiom Code | https://axiom-code-ruphakvarmaas-projects.vercel.app |

---

## What Sentinel Review does

- **Public diff reviewer** — paste any unified diff at `/review`, get AI analysis in ~8s
- **GitHub App** — installs on any repo, reviews every PR automatically with inline comments
- **CI integration** — GitHub Actions workflow that fails builds on critical findings
- **5 parallel LLM agents** — Security, Logic, Performance, Style, Maintainability
- **Claude Sonnet 4.6 + Haiku** via AWS Bedrock (no OpenAI dependency)
- **Shareable results** — every review gets a `/review/{share_id}` link (7 days)

---

## Deploy the backend (one-time setup)

The frontend is live but needs a backend to run reviews. Quickest free option:

### Option A — Render (free tier)
1. Go to https://render.com → New → Web Service
2. Connect GitHub → select `RuphakVarmaa/sentinel-review`
3. Set **Root Directory** to `backend`
4. Add env vars:
   ```
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   JWT_SECRET=any-32-char-string
   GITHUB_WEBHOOK_SECRET=any-random-string
   ```
5. Copy the Render URL, then run:
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production --scope ruphakvarmaas-projects
   # paste: https://sentinel-review-api.onrender.com
   vercel --prod --yes --scope ruphakvarmaas-projects
   ```

### Option B — Run locally + expose via ngrok
```bash
cd "/Users/ruphakvarmaa/Documents/Claude Code/sentinel-review/backend"
pip install -r requirements.txt
AWS_ACCESS_KEY_ID=your_key AWS_SECRET_ACCESS_KEY=your_secret uvicorn app.main:app --reload --port 8000
# In another terminal: ngrok http 8000
```

---

## CI integration (copy-paste ready)

Add `.github/workflows/sentinel-review.yml` to any repo:

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
            https://your-backend-url/v1/review)
          echo "severity=$(echo $RESPONSE | jq -r .overall_severity)" >> $GITHUB_OUTPUT
          echo "critical=$(echo $RESPONSE | jq -r .finding_counts.critical)" >> $GITHUB_OUTPUT
      - name: Fail on critical findings
        if: steps.review.outputs.critical > 0
        run: exit 1
```

---

## Architecture

```
┌──────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  Next.js 14      │────▶│  FastAPI Backend     │────▶│  AWS Bedrock        │
│  (Vercel)        │◀────│  (Render / Docker)   │     │  Claude Sonnet 4.6  │
└──────────────────┘     └─────────────────────┘     │  Claude Haiku 4.5   │
                               │          │           └─────────────────────┘
                         ┌─────▼──┐  ┌───▼────┐
                         │Postgres│  │ Redis  │
                         │+pgvec  │  │ cache  │
                         └────────┘  └────────┘
```

Review pipeline:
1. Parse unified diff → structured hunks
2. Run 5 parallel LLM agents (`asyncio.gather`) — Sonnet for security/logic/perf, Haiku for style/maintainability
3. Deduplicate findings by title + file path
4. Stream results via SSE as each agent completes
5. Post inline GitHub PR comments (GitHub App path)

---

## Required backend env vars

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS credentials (Bedrock access) |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_REGION` | `us-east-1` (cross-region inference profiles) |
| `DATABASE_URL` | PostgreSQL connection string (optional, uses SQLite fallback) |
| `REDIS_URL` | Redis connection string (optional, rate limiting) |
| `GITHUB_APP_ID` | GitHub App ID (for PR auto-review) |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key PEM |
| `GITHUB_WEBHOOK_SECRET` | Webhook HMAC secret |
| `JWT_SECRET` | Min 32 chars |

---

## Project structure

```
sentinel-review/
├── frontend/               # Next.js 14 — deployed on Vercel
│   ├── app/
│   │   ├── page.tsx        # Landing page
│   │   ├── review/         # Public diff reviewer + share URLs
│   │   ├── dashboard/      # User dashboard
│   │   └── docs/           # Integration docs
│   ├── components/review/  # FindingCard, SummaryCard, DiffEditor, etc.
│   └── lib/                # API client, types, utils, sample diff
│
├── backend/                # FastAPI Python 3.11 — deploy on Render/Docker
│   ├── app/
│   │   ├── routers/        # review, webhook, auth, repos, shares
│   │   ├── services/       # reviewer (5 agents), diff_parser, github, cache
│   │   └── models/         # Pydantic models for review, finding, user, repo
│   ├── migrations/         # PostgreSQL schema with pgvector
│   ├── Dockerfile
│   └── render.yaml
│
└── .github/workflows/
    └── sentinel-review.yml # Publishable CI workflow template
```
