/**
 * PWA registration is opt-in so the reference app and its Playwright suite are
 * deterministic. The optional merge patch 04 sets VITE_ENABLE_PWA=1.
 */
export function registerExperienceServiceWorker(): void {
  if (import.meta.env.VITE_ENABLE_PWA !== "1") return;
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./v18.3-sw.js", { scope: "./" })
      .catch(() => {
        // Offline registration failure must never break the live experience.
      });
  });
}
