# Typed Real-bound contracts

Ladon can record the typed shape of some Real-valued bound estimates from an
existing formal snapshot. This is the first stage of the
[Real-bound contracts plan](../openspec/changes/ladon-real-bound-contracts/tasks.md).
Native Real contracts require fresh predicate and canonical scalar checks.
Restricted analysis supports same-context predicate equivalence, explicit
identity edges, and individually checked input-prefix implications. General
cross-context comparison and transfer composition remain unresolved.

For authored prose, [typed prose observation](REAL_PROSE_OBSERVATION.md) supplies
a separate `observe-prose-bound` path. It captures the proposition value without
asserting a theorem or producing an admitted Real record. Its public exit code
tracks proposition capture; the formal shape observer below retains its existing
unresolved-admission exit semantics.

Use the current checkout:

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract produce \
  --channel formal --root /path/to/lean-project \
  --file Estimates.lean --module Estimates --declaration Estimates.bound \
  --output formal.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract observe-bound \
  --root /path/to/lean-project --input formal.json --output bound.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract inspect \
  --root /path/to/lean-project --input bound.json
```

`observe-bound` and inspection of its output return **exit code 2** while
mathematical admission is unresolved. A written result with `status: observed`
means its syntax was captured; `status: unsupported` means no supported candidate
was found. Both retain the original snapshot and named residuals. An output
collision does not overwrite the destination. A formal observation that failed
its memory limit remains a failed observation: honor its original stop-and-report
diagnostic rather than treating the wrapper as permission to retry.

The closed wrapper uses `ladon-real-bound-observation-v1` and observation profile
`real-bound-shape-v1`. Its `contract` is always null, `admission` is unresolved,
and `authority` is syntax-only. Existing `norm-scale-v1` production, digests and
semantic consumers are unchanged; the new wrapper is not a `proofir.contract`.

## Supported syntax

The initial shape has one existential coefficient K, an explicit `0 ≤ K`
conjunction, universal inputs f/S/C, an explicit `0 ≤ C` premise, a final bound
premise `J f S (n + d) C`, and conclusion `J (A f) S n (K*C)`. The direct index n
is also supported as loss zero. Here d is a nonnegative Nat literal; the Nat
addition instance is checked syntactically. The exact predicate, its implicit
parameters, operator application, set, all typed binders and proof premises are
retained. Other fixed parameters are allowed. Moving K later changes its
permitted binder scope, including earlier proof premises; this does not assert
that every such parameter is necessary.

Predicate and operator names are unrestricted within that shape. Real carrier,
order, numeral and multiplication expressions are observed syntax: the name
`Real` alone establishes no mathematical interpretation. The compiled negative
fixture intentionally defines a fake type with that name and still receives
only unresolved admission. No derivative or norm meaning follows from a
predicate name, a numerical loss, or a successful Lean build.

The observer walks the outer quantifier structure; it does not mine convenient
subformulas under negation/disjunction. Unsupported symbolic losses, mismatched
predicate parameters/sets and other shapes retain a residual. It does not infer
missing guards or normalize arbitrary algebra. Limits are 64 outer binders,
128 JSON-tree depth and 100,000 tree nodes. Exceeding a limit yields a named
residual. Input files use the existing 32 MiB aggregate loader limit.

## Replay and evidence

`observe-bound` verifies the existing formal snapshot before deriving a detached
wrapper. Inspection rechecks the source/environment/helper bindings, observation
profile and implementation identity, and recomputes the entire candidate from
the nested statement. Rehashing an edited loss or admission field cannot make it
pass replay. Verification preserves the original producer's attributed,
unreviewed trust boundary; it does not re-elaborate the source or authenticate an
imported observation as a proof receipt.

`candidate.input.originPath` and the other origins refer to the nested worker's
`normalizedTypeExpr`. Scoped expressions use ordered `binderId` references for
outer binders and retain de Bruijn references for inner binders. Ordinary
regularity assumptions remain typed premises, without an inferred interpretation.

Later admission must check the actual predicate definition/application and all
laws used by the selected consumer in the pinned environment. A derivative-prefix
adapter must preserve the full derivative and domain quantifiers. A prose
C^m-norm bridge remains a separate obligation. Known-source observation counts
must be reported separately from admitted contract counts and discovery benefit.

## Generic prefix-law checks

The separately compiled `LadonRealBound` family abstracts over an object F,
parameter domain P, point domain Y, and `measure : F → P → Y → Nat → Real`:

```text
PrefixBound measure f S n C :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y, measure f p y j ≤ C
```

It provides generic order-prefix and Real-bound monotonicity proofs, plus a
constructor from a checked predicate equivalence. The measure has no inferred
norm or derivative interpretation. Checked transfer composition is provided by
the separate library described below; contract consumers do not yet activate it.

`ladon.real_bound_admission.plan_prefix_admission(request)` generates three
closed goals: predicate equivalence to this family, order-prefix weakening and
monotonicity in C. The request has exactly these fields:

```json
{
  "source": {"path": "Bounds.lean", "sha256": "<64 lowercase hexadecimal characters>"},
  "environmentRef": "sha256:<pinned environment identity>",
  "predicate": "Example.bound",
  "measure": "Example.measure",
  "objectType": "Example.Object",
  "parameterType": "Nat",
  "pointType": "Unit"
}
```

Use the actual source digest and `pinned_toolchain(root).context_identity` from
`ladon.proof_slice`; declarations and types must be ordinary qualified names.
This interface handles closed predicate applications. Use the bound-prefix
commands below to instantiate the dependent telescope of an observed estimate.

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract plan-prefix-admission   --root /path/to/lean-project --input request.json --output prefix-plan.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-prefix-laws   --root /path/to/lean-project --input prefix-plan.json --terms terms.json   --timeout-seconds 900 --output checked-laws.json
```

