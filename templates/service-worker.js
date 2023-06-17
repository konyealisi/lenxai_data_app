const CACHE_NAME = 'my-cache';
const OFFLINE_CACHE_NAME = 'my-offline-cache';
const OFFLINE_URL = '/offline.html';

const offlineResponse = new Response(
  `<html><body><h1>You are offline</h1></body></html>`,
  {
    headers: { 'Content-Type': 'text/html' },
  }
);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll([OFFLINE_URL]);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName))
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (
          !navigator.onLine &&
          !event.request.url.includes('socket.io') &&
          !event.request.url.includes('/api/')
        ) {
          const responseClone = response.clone();
          caches.open(OFFLINE_CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        if (
          !navigator.onLine &&
          !event.request.url.includes('socket.io') &&
          !event.request.url.includes('/api/')
        ) {
          return caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            return offlineResponse;
          });
        }
      })
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag === 'upload-data') {
    event.waitUntil(uploadData());
  }
});

function uploadData() {
  return caches.open(OFFLINE_CACHE_NAME).then((cache) => {
    return cache.keys().then((keys) => {
      const promises = keys.map((request) => {
        return cache.match(request).then((response) => {
          return fetch(request).then((fetchResponse) => {
            if (fetchResponse.ok) {
              return cache.delete(request);
            }
          });
        });
      });
      return Promise.all(promises);
    });
  });
}

self.addEventListener('online', (event) => {
  event.waitUntil(uploadData());
});
