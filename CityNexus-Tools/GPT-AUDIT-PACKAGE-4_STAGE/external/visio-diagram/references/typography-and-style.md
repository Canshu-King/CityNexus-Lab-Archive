# Typography and line style

Use the default profile as a conservative visual baseline. Do not let styling rewrite the diagram structure or introduce a new visual language without user approval.

## Minimal JSON profile

`visio://styles/profiles` exposes only three groups and seven high-impact values:

```json
{
  "font": {
    "ordinaryFamily": "SimSun",
    "asianFamily": "SimSun",
    "mathFamily": "Times New Roman"
  },
  "text": {
    "fontSizePt": 10,
    "safeRatio": 0.8
  },
  "line": {
    "weightPt": 0.75,
    "cornerRadiusIn": 0.12
  }
}
```

This matches the comfortable early renderer baseline: compact宋体 text, thin black lines, white fill, and a small rounded corner. Page size does not silently rescale fonts or line weights.

Override only what the request needs:

```json
{
  "document": {
    "styleProfile": "engineering-standard",
    "typography": {
      "fontSizePt": 10,
      "mathFontSizePt": 12
    },
    "appearance": {
      "lineWeightPt": 0.75,
      "nodeCornerRadiusIn": 0.12
    }
  }
}
```

Per-node or per-edge `fontSizePt`, `lineWeightPt`, and `cornerRadiusIn` remain absolute overrides.

## Reference imitation

Do not activate a full style hierarchy merely because one reference contains it. For the supplied `id=0` engineering reference, use these measured values only on matching semantic elements:

| Element | Measured size |
|---|---:|
| primary module or formula block | 18 pt |
| signal or variable | 16 pt |
| loop or transform caption | 14 pt |
| secondary explanation | 12 pt |
| dense bilingual block | 10 pt |

The same reference uses square engineering blocks, 0.75 pt black lines, white fill, and arrow type 13/size 2. Apply `cornerRadiusIn: 0` only to elements that need that source style; do not globally replace the comfortable default.

## Fonts and formulas

- Ordinary default: `SimSun` for both Latin and Asian text.
- Formula role: `Times New Roman`; Asian fallback remains `SimSun`.
- Set both Visio `Char.Font` and `Char.AsianFont`.
- Variables and quantity symbols are italic; operators, numerals, constants, and units are upright.
- Vectors and matrices are bold italic.
- If mixed formula runs require different styles, split the formula into editable fragments or report the limitation. Do not claim whole-string italics are equivalent.

The notation convention follows [ISO house style and ISO 80000 references](https://www.iso.org/ISO-house-style.html).

## Visual constraints

- Keep ordinary output black on white unless color encodes stable meaning.
- Keep node text horizontally and vertically centered.
- Use the 0.80 text safe ratio; decisions may use 0.70.
- Preserve the profile corner radius unless the diagram semantics require a square symbol.
- Prefer explicit measured overrides over automatic global restyling.

## Required live gates

```text
nodeFontMismatchCount = 0
nodeAsianFontMismatchCount = 0
nodeFontSizeMismatchCount = 0
nodeFontStyleMismatchCount = 0
nodeTextColorMismatchCount = 0
nodeLineColorMismatchCount = 0
nodeFillColorMismatchCount = 0
nodeLineWeightMismatchCount = 0
nodeCornerRadiusMismatchCount = 0
connectorLabelFontMismatchCount = 0
connectorLabelAsianFontMismatchCount = 0
connectorLabelFontSizeMismatchCount = 0
connectorLineWeightMismatchCount = 0
captionFontMismatchCount = 0
captionAsianFontMismatchCount = 0
captionFontSizeMismatchCount = 0
maxFontSizeErrorPt <= 0.25
maxLineWeightErrorPt <= 0.10
maxNodeCornerRadiusErrorIn <= 0.005
fontRoleSizeDriftCount = 0
maxFontRoleSizeSpanPt <= 0.25
```

The compact profile mechanism borrows the idea of renderer-effective style fields from [Visiomaster style profiles](https://github.com/Rss3208/Visiomaster/blob/main/templates/style_profiles.json), while the default values come from the user-approved early output and supplied local Visio reference.
