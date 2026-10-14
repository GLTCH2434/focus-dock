#!/usr/bin/env python3
"""Desk Dock media bridge (Linux).

A tiny local web server that lets the Desk Dock page see and control whatever
is playing on this computer (Spotify, browser tabs, VLC, ...) through MPRIS,
using the `playerctl` command.

Needs:  python3 and playerctl      (sudo apt install playerctl)
Run:    python3 media_bridge.py --origin https://YOURNAME.github.io

Safety: it only listens on 127.0.0.1 (this computer), and it only answers pages
from the origins you list with --origin, so other websites cannot control your media.
"""
import argparse, json, mimetypes, os, subprocess, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

PORT = 8765
ALLOWED_ORIGINS = set()
ALLOWED_HOSTS = {'127.0.0.1:%d' % PORT, 'localhost:%d' % PORT}   # blocks DNS-rebinding tricks
COMMANDS = {'previous': 'previous', 'next': 'next', 'play-pause': 'play-pause'}
# one line per field, separated by a tab; empty fields stay empty
FORMAT = '{{status}}\t{{playerName}}\t{{artist}}\t{{title}}\t{{mpris:artUrl}}\t{{mpris:length}}\t{{position}}'


def playerctl(*args):
    """Runs playerctl and returns (ok, stdout). Never raises."""
    try:
        p = subprocess.run(['playerctl', *args], capture_output=True, text=True, timeout=3)
        return p.returncode == 0, p.stdout
    except FileNotFoundError:
        return False, 'playerctl-missing'
    except subprocess.TimeoutExpired:
        return False, ''


def read_state():
    ok, out = playerctl('metadata', '--format', FORMAT)
    if not ok:
        return {'active': False, 'error': 'playerctl is not installed' if out == 'playerctl-missing' else ''}
    f = (out.rstrip('\n').split('\t') + [''] * 7)[:7]
    status, player, artist, title, art, length, pos = f

    def secs(us):                       # MPRIS gives microseconds; the page wants seconds
        try:
            return max(0.0, int(us) / 1_000_000)
        except ValueError:
            return 0.0
    # file:// art cannot be shown by a web page, so we serve it through /art (see below)
    art_url = '/art' if art.startswith('file://') else art
    return {'active': True, 'playing': status == 'Playing', 'player': player, 'artist': artist,
            'title': title, 'art': art_url, 'length': secs(length), 'position': secs(pos),
            '_art_raw': art}


class Handler(BaseHTTPRequestHandler):
    server_version = 'DeskDockBridge'

    def log_message(self, *a):          # keep the terminal quiet
        pass

    def origin_ok(self):
        o = self.headers.get('Origin')
        return o is None or o in ALLOWED_ORIGINS      # no Origin = curl/local tool, fine

    def cors(self):
        o = self.headers.get('Origin')
        if o in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', o)
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            # Chrome/Brave ask permission before a public page may talk to a local server
            self.send_header('Access-Control-Allow-Private-Network', 'true')
            self.send_header('Access-Control-Max-Age', '600')

    def send(self, code, body=b'', ctype='application/json'):
        self.send_response(code)
        self.cors()
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def guard(self):
        if self.headers.get('Host') not in ALLOWED_HOSTS:
            self.send(403, b'{"error":"bad host"}'); return False
        if not self.origin_ok():
            self.send(403, b'{"error":"origin not allowed"}'); return False
        return True

    def do_OPTIONS(self):
        if not self.guard(): return
        self.send(204)

    def do_GET(self):
        if not self.guard(): return
        path = urlparse(self.path).path
        if path == '/status':
            st = read_state(); st.pop('_art_raw', None)
            self.send(200, json.dumps(st).encode())
        elif path == '/art':
            raw = read_state().get('_art_raw', '')
            if not raw.startswith('file://'):
                return self.send(404, b'{}')
            fp = os.path.realpath(unquote(urlparse(raw).path))     # ONLY the file the player reports right now
            ctype = mimetypes.guess_type(fp)[0] or ''
            if not ctype.startswith('image/') or not os.path.isfile(fp):
                return self.send(404, b'{}')
            with open(fp, 'rb') as fh:
                self.send(200, fh.read(), ctype)
        else:
            self.send(404, b'{}')

    def do_POST(self):
        if not self.guard(): return
        if urlparse(self.path).path != '/command':
            return self.send(404, b'{}')
        try:
            n = min(int(self.headers.get('Content-Length', 0)), 1024)
            cmd = json.loads(self.rfile.read(n) or b'{}').get('cmd')
        except Exception:
            return self.send(400, b'{"error":"bad request"}')
        if cmd not in COMMANDS:
            return self.send(400, b'{"error":"unknown command"}')
        ok, _ = playerctl(COMMANDS[cmd])
        self.send(200 if ok else 502, json.dumps({'ok': ok}).encode())


def main():
    global PORT
    ap = argparse.ArgumentParser(description='Desk Dock media bridge')
    ap.add_argument('--origin', action='append', default=[], metavar='URL',
                    help='page allowed to use the bridge, e.g. https://YOURNAME.github.io (repeatable)')
    ap.add_argument('--port', type=int, default=PORT)
    a = ap.parse_args()
    if not a.origin:
        sys.exit('Please give your dock page address, e.g.\n  python3 media_bridge.py --origin https://YOURNAME.github.io')
    PORT = a.port
    ALLOWED_HOSTS.clear(); ALLOWED_HOSTS.update({'127.0.0.1:%d' % PORT, 'localhost:%d' % PORT})
    ALLOWED_ORIGINS.update(o.rstrip('/') for o in a.origin)
    ok, out = playerctl('--version')
    if not ok:
        print('WARNING: playerctl not found. Install it first:  sudo apt install playerctl')
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print('Desk Dock media bridge on http://127.0.0.1:%d for %s' % (PORT, ', '.join(sorted(ALLOWED_ORIGINS))))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
