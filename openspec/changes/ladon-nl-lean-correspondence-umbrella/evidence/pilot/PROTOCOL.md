# Frozen comparison protocol

This is one constructed-case pilot, separate from development examples and the
historical target-paper audit. It cannot establish general detection performance.
Cases must be independently curated and use actual pinned Lean sources. The
population is eight short passages: four faulty argument passages, two faithful
controls, one valid alternative-method control, one genuinely ambiguous control.
At least two include surrounding nonfaulty reasoning; no auditor is told which
inference to select. Do not use development fixtures, target-paper passages,
prior experiment cases, or previously exposed answers. Curator explanations and
reference outcomes are separate from public inputs.

Freeze all public bytes, private reference-key bytes, toolchain/preparation
identities, this protocol, source/arm order and configuration before primary
auditors start. Curators and developers never serve as scored auditors.

There are exactly 18 fresh Luna-medium pilot contexts: one independent curator,
one independent source/step reviewer, and sixteen case/arm auditors. Each primary
case/arm uses a fresh context. The reviewer receives original sources and any
sanitized original obligations, never the key or prior verdicts. The same
reviewer comments and allocated reviewer cost are available to both arms, only
after each immutable first response is saved. Review is independent of the
primary response and cannot share one arm's answer with another.

All primary inputs are identical across arms. Each gets an exclusive writable
copy and the same installed pinned Lean, standard-library cache, and root-
compiled target artifacts. Current Ladon may be used only in the assisted arm,
from /home/codex/projects/ladon/src with PYTHONPATH explicitly set and existing
/home/codex/projects/ladon/.venv/bin/python. Ordinary-tool auditors use local
Lean and source tools without Ladon. No online searches, model APIs, new packages,
Lake cache downloads, or target-paper sources are available in this pilot.
Shared-filesystem separation is procedural, not an enforced security boundary.
Auditors may read only their assigned public inputs, their own outputs, this
protocol, and the independent reviewer comments supplied after first response.
They must not read private keys, peer/other-arm reports, or historical reports.
Board communication contains paths/compact identities/lifecycle only, never
case answers before all first responses are frozen. Read only relevant assigned
threads during blind work.

Case/arm order is generated with Python random.Random(2026101101), after sorting
opaque case IDs. Randomize the 16 (case, arm) entries once. Dispatch up to three
at a time in that order, never filling slots beyond available capacity. Actual
start/end/deadlines and all dispatch delays are recorded. Do not replace cases,
retry first responses, or choose a new seed after seeing results.

The inclusive per-case/arm budget is 900 seconds. Reserve 300 seconds for
independent review, reporting and coordinator replay; freeze the first response
within 600 seconds of primary dispatch. The single source reviewer works on all eight cases before the primary audits.
Its observed dispatch-to-completion wall time is allocated equally over eight
cases and charged equally to both arms, deducted from each 900-second budget.
Common comments are withheld until each arm freezes its first response.
Each first-report deadline is the earlier of dispatch+600 seconds and
dispatch+900 seconds minus allocated reviewer time. Any optional correction
must finish by dispatch+900 seconds minus allocated reviewer time.
Coordinator dispatch delay and post-key adjudication are reported separately.
Curator/compilation/setup costs are reported separately and equally allocated
where appropriate. Freeze the first response before receiving reviewer comments;
record any revision separately without changing first-response bytes. Unavailable
tooling, timeout, omitted work, and abstention stay in denominators. No missing
response is synthesized as a completed audit. Do not exceed the inclusive
budget to improve a score.

Save report.json plus actual command receipts and exact input/checker identities.
Required first-response fields: caseId, arm, verdict, selectedSpans, explanation,
claimFalse, interpretations, evidence, commands, omissions. Verdict is one of
argument-fault, faithful, method-difference, ambiguous, unresolved. Spans identify
path/startLine/endLine/quote. claimFalse is true, false, or null and concerns the
claimed endpoint separately from argument validity. Interpretations record the
original meaning(s), dependencies and any qualifications. Evidence identifies
actual outputs/terms or explicitly attributed mathematical reasoning; a failed
tactic alone is neither refutation nor support. Commands have exact argv,
exitCode, elapsedSeconds, retained stdout/stderr or output paths. A Lean build
alone does not establish correspondence with prose.

After all first responses are frozen, reveal the key to root and the independent
reviewer for adjudication. Preserve first verdicts, corrections and disputed key
references separately. Root replays claimed original goals/refutations; checked
terms must address the original premise/conclusion, not an easier repaired claim.
Post-key validation and adjudication costs are reported separately and cannot
retroactively improve the frozen budget-limited arm result or turn an unexecuted
proof into a claimed first-response kernel check. Any interpretation error or
unsupported transfer remains visible. A mismatch
with the key is adjudicated on sources/evidence, never forced into the key label.

Normalize exactly 16 paired first-response rows and, separately, corrections.
Score justified exact inference localization, source selection, valid evidence,
false alarms, abstentions, interpretation errors, formal gaps versus refutations,
correct controls, and false-endpoint claims. Aggregate counts mechanically from
rows and verify totals. Report wall time, commands and observed tool cost; token
usage is unavailable unless the platform exposes it, never invented. Compare
justified detection with false alarms, then cost conditional on equivalent
findings. If both arms tie or assistance underperforms, report unmet detection
benefit. A cost benefit requires comparable findings and lower actual allocated
cost, not worker confidence. Stop after this one pilot; no full-paper rerun.
