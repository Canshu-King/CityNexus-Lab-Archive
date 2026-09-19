import { useEffect, useState } from "react";

export interface OnlineStatus {
  online: boolean;
  lastChangedAt: string;
}

export function useOnlineStatus(): OnlineStatus {
  const [state, setState] = useState<OnlineStatus>(() => ({
    online: typeof navigator === "undefined" ? true : navigator.onLine,
    lastChangedAt: new Date().toISOString(),
  }));

  useEffect(() => {
    const update = () => setState({ online: navigator.onLine, lastChangedAt: new Date().toISOString() });
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  return state;
}

export function useLastUpdated(kind: "live" | "offline"): string | null {
  const [stamp, setStamp] = useState<string | null>(null);
  useEffect(() => {
    if (kind !== "offline") return undefined;
    const raw = window.localStorage.getItem("citynexus.v18.3.lastUpdated");
    setStamp(raw);
    return undefined;
  }, [kind]);
  return stamp;
}