`terms.json` supplies one Lean proof term for each exact goal ID:
`predicate-equivalence`, `order-prefix`, and `bound-monotonicity`. Caller-supplied
acceptance flags or replacement goals are invalid. The plan command verifies
current source/environment bindings and returns exit 2 because admission remains
unresolved. `check-prefix-laws` returns exit 0 only for `checked-laws`; it retains
`admission: unresolved` and `contract: null` even then.

The checker builds the fixed family in a fresh parent-owned temporary project
before loading target declarations. Existing compiled dependency roots are read
without running Lake or modifying their caches. A pre-existing module named
`LadonRealBound` in those roots is rejected to prevent an ambiguous family import.
The target must have compiled Mathlib dependencies compatible with its pinned
Lean toolchain. No dependency download or build is attempted.

Every goal uses source-goal capture, completion, independent replay and the
standard no-placeholder axiom policy. Source, environment, family and checker
identities are rechecked; compiled inventories must remain equal across goals.
The complete worker tree shares the requested deadline and the fixed 12 GiB cap.
Temporary files are owned and cleaned by the parent, including on worker stops.
Saved receipts are historical evidence; supplying them cannot bypass a fresh
check. The ordinary inspector does not promote a law-run receipt to admission.

This proves the supplied predicates have the checked prefix laws in that source
context. The bound-prefix commands below connect prefix laws to an exact observed
predicate application; full scalar semantics and consumer admission remain separate.
The bounded development gate checked a generic adapter and both laws, but one
late placeholder-negative run was incomplete at its shared deadline; see the
[implementation evidence](../openspec/changes/ladon-real-bound-contracts/evidence/prefix-admission-20261025/REPORT.md).

## Checking an observed predicate application

Supply a measure declaration and its explicit arguments as ordered binder IDs
from the observation, including implicit and instance parameters:

```json
{"declaration":"Example.sample","arguments":["b0","b1"]}
```

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract plan-bound-prefix \
  --root /path/to/lean-project --input bound.json --measure measure.json --output binding-plan.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-bound-prefix \
  --root /path/to/lean-project --input binding-plan.json --proof proof.json \
  --timeout-seconds 900 --output checked-binding.json
