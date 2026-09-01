#!/usr/bin/env bash
set -euo pipefail

# Convenience wrapper for Hugging Face Spaces and local Docker runs.
export PORT="${PORT:-7860}"
exec python start.py
