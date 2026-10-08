#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$SERVICE_DIR/desk-dock-media.service"
PYTHON_BIN="$(command -v python3)"

if ! command -v playerctl >/dev/null 2>&1; then
  echo "playerctl is required. Install it with:"
  echo "  sudo apt install playerctl"
  exit 1
fi

mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=Desk Dock Media Bridge
After=graphical-session.target

[Service]
Type=simple
ExecStart=$PYTHON_BIN $SCRIPT_DIR/media_bridge.py
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now desk-dock-media.service

echo
echo "Desk Dock media bridge is installed and running."
echo "Service: $SERVICE_FILE"
echo
echo "Useful commands:"
echo "  systemctl --user status desk-dock-media.service"
echo "  systemctl --user restart desk-dock-media.service"
echo "  systemctl --user disable --now desk-dock-media.service"
