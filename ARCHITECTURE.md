# Squidfall — Architecture Breakdown

> Local rebuild of the Army AI2C / CDSO **Squidfall** reference app, with a **fully-local CI/CD pipeline** driven by a self-hosted GitHub Actions runner.
> Source docs: `https://deathlabs.github.io/squidfall/` (mirror of `https://pages.cdso.army.mil/ai2c/squidfall/docs/`).
> This is *our* working architecture — what the published docs describe **plus** the parts we filled in ourselves (the empty CI/CD/Platform/Deployment/Documentation pages) and every fix we made to get it actually running.

> **Status — ✅ Phase 1 complete.** All 5 containers build, run, and a weather chat works **end-to-end** (verified: "weather in Pittsburgh, PA" → live geocode → live NWS forecast → streamed answer on both `http://localhost` and the dev server). The frontend carries a liquid-glass UI. **Phases 2–6 done** — public repo [`gasantiago16/squidfall`](https://github.com/gasantiago16/squidfall) + self-hosted runner `squidfall-win`; CI green on every push; CD on version tags deploys a separate prod-like stack (released **v0.1.0**); the blank upstream doc pages are authored in [`docs/`](docs/), and a one-command WSL bootstrap (`squidfall.sh`); hardened (SCRAM + private `pg_hba`, prod DB internal-only, Trivy blocks fixable HIGH/CRITICAL) and the pipeline is translated to GitLab CI (`.gitlab-ci.yml`). **All six phases complete.**

---

## 1. What Squidfall is

A **containerized, agentic AI chat application**. The shipped example is a **weather assistant**:

1. A user chats in a web UI.
2. An LLM **agent** decides when it needs real-world data.
3. It calls **tools** over MCP to geocode a place and pull a forecast from `api.weather.gov`.
4. Chat history can persist to **PostgreSQL** via a Django REST API.

Everything runs as **5 Docker containers**, orchestrated locally by a **Makefile + `compose.yml`** using **Compose profiles** (so you can bring up one service or the whole stack).

---

## 2. The 5 services at a glance

| # | Service (container) | Stack | Image base | Port | Compose profiles | Role |
|---|---------------------|-------|-----------|------|------------------|------|
| 1 | `database` (`squidfall-database`) | PostgreSQL | `alpine:3.23` | 5432 | `all, backend, database` | Persist chat history |
| 2 | `backend` (`squidfall-backend`) | Django + django-ninja + psycopg2 | `python:3.12-slim` | 8000 | `all, backend` | REST API (`/api/v1/chats/`) |
| 3 | `tools` (`squidfall-tools`) | FastMCP (MCP server) | `python:3.12-slim` | 8002 | `all, inference, tools` | `get_coordinates`, `get_forecast` |
| 4 | `inference` (`squidfall-inference`) | LangGraph ReAct + AG-UI + langchain-ollama | `python:3.12-slim` | 8001 | `all, inference` | The agent loop |
| 5 | `frontend` (`squidfall-frontend`) | Next.js 16 + CopilotKit + liquid-glass UI | `node:24-alpine` | 80→3000 | `all, frontend` | Chat web UI |

All containers join the default Compose network and reach each other by **container name** (e.g. `squidfall-database`, `squidfall-tools`, `squidfall-inference`).

---

## 3. Service detail

### 3.1 `database`
- **Base:** `alpine:3.23`, Postgres + contrib via `apk`.
- **Entrypoint (`entrypoint.sh`) — corrected from the reference:** on **first boot only** it runs `initdb` with the **real** superuser password (`$PGPASSWORD`), enables `listen_addresses='*'` + `host all all 0.0.0.0/0 md5`, then **creates the `$PGDATABASE` (`squidfall`) database** via a temporary socket-only server before `exec postgres`. Idempotent on restart (skips init if `PG_VERSION` exists).
- **Data:** named volume `squidfall_database` → `/var/lib/postgresql/data`.
- **Healthcheck:** `pg_isready -h 127.0.0.1` (TCP, so it only passes once the *real* server is up — not the socket-only init server). `backend` gates on `condition: service_healthy`.
- **Env (`database/.env`):** `PGPASSWORD=postgres`, `PGDATABASE=squidfall`.
- 🔒 **Hardened (Phase 6):** `initdb` uses **scram-sha-256** and `pg_hba` accepts only RFC1918 private ranges (Docker networks + host gateway), not `0.0.0.0/0`; the prod project drops the DB host port (internal-only). *(Applies to fresh volumes; existing volumes keep their original auth.)*

### 3.2 `backend`
- **Stack:** Django project `squidfall` + app `chats`, API via **django-ninja**.
- **Model:** `Chat(session_id, message)`.
- **API (`/api/v1/chats/`):** `GET /{session_id}`, `GET /` (optional filter), `POST /` (create). Verified: `POST` → `{"message_id": 1}`.
- **DB switch:** `DB_ENGINE=postgres` → Postgres; **otherwise SQLite** — deliberately so the container can run in CI **without a database dependency**.
- **Entrypoint:** waits for the DB TCP port (belt-and-suspenders with the compose healthcheck) → `python manage.py migrate` → `uvicorn squidfall.asgi:application :8000`.
- **Env (`backend/.env`):** `DB_ENGINE`, `PGHOST=squidfall-database`, `PGDATABASE`, `PGPORT`, `PGSSLMODE=disable`, `PGUSER`, `PGPASSWORD`.

### 3.3 `tools`
- **Stack:** **FastMCP** server, `transport="streamable-http"`, host `0.0.0.0`, port `8002`, mount `/mcp`.
- **Tools exposed over MCP:**
  - `get_coordinates(location)` → `geocode.maps.co/search` (needs `GEOCODING_API_KEY`).
  - `get_forecast(lat, lon)` → `api.weather.gov/points/...` → forecast (US-only).
- **Env (`tools/.env`, gitignored):** `GEOCODING_API_KEY` — **configured and verified** (real geocode results flowing).

### 3.4 `inference`
- **Stack:** a LangGraph **ReAct** agent (`langgraph.prebuilt.create_react_agent`) served over the **AG-UI protocol** via `ag-ui-langgraph` (`LangGraphAgent` + `add_langgraph_fastapi_endpoint(app, agent, "/api/v1")`), FastAPI/uvicorn on `8001`.
- **LLM (pluggable):** a provider **factory** (`llm.py::build_llm()`) selects the model from **`LLM_PROVIDER`** — `ollama` (dev default; `ChatOllama` native API, **not** `/v1` which has a tools+streaming bug), `openai` (any OpenAI-compatible gateway via `init_chat_model`), or `azure_openai` (`AzureChatOpenAI`; API-key **or** Entra-ID/Gov-cloud service-principal auth via `azure-identity`). Switching is config-only — the agent never names a provider; all three return a tool-capable model so the ReAct loop is unchanged.
- **Tools:** loaded over MCP with `langchain-mcp-adapters` `MultiServerMCPClient` (`transport: "streamable_http"`) from `TOOLS_ENDPOINT=http://squidfall-tools:8002/mcp`; a startup retry loop tolerates the tools container still booting.
- **Checkpointer (load-bearing):** the agent is compiled with `InMemorySaver`. The AG-UI adapter calls `graph.aget_state()` on every run; without a checkpointer it raises `ValueError: No checkpointer set` → the browser sees `INCOMPLETE_STREAM`.
- **Resolved dependency set (pinned where it matters):** `ag-ui-langgraph==0.0.41`, `langchain-mcp-adapters==0.3.0`, `langchain-ollama` 1.1.0, `langgraph` 1.2.5, **`langchain` 1.x** — note `ag-ui-langgraph 0.0.41` requires **langchain ≥ 1.2** (the 0.3 line is a hard conflict).

### 3.5 `frontend`
- **Stack:** Next.js 16 (App Router, TS, Tailwind) + `@copilotkit/runtime` + `@copilotkit/react-core` (v2 `CopilotSidebar`) + `@copilotkit/react-ui`.
- **UI:** a **liquid-glass** theme adapted from the Walking Trader terminal — aurora backdrop (drifting blobs under a 70px blur), frosted `.glass` panels, a topbar with a pulsing orb + live UTC clock, and a glass hero. (CopilotKit's v2 sidebar ships compiled Tailwind utilities with no semantic theme tokens, so it's set to `color-scheme: dark` rather than fully re-skinned — a possible follow-up.)
- **Route `app/api/copilotkit/route.ts`:** `CopilotRuntime` + `LangGraphHttpAgent` → `LANGGRAPH_DEPLOYMENT_URL`. In the container that's `http://squidfall-inference:8001/api/v1` (env_file); the dev server falls back to `http://localhost:8001/api/v1`.
- **Build:** multi-stage `node:24-alpine` (with `libc6-compat` for Next's SWC), `output: "standalone"`, served by `node server.js` on `3000` (host `:80`).

---

## 4. Runtime data flow

```
[Browser]
   │  HTTP :80
   ▼
[frontend] Next.js + CopilotKit runtime (liquid-glass UI)
   │  POST /api/copilotkit  → LangGraphHttpAgent (AG-UI)
   ▼
[inference] LangGraph ReAct agent :8001 /api/v1   (InMemorySaver checkpointer)
   ├──► [Ollama · qwen2.5]  host.docker.internal:11434   (token gen + tool-calling)
   └──► [tools] MCP :8002 /mcp
            ├──► geocode.maps.co      (get_coordinates, needs key)
            └──► api.weather.gov      (get_forecast, US-only)

[backend] Django API :8000  ──►  [database] PostgreSQL :5432   (chat persistence)
```

**Note (open integration gap):** the frontend wires to **inference** (the agent), while **backend + database** are a separate chat-persistence REST layer **not** wired into the chat flow. Persisting chat history end-to-end (frontend/inference → backend → Postgres) remains a deliberate future enhancement.

---

## 5. Orchestration

- **`Makefile`** — `make` (build) / `start` / `stop` / `status`, with `DOCKER_COMPOSE_PROFILE` selecting scope and `export COMPOSE_BAKE=true` for parallel builds.
- **`sf.ps1`** — a PowerShell wrapper with the same verbs, because **`make` is not installed** on this Windows box: `./sf.ps1 start all`, `./sf.ps1 build inference`, etc.
- **`squidfall.sh`** — one-shot bash bootstrap for **Linux/WSL**: `./squidfall.sh` preflights Docker, ensures the Ollama model, builds, starts, health-checks, and prints the URL (also `down`/`status`/`logs`/`build`). Makes a fresh-clone deploy "run one file."
- **`compose.yml`** — 5 services + named volume `squidfall_database`; `profiles:` gate which come up; `database` has a healthcheck and `backend` waits on it.

---

## 6. CI/CD — what *we* are adding (the blank pages)

The published **Continuous Integration, Continuous Delivery, Platform Resources, Deployment, and Documentation** pages are all empty stubs (`Step 1. Text goes here.`). We design and build these locally.

### 6.1 Continuous Integration (CI) — ✅ implemented (`.github/workflows/ci.yml`)
Runs on the self-hosted runner on every push / PR:
- Build all 5 images (Compose Bake; shares the local Docker cache → fast).
- **Backend** Django `check` + `test` on **SQLite** (no live DB) via an ephemeral `docker run`.
- **Tools / inference** image import checks (deps load).
- **Lint** — ruff critical rules (`E9,F63,F7,F82`) via the official ruff image.
- **Trivy** vuln scan — **blocks on FIXABLE HIGH/CRITICAL** (`--ignore-unfixed --exit-code 1`; pre-flighted clean on both images).
- Uses ephemeral `docker run` (not `compose up`) so CI never collides with a locally-running stack (fixed container names/ports). Full-stack integration testing lands in Phase 4 on the prod-like project.

### 6.2 Continuous Delivery (CD) — ✅ implemented (`.github/workflows/cd.yml`)
On a version tag (`v*`) or manual dispatch, on the self-hosted runner:
- Build → tag images by commit SHA → push to the **local registry** (`registry:2` on `localhost:5000`).
- **Deploy** to a separate **prod-like Compose project** (`compose.prod.yml`, project `squidfall-prod`) that runs *alongside* dev — distinct container names, shifted host ports (frontend `:8080`, backend `:18000`, inference `:18001`, tools `:18002`, db `:15432`), its own volume, and **network aliases** (`squidfall-database`, …) so the committed `.env` files resolve unchanged.
- **Health gate** (inference/frontend/backend all 200) → **promote** images to `:stable` → **roll back** to `:stable` on failure.
- First release: **v0.1.0** (CD run green in ~46s).

### 6.3 Local git runner — **CHOSEN**
- **Repo:** hosted on **GitHub.com** (code + workflow YAML).
- **Compute:** a **self-hosted GitHub Actions runner** on our own machine — every build, scan, image push, and deploy runs on our hardware, never on GitHub-hosted runners. GitHub stores the code and fires triggers; the runner (and the Docker daemon, local registry, deploy target) stays private. Workflows live in `.github/workflows/` with `runs-on: [self-hosted]`.
- **Live (Phase 2):** repo `https://github.com/gasantiago16/squidfall` (public); runner **`squidfall-win`** (labels `self-hosted, windows, x64`, `runner v2.335.1`) installed at `C:\actions-runner\squidfall`; `.github/workflows/hello.yml` verified green. Persistence: run interactively (`run.cmd`) or install as a Windows service (`svc.cmd install` from an admin shell).
- **GitLab (for the Army instance):** the same pipeline is translated in **`.gitlab-ci.yml`** for a **shell-executor** GitLab Runner (build → test/lint → Trivy → deploy on `v*` tags, with rollback). The `.github/workflows/` files are harmless/ignored on GitLab. Inject the geocoding key via a masked CI/CD variable `GEOCODING_API_KEY`; set the runner `tag`.

---

## 7. Build roadmap

| Phase | Goal | Status |
|------|------|--------|
| **0** | Scaffolding + architecture docs | ✅ done |
| **1** | Build & run the app locally | ✅ **done — 5 containers built + running, weather chat verified E2E, glass UI** |
| **2** | GitHub repo + self-hosted Actions runner | ✅ **done** — public repo `gasantiago16/squidfall`, runner `squidfall-win` online, hello-world green |
| **3** | CI pipeline | ✅ **done** — `.github/workflows/ci.yml` green (build · tests · ruff · Trivy report-only) |
| **4** | CD pipeline | ✅ **done** — `cd.yml`: registry + SHA images + prod-like deploy + health gate + rollback (released v0.1.0) |
| **5** | Author the blank doc pages | ✅ **done** — `docs/` has the 5 Setup pages, filled from the real pipeline |
| **6** | Platform Resources + hardening | ✅ **done** — SCRAM + private `pg_hba`, prod DB internal-only, Trivy blocking, GitLab CI translation, secrets via CI vars |

---

## 8. Decisions (all resolved)

1. ✅ **LLM** — local Ollama + **`qwen2.5`** via `ChatOllama` (native API); Azure a disabled toggle.
2. ✅ **Git runner** — **GitHub repo + self-hosted Actions runner** (compute stays local).
3. ✅ **`GEOCODING_API_KEY`** — obtained from geocode.maps.co, in `tools/.env` (gitignored), verified.
4. ✅ **Host** — this Windows box (Docker Desktop 29 / Compose v5).

### Reference-doc integration gaps — **FIXED during Phase 1**
- **DB password mismatch** (reference `initdb --pwfile=/dev/null` → empty password) → init with the real `$PGPASSWORD`.
- **`squidfall` DB never created** → created on first boot via a temporary server.
- **`.env` `export` ambiguity** → `.env` files are plain `KEY=val`; shell-source with `set -a; . ./x/.env; set +a`.
- **`inference/main.py` was the tools server by mistake** → rewritten as the real LangGraph + AG-UI agent.

---

## 9. Bugs found & fixed

### 9a. Reference-doc bugs (all fixed in our build)
| Where | Bug | Fix |
|------|-----|-----|
| `inference/main.py` | Copy-paste of `tools/main.py` (ends `port=8002`) | Real LangGraph + AG-UI agent on `:8001 /api/v1` |
| Frontend Step 12 | `route.txt` under `app/api/copilot/` | `route.ts` under `app/api/copilotkit/` |
| Frontend Dockerfile | `node_alpine:24` | `node:24-alpine` (+ `libc6-compat`) |
| `inference/.env` | `https://.openai.azure.us/` (no host) | Swapped to local Ollama |
| Makefile recipes | shown with 4 spaces | literal TABs (and added `sf.ps1` since `make` is absent) |
| Backend Step 20 | sentence cut off | `python manage.py makemigrations chats` |

### 9b. Runtime bugs found while building (fixed)
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `pip` `ResolutionImpossible` on inference build | researched pin `langchain<0.4` vs `ag-ui-langgraph 0.0.41` needing **langchain ≥ 1.2** | dropped the ceiling → resolver picks the 1.x set |
| `backend` crash: `connection refused` to db | `migrate` raced first-boot `initdb`/`createdb` | DB healthcheck + `depends_on: service_healthy` + entrypoint TCP wait |
| Browser chat: `INCOMPLETE_STREAM: terminated` | AG-UI calls `graph.aget_state()` but agent had **no checkpointer** | compile `create_react_agent(..., checkpointer=InMemorySaver())` |
| `get_coordinates` 401 Unauthorized | `GEOCODING_API_KEY` empty | added the key to `tools/.env`, reloaded `tools` |
| (avoided) Ollama tools + streaming break | open Ollama bug on the `/v1` path | use `ChatOllama` native API, not `ChatOpenAI`+`/v1` |

---

## 10. How to run it

```powershell
ollama pull qwen2.5                 # one-time (the 7B; tool-capable)
./sf.ps1 start all                  # build images if needed, bring up all 5
./sf.ps1 status all                 # confirm Up / healthy
# open http://localhost  → ask "What's the weather in Pittsburgh, PA?"
./sf.ps1 stop all                   # tear down
```

Geocoding key (for arbitrary places): copy `tools/.env.example` → `tools/.env`, set `GEOCODING_API_KEY`, then `docker compose up -d tools`.

---

*Living document. Companion: `architecture.html` (same content, browsable, with the system diagram). **All six phases complete** — app + CI/CD (GitHub Actions; GitLab CI translation in `.gitlab-ci.yml`) + hardening. Deploy a fresh clone with `./squidfall.sh`.*
