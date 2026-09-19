# Engineering and control diagrams

Use this reference for control loops, signal-flow diagrams, functional block diagrams, drive-control diagrams, and similar engineering drawings.

## Composition

- Establish the principal signal axis first, normally left-to-right.
- Align the centers of series blocks, summing junctions, and arrowed signal lines on that axis.
- Try a common width and height across the principal axis; retain a larger dimension only when measured content or port density makes the common value invalid.
- For a consecutive same-role block chain, keep absolute frame-to-frame gaps equal; compare page-coordinate boundaries rather than copied percentages.
- Put feed-forward paths in a close upper band above their receiving sums and feedback paths in a close lower return band.
- Cluster a source, gain, summing point, controller, transform, and feedback element around their semantic loop instead of distributing them evenly across the whole page.
- Keep comparable controllers and processing blocks in consistent size families.
- Derive taller multi-port blocks from absolute port separation; the label `multiport` alone never justifies height.
- Use a small `junction` node for summing or branching points.

## Ports and lanes

- Single-input/single-output blocks normally use side-center position `0.5`.
- Multi-port blocks use explicit port positions and paired lanes with identical Y or X coordinates.
- For differently sized blocks, derive each normalized port position from the shared absolute page coordinate; do not copy the same percentage blindly.
- Preserve a stable lane order; do not let Visio reorder semantic signals.
- Shared buses and repeated lanes must remain parallel and evenly spaced.
- Feedback should be one semantic orthogonal connector whenever possible, not several unrelated static line fragments.
- Every signal source must be a visible semantic node or declared port. Do not use floating note text as an electrical or control input.

## Labels and formulas

- Put signal names outside line geometry with the clearance rules in `connectors-and-text.md`.
- Keep signal labels near the relative midpoint of their selected segment; widen the semantic gap or shorten the signal name instead of pushing the label far away.
- Use shape-bound top captions for horizontal loop names and left/right centered captions for tall module names.
- Put block names inside blocks; put explanatory prose in notes away from signal paths.
- Formula blocks should be centered and enlarged until the formula remains inside the 80% safety envelope, leaving about 10% nominal padding per side.
- Use `module/operator/math/signal/caption/note/dense` roles from the active style profile. On a large control page they resolve to the calibrated 18/16/14/12/10 pt hierarchy; smaller pages retain each role's readable floor.
- Use concise mathematical text when equation objects are unavailable, and report that fidelity limit.

## Suggested regression metrics

```text
main-axis center spread <= 0.02 in
paired-port delta <= 0.01 in
max endpoint error <= 0.03 in
fully glued ratio = 1.0
flow connectors orthogonal ratio = 1.0
label clearance >= 0.08 in
formula bounding box <= 80% of its block width and height
source/target endpoint intrusion count = 0
arrowhead node overlap count = 0
same-axis gap <= max(0.8 in, 1.5 * nodeGap)
same-size-class absolute gap span <= 0.03 in
compact page utilization >= 75% width and 65% height
connector label anchor error <= 0.03 in
caption anchor error <= 0.02 in
ordinary text-block ratio = 0.80 +/- 0.02
font-size error <= 0.25 pt
same font-role + size-class span <= 0.25 pt
frame/connector base line weight = 0.75 pt before bounded large-page scaling
```

Fit the page to the content with about 5% to 8% intentional outer margin. Compare total connector length and bend count before and after compaction; do not copy excessive blank space from a reference file.

## Research basis

The rules synthesize the supplied engineering examples with:

- [deermiya/visio-skill](https://github.com/deermiya/visio-skill/tree/main/)
- [Visio MCP architecture article](https://blog.csdn.net/qinzhenyan/article/details/155921280)
- [Microsoft featured Visio templates and diagrams](https://support.microsoft.com/zh-TW/Visio/featured-visio-templates-and-diagrams)
- [Visiomaster scene schema](https://github.com/Rss3208/Visiomaster/blob/main/references/scene-schema.md)
- [Visiomaster style profiles](https://github.com/Rss3208/Visiomaster/blob/main/templates/style_profiles.json)
- [Visiomaster review contract](https://github.com/Rss3208/Visiomaster/blob/main/references/review-contract.md)
