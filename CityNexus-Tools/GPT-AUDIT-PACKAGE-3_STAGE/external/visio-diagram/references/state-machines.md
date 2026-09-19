# State machines

Use this reference for finite-state machines, mode diagrams, and lifecycle states.

## Semantics

- Use one consistent state shape family.
- Keep state names short; put entry/exit actions on separate lines only when necessary.
- Use a distinct initial marker and final marker when the notation requires them.
- Put transition conditions and actions next to, not on, transition lines.

## Layout

- Arrange the dominant lifecycle in one direction.
- Put exceptional or recovery states outside the main axis.
- Use orthogonal transitions for dense diagrams.
- Give self-loops two different ports, such as right-to-top, and enough external clearance.
- Avoid two transitions sharing the same label location.

## Quality checks

- every transition has a source and target;
- self-loops have visible area and do not collapse to zero length;
- transition labels clear all state frames and routes;
- parallel transitions remain distinguishable;
- state-size and center-axis consistency meet the general layout gate.
