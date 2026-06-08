#!/bin/bash
# UmbrealityAI — MkDocs live server
# Serves the documentation portal on port 6999
# Run: ./serve.sh
# Or install as systemd service for persistent serving

VENV_DIR="$(dirname "$0")/.venv"
PROJECT_DIR="$(dirname "$0")"

if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

cd "$PROJECT_DIR"
exec mkdocs serve -a 0.0.0.0:6999
