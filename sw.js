/* Service worker: saves a copy of the dock on the device so it opens instantly
   and keeps working with no internet (the font falls back to the system font). */

// Bump this number whenever you change any file, so devices fetch the new version.
const CACHE = 'desk-dock-v1';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon.svg',
               './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];

// On install: download and store all the app files.
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

// On activate: delete caches left over from older versions.
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// On every request: try the network first (so updates show up), save a copy,
// and if the network is down, use the saved copy instead.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
