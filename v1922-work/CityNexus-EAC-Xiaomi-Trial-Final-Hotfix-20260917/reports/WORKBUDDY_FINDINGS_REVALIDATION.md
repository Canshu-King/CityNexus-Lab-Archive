# WorkBuddy Findings Revalidation (WB-H1 … WB-H5)

**Task:** independent re-validation of five WorkBuddy (WB-O1) consumer-UI findings against the
CURRENT authoritative repository. Read-only: no source file was modified.

- **Authoritative repo:** `D:\moodle\CityNexus`
- **Branch / HEAD:** `eac/v19.2.2-realphone-codegate` @ `7d22cd0`
- **Verification time:** 2026-09-17, 08:51 → 10:35 (+08:00)
- **Reference (not authority):** `D:\moodle\_v1922_work\wb_in\CityNexus-EAC-WorkBuddy-Findings-Integration-20260917\`
  (WB-O1 baseline was an isolated ~01:15 snapshot; the integration README explicitly requires re-testing against CURRENT code)

## Important caveat about the working tree

The working tree was **being edited by another process while this verification ran**.
`CopilotDock.tsx`, `JourneyInboxWorkbench.tsx`, `V8Experience.tsx` and `StayExplorer.tsx` all changed
between 08:51 and 08:55, and `CopilotDock.tsx` changed again at ~10:21. All quotes below were taken
from the frozen, stable state reached afterwards (no further writes for 10+ minutes). MD5s of the exact
files quoted:

| File | MD5 (verified state) |
| --- | --- |
| `frontend/src/features/planning/PlanWithAiSheet.tsx` | `77554e21584adddbe4889add67248958` |
| `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | `a5839f06d7e760ab6c0fee9a5c2fae76` |
| `frontend/src/features/agent/CopilotDock.tsx` | `a89875ff0735e0fb2537035f6f471fad` |
| `frontend/src/features/agent/AgentComposer.tsx` | `10c942bc0e736ff65c4f99ba2205f29f` |
| `frontend/src/app/V8Experience.tsx` | `7d8968416619bed2664f8ae9ab60269d` |
| `frontend/src/features/stay/HotelsPanel.tsx` | `c2e9574eb43989a9c6fc0844d6464e0c` |
| `frontend/src/features/stay/StayExplorer.tsx` | `76c52e373102d1faf4e5a14c8d9e02f1` |
| `frontend/src/i18n/LocaleContext.tsx` | `a8d3122e9dc8717b5ceddfcf0dd808f1` |
| `frontend/src/lib/money.ts` | `a57c0849bf37c317d1a1f7e653070348` |
| `backend/app/agent/runtime_events.py` | `c6f4eff8d2810233b2f5493c31e15b62` |
| `backend/app/integrations/stay_osm.py` | `5dd6221246cedff48b3c434b98c0c8dc` |

Verdicts are given for this frozen state.

---

## WB-H1 — "AI planning can falsely report success"

### Verdict: **FIXED_BY_CURRENT_EAC**

The original symptom (sheet says 方案已准备好 while `/journeys/{id}/plans` returns `[]`) can no longer
occur. Success is now derived from a real plan count, not from the mission status.

**Files / lines:**
- `frontend/src/features/planning/PlanWithAiSheet.tsx:44-51` (status → copy)
- `frontend/src/features/planning/PlanWithAiSheet.tsx:135-146` (real plan count fetched)
- `frontend/src/features/planning/PlanWithAiSheet.tsx:180-197` (terminal status gated on `planCount > 0`)
- `frontend/src/features/planning/PlanWithAiSheet.tsx:262-267` (`data-testid="plan-ai-result"`, `data-plan-count`)
- `backend/app/main.py:3967-3975` (`GET /journeys/{id}/plans` — the count source)

**Verbatim current code (terminal-status computation):**
```tsx
      const missionStatus = String(mission?.status ?? "").toUpperCase();
      let status: string;
      if (planCount > 0) {
        status = "COMPLETED";
      } else if (missionStatus.includes("EXTERNAL") || missionStatus.includes("SKIPPED")) {
        status = "SKIPPED_EXTERNAL_DEPENDENCY";
      } else if (!response.ok) {
        status = `HTTP_${response.status}`;
      } else {
        // Compiled, but produced nothing the traveller can use.
        status = "NO_PLANS_PRODUCED";
      }
```
and the success copy, which is now parameterised by the real count:
```tsx
  if (s === "COMPLETED" || s === "SUCCEEDED") {
    return {
      title: zh ? `已生成 ${planCount} 个可选方案` : `${planCount} candidate plans are ready`,
```
and the result node:
```tsx
        {copy && (
          <div
            className={`plan-ai-result ${copy.tone}`}
            data-testid="plan-ai-result"
            data-plan-count={result?.planCount ?? 0}
            role="status"
```

**Evidence the old string is gone:** `grep -rn "方案已准备好" frontend/src` → no matches.

**Residual (non-blocking, not the original defect):** `planCount` is `plans.length` over
`GET /journeys/{id}/plans`, and that endpoint applies **no status filter**
(`backend/app/main.py:3970-3974`). A journey that already owns an `ACTIVE`/`SELECTED`/`REJECTED`/
`SUPERSEDED` `PlanVersion` would therefore report "N candidate plans are ready" even when no *new*
candidate was produced by this run. The wording says "可选方案 / candidate plans" but the count is
"all plans". If hardened, the fix belongs in `PlanWithAiSheet.submit()` at
`frontend/src/features/planning/PlanWithAiSheet.tsx:140-143` — filter to
`status === "CANDIDATE" && !stale && selectable !== false` before setting `planCount` (the same
predicate `PlanComparison.tsx:70-72` already uses). This does **not** reintroduce the false-success
case: with `/plans == []` the count is 0 and the sheet reports `NO_PLANS_PRODUCED`.

