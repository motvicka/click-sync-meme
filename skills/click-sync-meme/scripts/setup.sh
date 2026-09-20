#!/bin/sh
# One-time setup: Python venv with the analysis/render deps + headless Chromium. Needs ffmpeg and yt-dlp on PATH.
#   sh setup.sh [VENV_DIR]      (default: ~/.cache/click-sync-meme/venv)
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${1:-$HOME/.cache/click-sync-meme/venv}"
for t in ffmpeg ffprobe yt-dlp python3; do command -v $t >/dev/null || { echo "missing: $t  (macOS: brew install ffmpeg yt-dlp)"; exit 1; }; done
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" -q install -r "$HERE/requirements.txt"
"$VENV/bin/python" -m playwright install chromium
echo "ready: $VENV/bin/python"
