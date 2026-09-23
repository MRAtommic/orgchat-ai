const CACHE_NAME = 'orgchat-offline-v2';
const OFFLINE_URL = '/static/offline.html';

const ASSETS_TO_CACHE = [
    '/static/style.css',
    '/static/icon-192.png',
    '/static/offline.html'
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(ASSETS_TO_CACHE).catch(function(err) {
                console.warn('[SW] Cache addAll warning:', err);
            });
        }).then(function () {
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (cacheNames) {
            return Promise.all(
                cacheNames.map(function (cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(function () {
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', function (event) {
    // Only handle GET requests for navigation/offline fallback
    if (event.request.method !== 'GET') return;

    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(function () {
                return caches.match(OFFLINE_URL);
            })
        );
        return;
    }

    // Network-first for JavaScript files to always serve fresh code
    if (event.request.url.includes('/static/js/')) {
        event.respondWith(
            fetch(event.request).then(function (networkResponse) {
                if (networkResponse && networkResponse.status === 200) {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(function (cache) {
                        cache.put(event.request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(function () {
                return caches.match(event.request);
            })
        );
        return;
    }

    // Cache-first for other static assets (CSS/Icons/Images), Network-fallback
    if (event.request.url.includes('/static/')) {
        event.respondWith(
            caches.match(event.request).then(function (cachedResponse) {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(event.request).then(function (networkResponse) {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then(function (cache) {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return networkResponse;
                }).catch(function () {
                    // Return nothing or cached version
                });
            })
        );
    }
});

self.addEventListener('push', function (event) {
    try {
        const data = event.data ? event.data.json() : { title: 'OrgChat AI', body: 'มีการแจ้งเตือนใหม่' };
        const options = {
            body: data.body || '',
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png',
            data: {
                url: data.url || '/'
            }
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'OrgChat AI', options)
        );
    } catch (e) {
        console.error('[SW] Push notification error:', e);
    }
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});
