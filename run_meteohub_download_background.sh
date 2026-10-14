#!/usr/bin/env bash
# Run meteohub_download.py detached from the terminal, appending to meteohub_download.log.
#   ./run_meteohub_download_background.sh --from 2025-01-01T00:00:00Z --to 2025-01-10T23:59:00Z --out-dir output_test
# Credentials come from the environment or from ~/.config/meteohub.env (METEOHUB_USERNAME, METEOHUB_PASSWORD).
cd "$(dirname "$0")" || exit 1
if [ -f "$HOME/.config/meteohub.env" ]; then
  set -a
  . "$HOME/.config/meteohub.env"
  set +a
fi
nohup uv run python -u meteohub_download.py "$@" >> meteohub_download.log 2>&1 &
echo "avviato (pid $!), log in $(pwd)/meteohub_download.log"
