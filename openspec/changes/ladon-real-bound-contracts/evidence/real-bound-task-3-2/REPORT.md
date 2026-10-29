# Task 3.2 partial implementation report

Date: 2026-10-25; persistence update: 2026-10-26

## Implemented source-derived relation slice

- `compare_real_bounds` in `src/ladon/real_bound_native_analysis.py` freshly
  replays both saved productions through the current source-bound Lean admission
  path and compares complete normalized typed contexts. Context equality is
  only a precondition. For plans whose declarations come from the same exact
  source module, a separate worker rechecks both observed Expr ASTs, constructs
  an `Iff` between the live input predicates, and checks that goal in a bounded
  Lean process. The current proof term is `by intros; rfl`, so only definitional
  equivalence can resolve; mismatches and failed checks remain unresolved.
- `propagate_real_bound_identity` freshly replays an ordered bounded sequence
  and separately checks every adjacent identity-v1 predicate `Iff`. Each
  resolved edge carries its own supervised run and goal digest; propagation is
  complete only if all edges check. Failed edges remain unresolved while prior
  checked edges stay individually represented. There is no graph-label input
  or Nat rule dispatch.
- The relation worker revalidates both exact source plans and helper/checker
  identities, rejects reserved helper collisions, and retains the process
  supervisor's 12 GiB RSS, 8 MiB I/O, and outer deadline limits. Public
  operations keep one shared deadline capped at 600 seconds and 32 MiB aggregate
  JSON input.
- `compare-real-bounds` and `propagate-real-bound-identity` remain separate Real
  CLI routes with exit 0 only for resolved operations and exit 2 otherwise.
  The result is ordinary JSON, not a persisted `proofir.contract-analysis`
  artifact.

An initial draft treated identical typed context fingerprints as equivalence.
The independent audit (board post 1683) correctly rejected that promotion
because no Lean relation proposition was checked. Context identity remains a
precondition, and singleton propagation inputs remain rejected. This revision
adds source-derived and freshly checked predicate relations, restricted to
definitional equivalence.

All results retain `sourceTheoremProof: not-checked`,
`paperNormBridge: unresolved`, and `mathematicalFalsity: not-established`.
The relation check establishes only the input-predicate `Iff`; it does not
certify the source theorem bodies or a paper-norm bridge. Native analysis
artifact ownership and persistence are still absent.

## Verification

- `ruff check` over the relation worker, analysis, checker, and focused tests —
  passed.
- `LADON_MATHLIB_TEST_ROOT=../lean/matrix-factorization PYTHONPATH=src:tests
  pytest -q tests/test_real_bound_native_analysis.py
  tests/test_real_bound_native_analysis_cli.py
  tests/test_real_bound_relation_macro.py
  tests/test_real_bound_native_consumers.py
  tests/test_real_bound_native_records.py` — 37 passed, 1 skipped in 83.54
  seconds. The skipped case is the separately run opt-in live gate below.
- `LADON_MATHLIB_TEST_ROOT=../lean/matrix-factorization
  LADON_REAL_BOUND_LIVE_ANALYSIS=1 PYTHONPATH=src:tests pytest -q
  tests/test_real_bound_relation_macro.py::test_live_public_comparison_replays_both_native_productions`
  — 1 passed in 635.59 seconds. It separately admits
  `ScalarExamples.ordinary` and `ScalarExamples.ordinaryCopy`, obtains distinct
  contract owners, and invokes public comparison and identity propagation on
  both saved productions. Both resolve their definitional relation; the one
  propagation edge is individually checked and complete. This measures the
  full sequential path's elapsed wall time, not peak RSS. An earlier version
  of this gate passed the same saved production twice in 544.89 seconds; the
  distinct-owner run supersedes that weaker result.
- `openspec validate ladon-real-bound-contracts --strict` — valid.
- Bulletin-board frozen-test verification matches the three current task tests.
  Repository-wide verification still reports an unrelated mismatch in
  `tests/test_rational_lean_encoder_v2.py`; no pre-task baseline was established
  for that file.
- Live relation-worker integration built current Lean 4.33 plans in the
  compiled Mathlib environment. Same-source definitional equivalence checked;
  a false relation remained unresolved; stale source was rejected. The test
  uses a clean selected root to ensure no precompiled Ladon helper shadows the
  worker's private build.
