# Task 4.1 — Current Real-bound qualification

All Task 4.1 acceptance gates passed on 2026-10-27. This completes the
`ladon-real-bound-contracts` change within its documented grammar. The parent's
source-fidelity, independent-discovery, paper-norm and held-out evaluation gates
remain open. No exposition fault or source theorem proof is established here.

## Public native matrix

The current checkout ran the frozen generic cases before the informed cases.
No production code changed during qualification. Each shape observation retained
unresolved admission and no contract until its separate native predicate/scalar
checks succeeded. The measured cases are:

| Case | Literal loss | Native result | Predicate, scalar | Admission seconds | Peak GiB |
| --- | ---: | --- | --- | ---: | ---: |
| canonical | 0 | admitted | supported, supported | 90.74 | 4.986 |
| loss-seven | 7 | admitted | supported, supported | 90.14 | 4.988 |
| named | 0 | admitted | supported, supported | 76.87 | 4.192 |
| multiplication | 0 | unresolved | supported, unresolved | 87.66 | 4.992 |
| order | 0 | unresolved | supported, unresolved | 87.59 | 4.981 |
| zero | 0 | unresolved | supported, unresolved | 87.25 | 4.977 |
| placeholder | 0 | unresolved | unresolved | 47.39 | 4.977 |
| inverse_finiteJets | 5 | admitted | supported, supported | 225.79 | 5.810 |
| nonbarPart_finiteJets | 4 | admitted | supported, supported | 214.32 | 5.812 |

Denominators are separate:

- **8 distinct observed candidates**: six generic source statements and two
  informed statements. The placeholder attempt reuses the canonical observation.
- **3/3 intended generic native admissions**; **0/4 negative admission attempts
  promoted**, all four unresolved without native artifacts. Three counterfeits
  passed predicate admission and failed canonical scalar admission. The
  placeholder was rejected for `sorryAx`; no resource stop counted as rejection.
- **2/2 informed fixed-loss native interpretation contracts admitted**. Actual
  losses five and four, original endpoints and dependency scopes were preserved.
- **1 symbolic case unsupported**, with no fabricated loss, binding plan or
  native contract. It is not counted as an admitted or mathematically false case.
- Fresh native replay passed with a new worker request in **95.38 s**.
  Native validation and SQLite projection passed for every admitted artifact
  batch. Public inspection and reporting retained `authority:none` and
  `freshCheck:false`, including with current-source checking.

The complete native matrix took **1143.04 s** including its
formal-observation/planning/inspection work. Table costs measure admission
commands only. The highest recorded process-tree peak across the measured
qualification commands was **5.812 GiB**. Each public
worker retained its shared **600-second deadline and 12 GiB cap**; the outer CLI
supervisor allows 660 seconds for dispatch and report overhead. No cap or failed
operation deadline was reset. No cache or dependency was added.

## Adapter and negative matrices

The source/helper identities of the older adapter matrices differed, so they
were freshly executed instead of counted as current results. All prior cases
and expectations were preserved in new private output roots.

| Matrix | Positive bindings | Unresolved negative attempts | False promotions |
| --- | ---: | ---: | ---: |
| Fixed joint real derivative adapter | 2/2 | 8/8 | 0/8 |
| Named measure, including compiled-import mutation | 3/3 | 8/8 | 0/8 |

Adapter success remains `checked-binding`, with unresolved native admission and
no contract; these counts must not be added to the native admission totals.
Derivative negatives cover parameter-only derivatives, a restricted point
quantifier, squared norm, missing instances, complex-scalar derivatives,
retained proof-valued parameters, a placeholder and a non-product domain.
Named-measure negatives cover incorrect measures, placeholders, attempted rescue
by an unused False premise, forged live expressions, changed definitions,
changed instances, retained proof parameters and changed compiled meaning.

The compiled-import control deliberately changed one private `.olean` while
keeping the selected source and pinned context unchanged. A fresh check rejected
the formerly valid proof. It did not mutate protected target or dependency
libraries. The two independent matrix processes used private roots and shared
compiled dependencies read-only; their elapsed times are not added as wall time.
Aggregate measured durations were **371.20 s** for the derivative matrix,
**287.70 s** for the named-binding matrix and **80.13 s** for the import control.
All completed normally; recursive receipt checks reject timeout, memory and
output-limit outcomes as semantic negatives.

## Verification and independent review

- **123 focused tests passed in 18.55 s**, covering current observation,
  admission, binding, derivative and native planning/evidence/inspection paths.
- Task 3.2's final rule/storage/compatibility evidence is reused for unchanged
  relevant runtime and test conditions: its 68 affected tests, 13 genuine
  transfer persistence tests, 126 historical Real/Nat consumer tests and 13+8
  transfer kernel controls. Its original combined test-reader failure remains
  recorded as failed, with the separate repaired-reader/stale checks as its
  completion evidence. No new full-project test pass is claimed.
- Scoped strict quality and Ruff pass. The older analysis/relation-worker
  complexity findings documented in Task 3.2 are unchanged and outside this
  qualification's scoped strict check. No unrelated frozen mismatch was edited.
- All **610 runtime files**, **2670
  protected primary inputs**, **633
  artifacts in six preceding evidence packets and the five historical Nat
  recognition/profile/production/formal modules match their recorded identities.
- Independent Luna-medium source review at board **1819** examined the
  mathematical and trust boundary against the current runtime. It found no
  actionable unsound promotion or scope mismatch; all 60 reviewed Real-bound
  runtime identities matched. This was independent source review, not an
  independent Lean execution. Root ran and verified the public checks.

The admitted claim is the exact observed predicate interpretation and canonical
Real scalar semantics. Derivative admission uses the full joint real Frechet
operator norm with actual source-context instances. Historical artifacts are
consistent saved observations, not authenticated execution or fresh authority.
Conditional transfer composition still assumes both source-shaped transfer
steps; no uniform existential witness or source theorem proof follows. Rejected
or unsupported inputs are not mathematical refutations. These informed-source
results establish no unfamiliar-source detection or held-out benefit.

Final evidence review at board **1821** reconciled the case denominators,
87 public command receipts and resource totals, and found no omitted acceptance
gate or trust overclaim. All **73 relevant frozen artifacts** match. The existing
wheel matches all **610 runtime files**, so no redundant rebuild or full-suite
rerun was needed. See [FINAL-CHECKS.json](FINAL-CHECKS.json). Both Ladon skills,
OpenSpec strict validation and `git diff --check` pass.

## Evidence and reproduction

[VERIFICATION.json](VERIFICATION.json) contains the separate denominators,
per-case outcomes and integrity checks. [COMMANDS.json](COMMANDS.json) retains
commands, exits, bounds, durations, process-tree peaks and output digests; full
raw command receipts remain in `.codex/state/task41/`. Native productions,
observations, plans, proof terms and replay data are copied under [native](native/),
with adapter results under `derivative/`, `binding/` and `import/`.
The frozen `qualify_*.py` harnesses and `verify.py` retain the assertions used.
They require the existing protected informed checkout and a compiled Mathlib
project; use fresh output directories when reproducing, preserving this run.

The runtime manifest, protected-input manifest and prior packet integrity
verification bind the results to this checkout. Run with `PYTHONPATH=src:tests`
so the installed package cannot silently replace it. This task added evaluation
artifacts and qualification guidance, with no runtime implementation change.
Both bundled and shared Ladon skill guidance was updated. Nothing was pushed.
