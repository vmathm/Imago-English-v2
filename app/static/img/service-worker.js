const CACHE_NAME = 'ImagoEnglishCache';
const urlsToCache = [
    '/',
    '/static/styles.css',  // Adjust the path to your CSS file
    '/static/imagologo.png',  // Adjust the path to your image file
    // Add more paths to cache as needed
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(ImagoEnglishCache).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );  
});