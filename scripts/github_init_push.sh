#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ./scripts/github_init_push.sh https://github.com/<OWNER>/<REPO>.git"
  exit 1
fi

REMOTE_URL="$1"

git init
git branch -M main
git add .
git commit -m "Initial ETIDS Docker data science pipeline" || true
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi
git push -u origin main

echo "Done. Repository pushed to $REMOTE_URL"
