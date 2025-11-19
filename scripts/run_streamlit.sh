#!/bin/bash
# Streamlit 대시보드 실행 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Streamlit 대시보드 시작..."
streamlit run app/web_demo.py --server.port 8501 --server.address 0.0.0.0

