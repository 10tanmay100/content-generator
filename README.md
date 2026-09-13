# AI Content Creation Pipeline — CrewAI · ChatGroq · Azure

Production-grade, role-based multi-agent content creation pipeline. A CrewAI
crew (Researcher → Writer → Editor → SEO Specialist → Image Designer → Social
Strategist) generates blog posts, social content, and newsletters, powered by
**Groq-hosted LLMs**. Backed by Azure Cosmos DB, Azure AI Search, deployed on
Azure Container Apps via Azure DevOps Pipelines, with Application Insights
monitoring.

## Architecture

```
┌─────────────┐      ┌──────────────────────┐      ┌───────────────────┐
│  Next.js 14  │────▶│   FastAPI backend     │────▶│   CrewAI Crew      │
│  (App Router)│◀────│   (async job queue)   │◀────│  (6 Groq agents)   │
└─────────────┘      └──────────────────────┘      └───────────────────┘
                              │        │
                      ┌───────┘        └────────┐
                      ▼                          ▼
              Azure Cosmos DB            Azure AI Search
              (jobs + content)          (vector/semantic)

     All wired to Azure Monitor / Application Insights,
     deployed on Azure Container Apps via Azure DevOps Pipelines.
```

## Repo layout

```
content-pipeline/
├── backend/        FastAPI + CrewAI (Python 3.11)
│   ├── app/
│   │   ├── agents/     Research, Writing, Editing, SEO, Image, Social agents
│   │   ├── crew/       Task definitions + crew orchestration
│   │   ├── tools/      Custom CrewAI tools (web search, SEO scorer, image prompt)
│   │   ├── services/   Cosmos DB, Azure AI Search, LLM (Groq) service layers
│   │   ├── api/routes/ health, content, jobs endpoints
│   │   ├── core/       logging, exceptions, auth
│   │   └── models/     Pydantic schemas
│   ├── tests/       pytest suite (10 tests, mocked LLM/DB calls)
│   └── Dockerfile
├── frontend/        Next.js 14 (App Router) + Tailwind
│   ├── app/          pages: /, /generate, /preview/[id]
│   ├── components/   ContentForm, AgentProgress, ContentPreview, Navbar
│   └── Dockerfile
├── infra/            Bicep IaC: Cosmos DB, AI Search, Container Apps, Monitor
├── devops/           azure-pipelines.yml (CI/CD) + deploy.sh (manual deploy)
└── docker-compose.yml
```

## Prerequisites

- Python 3.11+, Node.js 20+, Docker
- A [Groq API key](https://console.groq.com) (free tier available)
- An Azure subscription (for Cosmos DB / AI Search / Container Apps / Monitor)

## Local development

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set GROQ_API_KEY at minimum. Cosmos/Search are optional locally
# (job persistence will error without Cosmos configured — see note below).
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

> **Note:** the job queue persists to Cosmos DB. For a quick local demo without
> Azure, use `POST /api/v1/content/generate/sync` which runs the crew inline
> and returns the full result without touching Cosmos.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# edit .env.local: NEXT_PUBLIC_API_BASE_URL, BACKEND_API_TOKEN (match backend's API_AUTH_TOKEN)
npm run dev
```

App: http://localhost:3000

### 3. Or run both with Docker Compose

```bash
cp backend/.env.example backend/.env   # fill in GROQ_API_KEY etc.
docker compose up --build
```

## Running tests

```bash
cd backend
pytest -v              # 10 tests: health, auth, request validation, agents/tools
```

## Deploying to Azure

1. **Provision infra + push images (one-shot):**
   ```bash
   ./devops/deploy.sh rg-content-pipeline-dev eastus <your-groq-api-key>
   ```
   This creates the resource group, deploys `infra/main.bicep` (Cosmos DB,
   Azure AI Search, Log Analytics + App Insights, Container Apps environment,
   ACR), then builds and pushes both images with `az acr build`.

2. **Continuous deployment:** import `devops/azure-pipelines.yml` into Azure
   DevOps. It lints/tests both apps, builds & pushes Docker images to ACR,
   redeploys the Bicep template, then rolls out new Container App revisions.
   You'll need:
   - A **Library variable group** `content-pipeline-secrets` with `GROQ_API_KEY`
     and any Cosmos/Search overrides.
   - Service connections named `acr-service-connection` and
     `azure-service-connection`.
   - An **Environment** named `content-pipeline-dev` (for approval gates).

## Key design choices

- **CrewAI + Groq**: agents use `crewai.LLM(model="groq/<model>")`, which
  routes through litellm — no extra Groq SDK needed. Swap models via
  `GROQ_MODEL` / `GROQ_MODEL_FAST` env vars.
- **Custom tools, not `crewai-tools`**: the web search / SEO / image-prompt
  tools are hand-rolled on `crewai.tools.BaseTool` to avoid `crewai-tools`'
  heavy transitive dependencies (embedchain, extra vector DBs) that aren't
  needed here.
- **Async job model**: `POST /content/generate` returns a `job_id`
  immediately (202 Accepted) and runs the crew in a FastAPI background task,
  since a full 6-agent run can take 30–120+ seconds. The frontend polls
  `GET /jobs/{id}` every 4s.
- **Multi-tenant partitioning**: Cosmos containers are partitioned by
  `/tenant_id` so this can scale to multiple customers/workspaces.
- **Token auth on the backend token stays server-side**: the Next.js app
  proxies through its own `/api/generate` and `/api/jobs/[id]` route handlers
  so the browser never sees `API_AUTH_TOKEN`.

## Extending

- Swap the image tool's prompt-only output for a live call to DALL·E/Stable
  Diffusion by wiring `OPENAI_API_KEY` / `STABILITY_API_KEY` into
  `app/tools/image_tool.py`.
- Add `SearchService.ensure_index()` + `index_content()` calls after a job
  completes to make past content searchable/retrievable by the Research Agent
  (RAG loop).
- Swap the sequential `Process.sequential` crew for `Process.hierarchical` if
  you want a manager agent to delegate dynamically.
