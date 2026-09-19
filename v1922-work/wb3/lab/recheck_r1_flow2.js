// R1 controlled flow part 2: generate + accept + identity compare
const fs = require("fs");
const path = require("path");
const OUT = path.join(__dirname, "..", "evidence");
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const BASE = "http://127.0.0.1:8011";
const EVENT = "72d0f756-631f-4b2c-861a-7ba108739175";

const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (name, obj) => {
  fs.writeFileSync(path.join(OUT, name), typeof obj === "string" ? obj : JSON.stringify(obj, null, 2), "utf8");
  log("saved", name);
};
async function api(method, url, body) {
  const res = await fetch(BASE + url, {
    method,
    headers: body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await res.text();
  let j = null; try { j = JSON.parse(t); } catch {}
  return { status: res.status, json: j, text: t };
}

(async () => {
  const gen = await api("POST", `/api/v1/journeys/${JID}/replans`, {
    trigger_event_id: EVENT,
    candidate_count: 2,
  });
  save("r1_proposal2.json", gen.json ?? gen.text);
  log("generate:", gen.status);
  const proposal = gen.json;
  if (gen.status >= 400 || !proposal?.id) { save("r1_result2.json", { verdict: "ABORT", status: gen.status }); return; }

  log("proposal id:", proposal.id);
  log("base plan:", proposal.base_plan_version_id);
  log("proposed plan:", proposal.proposed_plan_version_id);
  log("FULL DIFF:", JSON.stringify(proposal.diff, null, 1));
  log("summary:", proposal.summary ?? proposal.summary_text ?? "(none)");

  const accept = await api("POST", `/api/v1/replans/${proposal.id}/accept`, {});
  save("r1_accept2.json", accept.json ?? accept.text);
  log("accept:", accept.status);

  const after = await api("GET", `/api/v1/journeys/${JID}/experience`);
  save("r1_after_experience2.json", after.json ?? after.text);

  const before = JSON.parse(fs.readFileSync(path.join(OUT, "r1_before_activities.json"), "utf8"));
  // extract activities from after experience
  const findPlan = (obj) => {
    if (!obj || typeof obj !== "object") return null;
    if (obj.plan && obj.plan.activities) return obj.plan;
    for (const k of Object.keys(obj)) { const f = findPlan(obj[k]); if (f) return f; }
    return null;
  };
  const afterPlan = findPlan(after.json);
  const afterActs = afterPlan?.activities ?? null;
  save("r1_after_activities2.json", {
    plan_id: afterPlan?.id ?? null,
    activities: afterActs?.map((a) => ({ id: a.id, place_id: a.place_id ?? null, title: a.title, start_at: a.start_at ?? null, locked: a.locked ?? null })),
  });

  const TARGET = "\u9f13\u6d6a\u5c7f\u98ce\u7434\u535a\u7269\u9986";
  const beforeTarget = (before.activities ?? []).filter((a) => (a.title ?? "").includes(TARGET));
  const afterTarget = (afterActs ?? []).filter((a) => (a.title ?? "").includes(TARGET));
  const result = {
    before_plan_id: before.plan_id,
    after_plan_id: afterPlan?.id ?? null,
    plan_changed: before.plan_id !== (afterPlan?.id ?? null),
    proposal: {
      id: proposal.id,
      base: proposal.base_plan_version_id,
      proposed: proposal.proposed_plan_version_id,
      diff: proposal.diff,
    },
    target_before: beforeTarget,
    target_after: afterActs ? afterTarget.map((a) => ({ id: a.id, place_id: a.place_id ?? null, title: a.title, start_at: a.start_at ?? null })) : null,
    same_activity_id_survives: beforeTarget.some((b) => (afterTarget ?? []).some((a) => a.id === b.id)),
    same_place_id_survives: beforeTarget.some((b) => (afterTarget ?? []).some((a) => a.place_id && a.place_id === b.place_id)),
  };
  save("r1_result2.json", result);
  log("plan_changed:", result.plan_changed, `${result.before_plan_id} -> ${result.after_plan_id}`);
  log("target before:", JSON.stringify(beforeTarget));
  log("target after:", JSON.stringify(result.target_after));
  log("same_activity_id_survives:", result.same_activity_id_survives, "same_place_id_survives:", result.same_place_id_survives);
})().catch((e) => { console.error("FATAL", e); process.exit(1); });
