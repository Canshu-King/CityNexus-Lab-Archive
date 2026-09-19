import { useState } from "react";
import { TravelerCapabilityPanel } from "../features/capability/TravelerCapabilityPanel";
import { CapabilitySummary } from "../features/capability/CapabilitySummary";
import { loadCapabilities, saveCapabilities } from "../features/capability/capabilityStore";
import type { Capabilities } from "../features/capability/capabilityTypes";
import "../features/capability/capability.css";

export default function CapabilityRoute() {
  const [capabilities, setCapabilities] = useState<Capabilities>(() => loadCapabilities());

  return (
    <div className="capability-route" data-testid="capability-route">
      <TravelerCapabilityPanel
        mode="setup"
        value={capabilities}
        onChange={(next) => {
          setCapabilities(next);
          saveCapabilities(next);
        }}
      />
      <CapabilitySummary capabilities={capabilities} />
    </div>
  );
}
