#!/usr/bin/env bash
set -euo pipefail

cd /home/midea/GithubRepository/HiClaude

if [[ -x ".venv/bin/python3" ]]; then
  python_bin=".venv/bin/python3"
else
  python_bin="python3"
fi

export PYTHONPATH=src

echo "Starting HiClaude status service on http://127.0.0.1:18765/"
echo "Press Ctrl+C to stop."
echo

exec "$python_bin" -m agent_epaper.server --host 0.0.0.0 --port 18765 --collect
