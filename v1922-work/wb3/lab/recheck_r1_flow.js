// R1 controlled replan identity flow (API level) — hotfix candidate runtime
const fs = require("fs");
const path = require("path");
const OUT = path.join(__dirname, "..", "evidence");
const JID = "2bbe2657-c279-42e5-b920-ac3ab9bfc3a9";
const BASE = "http://127.0.0.1:8011";

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
  const text = await res.text();
  let json = null;
  try { json = JSON.parse(text); } catch {}
  return { status: res.status, json, text };
}

(async () => {
  const results = { steps: [] };

  // 1. BEFORE identity snapshot
  const before = await api("GET", `/api/v1/journeys/${JID}/experience`);
  save("r1_before_experience.json", before.json ?? before.text);
  results.before_status = before.status;

  // try to extract plan + activities from whichever shape the endpoint uses
  const findPlan = (obj) => {
    if (!obj || typeof obj !== "object") return null;
    if (obj.plan && obj.plan.activities) return obj.plan;
    if (obj.active_plan && obj.active_plan.activities) return obj.active_plan;
    if (obj.plan_version && obj.plan_version.activities) return obj.plan_version;
    for (const k of Object.keys(obj)) {
      const found = findPlan(obj[k]);
      if (found) return found;
    }
    return null;
  };
  const beforePlan = findPlan(before.json);
  const beforeActivities = beforePlan
    ? beforePlan.activities.map((a) => ({
        id: a.id, place_id: a.place_id ?? null, city_service_id: a.city_service_id ?? null,
        semantic_key: a.semantic_key ?? null, title: a.title, type: a.type ?? null,
        start_at: a.start_at ?? null, locked: a.locked ?? null,
      }))
    : null;
  save("r1_before_activities.json", { plan_id: beforePlan?.id ?? null, activities: beforeActivities });
  log("before plan:", beforePlan?.id, "activities:", beforeActivities?.length);

  // 2. POST closure command
  const cmd = await api("POST", `/api/v1/journeys/${JID}/agent/commands`, {
    command: "鼓浪屿风琴博物馆(临时展馆) 因修缮临时闭馆，无法参观",
    requested_autonomy: "EXECUTE_WITHIN_BOUNDS",
  });
  save("r1_command_response.json", cmd.json ?? cmd.text);
  results.command_status = cmd.status;
  const eventId = cmd.json?.event?.id ?? cmd.json?.event_id ?? null;
  log("command:", cmd.status, "event:", eventId);

  if (!eventId) {
    save("r1_result.json", { verdict: "ABORT_NO_EVENT", results });
    return;
  }

  // 3. Generate replan proposal
  const gen = await api("POST", `/api/v1/journeys/${JID}/replans`, {
    trigger_event_id: eventId,
    candidate_count: 2,
  });
  save("r1_proposal.json", gen.json ?? gen.text);
  results.generate_status = gen.status;
  const proposal = gen.json;
  const proposalId = proposal?.id ?? proposal?.proposal_id ?? null;
  log("proposal:", gen.status, proposalId);
  if (proposal) {
    log("diff:", JSON.stringify({
      removed: proposal.diff?.removed, added: proposal.diff?.added,
      moved_count: proposal.diff?.moved?.length, kept_count: proposal.diff?.kept?.length,
    }));
  }

  if (!proposalId || gen.status >= 400) {
    save("r1_result.json", { verdict: "ABORT_NO_PROPOSAL", results });
    return;
  }

  // 4. Accept through the same endpoint the UI uses
  const accept = await api("POST", `/api/v1/replans/${proposalId}/accept`, {});
  save("r1_accept_response.json", accept.json ?? accept.text);
  results.accept_status = accept.status;
  log("accept:", accept.status);

  // 5. AFTER identity snapshot
  const after = await api("GET", `/api/v1/journeys/${JID}/experience`);
  save("r1_after_experience.json", after.json ?? after.text);
  const afterPlan = findPlan(after.json);
  const afterActivities = afterPlan
    ? afterPlan.activities.map((a) => ({
        id: a.id, place_id: a.place_id ?? null, city_service_id: a.city_service_id ?? null,
        semantic_key: a.semantic_key ?? null, title: a.title, type: a.type ?? null,
        start_at: a.start_at ?? null, locked: a.locked ?? null,
      }))
    : null;
  save("r1_after_activities.json", { plan_id: afterPlan?.id ?? null, activities: afterActivities });

  // 6. Identity comparison
  const TARGET = "鼓浪屿风琴博物馆";
  const beforeTarget = (beforeActivities ?? []).filter((a) => (a.title ?? "").includes(TARGET));
  const afterTarget = (afterActivities ?? []).filter((a) => (a.title ?? "").includes(TARGET));
  const identityPairs = beforeTarget.map((b) => ({
    before: b,
    after_same_identity: (afterTarget ?? []).some((a) => a.id === b.id && a.place_id === b.place_id),
    after_same_place_diff_activity: (afterTarget ?? []).some((a) => a.id !== b.id && a.place_id && a.place_id === b.place_id),
    after_same_title: (afterTarget ?? []).some((a) => a.title === b.title),
  }));
  const verdict = {
    plan_changed: (beforePlan?.id ?? null) !== (afterPlan?.id ?? null),
    before_plan_id: beforePlan?.id ?? null,
    after_plan_id: afterPlan?.id ?? null,
    target_before: beforeTarget,
    target_after: afterTarget,
    identity_pairs: identityPairs,
    proposal_diff: proposal?.diff ?? null,
    affected_activity_id: cmd.json?.event?.affected_activity_id ?? null,
  };
  save("r1_result.json", verdict);
  log("plan_changed:", verdict.plan_changed, `${verdict.before_plan_id} -> ${verdict.after_plan_id}`);
  log("target before:", JSON.stringify(beforeTarget));
  log("target after:", JSON.stringify(afterTarget));
})().catch((e) => { console.error("FATAL", e); process.exit(1); });
