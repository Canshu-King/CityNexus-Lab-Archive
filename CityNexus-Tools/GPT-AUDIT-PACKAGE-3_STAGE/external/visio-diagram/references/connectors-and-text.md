# Connectors and text

This reference is mandatory for every diagram.

## Endpoint contract

- Default to `routing: orthogonal`.
- Use `sourcePort` and `targetPort` to choose `left`, `right`, `top`, or `bottom`.
- Omitted or `auto` ports must resolve deterministically from relative node positions and the layout direction.
- The default `sourcePortPosition` and `targetPortPosition` is `0.5`, the exact side center.
- For multi-port engineering blocks, use explicit normalized positions from `0` to `1`. On left/right sides the value runs bottom-to-top; on top/bottom sides it runs left-to-right.
- Paired semantic lanes must use the same page-axis coordinate.
- Align same-row multi-port lanes by absolute page coordinate. Reuse the same normalized position only when the two shape dimensions make that absolute coordinate identical.
- Every connector must be glued at both endpoints. A visually touching unglued line is a failure.
- The first segment must leave the source along the selected side's outward normal. The tail may touch the source boundary only at its endpoint and must not re-enter the source.
- The final segment must approach the target from outside along the selected side's normal. Only the arrow tip may touch the target boundary.
- Use the calibrated arrow contract (`EndArrow=13`, size 2, profile-resolved line weight; engineering base `0.75 pt`) or block as unverified. Reserve at least `0.18 in` of terminal length and keep the complete arrowhead envelope outside the source and every non-target node.

Use `straight` only when a direct line is intentional and does not cross another object. Use orthogonal routing for feedback loops, branches, control flow, and swimlanes.

## Route quality

- Prefer the fewest bends that preserve meaning.
- If two nodes share a row or column, choose the opposing port pair that permits a direct horizontal or vertical route. Do not add a dogleg to an unobstructed direct connection.
- Keep the first and last segment normal to the selected shape side.
- Do not route through unrelated nodes.
- Do not cross or overlap another connector without an explicit junction.
- Keep parallel lanes evenly spaced.
- Treat internal symbol geometry, such as transform-block diagonals, as shape decoration rather than process connectors.
- For self-loops, use two different ports, such as `right` to `top`.

## Text must never cover a line

Connector labels must have their own position; never accept Visio's default centered-on-line text placement.

- Default to `labelPosition: 0.5`.
- Anchor the label to the semantic segment nearest the requested relative position.
- Horizontal segments place the label above, then below; vertical segments place it right, then left.
- Keep tangential movement within `0.20 in` and normal collision avoidance within `0.16 in`.
- If no legal position exists inside that budget, return `CONNECTOR_LABEL_ANCHOR_UNRESOLVED`. Do not keep moving the text farther from its connector.
- Single-character engineering labels such as `d` and `q` use their measured compact width; do not reserve a long word-sized text box.

Required checks:

- label bounding box versus every connector path segment;
- label bounding box versus every node/frame bounding box;
- label bounding box versus every other label;
- node text or formula bounding box versus its frame safety area.

Use at least:

```text
line-to-label clearance >= max(0.08 in, 0.5 * label font height)
```

Place horizontal-route labels above or below the route, and vertical-route labels to the left or right. If the inter-box gap is narrower than the label, move the label outside the boxes rather than shrinking text into the line.

Use an opaque page-colored text background as a visual fallback, but do not treat masking the line as proof of non-overlap. Coordinate clearance remains mandatory.

## Shape-bound external captions

Use a node `caption` only when a module name belongs outside the frame.

- Ordinary or horizontal blocks default to `captionSide: top`.
- Tall vertical blocks default to the right side.
- `captionPosition: 0.5` centers a top/bottom caption horizontally or a left/right caption vertically.
- `captionOffset` is the visible frame-to-caption clearance and must be at least `0.08 in`.
- Captions remain separate text shapes but must be bound to the owner shape; moving or resizing the owner must retain the anchor.
- Explicit sides do not silently switch or drift. Insufficient space is a blocking layout defect.

## Text inside shapes

- Resolve node, caption, and connector-label fonts and sizes from [typography-and-style.md](typography-and-style.md). Set both Latin and Asian font cells; formulas use an explicit math role.
- Ordinary connector descriptions use `fontRole: edgeLabel`; important signals use `fontRole: signal`. Do not promote every edge label to the signal tier.
- Keep labels concise and use intentional line breaks.
- Grow the shape before reducing readable font size.
- Keep ordinary text inside an inset content area.
- For formulas, use the same 80% safety envelope unless an equation object has a measured tighter contract. Keep at least 10% nominal padding on all four sides.
- Move long explanations to separate note shapes; do not place paragraphs across process lines.

## Blocking findings

- `CONNECTOR_ENDPOINT_MISALIGNED`
- `SOURCE_ENDPOINT_INTRUSION`
- `SOURCE_TAIL_CLEARANCE_LOW`
- `TARGET_ENDPOINT_INTRUSION`
- `ARROW_TERMINAL_CLEARANCE_LOW`
- `ARROWHEAD_OVERLAPS_NODE`
- `ARROW_GEOMETRY_UNVERIFIED`
- `CONNECTOR_ROUTE_STYLE_MISMATCH`
- `CONNECTOR_NOT_FULLY_GLUED`
- `CONNECTOR_CROSSES_NODE`
- `CONNECTOR_CROSSING`
- `INEFFICIENT_CONNECTOR_PORT`
- `PORT_LANE_MISALIGNED`
- `AMBIGUOUS_SIGNAL_SOURCE`
- `TEXT_LINE_OVERLAP`
- `TEXT_LINE_CLEARANCE_LOW`
- `TEXT_SHAPE_OVERLAP`
- `TEXT_TEXT_OVERLAP`
- `TEXT_OVERFLOW_RISK`
- `CONNECTOR_LABEL_ANCHOR_UNRESOLVED`
- `CONNECTOR_LABEL_DRIFT_EXCESSIVE`
- `CONNECTOR_LABEL_ANCHOR_MISALIGNED`
- `CONNECTOR_LABEL_FONT_MISMATCH`
- `CONNECTOR_LABEL_ASIAN_FONT_MISMATCH`
- `CONNECTOR_LABEL_FONT_SIZE_MISMATCH`
- `CONNECTOR_LABEL_FONT_STYLE_MISMATCH`
- `CONNECTOR_LABEL_TEXT_COLOR_MISMATCH`
- `CONNECTOR_LINE_COLOR_MISMATCH`
- `CONNECTOR_LINE_WEIGHT_MISMATCH`
- `CAPTION_ANCHOR_UNRESOLVED`
- `CAPTION_NOT_RENDERED`
- `CAPTION_ANCHOR_MISALIGNED`
- `CAPTION_FONT_MISMATCH`
- `CAPTION_ASIAN_FONT_MISMATCH`
- `CAPTION_FONT_SIZE_MISMATCH`
- `CAPTION_FONT_STYLE_MISMATCH`
- `CAPTION_TEXT_COLOR_MISMATCH`