```

`proof.json` contains exactly `{"term":"<Lean proof term>"}`. The plan returns
exit 2. A fresh successful check returns `status: checked-binding` and exit 0;
it establishes predicate equivalence, prefix order and bound monotonicity for
the actual observed predicate. **`admission` remains unresolved and `contract`
remains null**: scalar operations, composition and
native consumer activation are separate gates. Derivative interpretation uses
the separate fixed adapter described below. This checks the predicate laws;
it does not certify the observed estimate's proof body.

The checker compiles the fixed family and binding helper in isolation, then
copies the selected source and derives the proposition from its live Lean Expr.
It compares the full normalized statement to the observation modulo bound-variable
display names; de Bruijn references, universes, binder types/kinds, constants and
instance applications remain exact. It uses the actual input/output predicate
prefix, typechecks all measure arguments and universally closes only the
parameters needed by that law, including dependencies of their types.
Unused hypotheses cannot support the proof. Retained proof-valued parameters
are explicitly unsupported, including transitive dependencies on proofs.

No particular measure is inferred from a predicate name. The supplied measure
must have a freshly checked equivalence to the predicate. This still says
nothing about a prose norm. Unresolved universes, changed definitions, malformed
applications, stale source bindings and forbidden axioms cannot produce
`checked-binding`. Checks use the same fixed 12 GiB cap and an explicit shared
deadline; neither command loads an old success receipt as proof authority.

These commands require current source snapshots and compiled dependencies. A
reserved `LadonRealBound` or `LadonRealBoundBinding` module in the target's
compiled roots is rejected. Ordinary contract comparison, propagation and
native storage continue to reject these separate observation/check schemas.

## Checked transfer law library

The shipped Lean module LadonRealBoundComposition imports LadonRealBound and
defines a pointwise transfer:

~~~text
TransferAt J Q x y S m n C K :=
  0 ≤ K ∧ (0 ≤ C → J x S m C → Q y S n (K*C))
~~~

Objects, sets, orders, bounds and coefficients are explicit. Each predicate may
have a different object type, while the parameter set uses the same domain.
A caller can wrap the proposition in its original telescope, preserving a
coefficient's dependencies on objects, parameters or the input bound.

The transfer_compose theorem takes a second transfer at exactly K*C and yields
coefficient L*K. It retains the intermediate object, predicate, set and order,
and obtains 0 ≤ K*C from the coefficient and input-bound guards. If L depends
on the bound, the caller evaluates it at that actual intermediate value.
The rule does not infer a uniform coefficient.

The transfer_input_prefix theorem permits a larger required input order with
the input predicate's OrderPrefix law. The transfer_output_prefix theorem
permits a smaller output order with the output law. The
transfer_coefficient_mono theorem permits K ≤ L with the output's BoundMonotone
law and the nonnegative input bound. The scaled_bound_mono theorem proves
C ≤ D implies K*C ≤ K*D for nonnegative K. The transfer_identity theorem
supplies an identity step with coefficient one.

Frozen integration fixtures instantiate the laws for scalar/product and
sequence bounds, independent object universes, and coefficients depending on
objects and bounds. Kernel-checked counterexamples disprove unrestricted
negative scaling and a pointwise-to-uniform quantifier exchange. Separate
elaboration controls reject mismatched intermediate data; an elaboration
failure alone is not a mathematical refutation.

Select an existing compatible compiled Mathlib project to run the checks:

~~~bash
LADON_MATHLIB_TEST_ROOT=/path/to/compiled-mathlib-project PYTHONPATH=src \
  .venv/bin/pytest -q tests/test_real_bound_rules_lean.py
~~~

Without that explicit project, these two integration cases are skipped.
Qualification sets it and requires both to execute. The temporary project reads
dependency libraries and compiles the shipped family, rule module and examples
with the fixed 12 GiB cap. It observes the compiler's axiom inventory for every
named rule and example. No dependency download occurs.

These are reusable checked Lean laws. Native admission below checks the exact
predicate and scalar operations; comparison and propagation remain separate gates.

## Full joint derivative adapter

The derivative adapter checks the fixed measure:

~~~text
jointDerivativeMeasure f p y j := ‖iteratedFDeriv Real j f (p,y)‖
~~~

It supports a nondependent function type P × Y → Z. P, Y and Z, their
universes, and the necessary real normed-space instances come from live source
expressions and the pinned environment. It adds no assumptions to supply a
missing instance. The norm is that of the full continuous multilinear derivative
on the product domain, including mixed directions. All j ≤ n, p ∈ S and y:Y
remain quantified. A restricted-point, parameter-only, differently scaled
norm or complex-scalar derivative requires a separate checked bridge.

~~~bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract plan-derivative-prefix \
  --root /path/to/lean-project --input bound.json --output derivative-plan.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-derivative-prefix \
  --root /path/to/lean-project --input derivative-plan.json --proof proof.json \
  --timeout-seconds 600 --output derivative-check.json
~~~

The plan has schema ladon-derivative-prefix-plan-v1 and profile
joint-real-frechet-prefix-v1. It has no caller-supplied measure selector or
admission switch. The proof file contains exactly a term field holding the
Lean proof of the displayed Admission proposition; inspect that goal before
supplying the proof. The plan returns exit 2. A successful fresh check returns
checked-binding, derivativeAdmission:checked and exit 0.

The checker compiles the family, shared binding helper and derivative helper
in isolation before copying the target source. The source's exact predicate
application is checked against the fixed derivative measure by equivalence,
prefix order and bound monotonicity, using capture, completion, independent
compiler replay and the no-placeholder axiom policy. All helpers, source and
compiled imports participate in freshness checks. Missing local instances,
dependent/non-product domains and retained proof parameters are unsupported.

Even after a successful derivative check, admission remains unresolved,
contract remains null and paperNormBridge remains unresolved. It establishes
the selected full-joint derivative interpretation of the predicate; it does
not validate the estimate's proof body, supply regularity, identify a prose
norm, or activate native contract comparison/propagation. The original
observation retains the operator, exact loss and coefficient scope. A saved
positive receipt remains historical evidence and cannot authorize a fresh run.


## Native admission, storage and historical reports

Start with either a bound-prefix or derivative-prefix **plan**, keeping its
original observation and complete telescope. A previous successful check is
historical data and cannot substitute for a new admission run.

~~~bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract plan-real-bound \
  --root /path/to/lean-project --input binding-plan.json --output real-plan.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract admit-real-bound \
  --root /path/to/lean-project --input real-plan.json --proofs proofs.json \
  --timeout-seconds 600 --output real-production.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract inspect-real-bound \
  --input real-production.json --root /path/to/lean-project

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract report-real-bound \
  --input real-production.json

PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract replay-real-bound \
  --root /path/to/lean-project --input real-production.json \
  --timeout-seconds 600 --output replay-production.json
~~~

The proofs file maps exactly predicate-admission and scalar-semantics to Lean
proof terms. Inspect the planned propositions before supplying terms. The first
checks the exact live predicate against the chosen prefix interpretation. The
second checks that the actual K/C guards and output product equal canonical
Real nonnegativity and multiplication. The scalar helper is compiled separately
before target commands; proof premises from the original statement cannot be
used to prove the scalar equalities. Nonstandard Real multiplication, order or
zero dictionaries therefore require proof of the actual equalities.

Planning returns exit 2 with admission unresolved and contract null. Admission
returns exit 0 only after both fresh checks succeed; unresolved checks return
exit 2 and no native artifacts. The source theorem's proof body is not certified
by these checks. A source build or separate proof review remains separate from
admitting the interpretation. Neither operation establishes a paper-norm bridge.

A successful production wrapper uses ladon-real-bound-production-v1 and contains
four native artifacts in order: source-map, predicate check-run, scalar check-run,
and proofir.contract with the closed real-bound-v1 record. Exact typed source,
statement and check owners are validated together. Expressions use scoped
fingerprints and typed references; the full observed syntax and process receipts
remain in bounded ordinary replay data. Every original binder, including proof
premises, remains in the record. Constant permissions retain their lexical scope.
SQLite uses the existing disposable native projection without a schema migration.
Historical norm-scale-v1 identities and meanings are unchanged.

A fresh admission command reports fresh-lean-check for that execution. Stored
native records retain recorded-checked and checkerAuthority:none. Inspection and
reports deterministically reconstruct saved artifacts and always return
validated-historical, authority:none and freshCheck:false. They do not authenticate
an imported producer or rerun Lean. Providing a root additionally verifies current
source/environment/helper/checker identities. Without a root, freshness is not
checked; historical helper identities remain readable. A digest is not a signature.
The ordinary contract inspect command accepts the same production wrapper, and
proofir inspect shows the historical Real profile on an extracted native contract.

Replay requires current source and implementation identities and executes both
checks again. Stale implementation evidence requires a new plan and admission;
replay does not silently rewrite a source reading. Output paths must be new files.
The shared admission deadline is configurable, defaults to 600 seconds, and retains
60-second compiler phases, 8 MiB worker I/O and the fixed 12 GiB process-tree cap.

The older comparison, graph propagation, obligations and application-probe
consumers remain Nat-only and reject the Real profile. A numeric loss alone does
not relate different operators, domains, sets, constant scopes or paper norms.

## Restricted native analysis

`compare-real-bounds` takes two saved production wrappers and a source root. It
replays both predicate and scalar checks and compares the complete typed
interpretation contexts: endpoint, telescope and binder roles,
function/set/order/bound expressions, constant permissions, guards, loss, and
interpretation. Matching contexts are only a precondition. For productions
from the same source module, Ladon rechecks both observed ASTs in a fresh Lean
environment, derives an `Iff` between their live input predicates, and runs a
separate supervised Lean check. The initial proof term is restricted to
definitional equivalence (`by intros; rfl`); a failed check remains unresolved.
Different contexts or source modules also remain unresolved. This does not
certify either source theorem body or the exposition's norm bridge. Fresh replay
evidence is returned in ordinary JSON. Use `compare-real-bounds-proofir` to
perform the same fresh checks and persist a closed native comparison bundle.

`propagate-real-bound-identity` accepts an ordered list of saved productions.
It replays each input and separately checks every adjacent identity-v1 edge
using the exact live-derived predicate `Iff`. Each edge records its own checked
goal and supervised run; a failed or skipped edge keeps propagation incomplete.
It has no graph-rule input and supports no non-identity rule. Results remain
ordinary JSON rather than persisted ProofIR analysis artifacts. Neither command
dispatches through the Nat comparison or propagation implementations.


`compare-real-bounds-proofir --left left.json --right right.json --root PROJECT`
returns a `ladon-real-bound-comparison-bundle-v1` wrapper. Its native
`proofir.contract-analysis` owns the ordered exact contracts and a separate
relation check-run. The bundle includes the original admission plans, terms,
source text and relation receipts needed for replay. Receipt timings use a
lossless hex-float encoding inside ProofIR's integer-only JSON profile. Native
batch validation and SQLite projection check exact evidence owners using the
existing comparison stage; no database migration or change to Nat semantics is
required.

`inspect-real-comparison --input comparison.json` and ordinary `contract inspect`
validate saved evidence offline. Both report `authority:none`, `freshCheck:false`
and unauthenticated historical evidence, even for a wrapper saved by a fresh
producer. `--root PROJECT` additionally checks current identities without running
Lean. `replay-real-comparison --input comparison.json --root PROJECT` rechecks
both admissions and the exact relation with one shared deadline (default and
maximum 600 seconds). A stale implementation requires new planning/admission.
A failed or resource-limited fresh relation remains unresolved and emits no
comparison artifacts. Output files must be new.

The saved native result always remains `recorded-checked` with `authority:none`.
Only the fresh producer/replay wrapper reports fresh execution authority. The
source theorem bodies and prose norm bridge remain unchecked. Persistence covers
comparison; propagation still returns ordinary JSON.


## Checked input-prefix weakening

`check-real-bound-prefix --stronger high.json --weaker low.json --root PROJECT`
replays both source-owned admissions, then checks an implication from the
higher-order input predicate to the lower-order input predicate. The owner order
is explicit: reversing unequal losses remains unresolved. Equality of numeric
losses or an ordering of them is only a candidate filter, never rule evidence.

The supported contexts must agree in predicate, operator, input object, set,
scalar guards, constant scope, interpretation and all other typed parameters.
Only the literal input-order loss and the terminal input-premise type may vary.
The Lean helper rechecks both live source types, aligns their data binders,
omits the original input-proof witness, and rejects retained proof-valued
dependencies. It checks the actual order expressions against the source roles,
re-elaborates the weaker owner's exact admission proof, extracts its OrderPrefix
law, and proves the numeric/order inequality in the kernel. Both named measures
and derivative-prefix admission plans use this same rule path.

Success reports `input-prefix-implies` and `order-prefix-v1` in the separate
`ladon-real-bound-prefix-analysis-v1` wrapper. This establishes the input-predicate
implication only. It does not certify either source theorem body, their full
estimate relationship, or a paper-norm bridge. Failed checking stays unresolved.
The result is ordinary JSON. Use `check-real-bound-prefix-proofir` with the same
ordered arguments to save the freshly checked implication as a native bundle.
Existing persisted equivalence comparisons retain their original closed schema.
The command keeps the shared 600-second maximum deadline and 12 GiB process-tree
memory cap. Source or implementation drift requires new plans/admissions.

The native wrapper is `ladon-real-bound-prefix-bundle-v1`. Its closed analysis
payload uses `analysisKind:real-bound-prefix-v1` within the existing `comparison`
storage stage, preserving stronger/weaker contract order and a separate prefix
check-run. The result remains `input-prefix-implies`, never `equivalent`.
Plans, admission terms, copied source and proof receipts are retained for exact
reconstruction; native batch validation and SQLite verify all evidence owners.

`inspect-real-prefix --input prefix.json` (or ordinary `contract inspect`)
validates history offline and always reports `authority:none`, `freshCheck:false`
and `evidenceAuthentication:not-established`. Optional `--root PROJECT` checks
current source/checker identities without running Lean. Historical inspection
without a root remains available after checker changes.

`replay-real-prefix --input prefix.json --root PROJECT` validates the saved
bundle, then freshly replays both admissions and the exact directional proof
under one shared deadline. A failed fresh proof cannot reuse a saved success;
it stays unresolved and emits no native artifacts. Fresh production and replay
preserve the input-predicate-only scope, source-theorem and paper-bridge limits.
Output paths must be new. The separate coefficient and conditional composition
operations below retain their own proof goals and claim boundaries.

## Native sequences of checked edges

`propagate-real-bounds-proofir` accepts 2 to 128 ordered `--production` paths and
one `--rule` for each adjacent pair. Supported rules are `identity-v1`
(definitional input-predicate equivalence) and `order-prefix-v1` (higher-to-lower
input-predicate implication). Rule names request checks; they are not evidence.

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract propagate-real-bounds-proofir \
  --production high.json --production low.json --production low-alias.json \
  --rule order-prefix-v1 --rule identity-v1 --root PROJECT --output chain.json
```

