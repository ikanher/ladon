# Universe-preservation follow-up review

**Assignment:** board #1600, continuation of the read-only audit.
**Conclusion:** source inspection supports independent universe preservation and exact closed-target replay. No defect found in the reviewed path. This is a source review plus inspection of root-owned artifacts; I did not run Lean or tests.

## Findings

- `originalLevelNames` in `src/ladon/lean/ladon_source_goal_completion_helper.lean:125-131` collects level parameters from the target and every original local declaration type and value. The submitted term is elaborated against the observed target with those names at lines 301-307. Collecting the levels in addition to target levels permits source-visible universe names during elaboration; it does not add term hypotheses.
- `emptyContextRoundtrip` at lines 135-163 clears the local context, namespace, and open declarations; it prints target/proof explicitly and reparses each using level names collected from the exact closed target and proof. It checks target definitional equality and proof definitional equality after reparsing.
- The completion path closes the support locals, rejects remaining free variables/metavariables, and checks `inferType closedProof` definitionally equals `closedTarget` (`closeChecked`, lines 85-120). The generated replay is therefore tied to that closed target rather than an independently reconstructed weaker goal.
- `tests/test_source_goal_completion_universes.py` uses independent `u` and `v`, asserts both survive in generated source, asserts the original goal matches capture, no residual goals, empty observed axioms, and unchanged source. `tests/test_source_goal_completion_universe_terms.py` additionally submits a term explicitly naming `u` and `v` and requires completed replay. These are focused positive regressions; they do not exercise all malformed or unsupported universe cases.
- Root-owned matrix artifacts inspected: `public-matrix/progress.json` records dependent-positive checked-binding and unresolved outcomes for wrong measure, sorry, unused-False-no-rescue, forged expression, and same-name changed definition. `public-matrix-followup/RESULTS.json` records unused-False-positive checked-binding, changed-instance unresolved, and retained-proof-parameter unresolved. The original mistaken harness selection is accurately preserved in board #1599 and is not counted as a pass. I did not independently reproduce these checks.

## Limits and evidence

Read-only commands were `rg`, `sed`, `nl`, `cat`, `find`, and `sha256sum` on the named helper/tests/artifacts. No tests, Lean commands, builds, or production edits were performed. The baseline recorded for the frontier is HEAD `e6479e465d652029502bc19b6a03e90b359bf5b5`; it covers other pre-frontier source files and does not establish pristine hashes for this dirty completion helper. Current SHA-256 values observed: helper `b09be4d2a5290fd029ea83557d1929c955a33e74f1a7a63df7404d2c7c943cb6`, universe test `99ccde62098c3c8d4d275f32f7caa946246112f867023dd4564007d768c43187`, term-universe test `b840ed7357e965e716337a5e5e3da83a073b0dce13ae55018446849112cc6de0`. No dependency changes observed.

Remaining gate: root-owned bounded matrix/integration evidence. This review does not independently validate the runtime checker, claim mathematical admission, or change the unresolved admission/contract status.
