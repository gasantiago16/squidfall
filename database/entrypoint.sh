#!/usr/bin/env sh
set -e

PGDATA=/var/lib/postgresql/data
DB_USER="${PGUSER:-postgres}"
DB_PASS="${PGPASSWORD:-postgres}"
APP_DB="${PGDATABASE:-squidfall}"

# First boot only: initialize the cluster and the application database.
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  # Initialize with the REAL superuser password (reference used /dev/null = empty).
  printf '%s' "$DB_PASS" > /tmp/pwfile
  initdb -D "$PGDATA" -U "$DB_USER" -A scram-sha-256 --pwfile=/tmp/pwfile
  rm -f /tmp/pwfile

  # Listen on all interfaces, but only ACCEPT connections from private (RFC1918)
  # ranges with SCRAM auth — covers the Docker bridge networks and the host
  # gateway, but not the public internet (Phase 6 hardening; was 0.0.0.0/0 md5).
  echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
  echo "password_encryption = scram-sha-256" >> "$PGDATA/postgresql.conf"
  echo "host all all 10.0.0.0/8 scram-sha-256"     >> "$PGDATA/pg_hba.conf"
  echo "host all all 172.16.0.0/12 scram-sha-256"  >> "$PGDATA/pg_hba.conf"
  echo "host all all 192.168.0.0/16 scram-sha-256" >> "$PGDATA/pg_hba.conf"

  # Start a temporary socket-only server to create the app database
  # (the reference never created it, so Django migrate had nowhere to connect).
  pg_ctl -D "$PGDATA" -o "-c listen_addresses=''" -w start
  if ! PGDATABASE=postgres psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$APP_DB'" | grep -q 1; then
    PGDATABASE=postgres createdb -U "$DB_USER" "$APP_DB"
  fi
  pg_ctl -D "$PGDATA" -m fast -w stop
fi

# Start Postgres in the foreground.
exec postgres -D "$PGDATA"