The operation freshly admits each position once, preserves its exact semantic
owner, and checks every adjacent edge in a separate Lean run. Both edges touching
a middle position retain the same admitted evidence owner. Repeated positions
are allowed, but do not skip checks. One shared maximum of 600 seconds covers the
operation; the fixed 12 GiB worker cap and aggregate 32 MiB input bound remain.
The position count is a structural maximum, not a promise that every sequence
fits these byte and time limits.

The closed `ladon-real-bound-chain-bundle-v1` wrapper contains the existing
single-edge analyses and a native `real-bound-chain-v1` propagation payload.
It retains ordered contract, edge-analysis and check-run references. Native
validation checks every edge and exact middle replay owner. SQLite retains the
contract positions and generic external references; this variant has no
derivation-goal row because it has no separately checked endpoint theorem.
No schema migration is needed.

`inspect-real-chain --input chain.json` (also ordinary `contract inspect`)
validates historical evidence without Lean and reports no fresh authority.
Optional `--root PROJECT` checks current identities. `replay-real-chain --input
chain.json --root PROJECT` rechecks all positions and edges under one deadline.
A failed edge keeps prior checked evidence in an unresolved result and emits no
complete native chain. Deadline expiry is distinguished by phase; it cannot
publish a fresh bundle. Source/checker drift requires new plans and admissions.