---

## WB-H2 — "Booking import default flow is developer-shaped"

### Verdict: **PARTIALLY_FIXED**

The consumer flow now exists and is placed **first** on the mobile/primary Trips path, and the raw-JSON
workbench was moved behind an "Advanced / developer" disclosure there. However several of the finding's
sub-claims are still reproducible on the desktop Travel Wallet route and inside the consumer component
itself, and the amount-loss defect is still present end-to-end.

**Files / lines:**
- `frontend/src/app/V8Experience.tsx:1104-1123` — Trips → Bookings: consumer `JourneyInboxWorkbench` first, `Bookings` (raw JSON) inside `<details className="trips-advanced">` (this is the fix)
- `frontend/src/app/V8Experience.tsx:913-921` — desktop `route === "bookings"` (Travel Wallet, sidebar route) still renders raw-JSON `Bookings` **first**
- `frontend/src/app/V8Experience.tsx:1822` — raw-JSON submit is still an unguarded `JSON.parse`
- `frontend/src/app/V8Experience.tsx:1865` — raw `realtime_status` rendered
- `frontend/src/app/V8Experience.tsx:1882` — `受保护 C4` / `Protected C4` rendered
- `frontend/src/features/inbox/JourneyInboxWorkbench.tsx:594-601` — raw `artifact_type`, `status`, `extraction_mode`, `anchor_role`, `payment_status`
- `frontend/src/features/inbox/JourneyInboxWorkbench.tsx:579` — raw memory `role`
- `frontend/src/features/inbox/JourneyInboxWorkbench.tsx:242` vs `backend/app/operations/v9.py:956` — amount key mismatch
- `frontend/src/i18n/LocaleContext.tsx:434-435, 482, 487-490, 449, 475` — DeepSeek / raw role labels

**Verbatim current code (the improved primary path — Trips → Bookings):**
```tsx
      {tab === "bookings" && (
        <>
          {/* Consumer flow first: paste a confirmation or enter it manually,
              review the parsed fields, then confirm.  The raw-JSON workbench is
              kept for developers behind an Advanced disclosure. */}
          <JourneyInboxWorkbench
            journeyId={data.journey.id}
            onConfirmed={onRefresh}
          />
          <details className="trips-advanced">
            <summary>{zh ? "高级 / 开发者" : "Advanced / developer"}</summary>
            <Bookings
```
**Verbatim current code (the still-developer-shaped desktop default):**
```tsx
          {route === "bookings" && (
            <>
              <Bookings
                data={data}
                selected={selected}
                wallet={wallet}
                onImport={importReservation}
                busy={busy}
              />
```
and inside `Bookings` the entry is still a raw JSON textarea whose submit throws on natural language:
```tsx
  const submit = async () => {
    const value = JSON.parse(input) as Record<string, unknown>;
    await onImport(value);
    setInput("");
  };
```
```tsx
        <aside className="v9-inbox">
          <span className="v8-kicker">{t("bookings.importKicker")}</span>
          <label htmlFor="reservation-json">{t("bookings.reservationJson")}</label>
          <textarea
            id="reservation-json"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={'{"reservation_type":"RAIL", "confirmation_ref":"…"}'}
          />
```
and the raw internal values are still rendered verbatim:
```tsx
                <span className="v8-selected-label neutral">
                  {item.type} · {item.realtime_status}
                </span>
                <h2>{item.confirmation_ref}</h2>
```
```tsx
              <span className="v8-booking-state safe">{t("bookings.protectedC4")}</span>
```
```tsx
          <div>
            <b>{draft.artifact_type} · {draft.status}</b>
            <small>{draft.extraction_mode}</small>
          </div>
          <section className="v13-2-interpretation" data-testid="v13-2-interpretation">
            <b>{t("inbox.semanticInterpretation")}</b>
            <span>{draft.interpretation?.anchor_role ?? "UNKNOWN"} · {confidence(draft.interpretation?.anchor_role_confidence)}</span>
            <span>{t("inbox.target")} {targetLabel}</span>
            <span>{t("inbox.payment")} {String(draft.interpretation?.payment_status ?? "UNKNOWN")}</span>
```

**What is still wrong / where the fix goes:**

1. **Desktop default is still raw JSON.** `V8Experience.tsx:913-921` (`route === "bookings"`, the
   sidebar "Travel Wallet" entry) renders `Bookings` before `JourneyInboxWorkbench`. The consumer-first
   ordering used at `V8Experience.tsx:1104-1123` was not applied here. Fix in `V8Experience()`'s
   `route === "bookings"` branch: render `JourneyInboxWorkbench` first and wrap `Bookings` in a
   disclosure, mirroring the Trips branch.
2. **Natural-language input still errors silently.** `Bookings.submit()`
   (`V8Experience.tsx:1821-1825`) calls `JSON.parse(input)` with no `try/catch` and no user-visible
   error state, so a pasted rail confirmation still throws with no feedback. Fix in
   `Bookings.submit()`: catch, and surface a localized message (the component already has the
   `t()` hook and `busy` prop available).
