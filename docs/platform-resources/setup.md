# Platform Resources — Setup

The Squidfall pipeline runs entirely on **local** platform resources (no cloud).
This page stands each one up. Verified on Windows 11 + Docker Desktop; the runner
is Windows, the app containers are Linux.

## Step 1. Docker
Docker Desktop (Engine 29+, Compose v2). On WSL, enable **WSL integration** so
`docker` / `docker compose` work inside the distro.

```
docker --version
docker compose version
```

## Step 2. Ollama + the model
The `inference` service uses a local LLM via Ollama — no API keys, no egress.

```
# install Ollama (https://ollama.com), then:
ollama pull qwen2.5
ollama list           # confirm qwen2.5 is present (the 7B; 0.5B is too small for tool-calling)
```

Containers reach Ollama at `http://host.docker.internal:11434` (i.e. the host; on
WSL that is the Windows host). Override via `OLLAMA_BASE_URL` in `inference/.env`.

## Step 3. Self-hosted GitHub Actions runner
CI/CD compute stays on our own hardware to limit exposure.

```
mkdir C:\actions-runner\squidfall && cd C:\actions-runner\squidfall
# download + extract the latest actions/runner (win-x64) release, then register:
.\config.cmd --url https://github.com/<owner>/squidfall --token <REG_TOKEN> \
  --name squidfall-win --labels self-hosted,windows,x64 --unattended --replace
.\run.cmd            # interactive; or `.\svc.cmd install` + `.\svc.cmd start` (service, admin)
```

Get `<REG_TOKEN>`:
```
gh api -X POST repos/<owner>/squidfall/actions/runners/registration-token -q .token
```

## Step 4. Local container registry
CD pushes SHA-tagged images here instead of an external registry.

```
docker run -d -p 5000:5000 --name squidfall-registry --restart unless-stopped registry:2
curl http://localhost:5000/v2/_catalog      # -> {"repositories":[...]}
```

With these four in place, CI (`.github/workflows/ci.yml`) and CD
(`.github/workflows/cd.yml`) run end-to-end, entirely locally.
