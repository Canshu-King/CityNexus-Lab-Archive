---
name: visio-diagram
description: "Create, imitate, edit, inspect, quality-check, repair, and export compact editable Microsoft Visio diagrams through visio-mcp. Use for engineering and control block diagrams, swimlanes, flowcharts, state machines, architecture diagrams, or VSDX/PNG/SVG/PDF outputs where bounded content-driven box sizes, restrained configurable typography and line style, center-axis and absolute port alignment, shape-bound captions, midpoint-anchored connector labels, fully external arrowheads/tails, orthogonal routing, fully glued connectors, and text that never overlaps connector or frame lines matter."
---

# Visio Diagram

Use Diagram IR as the single source of truth. Keep workflow decisions in this Skill and use `visio-mcp` only for generic diagram capabilities.

## Skill Type

This Skill is both `consistent-workflow` and `reusable-domain-knowledge`: it defines a repeatable Visio workflow and loads only the diagram-specific rules needed for the current request.

## Progressive references

Always read:

- [references/connectors-and-text.md](references/connectors-and-text.md)
- [references/size-and-containers.md](references/size-and-containers.md)
- [references/typography-and-style.md](references/typography-and-style.md)
- [references/layout-quality.md](references/layout-quality.md)
- [references/mcp-tools.md](references/mcp-tools.md)

Then read only the diagram reference required by the request:

- Engineering or control block diagram: [references/engineering-diagrams.md](references/engineering-diagrams.md)
- Swimlane or cross-functional process: [references/swimlanes.md](references/swimlanes.md)
- Flowchart: [references/flowcharts.md](references/flowcharts.md)
- State machine: [references/state-machines.md](references/state-machines.md)
- Reference imitation or Skill/MCP regression: [references/reconstruction-review.md](references/reconstruction-review.md)

Do not load unrelated diagram references. This Skill intentionally has no sequence-diagram workflow.

## Workflow Contract

Trigger: use this Skill for creating, imitating, editing, validating, repairing, or exporting a Visio diagram.

Inputs: user intent, optional VSDX/image references, target output formats, allowed paths, and any diagram-specific notation constraints.

Steps:

1. Run `visio_doctor`.
2. Read `visio://schemas/diagram`, `visio://schemas/style-profile`, and `visio://styles/profiles`. For imitation or regression work, also read `visio://schemas/renderer-effective-fields`.
3. If a VSDX or image is supplied as a reference, inspect it read-only. Extract measurable layout rules; do not modify or copy the source artifact unless the user explicitly asks.
4. Select a JSON `styleProfile`, then build Diagram IR with stable IDs, explicit diagram direction, measured role-based dimensions, `fontRole`, `layer`/`order`, connector ports, port positions, routing, and bounded text anchors. Keep the default close to the original compact renderer: SimSun 10 pt, black/white, 0.75 pt lines, 0.12 in small corners, and a centered 0.80 text safe area. Use formula font roles or explicit fields only where semantics require them. When imitating the supplied engineering reference, apply its measured 18/16/14/12/10 pt roles to the affected elements instead of globally rescaling every page. Use `captionSide`/`captionPosition` for external module titles and `labelPosition: 0.5` for connector descriptions. Set `layout.compact: true` for engineering and other diagrams that should fit their content envelope.
5. Run `diagram_validate`, then `diagram_plan`. Fix all blocking findings before rendering.
6. Before a visible or file-producing action, state the action and paths. Reuse authorization already given for those paths; otherwise obtain confirmation.
7. Render with `diagram_open_visible` for interactive review or `diagram_render` for headless work.
8. Run `diagram_inspect`, `diagram_snapshot`, and `diagram_quality_check`.
9. If repairable findings remain, preview `diagram_auto_repair` with `apply: false`, then apply the reviewed repair. Re-run inspection and quality checks. Stop after two automatic rounds.
10. Export only requested formats. Default to VSDX plus PNG when an editable diagram is requested without named formats.
11. Close the session with `diagram_close`.

Exit Criteria: the editable output and requested exports exist; structure and live connector scores have no blocking finding; the regression image has been reviewed; and every opened session is closed.

Validation: run `diagram_validate`, `diagram_plan`, `diagram_inspect`, `diagram_quality_check`, and a PNG snapshot comparison.

Blocking Hook: the MCP quality checker or repository Release profile must return non-zero when a required metric fails. Do not replace coordinate gates with visual judgment alone.

## Gate Rules

CLI checker: use the `visio-mcp` validation/quality commands or its repository test profile. Input is Diagram IR plus live inspection; any blocking finding is a failed check.

Hook gate: Release verification blocks on unit tests, real Visio COM rendering, inspection sidecar, quality sidecar, and export regression. Diagram-specific work that is not in repository CI still requires the same checks before handoff.

MCP tool library: `visio-mcp` supplies generic schema, render, inspect, quality, repair, snapshot, and export tools. Workflow and visual intent remain in this Skill.

Human confirmation / 人工确认: the requesting user is the owner and approves or rejects the final visual regression after machine gates pass.

Skip rationale: exact optical balance and notation fidelity are not fully stable as a CLI rule, so a human reviews the PNG after machine gates pass. This manual review may reject a technically valid but visually diffuse result.

