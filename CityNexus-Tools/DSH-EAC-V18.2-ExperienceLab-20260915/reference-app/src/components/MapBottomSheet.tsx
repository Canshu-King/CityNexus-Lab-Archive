import { useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import { useT } from "../i18n";
import { testIds } from "../testids";

export type SheetState = "24" | "55" | "90";

export function MapBottomSheet({
  children,
  onStateChange,
}: {
  children: (state: SheetState) => ReactNode;
  onStateChange?: (state: SheetState) => void;
}) {
  const t = useT();
  const [state, setState] = useState<SheetState>("55");
  const dragStart = useRef<{ y: number; state: SheetState } | null>(null);

  const update = (next: SheetState) => {
    setState(next);
    onStateChange?.(next);
  };

  const onPointerDown = (event: ReactPointerEvent) => {
    dragStart.current = { y: event.clientY, state };
    (event.target as HTMLElement).setPointerCapture?.(event.pointerId);
  };

  const onPointerUp = (event: ReactPointerEvent) => {
    if (!dragStart.current) return;
    const delta = dragStart.current.y - event.clientY;
    if (Math.abs(delta) > 40) {
      const order: SheetState[] = ["24", "55", "90"];
      const index = order.indexOf(dragStart.current.state);
      update(order[Math.max(0, Math.min(order.length - 1, index + (delta > 0 ? 1 : -1)))]);
    }
    dragStart.current = null;
  };

  const heights: Record<SheetState, string> = { "24": "24%", "55": "55%", "90": "90%" };

  return (
    <div
      className="sheet"
      data-testid={testIds.mapSheet}
      data-sheet-state={state}
      style={{ "--sheet-height": heights[state] } as CSSProperties}
    >
      <div
        className="sheet__handle"
        data-testid={testIds.sheetHandle}
        role="slider"
        aria-label="Map sheet height"
        aria-valuemin={24}
        aria-valuemax={90}
        aria-valuenow={Number(state)}
        tabIndex={0}
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        onKeyDown={(event: ReactKeyboardEvent<HTMLDivElement>) => {
          const order: SheetState[] = ["24", "55", "90"];
          const index = order.indexOf(state);
          if (event.key === "ArrowUp") update(order[Math.min(order.length - 1, index + 1)]);
          if (event.key === "ArrowDown") update(order[Math.max(0, index - 1)]);
        }}
      />
      <div className="sheet__tabs" role="tablist" aria-label="Map sheet state">
        {(["24", "55", "90"] as SheetState[]).map((value) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={state === value}
            className={`sheet__tab${state === value ? " active" : ""}`}
            data-testid={value === "24" ? testIds.sheet24 : value === "55" ? testIds.sheet55 : testIds.sheet90}
            onClick={() => update(value)}
          >
            {t(value === "24" ? "map.sheet24" : value === "55" ? "map.sheet55" : "map.sheet90")}
          </button>
        ))}
      </div>
      <div className="sheet__content" data-sheet-content={state}>
        {children(state)}
      </div>
    </div>
  );
}
