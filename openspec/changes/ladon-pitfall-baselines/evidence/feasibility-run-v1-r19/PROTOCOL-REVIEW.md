# Protocol review: feasibility r19

Independent review recomputed the acceptance-index identities, four case-record
hashes, 164 referenced raw-result hashes and eight generated source identities.
Runner, lock, policy, corpus and runtime identities agree. Capture source
digests match the attempted sources; CLI arguments retain capture/completion
requests; all cases retain selected-import, excluded-import, unrelated-failure
and exposed-module receipts.

The new [capture-binding countercheck](../protocol-checks/capture-binding-countercheck-v1.json)
passes under the locked runner. It accepts a valid expected-source binding,
keeps a genuinely unavailable capture unresolved, and rejects a wrong digest,
missing capture/source objects and a nonzero exit paired with `captured` status.
The raw r19 batch also completes all four cases under that runner.

This review qualifies protocol evidence; the separate blind review adjudicates
proof outcomes. Durable peer-reviewed audit is in
`.codex/state/pitfall-baselines/board.sqlite3` (posts 23, 24 and 27).