Do not export a final result while any of these are non-zero or unresolved:

- inconsistent size inside a comparable role family;
- non-centered node text, per-dimension underfit, or unbounded empty space;
- a normal node whose text-block safe area differs from 0.80 without measured `data.textLayoutReason`;
- Latin or Asian text that does not resolve to the requested default font;
- a role font size below its readable floor or drifting more than `0.25 pt` inside one `fontRole + sizeClass`;
- actual font size, weight/style, text color, fill, frame color, connector color, or line weight that differs from the resolved JSON style;
- an external module caption detached from its shape-side anchor;
- a connector label unresolved or drifting more than the bounded midpoint budget;
- same-axis peers that could share a dimension safely but do not;
- unequal absolute boundary gaps among consecutive same-axis peers in one `sizeClass`;
- row, column, layer, or intended center-axis error;
- excessive same-axis gap or low page utilization in compact mode;
- connector endpoint error at the selected side center or port lane;
- source tail or target arrow entering a node boundary;
- insufficient terminal length or arrowhead overlap with any node;
- inefficient port selection or absolute port-lane misalignment;
- connector route-style mismatch;
- connector missing or not glued at both endpoints;
- connector crossing an unrelated node;
- text intersecting a connector, node frame, or other text;
- text overflow or formula safety-padding failure;
- ambiguous signal sources represented only by floating notes;
- node overlap or out-of-page content.

For rendered connector quality, require:

```text
maxEndpointAlignmentError <= 0.03 in
fullyGluedRatio = 1.0
sourceEndpointIntrusionCount = 0
targetEndpointIntrusionCount = 0
arrowTerminalClearanceLowCount = 0
arrowheadNodeOverlapCount = 0
arrowGeometryUnverifiedCount = 0
nodeTextMisalignedCount = 0
maxNodeTextCenterError <= 0.02 in
sameAxisPeerGapInconsistentCount = 0
maxSameAxisPeerGapSpan <= 0.03 in
nodeTextBlockUtilizationMismatchCount = 0
maxNodeTextBlockRatioError <= 0.02
nodeFontMismatchCount = 0
nodeAsianFontMismatchCount = 0
nodeFontSizeMismatchCount = 0
nodeFontStyleMismatchCount = 0
nodeTextColorMismatchCount = 0
nodeLineColorMismatchCount = 0
nodeFillColorMismatchCount = 0
nodeLineWeightMismatchCount = 0
nodeCornerRadiusMismatchCount = 0
connectorLabelAnchorMisalignedCount = 0
maxConnectorLabelAnchorError <= 0.03 in
connectorLabelFontMismatchCount = 0
connectorLabelAsianFontMismatchCount = 0
connectorLabelFontSizeMismatchCount = 0
connectorLabelFontStyleMismatchCount = 0
connectorLabelTextColorMismatchCount = 0
connectorLineColorMismatchCount = 0
connectorLineWeightMismatchCount = 0
captionMissingCount = 0
captionAnchorMisalignedCount = 0
maxCaptionAnchorError <= 0.02 in
captionFontMismatchCount = 0
captionAsianFontMismatchCount = 0
captionFontSizeMismatchCount = 0
captionFontStyleMismatchCount = 0
captionTextColorMismatchCount = 0
maxFontSizeErrorPt <= 0.25
maxLineWeightErrorPt <= 0.10
maxNodeCornerRadiusErrorIn <= 0.005
fontRoleSizeDriftCount = 0
maxFontRoleSizeSpanPt <= 0.25
textLineOverlapCount = 0
textLineLowClearanceCount = 0
textShapeOverlapCount = 0
textTextOverlapCount = 0
connectorCrossingCount = 0
connectorConnectorCrossingCount = 0
```

Treat the exported image as a visual regression artifact, but use live coordinates and path geometry as the authority for alignment and collision decisions.

## Reference imitation

When testing the Skill against a supplied diagram:

1. Separate general rules from sample-specific measurements.
2. Recreate the requested semantics or a de-identified equivalent; do not blindly trace legacy defects.
3. Compare role-size consistency, center spread, port-lane delta, endpoint alignment, glue ratio, orthogonal-route ratio, bend count, label clearance, and page utilization.
4. Review topology/layout first, then typography/spacing. A metadata-only change or a render with no visible pixel change is not an improved round.
5. Report both improvements and remaining fidelity limits.

## Failure handling

- If Visio or COM is unavailable, stop at validated Diagram IR and report that rendering was not verified.
- If an output path is disallowed, choose an approved path rather than widening the boundary.
- If a live session fails, close known sessions and preserve the IR for retry.
- If blocking findings remain after two repair rounds, report affected IDs and ask before applying explicit edits.

## Human Confirmation

Owner/确认人: the requesting user owns the visual standard and final acceptance.

Accepted gates: coordinate and collision checks, Release regression, and manual PNG review are all blocking. The user may explicitly approve or reject another iteration after seeing the regression image.

Manual review scope: semantic grouping, compactness, notation fidelity, and overall visual balance remain human-reviewed because a diagram can satisfy geometry metrics and still look weak.