3. **Internal enum labels still user-visible.** `{item.realtime_status}`
   (`V8Experience.tsx:1865`) renders `UNKNOWN_REALTIME` / `STALE_REALTIME`
   (`backend/app/operations/v9.py:1022`, `backend/app/main.py:3448`);
   `t("bookings.protectedC4")` (`V8Experience.tsx:1882`) renders `受保护 C4` / `Protected C4`
   (`LocaleContext.tsx:203, 819`). Fix in `Bookings()`: map `realtime_status` and the C4 state to
   traveller words (the `inbox.*`/`bookings.*` key families already exist for this).
4. **Consumer component still prints raw draft internals.** `JourneyInboxWorkbench.tsx:594-601` and
   `:579` render `artifact_type`, `status`, `extraction_mode`, `anchor_role`, `payment_status` and
   memory `role` unlocalized. Fix in `JourneyInboxWorkbench()`: route these through the
   `TYPE_LABELS`/`DECISION_LABELS`/`FIELD_LABELS` maps already defined at lines 110-154 (they are used
   for `dl` fields but not for this header block).
5. **Amount is silently lost (key mismatch).** The manual form sends `amount_minor`
   (`JourneyInboxWorkbench.tsx:242`), but the review table only renders `price_amount_minor`
   (`JourneyInboxWorkbench.tsx:118` + filter at `:632`), and `confirm_reservation_draft` reads
   `data.get("price_amount_minor")` (`backend/app/operations/v9.py:956`). `prepare_semantic_intake`
   copies the payload verbatim (`normalized = dict(extracted)`, `semantic_intake.py:277`) and performs
   no key aliasing, so `amount_minor` is neither shown nor confirmed. A manually entered amount is
   therefore dropped end-to-end. Fix in `confirm_reservation_draft`
   (`backend/app/operations/v9.py:956`) or in `import_reservation_artifact`
   (`backend/app/operations/v9.py:831-838`) — normalise `amount_minor` → `price_amount_minor` for
   `STRUCTURED_JSON` payloads.

### WB-H2 — EVERY user-visible internal term on the default (non-advanced) surface

| # | File | Line | Literal string / expression | What the traveller sees |
| --- | --- | --- | --- | --- |
| 1 | `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | 594 | `{draft.artifact_type} · {draft.status}` | `STRUCTURED_JSON · READY_FOR_CONFIRMATION`, `TEXT · NEEDS_REVIEW` |
| 2 | `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | 595 | `{draft.extraction_mode}` | `DETERMINISTIC`, `DEEPSEEK_ELIGIBLE_AMBIGUOUS_TEXT`, `DEEPSEEK_RESPONSES_TEXT`, `DEEPSEEK_RESPONSES_VISION` |
| 3 | `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | 599 | `{draft.interpretation?.anchor_role ?? "UNKNOWN"}` | `ARRIVAL` / `DEPARTURE` / `MID_TRIP` / `UNKNOWN` |
| 4 | `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | 601 | `String(draft.interpretation?.payment_status ?? "UNKNOWN")` | `PAID` / `UNKNOWN` |
| 5 | `frontend/src/features/inbox/JourneyInboxWorkbench.tsx` | 579 | `{item.title} · {item.role}` | memory `role` = `ARRIVAL` / `DEPARTURE` / `MID_TRIP` |
| 6 | `frontend/src/i18n/LocaleContext.tsx` | 434 (en) / 1050 (zh) | `inbox.semanticReady` = `"DeepSeek interpreted the artifact. Review the semantic role and deterministic checks below."` / `"DeepSeek 已解读此工件。请查看下方的语义角色和确定性检查。"` | model brand + "semantic role" |
| 7 | `frontend/src/i18n/LocaleContext.tsx` | 435 / 1051 | `inbox.notConfigured` = `"DeepSeek extraction is not configured; deterministic import remains available."` / `"DeepSeek 提取未配置；确定性导入仍可用。"` | model brand |
| 8 | `frontend/src/i18n/LocaleContext.tsx` | 482 / 1098 | `inbox.semanticInterpretation` = `"DeepSeek semantic interpretation"` / `"DeepSeek 语义解读"` | model brand |
| 9 | `frontend/src/i18n/LocaleContext.tsx` | 487 / 1103 | `inbox.roleUnknown` = `"UNKNOWN · review required"` / `"未知 · 需要审核"` | raw enum token `UNKNOWN` |
| 10 | `frontend/src/i18n/LocaleContext.tsx` | 488 / 1104 | `inbox.roleArrival` = `"ARRIVAL · Journey start"` / `"到达 · 行程起点"` | raw enum token `ARRIVAL` |
| 11 | `frontend/src/i18n/LocaleContext.tsx` | 489 / 1105 | `inbox.roleMidTrip` = `"MID_TRIP · protected activity"` / `"途中 · 受保护活动"` | raw enum token `MID_TRIP` |
| 12 | `frontend/src/i18n/LocaleContext.tsx` | 490 / 1106 | `inbox.roleDeparture` = `"DEPARTURE · Journey end"` / `"出发 · 行程终点"` | raw enum token `DEPARTURE` |
| 13 | `frontend/src/i18n/LocaleContext.tsx` | 449 / 1065 | `inbox.multimodal` = `"MULTIMODAL INBOX"` / `"多模态收件箱"` | implementation-flavoured label |
| 14 | `frontend/src/i18n/LocaleContext.tsx` | 475 / 1091 | `inbox.authoritativeMemory` = `"AUTHORITATIVE MEMORY"` / `"权威记忆"` | implementation-flavoured label |
| 15 | `frontend/src/i18n/LocaleContext.tsx` | 436 / 1052 | `inbox.extractionStatus` = `"Extraction status:"` (composed with raw `result.status` at `JourneyInboxWorkbench.tsx:291`) | `Extraction status: FAILED_EXTERNAL` |
| 16 | `frontend/src/i18n/LocaleContext.tsx` | 440 / 1056 | `inbox.stoppedAt` = `"Smart intake stopped at {step}"` (composed with raw `result.status` at `JourneyInboxWorkbench.tsx:341`) | `Smart intake stopped at REQUIRES_CONFIRMATION` |
| 17 | `frontend/src/app/V8Experience.tsx` | 1865 | `{item.type} · {item.realtime_status}` | `RAIL · UNKNOWN_REALTIME` |
| 18 | `frontend/src/app/V8Experience.tsx` | 1882 | `t("bookings.protectedC4")` | `受保护 C4` / `Protected C4` |
| 19 | `frontend/src/i18n/LocaleContext.tsx` | 203 / 819 | `bookings.protectedC4` = `"Protected C4"` / `"受保护 C4"` | internal commitment level `C4` |
| 20 | `frontend/src/app/V8Experience.tsx` | 1893 | placeholder `'{"reservation_type":"RAIL", "confirmation_ref":"…"}'` | raw JSON schema on the desktop default surface |
| 21 | `frontend/src/i18n/LocaleContext.tsx` | 205 / 821 | `bookings.reservationJson` = `"Reservation JSON"` / `"预订 JSON"` | developer framing of the entry field |
| 22 | `frontend/src/i18n/LocaleContext.tsx` | 195 / 811 | `bookings.lede` = `"Paste structured reservation JSON, review it, then bind confirmed facts to the Journey as a durable commitment."` / `"粘贴结构化预订 JSON，审核后，将确认的事实绑定为行程的持久承诺。"` | developer instruction as the page lede |
| 23 | `frontend/src/i18n/LocaleContext.tsx` | 204 / 820 | `bookings.importKicker` = `"IMPORT CONFIRMATION"` / `"导入确认"` | implementation-flavoured kicker |

