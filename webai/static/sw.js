const CACHE_NAME = 'orgchat-offline-ve4d19b';
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
                url: data.url || '/',
                call: !!data.call
            }
        };
        // แจ้งเตือนซ้อนทับแทนที่จะสะสม (เช่น สายเข้าซ้ำ) และสายเข้าต้องค้างบนหน้าจอ + สั่น จนกว่าจะแตะ
        if (data.tag) options.tag = data.tag;
        if (data.renotify) options.renotify = true;
        if (data.require_interaction) options.requireInteraction = true;
        if (Array.isArray(data.vibrate)) options.vibrate = data.vibrate;

        // ผู้ใช้กำลังดูแอปอยู่ (หน้าต่างโฟกัส) → ไม่เด้งแจ้งเตือนระบบซ้ำ (ในแอปมีตัวเลข/โทสต์อยู่แล้ว); สายเข้ายังเด้งเสมอ
        event.waitUntil(
            clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
                const looking = list.some(function (c) { return c.visibilityState === 'visible' && c.focused; });
                if (looking && !data.call) return;
                return self.registration.showNotification(data.title || 'OrgChat AI', options);
            })
        );
    } catch (e) {
        console.error('[SW] Push notification error:', e);
    }
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/';
    const isCall = !!(event.notification.data && event.notification.data.call);
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
            // มีหน้าต่างแอปเปิดอยู่แล้ว → โฟกัสอย่างเดียว (สายเข้าจะมาทางซ็อกเก็ตเอง ห้ามรีโหลดจนสายหาย); ไม่มี → เปิดแอป
            for (const c of list) {
                if ('focus' in c) {
                    return c.focus().then(function () {
                        if (!isCall && 'navigate' in c && url && url !== '/') { try { return c.navigate(url); } catch (e) { } }
                    });
                }
            }
            return clients.openWindow(url);
        })
    );
});
