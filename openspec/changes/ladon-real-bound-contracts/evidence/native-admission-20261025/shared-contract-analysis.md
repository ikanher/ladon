# Bounded contract analysis and countermodel refinement

Read this for `ladon investigation contract` operations. Use the same selected
Ladon runtime throughout the audit. For a task that requires current development
code, invoke the actual checkout with its `src` on `PYTHONPATH` and record its
runtime identity, as described in the main skill. An installed release version
alone does not establish which capabilities or bytes are running.

Check `investigation contract --help` and the chosen subcommand's help before
building a request. Current operational guides live in the selected checkout's
`docs/`; do not assume that the analyzed project contains them. Start from the
prose's exact source span, domain and intermediate claim before selecting formal
matches. A missing source-to-formal adapter is an unresolved obligation.

## Choose a route

| Task | Public operation and guide |
| --- | --- |
| Snapshot an authored prose contract or selected formal declaration | `contract produce --channel prose` or `--channel formal`, then `contract inspect`; consult `docs/PROOF_CONTRACTS.md`. |
| Propagate conditional contracts over an authored derivation | `contract propagate`; consult `docs/PROOF_CONTRACTS.md`. |
| Generate and check localized obligations | `contract obligations`, `check-obligations`, and the relevant context/route bridge commands; consult `docs/PROOF_CONTRACTS.md`. |
| Check a distinguishing application | `probe-profile`, `probe`, `check-probe`, `review-probe`; consult `docs/PROOF_CONTRACTS.md` and `docs/RATIONAL_BRANCH_PROBES.md` for the separate rational branch route. |
| Run a bounded resumable sequence | `contract audit --input PLAN.json --output-dir NEW_RUN`; consult `docs/PROOF_CONTRACTS.md`. |
| Check a supplied abstract witness and its proposed refinements | `contract refine`, saved `contract inspect`, and `investigation report --refinement`; consult `docs/CONTRACT_REFINEMENT.md`. |

Confirm the guide paths in the selected checkout. The commands have different
closed request schemas and source/context inputs; use their own guides rather
than inventing a common JSON format. Planning and propagation do not discharge
the resulting obligations. Inspect exact generated goals, assumptions, source
bindings and trust coverage before supplying proof terms. Preserve alternative
routes and unsupported populations.

## Admit only the recognized formal fragment

Formal production is intentionally narrower than Lean's type language. In the
historical norm-scale-v1 estimate profile, the statement telescope is limited to
eight binders over `Nat`, and the conclusion must match the built-in Nat
inequality and estimate shapes documented in `docs/PROOF_CONTRACTS.md`. A
`telescope-limit`, `unsupported-domain`, or other residual means no complete
contract was produced. Do not remove binders, hypotheses, or domain conditions
to fit the profile. Raising a structural bound alone is not a semantic
extension: first establish that every type, assumption, carrier, and operation
has a checked representation in the target profile. Otherwise retain the
formal snapshot as unsupported and leave propagation unattempted.

For a prose/formal pair, freeze and hash the source reading before selecting or
inspecting the formal counterpart. Then produce the formal snapshot from the
actual Lean declaration and inspect its exact residuals and source identity. A
successful structural match or realizable frontier is conditional evidence;
it does not establish that the source reading faithfully represents the
paper. Obtain independent fidelity review and preserve any unsupported
components separately.

The audit driver writes an immutable run directory. Resume from its saved
identities and original deadline; a new invocation does not authorize a reset.
Retain completed stages and unresolved work. Memory, timeout and output stops
are operational results, and must not become mathematical counterexamples.

## Typed Real-bound observations and checked adapters

For a typed Real estimate outside the historical Nat profile, retain the full
formal snapshot and consult docs/REAL_BOUND_CONTRACTS.md in the selected Ladon
checkout. Check its subcommand help: the installed version number alone does not
establish that these development commands are present.

Use contract observe-bound to capture exact predicate/operator applications,
typed binder scope, guards and literal loss. Observe/inspect returns exit 2 while
mathematical admission is unresolved. Do not trim typeclass binders, quantified
point domains or regularity premises to fit a recognized profile.

For a proposed measure, plan-bound-prefix and check-bound-prefix check the exact
observed predicate application against the generic prefix family. For a full
joint derivative bound on f:P*Y->Z, plan-derivative-prefix and
check-derivative-prefix use the fixed measure given by the norm of
iteratedFDeriv Real j f(p,y). Its domains and instances come from live source
expressions; it quantifies over all j<=n, p in S and y:Y. Parameter-only,
directional or point-restricted bounds need their own checked bridge.

