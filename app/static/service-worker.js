/* service-worker.js
   Imago English (v2) — safe caching for auth apps
   - Cache ONLY static assets
   - NEVER cache HTML navigations (prevents login loops)
   - Clean up old caches on update
*/

const CACHE_VERSION = "v3";
const CACHE_NAME = `imago-v2-cache-${CACHE_VERSION}`;

// Only precache truly static assets (NO "/" and NO "/dashboard")
const STATIC_ASSETS = [
  "/static/css/styles.css",
  "/static/img/icons/icon-192.png",
  "/static/img/icons/icon-512.png",
  "/static/img/icons/maskable-icon.png",
  "/static/img/icons/apple-touch-icon.png",
];

// Install: precache static assets and activate ASAP
self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(STATIC_ASSETS);
    })()
  );
});

// Activate: delete old caches and take control immediately
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => k.startsWith("imago-v2-cache-") && k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      );
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1) Don’t touch cross-origin requests (e.g. accounts.google.com)
  if (url.origin !== self.location.origin) return;

  // 2) Never cache auth or API routes
  if (url.pathname.startsWith("/auth/") || url.pathname.startsWith("/api/")) {
    // Let the browser handle it normally (network)
    return;
  }

  // 3) Never cache navigations (HTML pages). This prevents “logged-out HTML” being
  //    served after login and causing redirect loops.
  if (req.mode === "navigate") {
    event.respondWith(fetch(req));
    return;
  }

  // 4) Cache-first ONLY for static files
  const isStatic =
    url.pathname.startsWith("/static/") ||
    /\.(?:css|js|png|jpg|jpeg|svg|webp|ico|woff2?|ttf|eot)$/.test(url.pathname);

  if (!isStatic) {
    // For anything else (non-static), use network
    event.respondWith(fetch(req));
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(req);
      if (cached) return cached;

      const res = await fetch(req);

      // Only cache successful basic/opaque responses
      if (res && (res.type === "basic" || res.type === "opaque") && res.status === 200) {
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, res.clone());
      }

      return res;
    })()
  );
});