---

## WB-H3 — "Copilot leaks internal implementation language"

### Verdict: **PARTIALLY_FIXED**

The exact items named in the finding were fixed **during this verification run** (a new `CopilotDock.tsx`
landed at 08:51 and was touched again at 10:21). Header subtitle, runtime row, chips, action button and
the timeline header are now human. However `NativeMissionTimeline` — explicitly named in the finding —
still renders raw internal tokens in the **always-visible** step rail, and the `/v8/agent`
`AgentComposer` surface still renders raw enum values.

**Files / lines:**
- `frontend/src/features/agent/CopilotDock.tsx:34-45` — humanized lifecycle labels
- `frontend/src/features/agent/CopilotDock.tsx:291-298` — **residual**: raw `tool_name` / `status` / `policy_decision`
- `frontend/src/features/agent/CopilotDock.tsx:134-139` — `?? event.friendly_label` fallback (backend default `"Hermes runtime"`)
- `frontend/src/features/agent/CopilotDock.tsx:383-393` — raw ids behind "Advanced detail" (acceptable)
- `frontend/src/features/agent/CopilotDock.tsx:590-597` — humanized header subtitle (fixed)
- `frontend/src/features/agent/CopilotDock.tsx:467-515` — `humanIntent` / `humanVerification` / `humanAction` (fixed)
- `frontend/src/features/agent/CopilotDock.tsx:607-621` — chips and action button now humanized (fixed)
- `frontend/src/features/agent/AgentComposer.tsx:208` — **residual**: raw `feasibility`
- `frontend/src/features/agent/AgentComposer.tsx:236-242` — raw semantic-envelope values (behind "Advanced details")
- `backend/app/agent/runtime_events.py:181` — `"Hermes runtime"` default label

**Verbatim current code (fixed: human header, no runtime row, humanized chips/actions):**
```tsx
          <header className="cn-copilot-head">
            <div>
              <b>{t("agent.citynexus")}</b>
              <small>
                {locale === "zh-CN"
                  ? "回答只依据已核验的行程事实，不会自己改动你的安排。"
                  : "Answers use verified journey facts only and never change your plan."}
              </small>
            </div>
```
```tsx
                {item.response?.intent && (
                  <span className="cn-copilot-chip">{humanIntent(item.response.intent.name, zh)}</span>
                )}
                {item.response?.verification && (
                  <span className="cn-copilot-chip">{humanVerification(item.response.verification.status, zh)}</span>
                )}
                {item.response?.action?.type && (
                  <button
                    type="button"
                    className="cn-copilot-link"
                    onClick={() => continueAction(item.response?.action?.type)}
                  >
                    {humanAction(item.response.action.type, zh)}
                  </button>
                )}
```
**Verbatim current code (residual leak in `NativeMissionTimeline`, default-visible):**
```tsx
  const steps = useMemo<AgentRailStep[]>(() => events.map((event, index) => {
    const detail: ReactNode = (
      <span className="cn-agent-event-detail">
        {event.tool_name ? <code>{event.tool_name}</code> : event.status}
        {event.duration_ms != null && ` · ${formatDuration(Number(event.duration_ms))}`}
        {event.policy_decision ? ` · ${event.policy_decision}` : ""}
      </span>
    );
```
and the unmapped-event fallback:
```tsx
  return lifecycleLabels[event.event_type]?.[zh ? "zh" : "en"] ?? event.friendly_label;
```
whose backend default is:
```python
        "friendly_label": TOOL_LABELS.get(tool or "", "Hermes runtime") if tool else "Hermes runtime",
```
**Verbatim current code (residual leak in `/v8/agent`, default-visible):**
```tsx
                      <div>
                        <span>{t("agent.feasibility")}</span>
                        <b>{item.response.what_if.feasibility}</b>
                      </div>
```

