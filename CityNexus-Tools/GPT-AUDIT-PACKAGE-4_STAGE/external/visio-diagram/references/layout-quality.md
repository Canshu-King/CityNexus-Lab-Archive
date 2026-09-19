# Layout quality

## Default layout contract

Use a deterministic `layered` or `grid` layout unless the user explicitly requires manual coordinates.

Set:

```json
{
  "engine": "layered",
  "direction": "LR",
  "uniformNodeSize": true,
  "nodeWidth": 2.4,
  "nodeHeight": 1.0,
  "nodeGap": 0.6,
  "layerGap": 1.2
}
```

Adjust dimensions to fit the longest label, then apply the same final width and height to all comparable boxes. Use separate size families for semantically different shapes such as junctions, decisions, lane containers, and multi-port engineering blocks. Prefer concise labels and deliberate line breaks over oversized shapes.

Use `sizeClass` as the machine-readable family. The content boundary and container exceptions are defined in [size-and-containers.md](size-and-containers.md).

## Compactness contract

For engineering, control, architecture, and flow diagrams that should converge around their content, set `layout.compact: true`.

- Establish the principal chain first, then place related branches in nearby semantic bands.
- Put feed-forward nodes directly above their receiving stage and feedback nodes below their return point.
- Minimize boundary-to-boundary gaps between connected same-axis peers. The default maximum is `max(0.8 in, 1.5 * nodeGap)`.
- For consecutive connected peers on one axis and in one `sizeClass`, calculate every gap from absolute page boundaries. In `LR/RL`, use `next.left - previous.right`; in `TB/BT`, use the corresponding top/bottom boundary gap. The group span must be no more than `0.03 in`.
- Fit the page to the full content envelope with intentional outer margin; compact mode requires at least 75% horizontal and 65% vertical page utilization.
- Require the final PNG to retain 4% to 8% page-colored margin; a Visio filter that crops to the black-bit bounds must not leave content touching the image edge.
- Minimize total connector length and bends after collision, label-clearance, and semantic routing constraints are satisfied.
- Prefer moving a branch closer to its anchor over stretching a long empty connector across the page.

Treat `LAYOUT_TOO_DISPERSED` and `LOW_PAGE_UTILIZATION` as blocking in compact mode.

## Layer and order semantics

- For `LR` or `RL`, nodes in one `layer` share an x-axis center. Nodes with the same `order` across layers share a y-axis row.
- For `TB` or `BT`, nodes in one `layer` share a y-axis center. Nodes with the same `order` across layers share an x-axis column.
- Assign `layer` from dependency depth or workflow stage.
- Assign `order` from the intended visual row or column, not from incidental input order.
- Keep layer-center gaps equal unless the user explicitly requests a grouped exception.

## Required checks

Treat these structural findings as blocking:

| Finding | Meaning | Required response |
|---|---|---|
| `INCONSISTENT_NODE_SIZE` | Uniform sizing is enabled but bounds differ | Normalize width and height |
| `LAYER_MISALIGNED` | Same-layer centers differ | Align the layer center axis |
| `ORDER_MISALIGNED` | Same-order nodes do not share a row or column | Align the repeated order axis |
| `NODE_OVERLAP` | Node bounds overlap | Increase spacing or reposition |
| `OUT_OF_PAGE` | A node exceeds page margins | Fit layout within page bounds |
| `AXIS_SIZE_INCONSISTENT` | Same-axis peers could safely share a dimension | Normalize that dimension |
| `SAME_AXIS_GAP_INCONSISTENT` | Comparable consecutive peers have unequal absolute boundary gaps | Reposition the peers from page coordinates |
| `LAYOUT_TOO_DISPERSED` | Connected peers leave an excessive empty gap | Move the related nodes closer |
| `LOW_PAGE_UTILIZATION` | Compact page is much larger than its content | Refit the page or regroup branches |

Treat `INCONSISTENT_LAYER_SPACING` as blocking for clean architecture and block diagrams unless the user explicitly approves irregular grouping.

Also review:

- `TEXT_OVERFLOW_RISK`
- image border contact
- low canvas utilization
- near-blank snapshots
- connector crossings
- endpoint and port-lane alignment
- fully glued ratio
- connector labels that collide with lines, frames, or other text
- connector labels that drift away from the requested relative midpoint
- external module captions that no longer follow their owner shape
- node/caption/connector font and 0.80 text-block ratios
- page-resolved font-role sizes, line weights, and semantic colors from the active JSON profile

## Repair loop

For each repair round:

1. Inspect actual live shape bounds and text.
2. Snapshot the current page.
3. Run structural and image quality checks.
4. Preview automatic repair without applying it.
5. Apply only the reviewed repair.
6. Inspect, snapshot, and check again.

Stop after two automatic repair rounds. If blocking findings remain, report their codes, affected object IDs, and the proposed explicit edits.

For imitation or regression rounds, also require an effective change: modify at least one field listed by `visio://schemas/renderer-effective-fields`, regenerate the PNG, and verify that the pixels or inspected geometry changed. A style-profile edit qualifies only when a resolved effective value changes. Metadata-only edits do not prove a visual improvement.
