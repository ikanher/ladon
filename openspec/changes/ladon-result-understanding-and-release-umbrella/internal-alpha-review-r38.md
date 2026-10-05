# Internal technical-alpha review: qualified r37, acceptance still blocked

Review question: do the qualified r37 implementation and its documented limits
preserve the boundary between lexical discovery, Lean application checks,
independent scratch compilation, and stored/derived evidence?

The recommended decision remains **no-go for completing the prerequisite
umbrella or granting formal internal-alpha acceptance**. Local trusted-project
experiments may use the exact qualified portable contracts. Public distribution
is not authorized. Preparing this review material does not provide independent
labels, establish missing historical order, or approve a release.

## Candidate and evidence

- Candidate: `3f182566c19afe82f8029685fe77f20759582d4c`.
- Wheel: `sha256:961c10c46c43ccfd01ae993928a46b8f6b1bb6449c604f45fc12b047c003802b`.
- Each installed Python runtime passed 2,659 integration, 1,060 authority,
  147 correctness, and 137 network-disabled discovery cases. All eleven
  integration prerequisites passed.
- The first Python 3.11 integration attempt was interrupted; its log and the
  fresh successful retry remain distinct. The interruption cause is unknown.
- The actual Real-module notation regression accepted `Eq.refl epsilon` and
  compiled independent scratch on both installed runtimes. The reporting helper
  later expected a full receipt in compact review output; a separate summary
  resolves the successful captured command without altering it.
- Four features admit contract support. Three extras remain experimental.
  External-outcome and owner-decision admission fail closed.

The qualification record, receipts, readiness matrix and semantic comparison
are included as source evidence. They name exact commands, execution scope,
timestamps and external content-addressed references. Their local paths are
not portable execution instructions, and the packet does not include the full
external log/object stores, wheel or installed environments.

## Source inspection priorities

1. Inspect `semantic_local_context.py`, `_semantic_observation_contract.py`,
   and `semantic_observation_closure.py` with their regression tests. Known
   notation must match a closed structural constant. A scratch spelling
   comparison must resolve the parent check and bind its structural context.
   It must not rewrite stored bytes or confer authority on a weak failure.
2. Inspect the seven evidence dimensions and receipt projection owner. Live,
   stored and derived results must retain or weaken evidence; source/index
   freshness and environment matching remain independent from proof checking.
3. Inspect readiness admission and candidate acceptance. Named semantic nodes
   must have passed on both supported installed runtimes. Help-only, stale,
   missing, mixed-candidate or fabricated evidence cannot promote a capability.
4. Review the external observations as operational outcomes. The matrix
   environment exceeds the 10,000-import evidence cap; standalone held-out
   dependencies/toolchains are incomplete. Neither issue establishes an
   incorrect mathematical suggestion or a baseline win.

## Remaining requirements

Task 6.8 has no independent architecture labels. The original 60-second cold
runs timed out. A separately preregistered 300-second diagnostic at r37 returned
a schema-valid mathlib report in about 96 seconds, with about 0.75 GiB sampled
RSS. Its only finding is the excluded no-policy diagnostic. The matrix analysis
reached serialization in about 155 seconds but exceeded the 2 MiB report cap,
with about 0.88 GiB sampled RSS. There are no eligible findings to label; both
precision and actionability remain unassessed. The longer diagnostic does not
replace or promote the original study.

Task 7.1 is only partially verified. Four current child exits match the normative
ledger, inventories and r37 scope. The readiness child has no completed exit.
Current receipts cannot prove the historical start order of the child changes.
An earlier prototype exists at the original workspace commit, but its presence
alone does not identify the formal start event of a later child. No chronology
or exception approval is invented.

The packet completes preparation for internal review, not the review itself.
The earlier r37 decision and progress records retain their historical packet
pending state. This r38 preparation supersedes that packaging interpretation
while preserving the same no-go decision and unresolved acceptance requirements.

## Replay boundary

This is a source excerpt and evidence summary, not a self-contained replay
bundle. Full replay requires the complete Ladon candidate, locked dependencies,
supported Python environments, the pinned Lean fixture and the referenced
evidence objects. Optional diagnostics additionally require the named local
project snapshots and toolchains. The current profile and this review entry
were written after the r37 freeze; they are interpretations of its evidence,
not claimed contents of its wheel.

Recorded executions do not authenticate the producer, establish human
understanding, sandbox imported initializers, prove universal mathematical
benefit, or grant publication rights. The packet stays local; it is not sent
to a reviewer or published by this workflow.
