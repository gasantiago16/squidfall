# Operations & Migration Runbook (GitLab + WSL + restricted network)

How Squidfall was migrated from the GitHub source to an **Army GitLab** instance,
deployed on **WSL** in a restricted/limited-egress environment, and run there.
Companion to the section Setup pages; the app + CI/CD design is in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md).

> **Status: deployed on the GitLab/WSL account and running** — LLM via OpenAI,
> geocoding live. (Forecast depends on `api.weather.gov` egress — see §6.)

## 1. Get the code onto the box
- **Into GitLab:** import the public GitHub mirror
  (`https://github.com/gasantiago16/squidfall`) via GitLab → **New project → Import → Repo by URL**.
  (Fully air-gapped: transfer a `git bundle` and import that.)
- **Onto WSL:** `git clone <your-gitlab-url>/squidfall.git`.
- The `glab` CLI is **not required** — plain `git` + the GitLab web UI cover everything.

## 2. Install Docker in WSL (native engine — not Docker Desktop)
Docker Desktop needs a paid commercial license (DoD qualifies) **and** Windows admin.
The **native Docker Engine inside WSL2** avoids both:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER && newgrp docker
sudo service docker start
docker version && docker compose version
```
Air-gapped: install from an internal apt mirror or offline `.deb`s.

**Auto-start (optional):** without systemd, `dockerd` won't start on its own each session.
```bash
printf '[boot]\nsystemd=true\n' | sudo tee -a /etc/wsl.conf
# from Windows PowerShell:  wsl --shutdown   (next launch has systemd)
sudo systemctl enable docker
```

## 3. Bring the stack up
```bash
cd squidfall
docker compose --profile all up -d      # or ./squidfall.sh (ignore the "ollama not found" warning)
docker compose --profile all ps         # expect 5 up, database (healthy)
curl -s http://localhost:8001/api/v1/health && echo
# UI: http://localhost
```

## 4. Restart after closing the WSL terminal
Closing the last shell can stop `dockerd` (no systemd). Data persists in the DB volume.
```bash
cd squidfall
docker info >/dev/null 2>&1 || sudo service docker start
docker compose --profile all up -d
```

## 5. Wire the LLM (no Ollama on this box)
Edit `inference/.env` (factory: `inference/squidfall/llm.py`):
```bash
# OpenAI / OpenAI-compatible gateway:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://<endpoint>/v1
OPENAI_API_KEY=<key>
# ...or LLM_PROVIDER=azure_openai (endpoint/deployment/version + API key OR Entra-ID).
# Full matrix: docs/deployment/setup.md section C.
```
Apply (runtime config — **no rebuild**): `docker compose --profile all up -d`.
Verify: `docker exec squidfall-inference python -c "from squidfall.llm import build_llm; print(type(build_llm()).__name__)"` → `ChatOpenAI`.

⚠️ `inference/.env` is **git-tracked** — do **not** commit a real key (gitignore it locally,
or inject `OPENAI_API_KEY` via the environment / a masked GitLab CI/CD variable).

## 6. Weather tools in a restricted network
Geocoding (`geocode.maps.co`) and forecast (`api.weather.gov`) are **different egress hosts**
— geocoding can work while `api.weather.gov` is blocked. Diagnose:
```bash
docker exec -i squidfall-tools python -c "import asyncio; from squidfall.providers import forecast; print(asyncio.run(forecast(40.44,-79.99)))"
```
Fix in `tools/.env`, then `docker compose --profile all up -d`:
- **blocked / unreachable** → `FORECAST_PROVIDER=static` (+ `FORECAST_STATIC_TEXT=...`), or
  `FORECAST_BASE_URL=<internal NWS-compatible mirror>`, or get `api.weather.gov` allowlisted.
- **`SSLError`** (TLS-intercepting proxy) → `FORECAST_VERIFY_SSL=false` (test) / install the proxy CA.
- **`403`** → set a real `FORECAST_USER_AGENT`. **404 / KeyError** → non-US coords (weather.gov is US-only).

Same knobs exist for geocoding (`GEOCODER_PROVIDER`, `GEOCODER_BASE_URL`, `GEOCODER_STATIC*`).

## 7. Golden rule — image vs config changes
- **Source/code change** (frontend, backend, tools, inference Python, any Dockerfile) →
  the containers run **compiled images**, so source edits do nothing until you
  **rebuild + recreate** that service:
  ```bash
  docker compose --profile all build <svc>
  docker compose --profile all up -d <svc>
  ```
  Hard-refresh the browser (Ctrl+Shift+R) for frontend text/UI changes.
- **`.env` change** → just recreate, **no rebuild**: `docker compose --profile all up -d`.

## 8. Quick reference
| Need | Command |
|---|---|
| Start daemon | `sudo service docker start` |
| Up (all) | `docker compose --profile all up -d` |
| Status | `docker compose --profile all ps` |
| Logs | `docker compose --profile all logs -f <svc>` |
| Rebuild one service | `docker compose --profile all build <svc> && docker compose --profile all up -d <svc>` |
| Down | `docker compose --profile all down` |

## 9. Air-gapped builds & GitLab CI
- Build mirrors (set in a root `.env` or GitLab CI/CD variables): `REGISTRY_PREFIX`,
  `PIP_INDEX_URL`/`PIP_TRUSTED_HOST`, `NPM_REGISTRY`, `APK_MIRROR`. See `.env.example`.
- `.gitlab-ci.yml` pushes images to GitLab's built-in **Container Registry**
  (`$CI_REGISTRY_IMAGE`); `RUFF_IMAGE`/`TRIVY_IMAGE` are overridable for internal mirrors.
- Register a **shell-executor GitLab Runner** with Docker; match its tag to `tags:` in `.gitlab-ci.yml`.
