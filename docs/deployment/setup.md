# Deployment — Setup

Two ways to deploy, both local.

## A. One-shot bootstrap (simplest — Linux / WSL)
After cloning the repo:

```
./squidfall.sh            # preflight -> pull model -> build -> start -> health -> print URL
```

It checks Docker, ensures the Ollama model is present, builds the 5 images, starts
them, waits for health, and prints `http://localhost`. Other verbs:

```
./squidfall.sh down       # stop + remove
./squidfall.sh status     # container status
./squidfall.sh logs [svc] # follow logs
./squidfall.sh build      # build only
```

On Windows (no `make`), the equivalent control surface is `./sf.ps1 start all`.

## B. Prod-like release (via CD)
The `squidfall-prod` project (`compose.prod.yml`) runs the registry images on
shifted ports so it coexists with the dev stack:

| Service | Dev port | Prod port |
|---|---|---|
| frontend | 80 | 8080 |
| backend | 8000 | 18000 |
| inference | 8001 | 18001 |
| tools | 8002 | 18002 |
| database | 5432 | 15432 |

Deploy a version with a tag (`git tag vX.Y.Z && git push origin vX.Y.Z`, CD does the
rest), or manually:

```
TAG=<sha-or-stable> docker compose -p squidfall-prod -f compose.prod.yml up -d --pull always
```

## Notes
- `host.docker.internal` lets containers reach Ollama on the host (on WSL, the Windows host).
- `tools/.env` (gitignored) holds the geocoding key; it is **optional** for startup
  (`env_file ... required: false`), so a fresh clone deploys without it.
- Postgres auth is wide-open (`0.0.0.0/0 md5`) for local dev — **tighten before any
  real network exposure** (Platform hardening, Phase 6).
