const CACHE_NAME = 'happy-farm-2d-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Let network handle requests, with fallback
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
