#!/bin/bash
cd "$(dirname "$0")"
exec .venv/bin/python workers/phase1-worker/worker.py "$@"
