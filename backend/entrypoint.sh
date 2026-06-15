#!/usr/bin/env sh

set -e

# Wait for Postgres to accept TCP connections. On first boot the database
# container runs initdb + createdb before the real server comes up, so a bare
# `migrate` can race it (Connection refused). Belt-and-suspenders with the
# compose healthcheck.
echo "Waiting for database at ${PGHOST}:${PGPORT}..."
python - <<'PY'
import os, socket, sys, time

host = os.environ.get("PGHOST", "squidfall-database")
port = int(os.environ.get("PGPORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), 2):
            break
    except OSError:
        time.sleep(1)
else:
    sys.exit(f"database {host}:{port} not reachable")
PY

python manage.py migrate

uvicorn squidfall.asgi:application --host 0.0.0.0 --port 8000
