#!/bin/bash
set -e
cd "Backend files"
python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}