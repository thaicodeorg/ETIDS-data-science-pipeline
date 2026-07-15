#!/usr/bin/env bash
set -e
curl -X POST http://localhost:8000/pipeline/run-all | python -m json.tool
