self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1) Don’t touch cross-origin requests (e.g. accounts.google.com)
  if (url.origin !== self.location.origin) return;

  // 2) Never cache auth or API routes
  if (url.pathname.startsWith("/auth/") || url.pathname.startsWith("/api/")) {
    return;
  }

  // 3) Never cache navigations (HTML pages). Let the browser handle it.
  if (req.mode === "navigate") {
    return;  // Don't intercept navigation requests
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


// service-worker.js
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
