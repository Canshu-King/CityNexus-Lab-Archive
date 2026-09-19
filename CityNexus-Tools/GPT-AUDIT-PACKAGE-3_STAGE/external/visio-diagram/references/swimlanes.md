# Swimlane diagrams

Use this reference for cross-functional processes and role/stage ownership.

## Structure

- Choose one lane axis and keep it consistent.
- Make lane headers a separate aligned band.
- Keep lane widths or heights consistent unless ownership density requires an explicit exception.
- Treat lanes as background containers; process nodes and connectors remain foreground content.
- Keep process boxes centered inside their lane and use one role-based size family.

## Flow

- Prefer a single reading direction across lanes.
- Use orthogonal connectors and shared branch rails.
- Cross a lane boundary only when responsibility actually changes.
- Place decision labels next to the outgoing branch, never on the connector.
- Avoid connector paths that run along header text or lane borders.

## Quality checks

- lane boundary alignment;
- node containment within the intended lane;
- equal lane spacing;
- branch symmetry;
- connector-to-border and text-to-border clearance;
- no label, connector, or node overlap.

For a dark-background reference, preserve contrast semantics rather than copying colors blindly. Keep semantic colors sparse and consistent.
