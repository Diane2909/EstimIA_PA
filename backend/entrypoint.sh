#!/bin/sh
set -e

python scripts/download_model.py

exec uvicorn api:app --host 0.0.0.0 --port "${PORT:-8000}"
