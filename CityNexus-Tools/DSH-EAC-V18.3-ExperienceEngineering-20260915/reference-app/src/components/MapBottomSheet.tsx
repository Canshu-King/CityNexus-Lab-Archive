import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { useT } from "../i18n";
import { testIds } from "../testids";

export type SheetState = "24" | "55" | "90";

const ORDER: SheetState[] = ["24", "55", "90"];

export function MapBottomSheet({
  children,
  onStateChange,
}: {
  children: (state: SheetState) => ReactNode;
  onStateChange?: (state: SheetState) => void;
}) {
  const t = useT();
  const [state, setState] = useState<SheetState>("55");
  const [dragOffset, setDragOffset] = useState(0);
  const dragStart = useRef<{ y: number; state: SheetState } | null>(null);

  const update = (next: SheetState) => {
    setState(next);
    setDragOffset(0);
    onStateChange?.(next);
  };

  // Orientation / resize keeps the snap state valid without remounting.
  useEffect(() => {
    const onResize = () => setDragOffset(0);
    window.addEventListener("resize", onResize);
    window.addEventListener("orientationchange", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("orientationchange", onResize);
    };
  }, []);

  const onPointerDown = (event: ReactPointerEvent) => {
    dragStart.current = { y: event.clientY, state };
    (event.target as HTMLElement).setPointerCapture?.(event.pointerId);
  };

  const onPointerMove = (event: ReactPointerEvent) => {
    if (!dragStart.current) return;
    setDragOffset(event.clientY - dragStart.current.y);
  };

  const onPointerUp = (event: ReactPointerEvent) => {
    if (!dragStart.current) return;
    const delta = event.clientY - dragStart.current.y;
    const index = ORDER.indexOf(dragStart.current.state);
    if (delta > 48 && index > 0) update(ORDER[index - 1]);
    else if (delta < -48 && index < ORDER.length - 1) update(ORDER[index + 1]);
    else setDragOffset(0);
    dragStart.current = null;
  };

  const heights: Record<SheetState, string> = { "24": "24%", "55": "55%", "90": "90%" };

  return (
    <div
      className="sheet"
      data-testid={testIds.mapSheet}
      data-sheet-state={state}
      style={{ "--sheet-height": heights[state], "--sheet-drag": `${dragOffset}px` } as CSSProperties}
    >
      <div
        className="sheet__handle"
        data-testid={testIds.sheetHandle}
        role="slider"
        aria-label="Map sheet height"
        aria-orientation="vertical"
        aria-valuemin={24}
        aria-valuemax={90}
        aria-valuenow={Number(state)}
        aria-valuetext={`${state} percent`}
        tabIndex={0}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onKeyDown={(event: ReactKeyboardEvent<HTMLDivElement>) => {
          const index = ORDER.indexOf(state);
          if (event.key === "ArrowUp") update(ORDER[Math.min(ORDER.length - 1, index + 1)]);
          if (event.key === "ArrowDown") update(ORDER[Math.max(0, index - 1)]);
          if (event.key === "Home") update("24");
          if (event.key === "End") update("90");
        }}
      />
      <div className="sheet__tabs" role="tablist" aria-label="Map sheet state">
        {ORDER.map((value) => (
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
