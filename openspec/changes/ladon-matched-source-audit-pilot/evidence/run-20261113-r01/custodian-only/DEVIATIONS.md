# Custodian event log

Append events in time order. This file is not part of either arm's input.

## 2026-11-12T22:51Z — Arm A output path error (reported during run)

Arm A reported that its first Ladon analysis command used an incorrect
relative output path. The command read only the assigned capsule, but the
output resolved to `arms/OUTPUT/evidence/ladon-bracket.json` rather than the
assigned `arms/A/OUTPUT/`. The agent is preserving the generated artifact in
its assigned evidence directory, recording its hash and the original path,
and removing only empty directories it created. No other arm or registration
content was reported inspected. Classify this as an output-boundary deviation;
retain it in the validity report and do not silently erase the history.
