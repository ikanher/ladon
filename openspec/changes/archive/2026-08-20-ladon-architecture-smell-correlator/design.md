# Design

## Composite Findings

The first correlator emits only when multiple independent signals co-occur:

- broad root import closure plus high module fan-in;
- facade-heavy inventory plus high module fan-out;
- narrow chosen-root reachability inside a broad inventory;
- repeated declaration-name family under a broad root import closure.

Each finding includes a `component_signals` list so review tooling can display
why the composite was raised.

## Boundary

The findings say "architecture pressure" because these are review triage
signals. They do not claim the graph is wrong, unsound, or poorly designed.
