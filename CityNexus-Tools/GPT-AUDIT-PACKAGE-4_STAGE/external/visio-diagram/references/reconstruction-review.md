# Reconstruction and regression review

Read this reference only when imitating an existing diagram or validating a Skill/MCP change.

## Mode selection

- Normal creation: use the main Skill workflow and ordinary quality gates.
- Reference imitation: use the source-driven loop below and compare the supplied source with the latest PNG.
- Strict replica: additionally require a source inventory, per-arrow topology plan, region strategy for dense pages, and two explicit review stages.

Do not force strict-replica bookkeeping onto a small ordinary diagram.

## Source-driven workflow

### 1. Establish source truth

1. Keep a stable readable local path for the source VSDX or image.
2. Inspect it read-only.
3. Record visible language and notation exactly. Do not translate, normalize formulas, or invent unreadable text.
4. Mark uncertainty explicitly when text or an endpoint cannot be read.
5. For dense pages, divide the source into semantic regions before authoring the whole page. A practical target is no more than about 12–18 visible nodes per region.

### 2. Inventory topology before coordinates

Record each meaningful source-visible connector separately:

- source object and source side/port;
- target object and target side/port;
- route family: straight horizontal, straight vertical, orthogonal, feedback, loop, merge, fork, or boundary handoff;
- arrowhead presence and direction;
- required branches, merges, trunks, buses, and junctions;
- objects or text that the route must not cross;
- certainty and any unresolved endpoint.

One visible source arrow must not silently become a vague multi-hop description. If it requires multiple IR segments, keep a common source-arrow identity and ordered segment facts.

### 3. Author fresh Diagram IR

1. Build a fresh IR from the source inventory. Old generated scenes may explain failures but are not source truth.
2. Use stable IDs, semantic component types, explicit ports, absolute port lanes, and route types.
3. Bind external module names with node captions and signal descriptions with connector label anchors.
4. Use source-pixel coordinates when exact visual proportions matter; otherwise use measured page coordinates.
5. Validate and plan before rendering.

### 4. Preflight before Visio

- Schema and ID/reference validation must pass.
- Every source-visible arrow must have an IR counterpart or an explicit unresolved record.
- Dense regions must have bounded node counts and declared containers/groups.
- Text must have a role: node content, caption, connector label, formula, or note.
- Requested fonts must exist or have an explicit fallback.
- No public field may be claimed as a repair unless it appears in the renderer-effective resource.

### 5. Two-stage render and review

Stage 1, layout and topology:

- page aspect and content envelope;
- region/container bounds;
- principal axes and absolute same-axis gaps;
- node families and port lanes;
- every branch, merge, loop, bus, and arrow endpoint;
- connector crossings and bend grammar.

Stage 2, typography and polish:

- the selected profile font or an explicit notation font;
- measured reference-role sizes, 0.25 pt live tolerance, and no unrequested global restyling;
- centered 0.80 text-block safe area and declared exceptions;
- caption anchoring;
- connector-label midpoint, side, and clearance;
- formula baselines, line breaks, and small text;
- arrowhead size, line weight, rounding, and local spacing.

Do not spend repeated micro-adjustment rounds on a semantically wrong component or route. Rebuild that local subsystem after two failed local adjustments.

### 6. Structured findings and repair order

Each finding should contain:

- focus region;
- affected object IDs;
- source fact;
- current replica fact;
- defect class;
- expected visible change;
- renderer-effective fields likely to change.

Repair in this order:

1. component/shape family;
2. topology, ports, and anchors;
3. formulas, captions, and connector labels;
4. container/title/content proportions;
5. colors, shadows, line weight, and other weak style.

### 7. Re-render and close the loop

Re-run validation, planning, real Visio inspection, quality checks, PNG export, and the same visual checklist. A repaired item passes only when both the machine metric and the inspected source-vs-replica fact pass.

## Standard metrics

Use these current `visio-diagram` gates as the executable standard:

| Area | Required result |
|---|---|
| Source topology | Every known source-visible arrow has one explicit IR mapping |
| Endpoint alignment | `maxEndpointAlignmentError <= 0.03 in` |
| Glue | `fullyGluedRatio = 1.0` |
| Port lanes | `maxPortLaneAlignmentError <= 0.01 in` |
| Same-axis peer gaps | `maxSameAxisPeerGapSpan <= 0.03 in` |
| Node text center | `maxNodeTextCenterError <= 0.02 in` |
| Ordinary text block | `0.80 +/- 0.02`; decision about `0.70` |
| Node/caption/label font | Latin and Asian mismatch counts all zero |
| Font size and role | all size mismatch counts zero; role/size-class span `<= 0.25 pt` |
| Frame and connector style | color and weight mismatch counts zero; weight error `<= 0.10 pt` |
| Caption anchor | `maxCaptionAnchorError <= 0.02 in` |
| Connector-label anchor | `maxConnectorLabelAnchorError <= 0.03 in` |
| Label relative drift | position shift no more than `0.20` |
| Text versus geometry | all line/frame/text overlap and low-clearance counts zero |
| Arrow boundary | source/target intrusion, short terminal, and arrow-node overlap counts zero |
| Compact page | at least 75% width and 65% height utilization when `compact: true` |
| No-op proof | at least one renderer-effective IR or inspected-geometry change and a non-zero PNG pixel change |

## Effective-change gate

Read `visio://schemas/renderer-effective-fields`.

- Metadata-only edits are documentation, not a visual repair.
- A repair round must change at least one listed planning/rendering field.
- Re-render and compare live inspection plus PNG pixels.
- A zero-geometry and zero-pixel-change round is a no-op and cannot be reported as improvement.

## Review evidence

Use exactly the original and the latest replica as the primary visual pair. Add the smallest useful local crop only when the full images are too dense to judge one connector, caption, formula, or arrow-dense subsystem. A generated crop that nobody inspects is a debug artifact, not review evidence.

Maintain two checklists:

- topology checklist: branches, merges, buses, loops, boundaries, endpoint sides, and arrow directions;
- visual checklist: alignment, spacing, wrapping, font, caption/label anchoring, line-through-text, and style fidelity.

Machine gates remain authoritative for coordinates, glue, font resolution, text-block ratios, and collisions. Human review remains authoritative for notation fidelity, semantic grouping, and overall visual balance.

## Research basis

This compact loop adapts the useful scene-contract, renderer-effective-field, explicit-topology, and iterative-review ideas from [Visiomaster scene schema](https://github.com/Rss3208/Visiomaster/blob/main/references/scene-schema.md), [review contract](https://github.com/Rss3208/Visiomaster/blob/main/references/review-contract.md), [renderer-effective fields](https://github.com/Rss3208/Visiomaster/blob/main/references/renderer-effective-fields.json), [no-op gate](https://github.com/Rss3208/Visiomaster/blob/main/scripts/round_noop_gate.py), and [font utilities](https://github.com/Rss3208/Visiomaster/blob/main/scripts/font_utils.py). It intentionally does not copy that repository's product identity, large exact-replica workflow, serif default, permissive tiny-font thresholds, or default edge-label placement.
