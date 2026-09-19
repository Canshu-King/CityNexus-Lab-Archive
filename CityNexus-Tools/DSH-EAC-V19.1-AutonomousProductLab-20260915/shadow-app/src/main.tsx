import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { CapabilityShadowExperience } from "../../lab/runtime/frontend/src/features/capability-experience/CapabilityShadowExperience";
import { scenarioById } from "../../lab/runtime/frontend/src/features/capability-experience/recordedFixture";
import "../../lab/runtime/frontend/src/features/capability-experience/styles/capability-experience.css";
import "./shadow.css";

interface ShadowIds {
  travelerId: string;
  journeyId: string;
  placeId: string;
}

function idsFromUrl(): ShadowIds {
  const params = new URLSearchParams(window.location.search);
  return {
    travelerId: params.get("traveler_id") ?? "",
    journeyId: params.get("journey_id") ?? "",
    placeId: params.get("place_id") ?? "",
  };
}

async function loadDemoIds(): Promise<ShadowIds> {
  const response = await fetch("/api/v1/demo/reset", { method: "POST" });
  if (!response.ok) throw new Error(`demo reset failed: ${response.status}`);
  const body = (await response.json()) as { traveler_id?: string; journey_id?: string };
  return { travelerId: body.traveler_id ?? "", journeyId: body.journey_id ?? "", placeId: "" };
}

function App() {
  const [ids, setIds] = useState<ShadowIds>(() => idsFromUrl());
  const [error, setError] = useState("");
  useEffect(() => {
    if (ids.travelerId && ids.journeyId) return;
    void loadDemoIds()
      .then((next) => setIds((current) => ({ ...next, placeId: current.placeId })))
      .catch((reason) => setError(String(reason)));
  }, [ids.journeyId, ids.travelerId]);

  const locale = window.location.search.includes("lang=en") ? "en" : "zh-CN";
  return (
    <div className="shadow-shell">
      <header className="shadow-header">
        <div>
          <span className="shadow-badge">V19.1 SHADOW</span>
          <h1>CityNexus Autonomous Product Lab</h1>
          <p>
            Live shadow data from the isolated V19 backend on port 8052. This page never calls the main
            worktree.
          </p>
        </div>
        <div className="shadow-ids">
          <code>traveler_id={ids.travelerId || "..."}</code>
          <code>journey_id={ids.journeyId || "..."}</code>
          <code>place_id={ids.placeId || "..."}</code>
        </div>
      </header>
      <main className="shadow-main">
        {error ? <p className="shadow-error" role="alert">{error}</p> : null}
        {ids.travelerId || ids.journeyId ? (
          <CapabilityShadowExperience
            baseUrl=""
            initialTravelerId={ids.travelerId}
            initialJourneyId={ids.journeyId}
            initialPlaceId={ids.placeId}
            locale={locale}
            fixtureCapabilities={scenarioById("A").capabilities}
          />
        ) : (
          <p className="shadow-error" role="status">Waiting for isolated backend demo ids…</p>
        )}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
