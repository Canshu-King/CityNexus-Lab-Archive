# New Targets From EAC Review

Validate these EAC claims rather than trusting them:

1. EAC hard severity fix.
2. EAC duplicate-code merge.
3. EAC numeric walking parser.
4. EAC clause-scoped negation/history.
5. EAC OSM accessibility normalization.
6. EAC provider-to-feasibility bridge.
7. EAC live source honesty.
8. EAC plan-impact semantics.

Specific adversarial cases:

- `I don't need a wheelchair, I can walk`
- `朋友说我可能需要轮椅，但我不这么认为`
- `我以前不用轮椅，但现在必须无障碍`

EAC non-main patch still false-positives the first two in independent review.

Provider evidence:

- only `toilets:wheelchair=yes`
  MUST NOT satisfy `STEP_FREE_REQUIRED`.

- only `ramp=yes`
  MUST NOT verify step-free.

- only `elevator=yes`
  MUST NOT verify route access.

- `wheelchair=yes` + `step_count=5`
  MUST be conflict.

- list-style tags like `["wheelchair=yes", "ramp=yes"]`
  must not be silently discarded.

- route-level step-free remains unknown unless real route evidence exists.

EAC extraction endpoint:
candidate-only is good, but deterministic local fallback is not sufficient for
semantic authority.
