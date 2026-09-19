# CityNexus V18.3 Mobile / PWA / Offline Reference

This document describes the mobile and offline behavior of the isolated
reference app. It is a compatibility reference for the existing CityNexus PWA,
not a second PWA framework.

## 1. Viewport matrix

| Viewport | Project | Purpose |
| --- | --- | --- |
| 430x932 | `mobile-large-chromium` | large phone / comfortable |
| 390x844 | `mobile-chromium` | primary mobile target |
| 320x720 | `mobile-small-chromium` | small-device sanity |
| 1280x720 | `desktop-1280-chromium` | compact desktop |
| 1440x900 | `desktop-chromium` | primary desktop |

Checks: no horizontal overflow, primary action visible, runtime identity
visible, approval visible, protected commitment visible, 44px touch targets,
safe-area insets, orientation/resize stability.

## 2. Bottom navigation

`Today / Map / Copilot / Wallet / Me`. The nav uses
`env(safe-area-inset-bottom)` and keeps a minimum 44px target per item.

## 3. Map bottom sheet

States `24% / 55% / 90%` with pointer drag, keyboard arrows/Home/End,
`role="slider"`, `aria-valuetext`, snap thresholds, and no heavy gesture
dependency. Resize/orientation resets the drag offset so the snap state stays
valid.

## 4. Offline and stale truth

`OfflineSnapshotAdapter` returns `source: "OFFLINE"` and a `lastUpdated` stamp.
The UI shows `OFFLINE / STALE`, a last-updated line, and disables destructive
approval actions. Reconnect triggers adapter refresh; stale data is never
rendered as `LIVE`.

## 5. PWA compatibility

The existing CityNexus main tree already has:
- `frontend/public/manifest.webmanifest`
- `frontend/public/sw.js`
- VitePWA/Workbox production worker in `frontend/vite.config.ts`

The V18.3 reference therefore adds only an optional, compatible shell:
- `public/manifest.webmanifest` with `start_url: ./index.html#/journey`
- `public/v18.3-sw.js` with cache-first shell + network-first API +
  `OFFLINE_STALE_SNAPSHOT` JSON for failed API reads
- `src/pwa/serviceWorker.ts` gated by `VITE_ENABLE_PWA === "1"`

Do not register a second worker in the host app. If the host wants PWA
behavior, reuse its existing Workbox worker and only borrow the offline/truth
state machine from this reference.

## 6. Tests

Playwright covers all viewports, map sheet states, offline banner, reconnect
recovery, and destructive-action-disabled behavior. The service worker is
disabled by default so tests remain deterministic; patch 04 enables it
explicitly.
