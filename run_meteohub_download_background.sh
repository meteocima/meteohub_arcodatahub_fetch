#!/bin/zsh
export HOME=/Users/andrea
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

cd /Users/andrea/Desktop/METEOHUB_DOWNLOAD || exit 1
exec /opt/homebrew/bin/uv run python -u meteohub_download.py >> meteohub_download.log 2>&1