**What is still wrong / where the fix goes:**

1. **Raw tool/status/policy tokens in the visible step rail.**
   `CopilotDock.tsx:294-296` (`NativeMissionTimeline.steps`) prints `event.tool_name`
   (e.g. `search_city_services`, `inspect_journey`), `event.status` (`started`/`completed`) and
   `event.policy_decision` (`ALLOW`/`DENY`). This `<small>` is rendered by
   `AgentRunRail.tsx:18` and is **not** inside a disclosure. Fix in `NativeMissionTimeline.steps`
   (`CopilotDock.tsx:291-298`): resolve `tool_name` through `toolLabels`, and only expose
   `status`/`policy_decision` inside the existing `<details className="cn-agent-raw">` block.
2. **`"Hermes runtime"` can reach the traveller.** `CopilotDock.tsx:138` falls back to
   `event.friendly_label`, and `backend/app/agent/runtime_events.py:181` defaults it to the literal
   `"Hermes runtime"` for any unmapped tool/event. Fix in `runtime_events.py:181` (neutral default
   such as a generic step description) and/or `CopilotDock.tsx:138` (neutral frontend fallback).
3. **Raw `feasibility` enum on the Copilot route.** `AgentComposer.tsx:208` prints
   `PASS` / `BLOCKED` / `UNKNOWN` (`backend/app/integrations/ai/copilot_contract.py:630,667,686,691`).
   Fix in `AgentComposer`'s what-if block (`AgentComposer.tsx:206-209`): map the value to traveller
   language, as `CopilotDock` now does for its chips.
4. **Raw semantic-envelope values.** `AgentComposer.tsx:236-242` prints `assertion_status`,
   `effective_time`, `event_type` and `requested_action` raw. These are inside
   `<details>` ("Advanced details"), so they are lower severity, but the task's target is that
   provider/runtime detail appears only under Advanced **and** in human words. Fix at the same
   location if the Advanced copy is to be fully humanized.

### WB-H3 — user-visible internal terms, split by visibility

**Default (non-advanced) surface — still leaking:**

| # | File | Line | Literal string / expression | What the traveller sees |
| --- | --- | --- | --- | --- |
| 1 | `frontend/src/features/agent/CopilotDock.tsx` | 294 | `{event.tool_name ? <code>{event.tool_name}</code> : event.status}` | `search_city_services`, `inspect_journey`, `started`, `completed` |
| 2 | `frontend/src/features/agent/CopilotDock.tsx` | 296 | `{event.policy_decision ? \` · ${event.policy_decision}\` : ""}` | `ALLOW` / `DENY` policy enum |
| 3 | `frontend/src/features/agent/CopilotDock.tsx` | 138 | `?? event.friendly_label` → `backend/app/agent/runtime_events.py:181` | `Hermes runtime` |
| 4 | `frontend/src/features/agent/AgentComposer.tsx` | 208 | `{item.response.what_if.feasibility}` | `PASS` / `BLOCKED` / `UNKNOWN` |
| 5 | `frontend/src/i18n/LocaleContext.tsx` | 270 / 886 | `agent.intentDiscover` = `"Discover"` / `"探索地点"` | the English label is the same word as the internal enum concept (not SCREAMING_CASE; low severity, listed for completeness) |
| 6 | `frontend/src/i18n/LocaleContext.tsx` | 280 / 896 | `agent.simulationOnly` = `"SIMULATION ONLY"` / `"仅模拟，不写入"` | internal simulation marker; borderline (it is a disclosure, but shouted and implementation-flavoured) |
| 7 | `frontend/src/i18n/LocaleContext.tsx` | 284 | `agent.feasibility` = `"Feasibility"` | label for the raw enum in #4; the value itself (`PASS`/`BLOCKED`) is the actual leak |
| 8 | `frontend/src/features/agent/CopilotDock.tsx` | 49 / 52 | `inspect_twin: { en: "Inspect JourneyTwin" … }`, `request_replan: { en: "Request deterministic replan" … }` | internal tool vocabulary (`JourneyTwin`, "deterministic replan") |
| 9 | `frontend/src/features/agent/CopilotDock.tsx` | 452 | `"Inspect JourneyTwin": "检查 JourneyTwin"` | internal noun `JourneyTwin` kept in the Chinese label |

**Advanced-gated (acceptable for now, listed for completeness):** `CopilotDock.tsx:307`
(`"Runtime details"` + JSON dump), `:386` (`task id` + raw `run_id`), `:387` (`mission` + raw
`mission_id`), `:389` (raw `currentTool`), `:401` (raw `step.operation`), `AgentComposer.tsx:236-242`
(raw `assertion_status` / `effective_time` / `event_type` / `requested_action`).

**Confirmed removed** (were named in the finding): `Semantic: DeepSeek` / `Execution:` / `Truth:`
runtime row, `DeepSeek` in the dock header, `Hermes` in the dock header, raw `DISCOVER` chip,
giant `REQUEST_PLACE_SEARCH` button label. `grep` finds none of these in
`frontend/src/features/agent/CopilotDock.tsx`.

