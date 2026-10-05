# Candidate readiness and evaluation

Maintainers promote a capability only from recorded candidate executions. The
ladder is experimental, contract-supported, externally-evaluated and
release-qualified. Implementation, parser help and fabricated digest labels
cannot promote a capability.

The current admission implementation qualifies contract evidence. Its
`externalOutcome` and `ownerDecision` validators remain unavailable and fail
closed, so it cannot currently issue externally-evaluated or release-qualified
levels. Recorded external studies remain separate observations. See the
[measured alpha profile](MEASURED_ALPHA_PROFILE.md) for the current decision.

The conservative committed feature matrix lists product roles and semantic test
requirements. Without execution evidence it reports experimental. Generate a
candidate-specific matrix with an explicitly selected evidence registry:

```bash
uv run --locked python scripts/generate_supported_feature_matrix.py \
  --evidence-registry /path/to/registry.json \
  --json-output /path/to/candidate-matrix.json \
  --markdown-output /path/to/candidate-matrix.md
```

A registry selects an independent acceptance inventory, a content-addressed
bundle root and feature evidence records. Contract admission verifies receipt
bytes, source/wheel/install scope, exact commands, successful named tests on
both supported runtimes, logs and execution timestamps. Missing objects,
unexecuted tests, help-only coverage, changed candidate identity or stale
execution demote the capability. Refreshing a timestamp cannot refresh old
execution evidence. Local integrity does not authenticate a producer.

`--verify-tests` executes the listed source tests; it does not itself issue an
installed qualification receipt. Optional evidence registries and external
repositories do not control required portable CI. Candidate-specific discovery
and integration exits are recorded in the result umbrella; a newer working tree
needs its own qualification.

The prerequisite umbrella's `evaluation/active-corpus.json` selects an immutable
registered corpus. It freezes source snapshots, revisions, toolchains, goals,
ordered locals, scope, labels, exclusions, ranking inputs and resource bounds
before measurement. Portable synthetic fixtures and the previously exercised
matrix-factorization project are excluded from external promotion. Changing
ranking code invalidates the study. Unavailable or drifting external checkouts
remain explicit observations and never become wins against a baseline.

Adapters retain generation and independent Lean closure replay separately for
Ladon, `exact?`, `apply?`, `#check` and `rg`. Editor search is unavailable without
an automatable protocol. Native tactics search their own environment; `#check`
uses a registered candidate pool and `rg` searches selected source text. These
population differences prevent a pooled leaderboard. A tactic command can
emit an admitted goal; independent suggestion replay must check the generated
proof and report `sorryAx` rather than inferring proof from exit zero.

Recall measures recovery of registered candidate labels. Incomplete labels do
not determine correctness of other suggestions. Incorrect suggestions require
independent verification; explicitly rejected shortlist rows are reported
separately. Closed proofs, partial applications and unassessed outcomes remain
distinct. Latency, scratch replay, runtime, sampled RSS and UTF-8 output volume
are separate measurements. No scalar combines them into proof or LLM quality.

Architecture-finding precision and actionability require independent maintainer
labels. The implementing agent and automated feedback cannot supply those
labels. The registered cold architecture runs currently have timeout outcomes,
so those metrics remain unassessed. Public publication still requires an
owner-granted license; technical readiness supplies no such authority.
