// probe: list journeys in snapshot DB via API, then try hub with each of the two newest
const { chromium } = require("playwright-core");
(async () => {
  const list = await fetch("http://127.0.0.1:8011/api/v1/journeys").then((r) => r.json()).catch((e) => ({ err: String(e) }));
  console.log("journeys endpoint:", typeof list === "object" ? JSON.stringify(list).slice(0, 400) : list);
})().catch((e) => console.error("FAIL", e.message));
