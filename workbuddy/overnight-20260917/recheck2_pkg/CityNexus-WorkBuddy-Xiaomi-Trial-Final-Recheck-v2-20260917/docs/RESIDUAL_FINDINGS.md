# Residual findings to verify

## R1 — disrupted target may survive accepted replan

Final trace says:

- event: `CLOSURE -> 鼓浪屿风琴博物馆(临时展馆)`
- proposal: removed=1, added=1
- plan changed
- accepted through UI

But `stop_titles_before_sample` and `stop_titles_after_sample` both still contain:

`鼓浪屿风琴博物馆(临时展馆)`

This is not enough evidence that the disrupted entity was actually removed.

Verify using IDs, not only titles:
- affected_activity_id
- affected_place_id / semantic key
- proposal.diff.removed
- proposal.diff.added
- accepted-plan activity IDs/place IDs/semantic keys

PASS only if:
- the actual disrupted entity is absent or materially transformed according to
  the recovery contract;
- a same-title replacement, if legitimate, has a distinct grounded identity and
  explanation.

If the same closed activity/place remains unchanged after accept:
P0 -> BLOCKED.

## R2 — Live shows multiple indistinguishable pending replan cards

The final Xiaomi screenshot shows two visually identical:

`推荐怎么改`

cards with the same `移除 1 项 · 新增 1 项` summary.

Source currently renders every PRESENTED/GENERATED proposal via `pending.map()`
without meaningful differentiation.

Verify whether these are:
- duplicate proposals; or
- genuinely different alternatives.

If alternatives:
show actual differences, destination/time/change, and why they differ.

If duplicates:
dedupe or show only the preferred proposal.

A traveler must not choose between indistinguishable "接受新方案" buttons.

## R3 — canonical booking review still exposes internal vocabulary

`JourneyInboxWorkbench.tsx` still directly renders fields such as:

- `item.role`
- `draft.artifact_type`
- `draft.status`
- `draft.extraction_mode`
- `anchor_role`
- `payment_status`
- `UNKNOWN`

The final screenshot also shows implementation-like values such as:
- `manual-entry`
- `Departure anchor`

Revalidate the final consumer path.

Default UI must use traveler language.
Raw semantic/extraction status may remain under Advanced.

## R4 — Copilot native mission timeline can still expose raw tool names

`NativeMissionTimeline` still renders:

`event.tool_name ? <code>{event.tool_name}</code> : event.status`

outside the Advanced/raw-details disclosure.

A simple place question may not trigger this path.

Test an agent/tool mission that does.

Default traveler surface must humanize the tool event.
Raw tool_name belongs under Advanced.

## R5 — Trips still leaks internal activity taxonomy

Final Trips screenshot visibly contains:
- `check_out`
- `departure`

and Activity Detail can show raw type labels such as `museum`.

Localize/humanize traveler-facing activity roles:
- 退房
- 离开 / 出发
- 博物馆
etc.

## R6 — persistent Copilot dock competes with core mobile content

The persistent bottom Copilot dock occupies a large vertical area on nearly every
screen and can compete with sheets/primary actions.

Verify:
- create flow;
- AI planning sheet;
- booking;
- Live;
- short 390px/412px-wide viewport.

Expected:
- dock collapses/minimizes when a modal/sheet or high-priority action surface is
  open;
- it must not obscure content or create stacked bottom controls.

## R7 — hotel cards are truthful but weakly differentiated

Final hotel evidence shows many cards with nearly identical:
- unknown price
- walk time
- arrival/departure fit
- cancellation state
- recommendation copy

Do not fabricate differentiation.

But verify that selection is not effectively arbitrary:
- show area/address/provider identity;
- expose real differences when provider data exists;
- clearly say when evidence is insufficient to rank.

This is primarily product quality unless the UI claims a ranking unsupported by evidence.

## R8 — run-specific AI gate has a fail-open baseline edge

The new planning logic snapshots existing plan IDs.

But if the baseline-plan fetch fails and returns an empty set, a later successful
GET can classify old plans as "new".

Test:
1. journey already has old plan(s);
2. baseline GET fails transiently;
3. new planning run produces no artifact;
4. post-run GET succeeds returning old plan(s).

Expected:
- terminal state is indeterminate/failure;
- never success.

Baseline snapshot failure must fail closed for success attribution.

## R9 — stale pre-hotfix acceptance report remains packaged

The package includes older acceptance evidence that contradicts the final trace.

This is packaging hygiene, not a product blocker.

Final package should clearly mark:
- PRE_HOTFIX
- SUPERSEDED

or omit stale acceptance files from the top-level evidence set.
