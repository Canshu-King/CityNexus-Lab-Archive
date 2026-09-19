import type { MapCameraCommand } from "./types";

export type MotionToken = "instant" | "fast" | "base" | "slow" | "map";

const TOKEN_MS: Record<MotionToken, number> = {
  instant: 90,
  fast: 160,
  base: 220,
  slow: 420,
  map: 650,
};

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function motionDuration(token: MotionToken): number {
  // Reduced motion collapses tokens to 0ms; callers still use the token API.
  return prefersReducedMotion() ? 0 : TOKEN_MS[token];
}

export const MOTION_TOKENS_MS = TOKEN_MS;

type ViewTransitionDocument = Document & {
  startViewTransition?: (update: () => void | Promise<void>) => { finished: Promise<void> };
};

/**
 * Progressive enhancement for route changes. When the View Transition API is
 * unavailable or the traveler asked for reduced motion, the update is applied
 * synchronously with no animation.
 */
export function withViewTransition(update: () => void): void {
  const doc = document as ViewTransitionDocument;
  if (prefersReducedMotion() || !doc.startViewTransition) {
    update();
    return;
  }
  doc.startViewTransition(update);
}

/**
 * MapLibre camera contract. The reference app works without network tiles, but
 * the API shape and duration tokens are the same contract Codex can merge.
 */
export function mapCameraOptions(command: MapCameraCommand): {
  center?: [number, number];
  zoom?: number;
  duration: number;
} {
  return {
    center: command.center,
    zoom: command.zoom,
    duration: command.animate ? motionDuration(command.duration_token) : 0,
  };
}

export function fitBoundsOptions(command: MapCameraCommand): {
  bounds: [[number, number], [number, number]] | undefined;
  duration: number;
  padding: number;
} {
  return {
    bounds: command.bounds,
    duration: command.animate ? motionDuration(command.duration_token) : 0,
    padding: 48,
  };
}

/** Keeps the <html data-reduced-motion> hook in sync for CSS and tests. */
export function syncReducedMotionAttribute(): () => void {
  const apply = () => {
    document.documentElement.setAttribute(
      "data-reduced-motion",
      prefersReducedMotion() ? "true" : "false",
    );
  };
  apply();
  const query = window.matchMedia("(prefers-reduced-motion: reduce)");
  query.addEventListener?.("change", apply);
  return () => query.removeEventListener?.("change", apply);
}
