# Desk Dock

[Live Demo →](https://gltch2434.github.io/focus-dock/)

A minimal, installable web app for a secondary screen. Clock, notes, Pomodoro focus timer, and generative white/pink/brown noise — all in a single file with zero dependencies.

## Features

- **Clock & Date** — 12h/24h toggle (click the time)
- **Notes** — Persistent todo list with click-to-complete, stored locally
- **Focus Timer** — Pomodoro-style sessions (focus / break / long break) with auto-switching and daily session count
- **White Noise** — White, pink, and brown noise generated via Web Audio API (no audio files)
  - Volume & softness (low-pass filter) controls
  - Sleep timer (15 min – 2 hours)
- **Customizable Colours** — Four animated gradient blobs with 5 presets + per-blob colour pickers
- **Fullscreen + Wake Lock** — Stays awake in fullscreen mode
- **PWA / Installable** — Add to home screen, works offline via service worker
- **Idle Mode** — UI fades after 5s of inactivity for a clean ambient look

## Quick Start

```bash
# Serve locally (required for service worker / PWA features)
npx serve .
# or
python3 -m http.server 8000
```

Open `http://localhost:3000` (or `8000`) in your browser.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Click time` | Toggle 12h / 24h |
| `Click note` | Mark complete/incomplete |
| `Enter` (in note input) | Add note |
| `Escape` | Close menu |
| `Click pill` (on dock) | Start next session or open Focus tab |

## Tech Stack

- Single `index.html` (~530 lines) — HTML, CSS, and vanilla JS
- Web Audio API for noise generation
- `localStorage` for persistence
- Service Worker (`sw.js`) for offline caching
- Web App Manifest for installability

## Customization

Edit the CSS variables at the top of `index.html` to re-theme:

```css
:root {
  --bg: #0a0f1c;        /* background */
  --ink: #eef0f8;       /* text */
  --dim: rgba(238,240,248,.55);
  --glass: rgba(255,255,255,.07);
  --edge: rgba(255,255,255,.16);
  --b1: #6d5efc;        /* blob 1 */
  --b2: #19c3b1;        /* blob 2 */
  --b3: #ff6f91;        /* blob 3 */
  --b4: #f5b94a;        /* blob 4 */
}
```

## License

MIT