# ---------------------------------------------------------
# Squidfall — Makefile
# On Windows without `make`, use ./sf.ps1 (same commands).
# ---------------------------------------------------------

.DEFAULT_GOAL := build

# Exported (not just a make var) so the `docker compose` child process sees it.
export COMPOSE_BAKE := true

# Default profile. Override: make DOCKER_COMPOSE_PROFILE=database start
DOCKER_COMPOSE_PROFILE ?= all

.PHONY: build start stop status
.SILENT: build start stop status

build:
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) build

start:
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) up -d

stop:
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) down

status:
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) ps --format "table {{.Name}}\t{{.Ports}}\t{{.Status}}"
