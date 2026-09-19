# Size, text alignment, and containers

This reference is mandatory for every diagram.

## Default text contract

- Node text is horizontally centered.
- Node text is vertically centered.
- Multi-line paragraphs are center-aligned.
- The text-block pin is the geometric center of the shape.
- Use intentional line breaks; do not simulate centering with spaces.
- Resolve Latin, Asian, math, size, weight, and color through the selected JSON style profile. `engineering-standard` preserves the compact SimSun baseline.
- For ordinary nodes, the centered ShapeSheet text block uses 80% of shape width and 80% of shape height. Diamonds use about 70%.
- Choose `fontRole` before calculating the required shape size. Default styling and measured reference overrides are defined in [typography-and-style.md](typography-and-style.md).

An explicit notation rule may override the default, such as a container title band or a left-aligned note. Record that exception rather than changing the global default.

Required live metrics:

```text
nodeTextMisalignedCount = 0
maxNodeTextCenterError <= 0.02 in
nodeTextBlockUtilizationMismatchCount = 0
maxNodeTextBlockRatioError <= 0.02
nodeFontMismatchCount = 0
nodeAsianFontMismatchCount = 0
nodeFontSizeMismatchCount = 0
maxFontSizeErrorPt <= 0.25
```

## Size families

Assign `sizeClass` to nodes that should share dimensions.

- First try a common width and height for all comparable nodes on one principal axis, even when their labels differ.
- Keep a shared dimension whenever the largest required value remains inside every node's allowed content/architecture envelope.
- Summing junctions, ordinary process blocks, controllers, gains, feedback blocks, multi-port stages, and containers are separate role families.
- A node may move to a larger family only because its content safety area or architecture role requires it.
- Never enlarge one node arbitrarily while leaving equivalent peers unchanged.

Block size must be justified only by:

1. contained text or formula;
2. required ports and lane spacing;
3. container membership and child layout;
4. an explicit semantic shape requirement.

## Content boundary

For ordinary centered text:

```text
text-block width  = 80% of block width
text-block height = 80% of block height
measured glyph width  <= 80% of block width
measured glyph height <= 80% of block height
minimum nominal padding on each side >= 10%
```

The 80% rule is the single ordinary-node safety envelope, not a demand that glyphs fill 80% of both dimensions. Do not use a looser glyph allowance than the editable text block. For diamonds, use a smaller text-block and content-safe interior, about 70% of the outer width and height.

An explicit ratio override requires `data.textLayoutReason`. Do not enlarge glyphs merely to fill the safe area, and do not use a ratio override to excuse an oversized frame.

Compute width and height independently:

```text
requiredWidth  = max(textWidth / safeRatio, top/bottom port span, measured architecture width)
requiredHeight = max(textHeight / safeRatio, left/right port span, measured architecture height)
allowedMaximum = max(required * 1.45, required + 0.45 in)
```

On one side, adjacent ports should have at least `0.22 in` absolute separation and the outermost port should remain at least `0.15 in` from the nearest corner. A `multiport` string is not an exemption; the real positions determine the required dimension.

If content exceeds the safe area, first add deliberate line breaks, then enlarge the entire `sizeClass` where appropriate. Do not shrink readable text or grow a single box without measured evidence.

When a semantic requirement is not derivable from text or ports, record numeric evidence as `data.sizeEvidence.requiredWidth` and/or `requiredHeight`, plus a short reason. Reject each excessive dimension independently; a justified height never licenses unrelated width growth.

## Containers and large frameworks

A container or large framework is an independent architecture role:

- it may be larger than ordinary nodes;
- it may geometrically contain child nodes without triggering ordinary overlap findings;
- it should be sent behind its children;
- its size is the child-content bounding box plus standardized internal padding;
- compare it only with containers of the same `sizeClass`.

Required container padding is the larger of `0.3 in` or 5% of the contained width/height. Reject members outside the container, insufficient padding, and unbounded extra slack. Do not use a large framework merely to hide an unresolved layout problem.

## Blocking findings

- `NODE_TEXT_NOT_CENTERED`
- `NODE_TEXT_BLOCK_UTILIZATION_NONSTANDARD`
- `NODE_TEXT_BLOCK_UTILIZATION_OUT_OF_RANGE`
- `NODE_FONT_MISMATCH`
- `NODE_ASIAN_FONT_MISMATCH`
- `NODE_FONT_SIZE_MISMATCH`
- `NODE_FONT_STYLE_MISMATCH`
- `FONT_BELOW_READABLE_MINIMUM`
- `FONT_SIZE_OVERRIDE_WITHOUT_REASON`
- `FONT_ROLE_SIZE_DRIFT`
- `TEXT_OVERFLOW_RISK`
- `SIZE_CLASS_INCONSISTENT`
- `AXIS_SIZE_INCONSISTENT`
- `OVERSIZED_NODE_WITHOUT_REASON`
- `CONTAINER_MEMBER_OUTSIDE`
- `CONTAINER_PADDING_LOW`
- `CONTAINER_EXCESS_SLACK`
