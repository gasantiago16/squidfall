#!/usr/bin/env bash
# Squidfall — one-shot bootstrap for Linux / WSL.
#
#   ./squidfall.sh            build + start the whole stack, then print the URL
#   ./squidfall.sh up         same as above
#   ./squidfall.sh down       stop + remove the containers
#   ./squidfall.sh status     show container status
#   ./squidfall.sh logs [svc] follow logs (all services, or just one)
#   ./squidfall.sh build      build images only
#
# The only things to set up on a fresh box ("hand-jam the WSL"):
#   - Docker (Docker Desktop w/ WSL integration, or native docker + compose v2)
#   - Ollama reachable at $OLLAMA_BASE_URL (default = the Windows host) with the model
set -euo pipefail
cd "$(dirname "$0")"

CMD="${1:-up}"
MODEL="${OLLAMA_MODEL:-qwen2.5}"

g=$'\033[32m'; r=$'\033[31m'; y=$'\033[33m'; d=$'\033[2m'; x=$'\033[0m'
say()  { printf '%s>%s %s\n' "$g" "$x" "$*"; }
warn() { printf '%s!%s %s\n' "$y" "$x" "$*"; }
die()  { printf '%sx %s%s\n' "$r" "$*" "$x" >&2; exit 1; }

compose() { docker compose --profile all "$@"; }

preflight() {
  command -v docker >/dev/null 2>&1 || die "docker not found — install Docker Desktop (WSL integration) or the docker engine"
  docker compose version >/dev/null 2>&1 || die "'docker compose' (v2) not found"
  docker info >/dev/null 2>&1 || die "Docker daemon not reachable — start Docker Desktop / dockerd"
  # tools/.env holds the optional geocoding key and is gitignored — create it so nothing breaks.
  [ -f tools/.env ] || cp tools/.env.example tools/.env 2>/dev/null || echo "GEOCODING_API_KEY=" > tools/.env
}

ensure_model() {
  if command -v ollama >/dev/null 2>&1; then
    if ollama show "$MODEL" >/dev/null 2>&1; then
      say "Ollama model '$MODEL' present"
    else
      say "pulling Ollama model '$MODEL' (one-time, ~4.7GB)..."
      ollama pull "$MODEL"
    fi
  else
    warn "ollama CLI not found in this shell."
    warn "inference expects Ollama at \$OLLAMA_BASE_URL (default http://host.docker.internal:11434 = the Windows host)."
    warn "ensure Ollama is running there with '$MODEL' pulled, or edit inference/.env."
  fi
}

wait_health() {
  command -v curl >/dev/null 2>&1 || { warn "curl not found — skipping health check"; return 0; }
  say "waiting for the stack to come up..."
  for _ in $(seq 1 60); do
    if curl -fsS http://localhost/ >/dev/null 2>&1 && curl -fsS http://localhost:8001/api/v1/health >/dev/null 2>&1; then
      return 0
    fi
    sleep 3
  done
  warn "stack not healthy yet — check './squidfall.sh logs'"
  return 1
}

case "$CMD" in
  up|"")
    preflight
    ensure_model
    say "building images...";    compose build
    say "starting containers..."; compose up -d
    if wait_health; then
      echo
      say "Squidfall is up  ->  http://localhost"
      printf '%s  backend :8000 - inference :8001 - tools :8002 - postgres :5432%s\n' "$d" "$x"
      printf '%s  weather needs a free geocoding key in tools/.env (https://geocode.maps.co/)%s\n' "$d" "$x"
    fi
    ;;
  down)   compose down ;;
  status) compose ps ;;
  build)  preflight; compose build ;;
  logs)   shift 2>/dev/null || true; docker compose --profile all logs -f "$@" ;;
  *)      die "unknown command '$CMD' (use: up | down | status | logs | build)" ;;
esac
