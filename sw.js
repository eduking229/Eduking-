// Eduking 229 Service Worker
const CACHE = 'eduking229-v1';
const ASSETS = [
  '/Eduking-/launcher-22.html',
  '/Eduking-/manifest.json',
  '/Eduking-/icon-192.png',
  '/Eduking-/icon-512.png'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE).then(function(cache) {
      return cache.addAll(ASSETS);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});