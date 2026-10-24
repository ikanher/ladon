# Bounded propagation acceptance

The acyclic contract evaluator and its native `propagate`/`inspect` workflow are
implemented and independently reviewed. [Validation](VALIDATION.json) binds the
accepted files, bounds, schema, checks and limitations. [Integration evidence](integration.xml)
records 615 passing contract, native graph and scoped-context tests with no skips
or failures in 77.854 seconds. Ruff passes for source, tests and scripts; strict
Python quality reports zero issues.

Ordered premise occurrences are conjunctive. Alternatives retain correlated
loss/dependency contracts, context and substitutions, with shared immutable
witness references. Certified profile dominance can prune a whole contract;
it cannot assemble a better contract from unrelated coordinates. The
three-versus-five trade-off, incompatible contexts, changed evidence, missing
conjuncts and repeated premises have explicit controls. Existing structural solver
semantics remain separate and their regressions pass.

The [finite oracle comparisons](ORACLE-COMPARISONS.json) check 64 seeded DAGs with eight statements and at most three
alternatives per derived statement. It enumerates complete tuple products without
using the production comparator, then compares exact nondominated loss/dependency
sets. This suite finishes within the 30-minute gate. The broader suite recompiles
the actual conditional [Lean rules](LEAN-RULES.json), including estimate composition,
maximum and constant sum; it does not certify source applications. Pure propagation
tests have no dependency on Quux, Lean or a model service.

[Independent reviews](INDEPENDENT-REVIEWS.json) established and then retested
resource and authority defects. Root integrated failing regressions before fixing
oversized expired goals, loss of an earlier partial frontier, post-hoc output
truncation, aggregate encoded input, CLI aggregate parsing, and removable deadline
limitations. The final independent review (post 226) verified both latest fixes
and 30 focused checks. Frozen tests remained intact.

All graph, step, depth, frontier, combination, input, output and shared-deadline
limits retain bounded partial results and named pending work. Cycles expose SCC
residuals. CLI propagation reads at most 8 MiB aggregate raw input before parsing;
native inspection shares a 32 MiB raw cap. Normalized SQLite schema 11 retains exact
derivation-goal ownership and an indexed lookup; rollback, rebuild and stale-schema
controls pass. [The documented example](../../../../docs/PROOF_CONTRACTS.md)
executes through the public CLI and replays against its exact inputs.

Acceptance is conditional on the supplied graph, profile and attributed contract
bindings. Deadline observations are replayable but unauthenticated. Source binding
is unchecked; mathematical falsity remains `not-established`. Frontier growth can
be exponential and truncated searches do not prove absence of a route. This child
does not complete the parent's independently sourced pair gate, the backward
workflow, or the detection-benefit evaluation.
