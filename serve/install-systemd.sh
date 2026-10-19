#!/usr/bin/env bash
# Install the on-demand user units. Fills in this checkout's path, so nothing is hardcoded.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[ -f "$HERE/model.env" ] || { echo "Create serve/model.env first (copy serve/model.env.example)." >&2; exit 1; }
PROXYD=$(ls /usr/lib/systemd/systemd-socket-proxyd /lib/systemd/systemd-socket-proxyd 2>/dev/null | head -1 || true)
[ -n "$PROXYD" ] || { echo "systemd-socket-proxyd not found; install systemd's proxy component." >&2; exit 1; }
U="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"; mkdir -p "$U"
sed "s|@SERVE_DIR@|$HERE|" "$HERE/systemd/llama-serve.service.in" > "$U/llama-serve.service"
sed "s|/usr/lib/systemd/systemd-socket-proxyd|$PROXYD|" "$HERE/systemd/llama-proxy.service" > "$U/llama-proxy.service"
cp "$HERE/systemd/llama-proxy.socket" "$U/"
systemctl --user daemon-reload
echo "Installed. Start listening with:  systemctl --user enable --now llama-proxy.socket"
