import { useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import { useT } from "../i18n";
import { testIds } from "../testids";

export type SheetState = "24" | "55" | "90";

export function MapBottomSheet({ children }: { children: ReactNode }) {
  const t = useT();
  const [state, setState] = useState<SheetState>("55");
  const dragStart = useRef<{ y: number; state: SheetState } | null>(null);

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
      setState(order[Math.max(0, Math.min(order.length - 1, index + (delta > 0 ? 1 : -1)))]);
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
          if (event.key === "ArrowUp") setState(order[Math.min(order.length - 1, index + 1)]);
          if (event.key === "ArrowDown") setState(order[Math.max(0, index - 1)]);
        }}
      />
      <div className="sheet__tabs">
        {(["24", "55", "90"] as SheetState[]).map((value) => (
          <button
            key={value}
            type="button"
            className={`sheet__tab${state === value ? " active" : ""}`}
            data-testid={value === "24" ? testIds.sheet24 : value === "55" ? testIds.sheet55 : testIds.sheet90}
            onClick={() => setState(value)}
            aria-pressed={state === value}
          >
            {t(`map.sheet${value}`)}
          </button>
        ))}
      </div>
      <div className="sheet__content">{children}</div>
    </div>
  );
}
