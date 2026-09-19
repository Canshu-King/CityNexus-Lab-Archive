# Accessibility Evidence UX

## 1. The central rule

`UNKNOWN != ACCESSIBLE`.

The UI must never turn missing or ambiguous accessibility information into a
positive availability claim. The implementation applies this rule in three
layers:

1. **Adapter** — `normalizeEvidenceState` maps unrecognised, missing, stale, or
   expired values to `NEEDS_LIVE_EVIDENCE`.
2. **Component** — `EvidenceBadge` renders a non-green, non-check visual for
   unknown states and includes an explicit text label.
3. **Content** — unknown rows are shown under "Unknown evidence" or
   "Evidence gaps", with the rule text "Unknown is not accessible".

## 2. Evidence states and visual language

| State | Glyph | Shape | Text | Never |
| --- | --- | --- | --- | --- |
| `VERIFIED` | `✓` | Solid badge | "Verified" | Never used for absent evidence |
| `UNVERIFIED` | `?` | Dashed badge | "Unverified" | Never green |
| `CONFLICT` | `!` | Double border | "Conflict" | Never hidden behind a generic warning |
| `NEEDS_LIVE_EVIDENCE` | `⌛` | Dotted badge | "Needs live evidence" | Never a check or "accessible" label |

All four states are distinguished by glyph, border style, text, and colour.
Removing colour does not remove meaning.

## 3. Plan evidence UX

`CapabilityPlanExplanation` renders three separate sections:

- **Why selected** — positive capability preservation with observed/limit
  values where available.
- **Rejected** — the capability reason a candidate was excluded, e.g.
  "route walking 780m exceeds hard limit".
- **Unknown** — evidence gaps with `EvidenceSummary` and the explicit unknown
  rule. A missing step-free check is never displayed as a positive.

C4 protected commitments are rendered in a separate `cne-c4` block, not mixed
with ordinary capability rows.

## 4. Recovery diff

`RecoveryDiffCapability` shows:

- `BEFORE`
- `AFTER`
- `Capabilities preserved`
- `Capabilities at risk`
- `Evidence gaps`
- C4 commitments separately

A recovery that preserves one verified entrance can still show an unknown
candidate as `AT_RISK`; the UI does not mark the whole journey "accessible".

## 5. Map markers

`CapabilityMapOverlay` supports distinct markers:

- verified accessibility point (`♿`, solid)
- unknown accessibility information (`?`, dashed)
- known conflict (`!`, double border)
- rest stop (`R`, dotted)
- nap/rest window (`Zz`, dotted)
- walking limit warning (`△`, dashed)
- protected commitment (`C4`, solid)

The legend uses the same glyphs and labels as the markers. Unknown markers are
not drawn with a check and are not described as accessible.

## 6. Twin evidence

`TwinCapabilitySummary` separates:

- explicit capability
- explicit preference
- learned soft preference

HARD accessibility needs show `Explicit`, `Traveler stated`, `Active`, and
`Scope`. They never show a confidence progress bar. Learned soft preferences
may show strength and confidence, because they are explicitly labelled as
learned ranking context rather than planning authority.

## 7. Provenance labels

Every evidence badge can display its provenance:

- `LIVE`
- `RECORDED_FIXTURE`
- `LOCAL_UI_ONLY`

Recorded fixture scenarios are labelled on every surface and in the source
banner. The live adapter throws
`CapabilityAdapterNotConfiguredError` when the proposed endpoints are absent,
rather than replacing live data with fixtures.
