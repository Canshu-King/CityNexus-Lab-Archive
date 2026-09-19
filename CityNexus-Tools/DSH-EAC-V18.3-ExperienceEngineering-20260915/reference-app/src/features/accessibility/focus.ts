/**
 * Small dependency-free focus helpers for dialogs, sheets, and overlays.
 * 中文说明：无外部依赖的焦点管理工具。
 */

export const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "summary:not(:disabled)",
  "audio[controls]",
  "video[controls]",
  "[contenteditable='true']",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

function isFocusable(element: Element): boolean {
  const html = element as HTMLElement;
  if (typeof html.focus !== "function") return false;
  if (html.hasAttribute("disabled")) return false;
  if (html.getAttribute("aria-hidden") === "true") return false;
  if (html.hidden) return false;
  if (html.getAttribute("tabindex") === "-1" && html.getAttribute("contenteditable") !== "true") {
    return false;
  }
  if (typeof window !== "undefined" && typeof window.getComputedStyle === "function") {
    const style = window.getComputedStyle(html);
    if (style.display === "none" || style.visibility === "hidden") return false;
  }
  return true;
}

/** Returns keyboard-focusable elements in document order. */
export function getFocusable(
  container: ParentNode | null | undefined,
): HTMLElement[] {
  if (!container) return [];
  const nodes = container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
  return Array.from(nodes).filter(isFocusable);
}

/** Focuses the first focusable element and returns it, or `null` if none exist. */
export function focusFirst(
  container: ParentNode | null | undefined,
): HTMLElement | null {
  const first = getFocusable(container)[0] ?? null;
  if (first) first.focus();
  return first;
}

function containsNode(container: ParentNode, node: Element | null): boolean {
  if (!node) return false;
  const asNode = container as Node;
  return typeof asNode.contains === "function" ? asNode.contains(node) : false;
}

/**
 * Handles a Tab keydown event for a focus trap.
 * Returns `true` when the event was handled and default navigation prevented.
 */
export function trapFocus(
  container: ParentNode | null | undefined,
  event: KeyboardEvent,
): boolean {
  if (!container || event.key !== "Tab") return false;
  const focusable = getFocusable(container);
  if (focusable.length === 0) return false;

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = typeof document !== "undefined" ? document.activeElement : null;
  const activeElement =
    active && typeof Element !== "undefined" && active instanceof Element ? active : null;

  if (event.shiftKey) {
    if (activeElement === first || !containsNode(container, activeElement)) {
      event.preventDefault();
      last.focus();
      return true;
    }
    return false;
  }

  if (activeElement === last || !containsNode(container, activeElement)) {
    event.preventDefault();
    first.focus();
    return true;
  }
  return false;
}

/** Restores focus when the element is still available. */
export function restoreFocus(element: HTMLElement | null | undefined): boolean {
  if (!element || typeof element.focus !== "function") return false;
  try {
    element.focus();
    return true;
  } catch {
    return false;
  }
}
