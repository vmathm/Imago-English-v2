const CACHE_NAME = "imago-v2-cache";
const STATIC_ASSETS = [
  "/",
  "/static/css/styles.css",
  "/static/img/icons/icon-192.png",
  "/static/img/icons/icon-512.png"
];

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 1) Don’t touch cross-origin requests (e.g. accounts.google.com)
  if (url.origin !== self.location.origin) {
    return; // Let the browser handle it normally
  }

  // 2) Optionally: don’t cache auth or API routes
  if (url.pathname.startsWith("/auth/") || url.pathname.startsWith("/api/")) {
    return;
  }

  // 3) Cache-first for *static* same-origin assets only
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
