/* CityNexus V18.3 experience reference service worker (optional merge patch 04). */
const CACHE = "citynexus-v18.3-experience-v1";
const APP_SHELL = ["./", "./index.html", "./manifest.webmanifest", "./favicon.svg"];
const LAST_UPDATED_KEY = "citynexus.v18.3.lastUpdated";

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

async function touchLastUpdated() {
  const stamp = new Date().toISOString();
  await caches.open(CACHE).then((cache) => cache.put(LAST_UPDATED_KEY, new Response(JSON.stringify({ lastUpdated: stamp }))));
  return stamp;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // API truth is network-first; never serve stale API as if it were current.
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(request)
        .then(async (response) => {
          await touchLastUpdated();
          return response;
        })
        .catch(
          () =>
            new Response(JSON.stringify({ detail: "OFFLINE_STALE_SNAPSHOT", lastUpdated: null }), {
              status: 503,
              headers: { "content-type": "application/json", "x-citynexus-offline": "true" },
            }),
        ),
    );
    return;
  }

  // App shell: stale-while-revalidate.
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then(async (response) => {
          const copy = response.clone();
          const cache = await caches.open(CACHE);
          await cache.put(request, copy);
          await touchLastUpdated();
          return response;
        })
        .catch(() => cached ?? caches.match("./index.html"));
      return cached ?? network;
    }),
  );
});
