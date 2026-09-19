# visio-mcp tools

Use `visio://schemas/diagram` as the Diagram IR field authority. Read `visio://schemas/style-profile` and `visio://styles/profiles` before choosing typography, line weights, or colors. For imitation and regression work, also read `visio://schemas/renderer-effective-fields` so an iteration changes fields that the planner or renderer actually consumes.

## Read-only tools

| Tool | Purpose | Required input |
|---|---|---|
| `visio_doctor` | Check platform, renderer, and output boundaries | None |
| `diagram_validate` | Validate Diagram IR and references | `diagram` |
| `diagram_plan` | Compute deterministic layout and structural quality | `diagram` |
| `diagram_inspect` | Read actual shape text, positions, and dimensions | `sessionId` |
| `diagram_quality_check` | Evaluate structural or rendered-image quality | `sessionId` or `image` |

## Side-effecting tools

Obtain explicit user approval for the stated visible action and output paths before using these tools.

| Tool | Purpose | Required input |
|---|---|---|
| `diagram_render` | Render Diagram IR to an artifact | `diagram`, `output`; optional `visible`, `autoRepair` |
| `diagram_open_visible` | Render and open a visible Visio window | `diagram`, `output` |
| `diagram_snapshot` | Export the current page to PNG | `sessionId`, `output` |
| `diagram_edit` | Apply explicit move, resize, text, or selection operations | `sessionId`, `operations` |
| `diagram_auto_repair` | Preview or apply bounded repair | `sessionId`; use `apply: false` before `apply: true` |
| `diagram_export` | Export VSDX, PNG, SVG, or PDF | `sessionId`, `formats`, `outputDir` |
| `diagram_close` | Close the live session and optionally save | `sessionId`, `save` |

## Invocation rules

- Validate and plan before any render or open call.
- For engineering or dense process diagrams, set `sourcePort`, `targetPort`, `sourcePortPosition`, `targetPortPosition`, and `routing` explicitly where auto placement is ambiguous.
- Set `sizeClass` for comparable nodes. Port density is measured from real positions; for other semantic sizing evidence use numeric `data.sizeEvidence.requiredWidth` or `requiredHeight`.
- Set `layout.compact: true` when the page should be fitted and branch spacing should be gated.
- Default to `styleProfile: engineering-standard`. It preserves the compact baseline; change only `fontSizePt`, `mathFontSizePt`, `lineWeightPt`, or `nodeCornerRadiusIn` when the target requires it.
- Use `fontRole` for module, operator, math, signal, body, caption, note, dense, and ordinary edge-label distinctions. Keep ordinary node text-block width/height ratios at `0.8`, connector `labelPosition` at `0.5`, and external caption positions at `0.5`.
- Pass allowed output paths only; never ask the server to widen its output roots.
- Keep `autoRepair` bounded by the Skill workflow even when a tool offers automatic behavior.
- Prefer `diagram_auto_repair` for known repairable quality findings. Use `diagram_edit` only for explicit residual changes.
- Require live connector metrics to show `fullyGluedRatio: 1.0`, zero endpoint intrusion, zero arrowhead overlap/unverified geometry, zero endpoint misalignment, and zero text/geometry collisions.
- Require live node text metrics to show centered paragraph/vertical alignment and zero text-center error.
- Require zero node/caption/connector font-family, font-size, font-style, text-color, line-color, fill-color, and line-weight mismatch; also require zero text-block ratio mismatch, zero caption anchor error, and zero connector-label anchor error.
- Require `sameAxisPeerGapInconsistentCount: 0` and `maxSameAxisPeerGapSpan <= 0.03 in` in both structural and live inspection results.
- Run `diagram_close` after success or failure whenever a live `sessionId` exists.