---

## WB-H4 — "Today / Copilot empty states can become blank"

### Verdict: **PARTIALLY_FIXED**

The two named components (`Hub` = Today, and the `agent` route) are **not** blank: both render a
heading, context, and a prominent next action even with no plan. **But the exact URLs named in the
finding (`/v8/today`, `/v8/copilot`) still resolve to an empty content area**, because those route
keys do not exist and `V8Experience` has no fallback branch. The "plan at a glance" day row also
renders an empty container when there are no options.

**Files / lines:**
- `frontend/src/app/V8Experience.tsx:109-111` — `routeFromPath()` returns the raw path segment
- `frontend/src/app/V8Experience.tsx:811-956` — content switch has **no fallback/default branch**
- `frontend/src/routes/v8Routes.ts:1-23` — canonical keys are `hub` and `agent` (no `today`/`copilot`)
- `frontend/src/app/V8Experience.tsx:1222-1258` — Hub always renders intro + "Plan my trip with AI" CTA
- `frontend/src/app/V8Experience.tsx:1286-1345` — Today's Next / Stay / Attention cells with honest no-plan copy
- `frontend/src/app/V8Experience.tsx:1375-1376` — **residual**: empty `.v8-day-row` when no options
- `frontend/src/features/agent/AgentComposer.tsx:102-115, 260-270` — Copilot route always renders content

**Verbatim current code (Today with no plan — honest, non-blank):**
```tsx
          <div className="today-actions" data-testid="today-next">
            <div>
              <span>{zh ? "下一步" : "Next"}</span>
              <strong>
                {nextStop
                  ? `${nextClock ?? ""} ${nextStop.title}`.trim()
                  : zh
                    ? "还没有安排"
                    : "Nothing scheduled"}
              </strong>
```
```tsx
          <button
            className="v8-primary"
            data-testid="hub-plan-with-ai"
            onClick={onPlanWithAi}
          >
            <Icon name="spark" />
            {locale.startsWith("zh") ? "AI 帮我规划" : "Plan my trip with AI"}
          </button>
```
**Verbatim current code (the residual — no route fallback):**
```tsx
function routeFromPath() {
  return window.location.pathname.replace(/^\/v8\/?/, "") || "hub";
}
```
```tsx
          {route === "agent" && (
            <AgentComposer data={data} busy={busy} onNavigate={navigate} />
          )}
          {route === "me" && (
            <Me data={data} policy={policy} onActivate={activateAutonomy} />
          )}
        </div>
```
**Verbatim current code (the residual — empty day row):**
```tsx
      <div className="v8-day-row">
        {selected?.days.map((day) => (
```
(`selected` is `null` when `data.options` is empty — `V8Experience.tsx:336-339`.)

**What is still wrong / where the fix goes:**

1. **No fallback for an unknown route → blank content area.**
   `routeFromPath()` (`V8Experience.tsx:109-111`) returns `today` / `copilot` for `/v8/today` and
   `/v8/copilot`, but the content switch (`V8Experience.tsx:811-956`) only matches the canonical keys
   from `v8Routes.ts` and has no `default`. The result is a shell with an empty `.v8-content`.
   Fix in `V8Experience()`: either add aliases (`today → hub`, `copilot → agent`) in `routeFromPath()`
   / `navigate()`, or add a fallback branch that renders the Hub.
2. **"Plan at a glance" renders an empty row with no explanation.**
   `V8Experience.tsx:1375-1388` maps `selected?.days` with no empty branch, so with no options the
   section heading ("Every day, connected.") is followed by nothing. Fix in the `Hub` component: add
   an explicit no-plan note (the pattern already exists at
   `frontend/src/features/trip/TripItinerary.tsx:106-124`, which renders a
   `trip-itinerary-empty` state with the same AI CTA).

The Copilot route itself (`/v8/agent`) is fine: `AgentComposer` always renders the intro, the composer
card, three suggested prompts, the history region and the "What I understood" panel
(`AgentComposer.tsx:102-115`, `154-165`, `260-270`). The dock (`CopilotDock`) also always renders an
empty-state prompt at `CopilotDock.tsx:602`.

---

## WB-H5 — "Hotel no-data state can masquerade as evidence"

### Verdict: **PARTIALLY_FIXED**

The exact pseudo-evidence strings named in the finding are gone, and both hotel surfaces now have an
explicit, honest no-option state. **However**, a real no-price path still renders a fabricated-looking
`CN¥0.00` price on the Stay Explorer card/detail, because the OSM provider writes
`nightly_amount_minor = 0` and nothing filters or labels a zero price in that surface.

**Files / lines:**
- `frontend/src/features/stay/HotelsPanel.tsx:125-141` — explicit `hotels-empty` state (fixed)
- `frontend/src/features/stay/HotelsPanel.tsx:179-186` — honest "Price unavailable" when nightly is 0 (fixed)
- `frontend/src/features/stay/StayExplorer.tsx:13-32` — explicit `stay-no-options` state (fixed)
- `frontend/src/features/stay/StayExplorer.tsx:65-94` — `priceLabel` / `cancellationLabel` / `evidenceLabel` honesty helpers (fixed)
- `frontend/src/features/stay/StayExplorer.tsx:38, 43, 62, 77` — **residual**: `money(0)` → `CN¥0.00`
- `backend/app/integrations/stay_osm.py:174-183` — **residual source**: OSM offers written with price 0
- `backend/app/stay_mobility.py:246-251, 269` — OSM provider used for non-fixture cities; total = 0 × nights
- `backend/app/stay_mobility.py:1217-1226` — `generate_stay_options` does not exclude zero-price offers
- `frontend/src/lib/money.ts:20` — `formatMinorMoney` returns `"Provider price unavailable"` only for `null`, not for `0`

