#!/bin/sh
# viktor-local one-liner: curl -fsSL https://ocb2016.me/viktor-local/install.sh | sh -s -- ~/games
# Installs a `viktor-local` command; later just run: viktor-local [folder]
set -e
URL="${VIKTOR_LOCAL_URL:-https://ocb2016.me/viktor-local/viktor_local.py}"
command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
DIR="$HOME/.cache/viktor-local"; BIN="$HOME/.local/bin"
mkdir -p "$DIR" "$BIN"
curl -fsSL "$URL" -o "$DIR/viktor_local.py"
cat > "$BIN/viktor-local" <<WRAP
#!/bin/sh
# viktor-local [folder]   |   viktor-local update
if [ "\$1" = "update" ]; then curl -fsSL "$URL" -o "$DIR/viktor_local.py" && echo "updated"; exit; fi
exec "$(command -v uv)" run "$DIR/viktor_local.py" "\${1:-\$PWD}"
WRAP
chmod +x "$BIN/viktor-local"
echo "  installed: viktor-local  (next time just run: viktor-local ~/games)"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "  note: add $BIN to PATH, or run $BIN/viktor-local";; esac
exec "$BIN/viktor-local" "${1:-$PWD}"
