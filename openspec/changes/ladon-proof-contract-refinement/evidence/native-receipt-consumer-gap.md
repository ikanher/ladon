# Native rational-branch receipt consumer gap

Status: Task 2.2 is accepted for the bounded set of consumers that actually depend on the rational branch type: finite-assignment generated propositions and their dependent finding/report/final-receipt projections. The checked result is consistency-validated local evidence, not authenticated provenance or proof of source fidelity. Generic typed bridges and paired probes remain outside the claim because they do not accept this branch type.

## Original gap, now addressed for the bounded route

The initial implementation of `check_rational_branch_probe` in `src/ladon/proof_contract_rational_probes.py` regenerated its plan, replayed each generated Lean goal and returned per-goal `proofir.check-run` artifacts plus a rational receipt. The plan was a `proofir.contract-analysis` artifact at stage `rational-branch`.

At that point, the plan artifact deliberately had empty `checkRunRefs`; it represented planning only. The returned check-runs were not linked by a second owning analysis artifact. Their branch and goal binding appeared in `extensions["ladon.rational-branch-receipt/v1"]`. Core ProofIR validation checks extension names but does not assign semantic authority to extension contents. This left no native owner proving that the accepted check-runs belonged to the regenerated branch goals.

Investigation attachment validation at that point accepted a native artifact batch and one contract-analysis artifact, while `contract_dimensions` kept `routeSupport` at `not-established`. The implementation slice below added the closed native checked-result artifact connecting Lean receipts to the exact rational plan.

## First implementation slice

The rational check route now returns a sibling `proofir.contract-analysis` artifact at stage `rational-branch-check`. It references the exact rational plan and each per-goal check-run. Native batch validation resolves those references and compares the receipt fields, branch identity, generated goal text and digest, checker identity, term digest, and compiled-module inventory against the referenced plan and run extensions. It also requires complete trust coverage under `lean-standard-no-placeholders-v1` and validates observed axioms against the declared standard set. The plan retains the full immutable branch record; native validation recomputes its branch digest, checks the original finding identity, reconstructs the derived goal from the base goal and exact constraints, and recomputes source-span identities from cited constraints. The checked-result receipt carries that finding ID, and investigation attachments must match it to the observation ID. This prevents attaching one branch's checked result to another observation. The prior plan-only artifact remains unchanged.

Investigation findings, reports, and final progress receipts now carry the checked artifact and its reference closure. Their existing dimensions still report route support and mathematical falsity as `not-established`; source formula fidelity remains a separate attributed review. The checked artifact describes only finite-assignment generated goals and cannot establish fidelity to cited prose, universal validity, or refutation of the original theorem.

Focused verification: the rational receipt suite plus native artifact/trust mutation and finding/report projection checks and investigation attachment regressions passed: 57 passed, one slow integration skipped. The added frozen stale-identity regression changes a branch rule or base-goal conclusion while preserving display identities, regenerates a new plan ID, and rejects the old positive plan/cache evidence before replay; the combined focused command passed 59 tests, one slow integration skipped. Ruff, `git diff --check`, and OpenSpec validation passed. Independent review #1136 accepted the owning checked-result slice; post-integration audit #1150 confirmed the stale-identity behavior, and follow-up review #1152 accepted the clarified bounded Task 2.2 scope. The test counts above are root-run.

## Scope boundary and remaining work outside Task 2.2

Mutation coverage now includes branch identity and branch-record linkage, cited source-span identities, base/derived goals, assignment, checker, workspace, compiled inventory, and complete check-run coverage. The focused tests rebind the outer ProofIR artifact hash before asserting rejection.

The investigation attachment accepts the checked result only when its original finding ID matches the observation. It projects the artifact as attached evidence while retaining `routeSupport` and original-theorem refutation as unestablished. A future slice may expose finite-assignment route support only after source fidelity and branch-to-claim semantics are separately checked.

This is one bounded consumer route. It does not make ordinary propagation, context bridges, or paired application probes branch-aware; each requires a semantic adapter before it can claim branch invalidation. Those routes are excluded from Task 2.2 because they do not consume refinement-branch inputs today.

## Independent inspection

The first two read-only audits identified the missing checked-result owner and opaque extension binding. The follow-up audit accepted this integrated finite-assignment slice after checking branch-to-goal closure, trust receipt consistency, and finding/report/final-receipt attachment. It explicitly does not authenticate the unkeyed artifact/process provenance or establish source formula fidelity. Generic bridges and paired probes remain outside the reviewed scope.
