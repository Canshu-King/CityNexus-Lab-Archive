// R1 controlled flow on FRESH journey: closure command -> proposal -> accept -> identity compare
const fs = require("fs");
const path = require("path");
const OUT = path.join(__dirname, "..", "evidence");
const BASE = "http://127.0.0.1:8011";
const JID = "841a1c79-249d-4844-95ed-647279acd603";
const BEFORE_PLAN = "f19d1146-712d-4020-b634-5bf3bc61f6f0";

const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const save = (n, o) => { fs.writeFileSync(path.join(OUT, n), typeof o === "string" ? o : JSON.stringify(o, null, 2), "utf8"); log("saved", n); };
async function api(method, url, body) {
  const res = await fetch(BASE + url, { method, headers: body ? { "Content-Type": "application/json", Accept: "application/json" } : { Accept: "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const t = await res.text(); let j = null; try { j = JSON.parse(t); } catch {}
  return { status: res.status, json: j, text: t };
}

(async () => {
  // 1. closure command
  const cmd = await api("POST", `/api/v1/journeys/${JID}/agent/commands`, {
    command: "鼓浪屿风琴博物馆(临时展馆) 因修缮临时闭馆，无法参观",
    requested_autonomy: "EXECUTE_WITHIN_BOUNDS",
  });
  save("r1f_command.json", cmd.json ?? cmd.text);
  log("command:", cmd.status);
  const eventId = cmd.json?.event?.id ?? null;
  const affected = cmd.json?.event?.affected_activity_id ?? cmd.json?.mission?.mutable_activity_ids?.[0] ?? null;
  log("event:", eventId, "affected:", affected);
  if (!eventId) { save("r1f_result.json", { verdict: "ABORT_NO_EVENT" }); return; }

  // 2. generate proposal
  const gen = await api("POST", `/api/v1/journeys/${JID}/replans`, { trigger_event_id: eventId, candidate_count: 2 });
  save("r1f_proposal.json", gen.json ?? gen.text);
  log("generate:", gen.status);
  const p = gen.json;
  if (gen.status >= 400) { save("r1f_result.json", { verdict: "ABORT_GENERATE", status: gen.status, error: p }); return; }
  log("proposal:", p.id);
  log("base:", p.base_plan_version_id, "proposed:", p.proposed_plan_version_id);
  log("diff:", JSON.stringify(p.diff));

  // 3. accept
  const acc = await api("POST", `/api/v1/replans/${p.id}/accept`, {});
  save("r1f_accept.json", acc.json ?? acc.text);
  log("accept:", acc.status);

  // 4. after identity
  const after = await api("GET", `/api/v1/journeys/${JID}/experience`);
  save("r1f_after_experience.json", after.json ?? after.text);
  const findPlan = (o) => { if (!o || typeof o !== "object") return null; if (o.plan && o.plan.activities) return o.plan; for (const k of Object.keys(o)) { const f = findPlan(o[k]); if (f) return f; } return null; };
  const afterPlan = findPlan(after.json);
  const afterActs = (afterPlan?.activities ?? []).map((a) => ({ id: a.id, place_id: a.place_id ?? null, title: a.title, start_at: a.start_at ?? null, locked: a.locked ?? null }));
  save("r1f_after_activities.json", { plan_id: afterPlan?.id ?? null, activities: afterActs });

  const TARGET = "\u9f13\u6d6a\u5c7f\u98ce\u7434\u535a\u7269\u9986";
  const beforeTarget = [{ id: `${BEFORE_PLAN.slice(0, 8)}-a2`, place_id: "place-gulangyu-organ", title: TARGET + "(\u4e34\u65f6\u5c55\u9986)" }];
  const afterTarget = afterActs.filter((a) => (a.title ?? "").includes(TARGET));
  const result = {
    before_plan_id: BEFORE_PLAN,
    after_plan_id: afterPlan?.id ?? null,
    plan_changed: BEFORE_PLAN !== (afterPlan?.id ?? null),
    proposal_diff: p.diff ?? null,
    ui_summary: p.summary ?? p.summary_text ?? null,
    affected_activity_id: affected,
    target_before: beforeTarget,
    target_after: afterTarget,
    same_activity_id_survives: beforeTarget.some((b) => afterTarget.some((a) => a.id === b.id)),
    same_place_id_survives: beforeTarget.some((b) => afterTarget.some((a) => a.place_id === b.place_id)),
  };
  save("r1f_result.json", result);
  log("plan_changed:", result.plan_changed);
  log("target after:", JSON.stringify(afterTarget));
  log("same_activity_id_survives:", result.same_activity_id_survives);
  log("same_place_id_survives:", result.same_place_id_survives);
})().catch((e) => { console.error("FATAL", e); process.exit(1); });
