#!/bin/bash
# FastAPI 백엔드 실행 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "FastAPI 백엔드 시작..."
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