Both check commands consume a plan plus a proof JSON containing exactly a term
field, and perform fresh capture, completion, compiler replay and axiom checks.
A checked-binding and exit 0 establish those predicate laws. The derivative
route additionally reports derivativeAdmission:checked. They retain
admission:unresolved and contract:null; the paper-norm bridge stays unresolved.
These outputs do not themselves admit native contracts. Use plan-real-bound on
that exact binding plan, then admit-real-bound with a proofs JSON mapping both
predicate-admission and scalar-semantics to Lean terms. It freshly checks the
predicate and equality of the actual guards/product with canonical Real scalars.
A successful run returns four native artifacts; unresolved runs return none.
Planning exits 2; successful admission exits 0. It does not certify the original
theorem proof body or the prose norm bridge. Real comparison/propagation and old
Nat obligation/probe consumers remain unsupported.

Use inspect-real-bound or report-real-bound on the production wrapper for
validated-historical evidence with authority:none and freshCheck:false. The
optional root verifies current source/environment/helper/checker identity but
does not replay Lean. Without it, freshness is unchecked. replay-real-bound
requires current identities and executes both checks again; stale implementations
require a new plan. Saved success flags and content hashes are not authenticated
proof authority. Admission/replay default to a shared 600-second deadline,
60-second compiler phases and 12 GiB RSS. Preserve original resource-stop results.
Do not turn a predicate/scalar admission into a whole-exposition claim.

## Refine one witness without rewriting its claim

`contract refine` accepts a caller-authored rational goal, its original finding
and witness, a selected formal interpretation and proof term, and source-cited
or repair predicates. It validates that the original assignment satisfies every
premise and falsifies the conclusion. The current original-context lift profile
is one rational variable interpreted through a natural-number cast. General
analytic/function-space realization remains unsupported.

A fresh successful lift may establish a counterexample to the selected formal
claim, or prove that the abstract witness has no realization in that selected
interpretation. Failure to find a realization does not establish spuriousness.
Even a successful formal mapping leaves prose fidelity unverified. Do not
label the original exposition false from a rational assignment alone.

Source-cited predicates and proposed repairs produce separate sibling branches.
Keep the original finding, witness and goal intact. A citation validates the
span's bytes, not the fidelity of its encoded predicate. A repair that adds an
assumption absent from the passage is not support for the original claim.
`outside-assumptions` means only that the old assignment violates the new
premises; it proves no universal statement. This CLI checks one supplied
witness and does not discover predicates, proof terms or new witness families.

The request schema is `ladon-proof-contract-refinement-request-v1`; its output
schema is `ladon-proof-contract-refinement-workflow-v1`. These are separate from
native ProofIR contract-analysis envelopes. Confirm the archived schema before
using it as current input; do not migrate historical JSON by guessing fields.

```bash
ladon investigation contract refine --input request.json --root SOURCE_ROOT \
  --output refinement.json
ladon investigation contract inspect --input refinement.json --root SOURCE_ROOT \
  --output inspection.json
ladon investigation report --plan observed.json --root SOURCE_ROOT \
  --refinement refinement.json --output report.json
```

Use new output files. The refinement command shares a finite deadline and
defaults to 120 seconds and 12 GiB RSS, retaining the lift owner's stricter
per-attempt caps. `--deadline-monotonic` carries an existing absolute clock on
the same machine/boot. Incomplete and unsupported results exit 2; retain the
JSON and stop dependent checks on resource exhaustion. A fresh retry is an
explicit new attempt under the authorized budget, never an automatic reset.

## Read saved evidence at its actual authority

Refinement inspection recomputes rational checks and verifies current source
hashes and quotations. It returns `validated-historical`, `leanReplayed: false`
and `liftAuthority: "unverified-saved-result"`. Nested saved positive flags are
claims in the historical record, not fresh Lean results or authenticated proof
provenance. A content digest is not a signature. Obtain fresh lift authority
through a new `refine` attempt on the original request.

Reports accept at most four refinement supplements. Their original finding IDs
must match existing report findings; an observation uses its `observationId`,
not the author's label. Report v3 preserves both records, branches and pending
work, adding `refinementEvidence` and finding `refinementIds`. Association is
attributed by ID only and does not certify semantic correspondence. These
supplements do not change plans, close reviews or enter finalization receipts.
The native observation attachment route has its own validation and receipt
contract; do not substitute a refinement workflow artifact for that envelope.

For blind evaluation, read generic schemas and help without consulting
target-specific examples, prior findings or reference answers. Constructed
examples and known-target replays establish their own checked scope; they do
not establish unfamiliar-source fault detection or whole-paper certification.