These records establish individually checked input-predicate edges. They do not
certify either source theorem body, transfer composition, a paper-norm bridge,
or a separately elaborated endpoint theorem. General derivation graphs and
coefficient/composition rules remain outside this sequence API.

## Pointwise coefficient weakening

`check-real-bound-coefficient --input admitted.json --root PROJECT --output
coefficient.json` freshly admits one source owner and checks a conditional law
over its exact output predicate. For original coefficient `K`, input bound `C`
and a new universally quantified `L`, it proves:

```text
K ≤ L → 0 ≤ C → J y S n (actualProduct K C) → J y S n (L * C)
```

The predicate, its parameters, output object, set and order remain fixed. If
any of them depends on `K`, it retains that original `K`. The rule does not
substitute `L` into the operator or predicate. It consumes both the admitted
bound-monotonicity law and the scalar equality identifying the actual product
with canonical Real multiplication. The Lean helper supports propositional
equality here; the observation grammar still requires a syntactic `K * C`
application and is not expanded to arbitrary arithmetic.

The generated law retains only original data dependencies, rejects inherited
proof-dependent parameters, and includes explicit ordering and sign guards.
It does not extract, compare or uniformize existential witnesses, use the source
theorem body, or certify a paper-norm interpretation.

Success returns `output-coefficient-implies`, `coefficient-mono-v1` and
`scope:pointwise-fixed-output-context` in ordinary JSON with schema
`ladon-real-bound-coefficient-analysis-v1`. Its proof receipts undergo exact
owner, term, goal, capture, current checker and resource checks. A shared
`--timeout-seconds` budget of at most 600 seconds covers admission and rule
checking; workers retain the 12 GiB process-tree cap. Timeouts preserve available
evidence but return unresolved with no authority. An incomplete admission stops
before the coefficient worker and retains its process receipt and diagnostic,
including the instruction to report memory exhaustion to the user.
Source/checker drift requires
current plans and admissions. Output files must be new.

