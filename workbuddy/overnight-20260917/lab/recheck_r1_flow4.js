// R1 part 2 on fresh journey: generate -> accept -> identity compare
const fs = require("fs");
const path = require("path");
const OUT = path.join(__dirname, "..", "evidence");
const BASE = "http://127.0.0.1:8011";
const JID = "841a1c79-249d-4844-95ed-647279acd603";
const BEFORE_PLAN = "f19d1146-712d-4020-b634-5bf3bc61f6f0";
const EVENT = "658a0e16-7a0b-4b13-be9b-b9dc6eb631a7";

const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (n, o) => { fs.writeFileSync(path.join(OUT, n), typeof o === "string" ? o : JSON.stringify(o, null, 2), "utf8"); log("saved", n); };
async function api(method, url, body) {
  const res = await fetch(BASE + url, { method, headers: body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const t = await res.text(); let j = null; try { j = JSON.parse(t); } catch {}
  return { status: res.status, json: j, text: t };
}

(async () => {
  const gen = await api("POST", `/api/v1/journeys/${JID}/replans`, { trigger_event_id: EVENT, candidate_count: 2 });
  save("r1f2_proposal.json", gen.json ?? gen.text);
  log("generate:", gen.status);
  const p = gen.json;
  if (gen.status >= 400) { save("r1f2_result.json", { verdict: "ABORT_GENERATE", status: gen.status, error: p }); return; }
  log("proposal:", p.id, "base:", p.base_plan_version_id, "proposed:", p.proposed_plan_version_id);
  log("diff:", JSON.stringify(p.diff));
  log("ui summary keys:", JSON.stringify(p.summary ?? p.summary_text ?? p.description ?? null));

  const acc = await fetch(`${BASE}/api/v1/replans/${p.id}/accept`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json", "Idempotency-Key": `wb-r1-accept-${Date.now()}` },
    body: JSON.stringify({}),
  });
  const accT = await acc.text();
  let accJ = null; try { accJ = JSON.parse(accT); } catch {}
  save("r1f2_accept.json", accJ ?? accT);
  log("accept:", acc.status);

  const after = await api("GET", `/api/v1/journeys/${JID}/experience`);
  save("r1f2_after_experience.json", after.json ?? after.text);
  const findPlan = (o) => { if (!o || typeof o !== "object") return null; if (o.plan && o.plan.activities) return o.plan; for (const k of Object.keys(o)) { const f = findPlan(o[k]); if (f) return f; } return null; };
  const afterPlan = findPlan(after.json);
  const afterActs = (afterPlan?.activities ?? []).map((a) => ({ id: a.id, place_id: a.place_id ?? null, title: a.title, start_at: a.start_at ?? null, locked: a.locked ?? null }));
  save("r1f2_after_activities.json", { plan_id: afterPlan?.id ?? null, activities: afterActs });

  const TARGET = "\u9f13\u6d6a\u5c7f\u98ce\u7434\u535a\u7269\u9986";
  const afterTarget = afterActs.filter((a) => (a.title ?? "").includes(TARGET));
  const result = {
    before_plan_id: BEFORE_PLAN,
    after_plan_id: afterPlan?.id ?? null,
    plan_changed: BEFORE_PLAN !== (afterPlan?.id ?? null),
    proposal_diff: p.diff ?? null,
    proposal_summary: p.summary ?? p.summary_text ?? p.description ?? null,
    target_after: afterTarget,
    target_place_survives: afterTarget.some((a) => a.place_id === "place-gulangyu-organ"),
    target_activity_survives: afterTarget.some((a) => a.id === `${BEFORE_PLAN.slice(0, 8)}-a2`),
    after_all: afterActs,
  };
  save("r1f2_result.json", result);
  log("plan_changed:", result.plan_changed, `${result.before_plan_id} -> ${result.after_plan_id}`);
  log("target after:", JSON.stringify(afterTarget));
  log("closed PLACE survives:", result.target_place_survives, "| closed ACTIVITY survives:", result.target_activity_survives);
})().catch((e) => { console.error("FATAL", e); process.exit(1); });
