import type { CSSProperties } from "react";

const VISUALLY_HIDDEN: CSSProperties = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
  border: 0,
};

/**
 * Screen-reader live region.
 *
 * Default: `role="status"` + `aria-live="polite"`.
 * `assertive` switches to `role="alert"` + `aria-live="assertive"` for
 * genuinely urgent lifecycle transitions only.
 *
 * 中文说明：默认 polite；仅紧急生命周期变化使用 assertive。
 */
export function LiveRegion({
  message,
  assertive = false,
  className,
}: {
  message: string;
  assertive?: boolean;
  className?: string;
}) {
  return (
    <div
      className={className ? `cnx-live-region ${className}` : "cnx-live-region"}
      data-testid="live-region"
      data-live-mode={assertive ? "assertive" : "polite"}
      role={assertive ? "alert" : "status"}
      aria-live={assertive ? "assertive" : "polite"}
      aria-atomic="true"
      style={VISUALLY_HIDDEN}
    >
      {message}
    </div>
  );
}
