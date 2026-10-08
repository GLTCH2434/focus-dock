#!/usr/bin/env python3
"""Tiny local MPRIS bridge for Desk Dock.

Requires: playerctl (apt install playerctl)
Run:      python3 media_bridge.py
Then open Desk Dock. The page polls this local service for the active MPRIS player.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import urllib.parse

HOST = "127.0.0.1"
PORT = 8765


def run_playerctl(*args):
    try:
        p = subprocess.run(
            ["playerctl", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=1.2,
            check=False,
        )
        return p.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return ""


def active_player():
    # Prefer a currently playing player, but keep paused players available so
    # the controller remains visible after the user pauses playback.
    rows = run_playerctl("-a", "metadata", "--format", "{{playerName}}\t{{status}}").splitlines()
    paused = None
    for row in rows:
        player, _, status = row.partition("\t")
        player = player.strip()
        status = status.strip().lower()
        if status == "playing":
            return player
        if status == "paused" and paused is None:
            paused = player
    return paused


def status_payload():
    player = active_player()
    if not player:
        return {"playing": False}

    fmt = "{{playerName}}\t{{status}}\t{{artist}}\t{{title}}\t{{album}}\t{{mpris:length}}\t{{position}}\t{{mpris:artUrl}}"
    row = run_playerctl("-p", player, "metadata", "--format", fmt)
    parts = row.split("\t", 7)
    parts += [""] * (8 - len(parts))
    _, status, artist, title, album, length, position, art = parts[:8]
    try:
        length_us = int(length or 0)
    except ValueError:
        length_us = 0
    try:
        position_us = int(position or 0)
    except ValueError:
        position_us = 0
    return {
        "active": status.lower() in {"playing", "paused"},
        "playing": status.lower() == "playing",
        "player": player,
        "artist": artist,
        "title": title,
        "album": album,
        "length": length_us,
        "position": position_us,
        "art": art,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/status":
            self._send(status_payload())
        elif parsed.path == "/command":
            cmd = urllib.parse.parse_qs(parsed.query).get("cmd", [""])[0]
            self._command(cmd)
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/command":
            self._send({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            data = {}
        self._command(str(data.get("cmd", "")))

    def _command(self, cmd):
        if cmd not in {"play-pause", "previous", "next"}:
            self._send({"ok": False, "error": "invalid command"}, 400)
            return
        player = active_player()
        if not player:
            self._send({"ok": False, "error": "no active player"}, 409)
            return
        try:
            subprocess.run(
                ["playerctl", "-p", player, cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.2,
                check=False,
            )
            self._send({"ok": True})
        except subprocess.SubprocessError:
            self._send({"ok": False, "error": "command failed"}, 500)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"Desk Dock media bridge: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