- Analysis operation unit tests mock replay and relation-worker boundaries;
  the opt-in integration gate now also exercises compare/propagate end-to-end
  using two freshly admitted native production wrappers with distinct owners.
- The first integrated audit (#1683) caught and corrected fingerprint-based
  false promotion and singleton vacuity. The second audit (#1686) found no
  remaining false promotion in that earlier diagnostic slice. The fresh
  read-only audit of this relation-check revision (#1695) found no actionable
  false-promotion or ownership defect. It independently reviewed source/AST
  freshness, checker identity, process receipts, edge checks and dispatch. It
  predates the distinct-owner integration gate above; that run adds direct
  end-to-end evidence but does not broaden the proof rule beyond definitional
  equivalence.

## Native comparison persistence (2026-10-26)

The frozen dispatch red is now green. The exact Real profile selects a closed
`proofir.contract-analysis` comparison payload. Nat and unknown-profile dispatch
remain unchanged. No SQLite schema migration was needed.

`compare-real-bounds-proofir` freshly replays both admitted inputs and the exact
relation, then emits a bundle containing the source maps, admission checks,
contracts, separate relation check-run and comparison analysis. The analysis
retains the exact plans, terms, source text and historical receipts needed for
replay. Process timing floats are encoded losslessly using finite hex-float tags
inside the integer-only native profile. Ordered input owners, typed goal,
canonical source-derived proposition and evidence owners are reconstructed;
rehashed labels cannot replace them.

`inspect-real-comparison` and ordinary contract inspection report historical-only
results. A producer's saved freshness claim is not authority. An optional root
checks identities without running Lean. `replay-real-comparison` verifies the
saved bundle and current identities before running both admissions and the
relation under one shared deadline. It compares semantic owner identity while
allowing new process timing receipts. A failed or limited fresh result stays
unresolved and does not acquire saved success or native comparison artifacts.

The result remains restricted to same-source definitional predicate equivalence.
It does not certify source theorem bodies, a paper-norm bridge, or general
transfer rules. Native propagation persistence is not included.

### Verification

- Initial core red: 25 failed, 1 passed (missing implementation/dispatch).
- Core historical ownership, tampering, SQLite, replay and resource controls:
  26 passed in 117.27 seconds.
- CLI red: four missing-route failures. After implementation: six passed in
  19.02 seconds including existing comparison/propagation routes.
- Codec red caught a hexadecimal overflow escaping as `OverflowError`; after
  the fix all eight lossless/canonical/malformed transport tests pass.
- Independent re-audit found outer receipt input/bounds consistency was missing.
  Eight new controls failed before the fix. Outer input digest and requested
  bounds now match the supervised run; bounds must satisfy the recorded policy.
  Native timeout is rounded up from the actual effective budget, and RSS remains
  in replay evidence. All 16 receipt/codec tests pass in 8.90 seconds.
- Combined Real persistence, CLI, historical inspection and existing native
  consumer tests: **88 passed in 161.23 seconds**.
- Existing Nat/native SQLite and CLI compatibility tests: **39 passed in 0.76
  seconds**.
- Existing admission CLI, native audit and ProofIR CLI checks: **11 passed in
  0.31 seconds**.
- Ordinary `proofir validate`, `proofir inspect`, and `contract inspect` with
  exact native dependency context accept the live-produced comparison artifact;
  inspection preserves `authority:none`.
- New persistence modules pass strict complexity/dead-code checks and Ruff.
  This is a scoped quality result, not a repository-wide clean-quality claim.
- Frozen tests and fixture for this slice match their recorded identities. The
  pre-existing unrelated `tests/test_rational_lean_encoder_v2.py` mismatch remains;
  this work did not edit that file. Both updated Ladon skills validate.
- Final independent source review (#1724) found no further concrete defects
  after the receipt correction. It did not run Lean or authenticate saved
  receipts. Root owns the test and live-check evidence.
- Live public CLI qualification passed on the final implementation: **1 passed
  in 698.83 seconds**. Two distinct declarations were admitted in 199.11 seconds;
  fresh native comparison took 243.65 seconds; inspection and explicit fresh
  replay took 255.91 seconds. All eight sequential admission/relation workers
  succeeded. The maximum measured worker process-tree RSS was **4.94 GiB**,
  below the fixed 12 GiB limit. This is not a whole-machine memory measurement.
  The saved bundle contains 10 artifacts and is 5,991,358 bytes. Replay created
  new receipt/artifact identities while preserving the exact semantic owners.
  See [qualification receipt](persistence-qualification.json) for per-worker
  limits, peaks, timings, input/output digests and the tested source manifest.
  No production-source changes were made while qualification was running.

## Individually checked input-prefix rule (2026-10-26)

`check-real-bound-prefix --stronger ... --weaker ... --root ...` now has a
separate source-derived implication route. It replays both owners, preserves
all context except literal input loss and the terminal premise being related,
and re-elaborates the actual admission proof in the relation worker. The Lean
helper extracts OrderPrefix and checks the order inequality. Removing the
original input witness and rejecting retained proof-valued dependencies prevent
accidental conditional proof reuse. This proves only a higher-to-lower
input-predicate implication, not a source theorem or paper-norm bridge.

The ordinary-JSON result is separate from native Iff comparison history.
Native directional-rule persistence remains open. No cache, dependency,
case-name registry or fixed mathematical offset was added.

- Initial API/CLI red: six missing-module failures, subsequently six passed.
- Candidate-context and resource-bound controls: **20 passed in 1.95 seconds**.
- First kernel gate: two intended positive cases failed because the generated
  primitive Nat inequality lacked the expected decidability instance; three
  rejection controls passed. Constructing the standard `LE.le` proposition
  fixed the proof construction without changing expectations.
- Final generic kernel gate: **5 passed in 15.45 seconds**, covering a Real-valued
  object family (losses 4 to 0), an independently named function-valued family
  with an ambient Real parameter (7 to 2), reversed implication, bad admission,
  wrong observed order and stale source expression. Negative controls may make
  multiple assertions within one test.
- Independent integrated source audit #1736 found no actionable false-promotion
  or ownership defect. It did not run tests or Lean; root owns those results.
- New Python modules pass strict complexity/dead-code checks and Ruff.
- First public live run: **failed after 359.36 seconds**, conservatively unresolved.
  Lean had accepted the proof, but `mkArrow` generated a module-dependent hygienic
  binder name, so capture and independently elaborated typed-goal structures
  differed. Evidence equality remained strict. A separate cross-module expression
  regression reproduced the difference before the fix.
- The generated implication now uses a deterministic `prefixInput` binder name.
  All **6 kernel/goal-identity tests passed in 24.96 seconds**. A narrow real
  supervisor retry then passed exact evidence acceptance in **46.73 seconds**.
- Final focused audit #1740 found no naming/capture defect after that change.
  The fixture import/export lint correction preserves every test function AST
  and assertion; the board retains its prior frozen revision (#1737).
- Existing native comparison persistence, inspection, Nat/SQLite and CLI paths:
  **85 passed in 160.20 seconds**. This is compatibility evidence; it does not
  reclassify stored receipts as fresh.
- Final focused boundary/CLI run: **24 passed in 2.05 seconds**. Ruff, scoped
  strict complexity/dead-code checks, OpenSpec validation and both skills pass.
  An offline local wheel build includes the new Python modules and Lean helper.
- Final two-family public CLI and existing live equivalence-consumer gate:
  **5 passed, 1 skipped in 1099.41 seconds**. The skipped case is the separate
  opt-in, expensive old comparison/propagation API gate; the four existing live
  equivalence helper/worker controls ran and passed. The new public prefix gate
  itself took **1021.22 seconds** and established 4 admitted generic owners and
  **2/2 checked prefix pairs**. Both reversed CLI requests stayed unresolved;
  ten altered-evidence controls and the stale-source control rejected.
- The whole test process tree peaked at **5,386,752,000 bytes (5.02 GiB)**;
  no memory or timeout limit was hit. The enclosing test budget was 3600 seconds
  and 12 GiB. Each public rule operation retained its own shared 600-second
  maximum and 12 GiB cap. This baseline includes repeated admission replay and
  the existing equivalence tests; it is not the cost of a single rule proof.
  See [prefix qualification receipt](prefix-qualification.json) for source
  identities, goal/owner references, per-case receipts and whole-run accounting.
- No implementation files changed during final qualification. Original Iff
  schemas and stored meanings remain unchanged; old runtime identity still
  requires fresh admission. These are authored generic capability tests, not an
  unfamiliar-source discovery result or a new paper audit.

## Native directional-prefix persistence (2026-10-26)

The prefix rule now has a separate closed native bundle and explicit
`check-real-bound-prefix-proofir`, `inspect-real-prefix` and `replay-real-prefix`
commands. The payload uses `analysisKind:real-bound-prefix-v1` within the existing
comparison storage stage. Exact stronger/weaker owners, source/admission inputs,
deterministic directional proof request and a separate check-run are retained.
It never reinterprets the old equivalence payload or changes Nat semantics.

Historical validation requires consistent saved checker identities across both
admissions and the prefix proof, rather than equality with the current runtime.
Offline inspection remains unauthenticated historical evidence with no fresh
checking authority, including when the saved wrapper claims a fresh execution.
Explicit replay requires current identities and checks both admissions plus the
prefix proof under one shared <=600-second deadline and 12 GiB cap. It preserves
exact semantic owners and cannot reuse saved success after a failed fresh check.

- Test-first: **31 failures** at the missing native-prefix modules, then **31
  passing in 108.37 seconds**. The fixture contains unmodified actual production
  and relation receipts from the preceding scalar-family qualification, not a
  synthetic accepted proof. Mocked orchestration tests count only call/deadline
  behavior, not Lean validity.
- Controls cover reversed owners, substituted relation/rule/goal/admission term,
  changed capture, missing check owner, limited process receipts, forged fresh
  authority, stale source, substituted fresh admissions, invalid/oversized input,
  SQLite ordered-owner projection, and public CLI exit semantics.
- Root-reviewed helper-only refactors preserve all 40 assertion ASTs and every
  case in the two refactored tests. Original frozen revisions are retained on
  the board and in ignored state. This resolved strict complexity failures
  without changing expectations. Scoped strict quality and Ruff pass.
- Independent source review #1750 and final CLI refactor review #1752 found no
  unresolved issue. Review #1746 specifically required historical checker drift
  to remain readable. Review ran one offline fixture probe, not Lean; root owns
  compiler and test verification.
- Final focused/native/CLI/Nat/SQLite compatibility suite: **114 passed in
  266.34 seconds**. Reconstructing the previously saved equivalence artifact from
  its own original replay inputs preserves that artifact exactly.
- Offline wheel build includes all new persistence modules and the existing
  prefix Lean helper. OpenSpec, bundled/shared skill validation and diff checks
  pass. Frozen tests match after helper-only supersession; the unrelated prior
  `test_rational_lean_encoder_v2.py` mismatch remains untouched.
- Actual public CLI qualification: **1 passed in 584.45 seconds**. Two distinct
  declarations in the parameterized function-valued family were admitted in
  165.39 seconds; native prefix production took 200.83 seconds; SQLite, inspection
  and explicit fresh replay took 208.87 seconds. The final source-drift control
  preserved offline history and rejected fresh replay. Fresh replay produced a
  new analysis owner while retaining the exact semantic inputs and direction.
- The entire supervised test tree took **584.77 seconds** and peaked at
  **4,564,299,776 bytes (4.25 GiB)**, with no memory, output or timeout limit hit.
  The enclosing test budget was 3600 seconds and 12 GiB; each public operation
  kept its shared maximum of 600 seconds. No production source changed during
  qualification. The saved bundle is 4,369,792 bytes.
- The full local entrypoint also inspected the standalone native analysis with
  its explicit context; exit 0 and output exactly equal to the original artifact.
  No compiler ran for that historical inspection.
- [Qualification receipt](prefix-persistence-qualification.json) retains the
  source manifest, whole-process accounting, exact owners and each fresh
  admission/relation receipt. The original two-family rule qualification above
  remains a separate historical result; this persistence gate exercised one
  parameterized family. No new paper audit or discovery claim is made.

## Native ordered predicate-edge chains (2026-10-26)

`propagate-real-bounds-proofir` now accepts explicit ordered productions and
identity-v1/order-prefix-v1 rules. It freshly admits every position once and
checks each adjacent edge separately. The native chain records existing
single-edge analyses and requires the same middle contract and replay owner.
Repeated positions do not skip checks; nested chains cannot substitute for an
individual edge. Inspection is historical; explicit replay repeats every
admission and edge check under one shared <=600-second deadline.

The new closed variant uses the existing propagation storage stage, with
separate ordered edge-analysis refs and ordinary contract refs. SQLite retains
those contract positions and generic reference closure. Only this exact variant
omits the derivation-goal row, because it does not assert a separately checked
endpoint theorem. Nat graph propagation and earlier Real artifacts retain their
meanings. No schema migration, dependency, cache or graph-query API was added.

- Test-first: 20 missing-module failures, then **20 passed in 195.48 seconds**.
- An additional between-edge timeout regression failed by losing the structured
  partial result. The fix retains earlier checked evidence and leaves the chain
  unresolved. The nine boundary controls passed in **19.13 seconds**.
- Source audit #1762 found delayed deadline checks in validation/source loops;
  a new preflight regression reproduced the read-after-expiry behavior. Checks
  now precede each source/verification operation and publication phase. Both
  focused timeout regressions passed in **1.47 seconds**; re-review #1764 found
  no remaining defect. Reviews were source-only and did not run Lean.
- The replay-test lint attempt changed no bytes; the initial diagnostic
  disappeared once the implementation module existed. An unnecessary freeze
  supersession marker was restored with its history retained (#1766). All five
  chain test files retain their original frozen bytes. Scoped strict quality,
  Ruff, OpenSpec and bundled/shared skill validation pass.
- Affected compatibility suite: **109 passed in 470.61 seconds**. It covers
  prior prefix/equivalence persistence, CLI routes and Nat/SQLite consumers.
  The final per-position deadline refinement landed during that run; the final
  chain-focused suite was therefore rerun on the unchanged qualification source:
  **30 passed in 233.17 seconds**. This includes the final deadline regressions.
- Offline wheel build includes all four new chain modules; source/test manifest
  matches. No implementation edits occurred during live qualification.
- **Live public mixed-chain qualification passed: 1 test in 981.56 seconds.**
  Three distinct generic declarations were initially admitted in 242.54 seconds.
  Native publication of the prefix-plus-identity sequence took 340.06 seconds;
  SQLite, historical inspection and explicit fresh replay took 378.94 seconds.
  Replay retained the same middle owner across its two edges and created a new
  chain analysis identity. The final changed-source replay rejected. This is
  one authored generic family with two different rule kinds, not a new paper
  audit or an unfamiliar-source discovery result.
- The whole supervised test tree took **981.88 seconds**, peaking at
  **4,629,114,880 bytes (4.31 GiB)**. No memory, output or timeout limit was hit.
  The enclosing test budget was 3600 seconds; each public operation retained one
  shared maximum of 600 seconds and the fixed 12 GiB worker cap. The native
  bundle is 8,505,336 bytes. No source/test file changed during qualification.
- The standalone native analysis also passed the full local CLI `inspect` path
  with its explicit context, preserving the exact artifact. Both old
  same-input equivalence and prefix artifacts reconstruct unchanged. The SQLite
  contract schema text is unchanged; no migration or new projection table was
  introduced. All five chain tests match their original frozen bytes. The prior
  unrelated rational-encoder test mismatch remains untouched.
- [Chain qualification receipt](chain-qualification.json) retains source/test
  identities, exact ordered owners, both per-edge check receipts and all three
  admission receipts for each fresh operation, whole-process metrics, final
  focused results and compatibility scope. There is no separate endpoint theorem
  or transfer-composition certificate, and saved receipts remain unauthenticated
  historical observations.

### Open task 3.2 gates

- Add other bounded non-definitional comparisons and coefficient/composition
  rules; single-edge directional prefix persistence is now qualified.
- Extend public-operation qualification to non-definitional equivalences,
  changed-context matrices and end-to-end per-edge stale/missing-evidence controls.
- Complete task 4.1's full generic/informed matrix and resource accounting.

Task 3.2 remains unchecked, and task 4.1 has not started. The parent discovery
and acceptance gates remain open.

## Source-bound pointwise coefficient weakening (2026-10-26)

**Qualified:** `check-real-bound-coefficient --input ADMITTED --root PROJECT
--output NEW` freshly admits one exact source owner and proves conditional
output-bound weakening. For original source data and a new `L`, the checked law
is `K ≤ L → 0 ≤ C → J y S n actualProduct → J y S n (L*C)`.
Predicate parameters, object, set and order remain fixed, including their
original dependence on `K`. It is not a uniform existential estimate or a source
theorem implication. Native coefficient persistence and transfer composition
remain open, so task 3.2 stays incomplete.

The Lean helper consumes the actual Admission and scalar equality proofs. Its
source walker is shared with scalar admission, preserving the existing goal
structure. It rejects inherited proof-dependent data and uses equality
transport for products not definitionally equal to canonical multiplication.
The kernel-only commuted-product example checks this transport; the public
observation grammar still requires a syntactic `K*C` application. No new parser
coverage is claimed.

The new supervised worker checks exact request reconstruction, private helper
compilation, independent source-goal capture/replay, accepted trust evidence,
compiled inventory, source freshness and current checker identity. Public
validation checks complete receipts and exact semantic ownership. Each operation
retains a shared maximum 600-second deadline and 12 GiB process-tree cap.
Incomplete admission stops the rule worker and preserves its receipt/diagnostic;
resource exhaustion cannot be promoted to success. The result is ordinary JSON,
not a native analysis or an edge in the identity/prefix chain schema.

### Verification

- Test-first kernel controls: observed missing-elaborator red, then **13 passed**.
  Cases include ordinary and commuted products, a coefficient after the function
  binder, original-K-dependent predicate/operator parameters, changed predicate
  parameters, stale source, invalid admission/scalar evidence, proof-dependent
  contexts, and missing/reversed guards. Concrete goal types are checked.
- Orchestration: **12 controls**, including shared budget, expired preflight,
  exact owner substitution, unaccepted proof, final expiry and aggregate size.
  These use mocks and are not mathematical qualification.
- Additional failure-path regression: **3 controls** first exposed a generic
  error that discarded failed admission evidence; timeout, memory and rejection
  now preserve diagnostics/receipts and skip the rule worker. The change is local
  to the coefficient operation; the shared comparison helper is unchanged.
- Final focused suite: **28 passed in 25.80 s**. Final affected suite:
  **83 passed in 57.27 s**, including those 28. Historical comparison, prefix and
  chain persistence suite: **57 passed in 302.44 s**. These retain old schema
  meanings; there is no database migration.
- Unmocked public gate: **1 test passed in 392.35 s**, covering **2/2 generic
  cases**, all **14 receipt/proof tampering mutations rejected**, and stale-source
  rejection. Whole-test supervisor elapsed **392.664 s**, peak
  **4,493,025,280 bytes (4.18 GiB)**; no memory, output or time limit hit.
  Source and test manifests matched before/after execution.
- Actual CLI with a 0.001-second budget returned exit 2/unresolved/no authority,
  with no admission or rule worker launched.
- Scoped strict radon/vulture, Ruff, OpenSpec validation, both Ladon skill
  validators and `git diff --check` passed. The offline wheel includes all four
  new Python modules and `LadonRealBoundCoefficient.lean`.

Measured worker process times (excluding source extraction and surrounding
publication/validation overhead):

| Generic case | Initial admission | Fresh admission inside CLI | Coefficient proof |
| --- | ---: | ---: | ---: |
| Coefficient quantified after the function | 72.434 s | 72.148 s | 39.998 s |
| Original-K-dependent predicate and operator | 71.822 s | 73.000 s | 39.241 s |

The 1,800-second enclosing test budget covers several separate admissions and
public operations; it does not raise the 600-second public-operation maximum.
These are constructed generic cases, not informed targets or unfamiliar-source
fault detection. There is no new paper audit or paper-norm bridge result.

### Review, provenance and limits

Independent Luna scope review: board #1771/#1772, with root clarification #1773
that K-dependent values are supported when retained unchanged. Independent
integrated review: #1778; corrected anchors and helper-only test review: #1780;
final admission-failure delta review: #1784. Reviewers ran no Lean tests; root
observed the qualification above.

Two frozen test files received an independently reviewed helper-only refactor
for complexity/lint. All **34 assertion ASTs**, case names, decorators and
parametrization were preserved. Prior bytes and the exact patch remain in
`.codex/state/real-coefficient/quality-proposal/` and board revision history.
All six active coefficient contract/test/fixture freezes match. The pre-existing
unrelated frozen mismatch in `tests/test_rational_lean_encoder_v2.py` was left
untouched; no repository-wide frozen-clean claim is made.

One prototype live attempt was intentionally interrupted at 214.038 seconds
before fixing the admission-failure path. It is not qualification evidence.
The strict quality wrapper also unexpectedly launched the entire test suite;
that run was interrupted after 429 passing tests and is not a full-suite pass.
Final quality evidence uses the same scoped strict quality function, Ruff, and
explicit relevant test suites. Both interruptions are retained in the receipt.

Machine-readable evidence: [coefficient qualification](coefficient-qualification.json).
Detailed process logs, source manifest, frozen verification and scoped quality
receipts are under `.codex/state/real-coefficient/`. The final synthetic project
was deliberately changed for the stale-source negative check, so its saved
productions are now historical against that directory. Nothing was pushed.


## 2026-10-26 — Task 3.2 completed: native conditional rules and public comparison matrix

Task 3.2 is complete within the supported, source-bound Real grammar. This
closes the remaining native coefficient persistence, conditional transfer
composition and public comparison gates. Task 4.1's full generic/informed
matrix and the parent's discovery, source-fidelity and paper-bridge gates remain
open. This was not a paper audit and establishes no detection benefit.

### Implemented behavior

- `check-real-bound-coefficient-proofir`, `inspect-real-coefficient` and
  `replay-real-coefficient` retain one exact source owner, its conditional
  pointwise output-bound goal and a separate rule check-run. The unary replay
  format does not widen historical two-owner codecs.
- `compose-real-bounds[-proofir]`, `inspect-real-transfer` and
  `replay-real-transfer` derive a conditional composition law from the two actual
  source applications. Lean checks the exact middle predicate, object, set,
  order and actual scalar products, preserving guards and data dependencies.
  Both source-shaped transfer steps remain explicit assumptions. The outer
  factor is `L*K`; no existential witnesses are extracted or made uniform.
- Both native propagation variants own their actual conditional derivation
  goals. SQLite projects their exact goal/check-run/contract references without
  a schema migration. Generic and dedicated inspection remain historical and
  unauthenticated; explicit replay rechecks admissions and the rule. Neither
  variant is accepted as an identity/prefix input-predicate chain edge.
- Unsupported telescope layouts, changed dependent data types and retained
  proof-valued data remain unresolved. Source theorem bodies, coefficient
  uniformity and paper-norm bridges remain separate obligations. Nat profile
  meanings and historical Real schemas remain unchanged.

### Public acceptance evidence

Eight generic source estimates were freshly admitted. The public matrix then
established one matching-context equivalence and left all four changed-context
relationships unresolved. No negative case was promoted to equivalence or
mathematical falsity:

| Public check | Required and observed result | Seconds |
| --- | --- | ---: |
| Native conditional transfer production | checked; premises assumed | 205.29 |
| Fresh native transfer replay | checked with new evidence owners | 210.20 |
| Native coefficient production | checked; pointwise original output context | 121.75 |
| Fresh native coefficient replay | checked with new evidence owners | 123.91 |
| Same-context comparison | equivalent | 197.90 |
| Different operators, equal loss | unresolved | 157.78 |
| Changed set identity | unresolved | 156.51 |
| Changed predicate parameter | unresolved | 156.15 |
| Changed constant dependency scope | unresolved | 155.99 |
| Incompatible middle parameter in composition | unresolved; attempted check retained; no native bundle | 170.33 |

Both native rules passed SQLite goal/owner/foreign-key checks, generic historical
inspection, new-owner fresh replay and rejection as predicate chain edges.
Ten rehashed transfer claim/owner mutations were rejected in the live test.
Dedicated inspection with current-source checking also passed without acquiring
fresh authority. The generic scalar and function-valued composition kernel
positives are independently named and unrelated to a paper target.

Each public operation retained its shared maximum **600-second** deadline and
**12 GiB** process-tree RSS cap. The retry's complete measured process tree
peaked at **4.29 GiB**, with no timeout, memory limit or output limit. Its runtime
source and loaded test files remained unchanged throughout the run. A single
3600-second aggregate deadline was retained across qualification attempts;
no operation's resource limit was increased. No cache was added.

### Failures preserved and corrected

The first public attempt failed at native publication after **369.69 s**:
`contextDigest` passed a bare list to the object-only `snapshot_identity`
helper. A frozen regression reproduced the exact `AttributeError`. The repair
hashes an object containing the two ordered contexts. A fresh independent delta
audit found no further defect. The corrected public retry performed new
admissions and native checks; the failed attempt remains recorded.

The retry completed **all native and comparison assertions**, then its test
reader failed on the expected stale-source rejection: the CLI printed status 2
and `stale formal source digest` to stdout and correctly created no output
artifact. The reader expected a file. The original combined pytest result is
therefore preserved as **failed after 2333.91 s**, not relabeled a passing run.
Its supervisor measured **2334.25 s**.

A frozen test using the actual invalid-input CLI reproduced that reader error.
The helper-only repair reads stdout when no output artifact exists; all **24
assertion conditions are AST-identical**, and no case was removed. Original
frozen bytes remain in board revision history. The repaired reader and both
independent stale-source checks passed **3/3 in 14.34 s**, using the preserved
public bundles and already-drifted source. Both saved bundles remained unchanged;
historical inspection succeeded and fresh replay rejected stale input. These
separate passing gates complete acceptance without repeating the completed
Lean work. There is no claim of one uninterrupted passing combined pytest run.

### Verification and limits

- Post-fix affected Python suite: **68 passed in 73.02 s**.
- Genuine-transfer historical persistence suite: **13 passed in 48.05 s**,
  including exact ordered context digest reconstruction, SQLite, ten native
  mutations, seven deep receipt mutations, checker drift, limited replay and
  publication expiry. Mock orchestration controls are explicitly labeled.
- Existing Real comparison/prefix/chain history and Nat consumers:
  **126 passed in 334.96 s**. Their relevant implementation remained unchanged
  by the concurrent transfer-only digest repair.
- Source-bound transfer kernel: **13 passed in 25.53 s**, reused because no Lean
  helper changed during the later Python repair. Additional exact-middle and
  dependency controls: **8 passed in 19.08 s**, including changed object/set/
  order/bound, guards, original input endpoint, `Fin n` data substitution and
  inherited proof-valued predicate parameters. Type-mismatch controls are not
  presented as proofs of mathematical falsity.
- Scoped strict quality and Ruff pass; **68 relevant frozen artifacts match**.
  An import-formatting-only test revision preserves an identical AST. Four
  pre-existing complexity findings in the older analysis/relation-worker files
  are outside this final change's strict-quality scope; no repository-wide
  quality or whole-project test pass is claimed.
- The offline wheel contains the exact final native modules and Lean helper.
  OpenSpec and both Ladon skills validate. No new dependency or migration was
  introduced; no code was pushed.

Independent source audits are board posts **1801–1802**, with the final
publication-fix audit at **1808**. They are source-review evidence, not test
execution. Root observed every acceptance result. The generality boundary is
matching source context/role layout and the documented bounded grammar;
unsupported contexts do not acquire rule authority.

Machine-readable evidence: [Task 3.2 qualification](task-3-2-qualification.json).
Detailed preserved attempts, manifests and logs are in
`.codex/state/task32-final/` and `.codex/state/task32-retry/`. The genuine
historical transfer fixture is `tests/fixtures/real_bound_native/recorded-transfer.json`.
Both `skills/ladon/SKILL.md` and the shared
`../codex-skills/ladon/references/contract-analysis.md` now describe the native
commands, conditional claim boundary and explicit replay requirements.
