# Checked Real transfer laws

Task 2.2 is complete as a reusable checked Lean law library. The new
LadonRealBoundComposition module supplies six theorems: identity, composition,
input/output prefix weakening, coefficient weakening, and multiplication
monotonicity. Full semantic contracts and native rule activation remain open;
informed contracts remain 0/2.

## Behavior and mathematical boundary

TransferAt retains both endpoint objects and predicates, the common parameter
set, input/output orders, input bound C and coefficient K. It requires K ≥ 0,
then proves the transfer implication under C ≥ 0. Its arguments can occur
inside the caller's original telescope, including coefficients that depend on
objects, sets, orders or C.

Composition requires exactly the same intermediate object, predicate, set,
order and bound K*C. The second coefficient is evaluated in that actual context,
and the result uses L*K. It does not move existential coefficients outside their
original scope. Prefix weakening takes the actual predicate's OrderPrefix law;
coefficient weakening takes BoundMonotone and K ≤ L and uses C ≥ 0.
Multiplication monotonicity explicitly takes a nonnegative multiplier.

The module imports the unchanged prefix family. It changes no Python runtime
or existing profile meaning. Native comparison and propagation are still gated
by tasks 3.1 and 3.2.

## Verification

- Eleven positive Lean examples passed, covering scalar/product and sequence
  bounds, nonzero distinct orders, four independent universes, and coefficients
  depending on objects and input bounds.
- Three kernel-checked counterexamples establish failure of unrestricted
  negative scaling, failure of coefficient monotonicity with negative input
  bounds, and failure of a pointwise-to-uniform coefficient exchange.
- Seven elaboration controls reject changed intermediate predicate, set, order,
  object or bound, a missing multiplier sign, and a missing prefix law. These
  are application controls, not mathematical refutations.
- Both configured pytest integration cases passed, zero skipped, in 3.98
  seconds. Without an explicitly configured compiled Mathlib project these
  integration tests skip; the qualifying invocation supplied it.
- The compiler/axiom observer checked 27 unique declarations: the eleven
  examples, ten negative/control theorems and six reusable laws. All transitive
  axioms stayed within propext, Classical.choice and Quot.sound.
- The final compilation qualification built four modules in 2.45 seconds,
  peaking at 1.655 GiB of process-tree RSS. Each compiler phase had a 60-second
  timeout, with a 600-second qualification deadline and fixed 12 GiB cap.
  This excludes initial failures, the separate pytest execution, import
  inventory and packaging.
- An actual import observer captured and verified 2,328 compiled modules and
  their sidecars. See COMPILED-INVENTORY.json and TOOLCHAIN.json.
- The offline wheel build contains the exact new Lean source module.
- Ruff, scoped strict quality, OpenSpec strict validation and diff checks passed.

The earlier 172-test binding result is reused after verifying every recorded
implementation/test identity and its checker identity remain unchanged. It is
not claimed as a newly rerun suite. All 2,670 primary files and 184 frozen
artifacts from the preceding three child packets are unchanged.
The one pre-existing frozen-test mismatch remains untouched.

See VERIFICATION.json, CHECKS.json, IMPLEMENTATION.json, the raw compilation and
axiom records under qualification-green-2/, and REVIEW.md.

## Test-first work and independent review

Root observed missing-law failures in both frozen fixtures before production
implementation, using a temporary import-only module that exposed just the
existing prefix family. The baseline is explicitly an API-absence probe,
not an implemented rule module. Tests and fixtures remained frozen thereafter.

The guard and test-design workers completed independent first passes and a real
peer challenge. Their exchange caught the risk of silently changing a
scalar-dependent coefficient into a constant. Root selected the pointwise
form and integrated the production code. A distinct final reviewer found no
source-level correctness blocker and inspected the harness. That was a source
review; the reviewer did not independently run Lean or pytest.

Initial harness startup collided with the test worker's scratch directory;
the runner now uses distinct qualification directories. The first production
compile rejected a local binder named prefix, which is a Lean keyword; the
production binder was renamed. Both failures are retained, and no frozen test
was changed to obtain green. Legacy board history entries with null match flags
were initially miscounted during verification; only explicit false flags are
active mismatches, leaving the single pre-existing mismatch.

Next is the derivative-prefix adapter, preserving all joint derivative,
domain and norm/carrier data. The paper-norm bridge and parent independent
discovery/evaluation gates remain open. Nothing was pushed.