The ordinary command does not produce a new admitted estimate. Use
`check-real-bound-coefficient-proofir` with the same arguments for native evidence.
Its closed `ladon-real-bound-coefficient-bundle-v1` wrapper contains a separate
`real-bound-coefficient-v1` propagation analysis with one exact admitted owner,
one rule check-run and a reference to the actual checked conditional goal.
SQLite projects that goal and its owner references without a schema migration.

`inspect-real-coefficient --input coefficient.json` (also ordinary `contract
inspect`) validates history offline. It reports `authority:none`,
`freshCheck:false` and `evidenceAuthentication:not-established`. Optional
`--root PROJECT` checks source freshness without executing Lean.
`replay-real-coefficient --input coefficient.json --root PROJECT` freshly checks
the source admission and coefficient law under one shared deadline. A failed
fresh check cannot reuse saved success. Coefficient analyses cannot be inserted
into the identity/prefix chain API.

## Conditional composition from source applications

`compose-real-bounds --left first.json --right second.json --root PROJECT`
freshly admits both inputs, then checks a composition law derived from their
actual source applications. For native evidence, use `compose-real-bounds-proofir`
with the same arguments and a new `--output` path.

The supported route requires the same exact source environment and matching
role/telescope layouts. It shifts the first base order by the second literal
loss, substitutes the first output object and bound into the second input, and
requires the complete middle predicate application to match in Lean. Predicate
parameters, sets, data dependencies, actual scalar products and nonnegative
guards are checked. Unsupported dependent substitutions or retained proof-valued
data remain unresolved. Equal losses alone never establish compatibility.

