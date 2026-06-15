# Continuous Integration — Setup

CI runs on the self-hosted runner on every push / PR.
Workflow: `.github/workflows/ci.yml`.

## Step 1. Prerequisites
Docker + a registered self-hosted runner labelled `self-hosted, windows, x64`
(see [Platform Resources — Setup](../platform-resources/setup.md)).

## Step 2. Add `.github/workflows/ci.yml`
Abridged (see the repo for the full file):

```yaml
on: { push: { branches: [main] }, pull_request: {}, workflow_dispatch: {} }
jobs:
  ci:
    runs-on: [self-hosted, windows, x64]
    steps:
      - uses: actions/checkout@v5
      - name: Build all images
        env: { COMPOSE_BAKE: "true" }
        run: docker compose --profile all build
      - name: Backend check + tests (SQLite, no DB)
        run: docker run --rm squidfall/backend:latest sh -c "python manage.py check && python manage.py test --noinput 2>&1"
      - name: Tools import check
        run: docker run --rm squidfall/tools:latest python -c "import fastmcp"
      - name: Inference deps import check
        run: docker run --rm squidfall/inference:latest python -c "import langgraph, langchain_ollama, ag_ui_langgraph, langchain_mcp_adapters"
      - name: Lint (ruff, critical rules)
        run: docker run --rm -v "${{ github.workspace }}:/src" -w /src ghcr.io/astral-sh/ruff:latest check --select E9,F63,F7,F82 backend tools inference
      - name: Trivy (report-only)
        continue-on-error: true
        run: |
          docker save squidfall/backend:latest -o backend.tar
          docker run --rm -v "${{ github.workspace }}:/work" aquasec/trivy:latest image --input /work/backend.tar --severity HIGH,CRITICAL --exit-code 0 --no-progress
          Remove-Item backend.tar
```

## Step 3. Why `docker run`, not `compose up`?
The stack uses **fixed container names + ports**, so `compose up` in CI would
collide with a locally-running stack. Ephemeral `docker run` checks avoid that;
full-stack integration testing happens in CD against the prod-like project.

## Step 4. Run it
Push to `main`. The run appears under the repo's **Actions** tab and goes green:
build · backend tests on SQLite · import checks · ruff · Trivy (report-only).
Backend tests use SQLite (no `DB_ENGINE`) so CI needs no live Postgres.
