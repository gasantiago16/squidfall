# Squidfall (local rebuild)

Local recreation of the Army AI2C / CDSO **Squidfall** reference app — a containerized,
agentic AI **weather assistant** — plus a fully-local CI/CD pipeline (GitHub repo +
self-hosted runner) built out over later phases.

**Repo:** <https://github.com/gasantiago16/squidfall> (public)

> **Status: ✅ Phases 1–4 complete.** All 5 containers build and run; a weather chat works
> end-to-end (verified: *"weather in Pittsburgh, PA"* → live geocode → live NWS forecast →
> streamed answer). The frontend has a liquid-glass UI. Public repo + self-hosted runner are live;
> CI green on every push, and CD (on version tags) deploys a prod-like stack — released **v0.1.0**.
> **Next: Phase 5 (author the upstream blank doc pages).**

See **`ARCHITECTURE.md`** / **`architecture.html`** for the full breakdown, data flow, and bug log; section setup guides live in **[`docs/`](docs/)**.

## Stack

| Service | What it is | Image | Port |
|---|---|---|---|
| database | PostgreSQL | alpine:3.23 | 5432 |
| backend | Django + django-ninja | python:3.12-slim | 8000 |
| tools | FastMCP weather tools | python:3.12-slim | 8002 |
| inference | LangGraph ReAct + AG-UI on **local Ollama + Qwen** | python:3.12-slim | 8001 |
| frontend | Next.js 16 + CopilotKit (liquid-glass UI) | node:24-alpine | 80 |

## Prerequisites (verified on this machine)

- Docker 29 + Compose v5 ✅
- Ollama 0.30 ✅ with **`qwen2.5` pulled** (`ollama pull qwen2.5` — the 7B; the 0.5B is too small for tool-calling)
- Node 24 ✅, Python 3.13 ✅ (only used to scaffold backend/frontend)
- `make` is **not** installed → use `./sf.ps1`

## Run it

**Linux / WSL — one command** (preflight → pull model → build → start → health → URL):

```bash
./squidfall.sh          # then open http://localhost  ·  also: down | status | logs | build
```

**Windows (no `make`):**

```powershell
./sf.ps1 start all      # build (if needed) + bring up all 5 containers
./sf.ps1 status all     # confirm Up / healthy
# → open http://localhost and ask "What's the weather in Pittsburgh, PA?"
./sf.ps1 stop all       # tear down
```

Per-service: `./sf.ps1 build|start|status|stop <database|backend|tools|inference|frontend|all>`.
Raw equivalent: `docker compose --profile <svc> build | up -d | down | ps`.
If you install make (`winget install GnuWin32.Make`), the `Makefile` mirrors these verbs.

## CI/CD (self-hosted runner)

- **CI** (`.github/workflows/ci.yml`) — every push/PR: build all images, Django tests on SQLite, ruff (critical), Trivy (report-only). Ephemeral `docker run` checks (no `compose up`) so it never collides with a running stack.
- **CD** (`.github/workflows/cd.yml`) — on a `v*` tag: build → SHA-tag → push to a local registry (`registry:2` @ `:5000`) → deploy the **prod-like** `squidfall-prod` project (`compose.prod.yml`, ports `:8080 / :18000 / :18001 / …`) → health gate → promote `:stable` → rollback on failure.
- **Cut a release:** `git tag vX.Y.Z && git push origin vX.Y.Z`. Prod UI → <http://localhost:8080> (runs alongside dev on `:80`).

## Status

- ✅ Orchestration — `Makefile`, `sf.ps1`, `compose.yml` (DB healthcheck gating backend)
- ✅ database — corrected entrypoint (real password + creates the `squidfall` DB)
- ✅ tools — FastMCP weather server (geocoding key wired in)
- ✅ inference — real LangGraph + AG-UI agent (Ollama/Qwen + MCP tools + checkpointer)
- ✅ backend — Django, migrates, API returns 200
- ✅ frontend — Next.js + CopilotKit + liquid-glass UI, on `:80`
- ✅ Phase 2 — public GitHub repo + self-hosted runner (`squidfall-win`)
- ✅ Phase 3 — CI pipeline green (`ci.yml`: build · Django tests · ruff · Trivy report-only)
- ✅ Phase 4 — CD pipeline (`cd.yml`): local registry + prod-like deploy (`compose.prod.yml`) + health gate + rollback; released v0.1.0
- ⬜ Phase 5 (author upstream docs) · Phase 6 (hardening)

## Deliberate deviations from the reference docs (so it actually builds/runs)

- **Python base image** `python:3.12-slim` instead of `alpine` for backend/tools/inference
  (alpine/musl forces source builds of pydantic-core / psycopg2 and breaks the reference Dockerfiles).
- **`inference/main.py`** rewritten as the real agent — the reference shipped the tools server by mistake.
- **LLM** = local Ollama `qwen2.5` via `langchain_ollama.ChatOllama` on the **native** API
  (not `/v1`; Ollama has an open tools+streaming bug there).
- **Agent compiled with an `InMemorySaver` checkpointer** — the AG-UI adapter calls `aget_state()` each run; without it the chat errors with `INCOMPLETE_STREAM`.
- **`langchain` is the 1.x line** (not 0.3) — `ag-ui-langgraph 0.0.41` requires `langchain >= 1.2`.
- **`database/entrypoint.sh`** initializes the superuser with the real password and creates `$PGDATABASE`;
  a **DB healthcheck + `depends_on: service_healthy`** keeps `backend` from racing first-boot init.
- **`.env` files** are plain `KEY=val` (no `export`). Shell-source for manual checks: `set -a; . ./database/.env; set +a`.
- **Frontend** carries a liquid-glass UI (aurora + frosted glass), adapted from the Walking Trader terminal.

## Secrets

`tools/.env` is gitignored. Copy `tools/.env.example` → `tools/.env` and add a free key
from <https://geocode.maps.co/>, then `docker compose up -d tools`. `get_forecast` (weather.gov)
needs no key but is **US-only**.
