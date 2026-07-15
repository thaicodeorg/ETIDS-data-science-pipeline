#!/usr/bin/env bash
set -euo pipefail
USER_NAME="${AIRFLOW_ADMIN_USERNAME:-admin}"
USER_PASS="${AIRFLOW_ADMIN_PASSWORD:-admin}"

docker compose exec airflow airflow users reset-password -u "$USER_NAME" -p "$USER_PASS" \
  || docker compose exec airflow airflow users create -u "$USER_NAME" -p "$USER_PASS" -f ETIDS -l Admin -r Admin -e admin@example.com

echo "Airflow admin user is ready: $USER_NAME / $USER_PASS"
