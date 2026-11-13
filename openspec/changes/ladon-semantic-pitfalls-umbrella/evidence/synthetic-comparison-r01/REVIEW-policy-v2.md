# Policy v2 review

Reviewed `REGISTRATION.md`, `HANDOFF.md`, `ARM-PROMPT.md`, and
`POLICY-REVISION.json` only. Case materials, answers, and custody records were
not read. No execution or tests were performed.

## Result: accepted

The revised counting rule is coherent across the packet. It caps auditor-issued
top-level Lean, Lake, and Ladon invocations at 20, counts failed attempts,
probes, retries, and each invocation inside a script or batch, prohibits
parallel invocations, and specifies a numbered log checked against available
transcripts. Scripts containing one tool invocation count once. The policy
also names the consequences of a verified overrun and of unknown accounting.

The arms have the same 20-command allowance, 20-minute deadline, per-command
600-second/remaining-deadline limit, 12 GiB process-tree RSS cap, and 16 MiB
captured-output cap. The same supervisor and deadline rule apply to every
checking command. Assisted-only Ladon setup/indexing consumes the assisted
arm's command allowance; shared package setup is excluded only when completed
for both arms before their clocks start. This is explicit and preserves the
registered comparison rather than leaving setup counting implicit.

Underlying Lean starts are consistently descriptive telemetry in the
registration, handoff, prompt, and revision record. Their unavailability limits
cost comparison only; it is not a launch blocker or a mathematical failure.
The old lifetime child-process ceiling is removed throughout the operative
policy. No obsolete gate or lifetime-process stop condition remains.

No blocking issue found. Policy v2 is ready for its stated preparation and
future launch preconditions; this review does not certify that those
preconditions have been fulfilled.
