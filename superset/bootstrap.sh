#!/usr/bin/env bash
set -e

DATABASE_URI="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

superset db upgrade
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
  --firstname Admin \
  --lastname User \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true
superset init
superset set-database-uri -d ManufacturingDW -u "$DATABASE_URI" || superset set_database_uri -d ManufacturingDW -u "$DATABASE_URI" || true

superset run -h 0.0.0.0 -p 8088