**Verbatim current code (the fixed no-option state — HotelsPanel):**
```tsx
  if (options.length === 0) {
    return (
      <section className="v8-page" data-testid="hotels-empty">
        <div className="v8-page-intro compact">
          <div>
            <p className="v8-kicker">{zh ? "住宿" : "Stay"}</p>
            <h1>{zh ? "暂时没有可比较的住宿" : "No stays to compare yet"}</h1>
            <p className="v8-lede">
              {zh
                ? "这个城市还没有拿到可用的住宿数据。换个城市或稍后再试——我们不会编造酒店。"
                : "No provider-backed accommodation is available for this city yet. Try again later — we will not invent hotels."}
            </p>
```
**Verbatim current code (the fixed no-option state + honesty helpers — StayExplorer):**
```tsx
  if (!data.options.length) {
    return (
      <section className="v8-page" data-testid="v8-stay-explorer">
        <div className="v8-page-intro compact">
          <div>
            <p className="v8-kicker">{t("stay.kicker")}</p>
            <h1>{t("stay.title")}</h1>
          </div>
        </div>
        <div className="v8-empty-state" data-testid="stay-no-options">
          <b>{zh ? "还没有可用的住宿候选" : "No stay candidates yet"}</b>
```
```tsx
function evidenceLabel(option: V8Data["options"][number] | null | undefined, zh: boolean): string {
  const confidence = option?.stay?.evidence?.confidence;
  if (typeof confidence !== "number" || confidence <= 0) {
    return zh ? "暂无供应商证据" : "No provider evidence";
  }
```
**Verbatim current code (the residual — zero price is rendered as a real amount):**
```tsx
function priceLabel(
  minor: number | null | undefined,
  currency: string | undefined,
  locale: string,
  zh: boolean,
): string {
  if (minor === null || minor === undefined) {
    return zh ? "价格未知（供应商未提供）" : "Price unknown (not provided)";
  }
  return `${money(minor, currency, locale)} · ${currency || "CNY"}`;
}
```
```tsx
        <div className="v8-stay-card-body">…<div className="v8-stay-price"><strong>{money(item.stay_total_minor, item.stay.currency, locale)}</strong><span>total · {money(item.stay.nightly_amount_minor, item.stay.currency, locale)}/{t("stay.nightly")}</span></div>…
```
and the backend source of the zero:
```python
            drafts.append(
                AccommodationOfferDraft(
                    external_offer_id=f"osm:{ref}",
                    property_name=name,
                    latitude=lat,
                    longitude=lon,
                    # OSM carries no price. Zero + explicit unknown beats a
                    # fabricated nightly rate.
                    nightly_amount_minor=0,
                    room_type=tourism or "hotel",
                    refundable=False,
                    evidence_confidence=0.6,
```

**What is still wrong / where the fix goes:**

1. **`CN¥0.00` masquerades as a rate.** `StayExplorer.tsx:68-78` (`priceLabel`) treats `0` as a known
   amount, and the card at `StayExplorer.tsx:38` calls `money(...)` directly, which formats `0` as
   `CN¥0.00` (`frontend/src/lib/money.ts:20-25` only guards `null`). Fix in
   `StayExplorer`'s `priceLabel` (and the card's `money(...)` call at line 38): treat `0` /
   non-positive as "price unknown", matching `HotelsPanel.tsx:180-185` which already uses
   `priceKnown = (stay.nightly_amount_minor ?? 0) > 0`.
2. **Zero-price offers are not filtered or flagged at the source.**
   `backend/app/stay_mobility.py:1217-1226` (`generate_stay_options`) ranks every captured offer,
   including `total_amount_minor == 0` from `OsmAccommodationProvider`
   (`backend/app/integrations/stay_osm.py:178`). Fix in `capture_accommodation_offers` /
   `generate_stay_options` (`backend/app/stay_mobility.py`): carry an explicit
   `price_status = "UNKNOWN"` on the snapshot (the column already exists —
   `backend/app/db/models.py:990`) instead of the sentinel `0`, and have the UI branch on it.
3. **`evidence_confidence = 0.6` is attached to a price-less OSM record.**
   `stay_osm.py:181` sets 0.6 for the *identity* of the property, but `evidenceLabel`
   (`StayExplorer.tsx:86-93`) then reports "Provider evidence confidence 60%" next to an invented
   price, which still reads as a rate-evidence card. Fix in `stay_osm.py`/`stay_mobility.py`:
   separate identity confidence from price evidence, and only surface price evidence when a real
   price exists.

The two literal strings from the finding are confirmed absent:
`grep -rn "captured hotel"` → no matches; `grep -rn "Provider price unavailable · explicit"` → no
matches. (`formatMinorMoney`'s `"Provider price unavailable"` still exists in
`frontend/src/lib/money.ts:20`, but is no longer composed with `" · explicit"`, and the stay surfaces
no longer call it with `null` for a captured hotel.)

---

## VERIFIED GOOD

Behaviours that are already correct and must not be regressed while the remaining items above are fixed:

1. **AI planning never fabricates a percentage and never fakes progress completion.**
   `PlanWithAiSheet.tsx:119-123` advances an indeterminate stepper only; there is no percentage.
