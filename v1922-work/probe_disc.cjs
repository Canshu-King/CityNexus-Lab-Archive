const fs = require("fs");
const J = process.argv[2];
(async () => {
  const B = "http://127.0.0.1:8000/api/v1";
  for (const q of ["museum","park","garden"]) {
    const r = await fetch(`${B}/journeys/${J}/provider-mesh/discover`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, limit: 6, mode: "live" }),
    });
    const d = await r.json();
    console.log(q, "->", d.mode, "candidates:", (d.candidates || []).length,
                "| anchor:", d.provider_status && d.provider_status.anchor ? "yes" : "no");
  }
})();