The result is a **conditional law**: the two source-shaped transfer steps are
explicit premises. With their nonnegative factors `K` and `L`, it derives the
outer transfer with factor `L*K`. The source theorem bodies are not checked;
the operation neither extracts existential witnesses nor infers uniformity.
It reports `scope:conditional-source-shaped-transfer-composition`,
`transferPremises:assumed`, `sourceTheoremProof:not-checked`,
`coefficientUniformity:not-inferred` and `paperNormBridge:unresolved`.

The native `ladon-real-bound-transfer-bundle-v1` wrapper contains a separate
`real-bound-transfer-v1` propagation analysis, both ordered owners and the exact
conditional derivation goal. `inspect-real-transfer --input transfer.json`
(also ordinary inspect) reconstructs historical evidence without fresh authority
or authentication. `replay-real-transfer --input transfer.json --root PROJECT`
rechecks both admissions and the rule. These analyses cannot serve as
input-predicate identity/prefix chain edges.

Each public composition or replay shares a maximum 600-second deadline across
validation, admissions, checking, final source verification and publication.
Workers retain the 12 GiB process-tree cap. Failures preserve available receipts
with unresolved status and no native success bundle. No caching, Nat-rule
fallback, automatic paper-norm bridge or source-theorem certification is added.

## Qualification scope

The [current qualification record](../openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/REPORT.md)
separates shape observations, checked adapter bindings and native predicate/scalar
admissions. Generic fixtures ran before the two informed fixed-loss admissions;
symbolic loss remained unsupported. Negative controls cover changed definitions,
instances and compiled meaning, forged expressions, scalar dictionaries,
placeholders and derivative near-misses.

Use its runtime manifest when reusing these results. An informed-source success
establishes the exercised interpretation capability, not unfamiliar-source
discovery, source-theorem proof checking or a prose norm bridge. A resource stop
is incomplete work and cannot count as a successful semantic rejection.