2. **AI planning success requires a real plan artifact.**
   `PlanWithAiSheet.tsx:182-191` sets `COMPLETED` only when `planCount > 0`; with `/plans == []` it
   reports `NO_PLANS_PRODUCED` with an explicit "your trip is unchanged" body, and it attempts the
   real `/plans/generate` product path first (`PlanWithAiSheet.tsx:151-178`).
3. **The AI sheet exposes machine-checkable truth.**
   `data-testid="plan-ai-result"` and `data-plan-count={result?.planCount ?? 0}` are present
   (`PlanWithAiSheet.tsx:265-266`).
4. **Consumer booking entry now exists as the primary flow on the Trips path.**
   `V8Experience.tsx:1104-1123` renders paste / manual / screenshot (`JourneyInboxWorkbench`) first and
   tucks the raw-JSON workbench behind `Advanced / developer`. The manual form
   (`JourneyInboxWorkbench.tsx:443-540`) and the natural-language `text-extract` path
   (`JourneyInboxWorkbench.tsx:295-311`) are real, working entry points.
5. **Human-facing booking field mapping exists and is used for the review table.**
   `JourneyInboxWorkbench.tsx:110-154` defines `BOOKING_FIELDS`, `FIELD_LABELS`, `TYPE_LABELS`,
   `DECISION_LABELS`, `fieldLabel`, `decisionLabel`, `timeLabel`, `moneyLabel`, `renderFact`, and the
   `dl` at lines 631-639 already uses them. (The header block at 594-601 is the part still bypassing
   them.)
6. **Copilot dock now speaks traveller language for intents, verification and actions.**
   `CopilotDock.tsx:459-515` maps intent / verification / action enums to human strings, and
   `CopilotDock.tsx:607-621` uses them for the chips and the continuation button.
7. **Copilot raw identifiers are behind an Advanced disclosure.**
   `CopilotDock.tsx:383-393` puts `run_id` / `mission_id` / execution detail inside
   `<details … data-testid="native-hermes-observability">`.
8. **Copilot never claims execution it did not observe.**
   `CopilotDock.tsx:283-289` derives `executed` only from real `HERMES_NATIVE` `run.started` /
   `tool.*` events; `CopilotDock.tsx:366-371` and `:496-500` render "Planned locally only" otherwise.
9. **Copilot makes no silent mutation claim.**
   `CopilotDock.tsx:409-415` states "There is nothing for you to decide yet" / "A suggestion is ready…",
   and `:426-433` requires explicit user confirmation for anything touching bookings or protected plans.
10. **Today (Hub) is never a dead page.**
    `V8Experience.tsx:1222-1258` always renders the greeting, trip title, dates and the
    `hub-plan-with-ai` CTA; `:1286-1345` renders honest no-plan copy for Next / Stay / Attention.
11. **Trips has a real no-plan empty state with a next action.**
    `frontend/src/features/trip/TripItinerary.tsx:106-124` renders `trip-itinerary-empty` plus the
    "Plan my trip with AI" button.
12. **Map refuses to invent a city.**
    `frontend/src/components/v8/MapPanel.tsx:79-84, 195-213` renders a `v8-map-empty` state when there
    are no trustworthy coordinates.
13. **Hotel no-option states are honest and explicit.**
    `HotelsPanel.tsx:125-141` (`hotels-empty`) and `StayExplorer.tsx:13-32` (`stay-no-options`) both
    state that no provider-backed accommodation exists and that no hotel will be invented.
14. **Hotel price absence is stated, not fabricated (in HotelsPanel).**
    `HotelsPanel.tsx:160, 179-186` uses `priceKnown = (stay.nightly_amount_minor ?? 0) > 0` and prints
    "Price unavailable" / "暂无价格".
15. **Offline mode is explicit and read-only.**
    `V8Experience.tsx:662-663, 1913-1956` renders `OfflineJourneyView` with the
    `offline.readOnly` pill and the saved 24 h snapshot; `:277-286` refuses to discard a journey id on
    a network error.
16. **Duplicate confirmation protection is real.**
    `backend/app/operations/v9.py:921-929` rejects a duplicate `confirmation_ref`, and
    `backend/app/main.py:3355-3370` converts a racing insert into a deterministic 409 with an
    idempotent replay instead of a 500.
17. **Stale plans cannot be selected.**
    `backend/app/main.py:4024-4034` returns `409 STALE_RECOMPOSE_REQUIRED` for evidence-less / expired
    / inconsistent plans, and `backend/app/services.py:479-480` marks them `selectable=false`.
18. **Plan comparison does not invent candidates.**
    `frontend/src/features/planning/PlanComparison.tsx:70-73` filters to
    `status === "CANDIDATE" && !stale && selectable !== false` and returns `null` when none survive.

---

### Verdict summary

| Finding | Verdict |
| --- | --- |
| WB-H1 — AI planning false success | **FIXED_BY_CURRENT_EAC** (residual: plan count is unfiltered by status) |
| WB-H2 — Booking import developer-shaped | **PARTIALLY_FIXED** |
| WB-H3 — Copilot internal-language leaks | **PARTIALLY_FIXED** |
| WB-H4 — Today / Copilot blank empty states | **PARTIALLY_FIXED** |
| WB-H5 — Hotel no-data masquerades as evidence | **PARTIALLY_FIXED** |

No finding was `NOT_REPRODUCIBLE`: every one of the five original symptoms either still reproduces in
some surface (H2, H3, H4, H5) or was demonstrably removed by a current-code change (H1).
