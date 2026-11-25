#!/bin/sh
# viktor-local one-liner: curl -fsSL https://ocb2016.me/viktor-local/install.sh | sh -s -- ~/games
set -e
URL="${VIKTOR_LOCAL_URL:-https://ocb2016.me/viktor-local/viktor_local.py}"
command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
mkdir -p "$HOME/.cache/viktor-local"
curl -fsSL "$URL" -o "$HOME/.cache/viktor-local/viktor_local.py"
exec uv run "$HOME/.cache/viktor-local/viktor_local.py" "${1:-$PWD}"
