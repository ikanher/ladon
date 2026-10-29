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

Report shape observations, checked adapter bindings and native admissions with
separate denominators. The qualification linked from that guide records its
runtime and input identities; verify those before reusing results. Informed-source
success does not establish unfamiliar-source detection. Resource stops remain
incomplete and cannot count as successful semantic rejections.

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
theorem proof body or the prose norm bridge. Old Nat obligation/probe consumers
remain unsupported for the Real profile.

Use inspect-real-bound or report-real-bound on the production wrapper for
validated-historical evidence with authority:none and freshCheck:false. The
optional root verifies current source/environment/helper/checker identity but
does not replay Lean. Without it, freshness is unchecked. replay-real-bound
requires current identities and executes both checks again; stale implementations
require a new plan. Saved success flags and content hashes are not authenticated
proof authority. Admission/replay default to a shared 600-second deadline,
60-second compiler phases and 12 GiB RSS. Preserve original resource-stop results.
Do not turn a predicate/scalar admission into a whole-exposition claim.


Use compare-real-bounds with two saved production wrappers and a source root for
same-source definitional predicate equivalence. Typed context equality is only a
precondition: a separate Lean check derives the exact input-predicate Iff from
both live declarations. Non-definitional relations remain unresolved.
propagate-real-bound-identity replays every input and checks each adjacent edge;
it supports no non-identity rule and returns ordinary JSON.

Use compare-real-bounds-proofir with --left, --right and --root to create a closed
native comparison bundle. It retains exact ordered contract owners, a separate
relation check-run, and bounded replay inputs. Native validation and SQLite use
the existing comparison stage. inspect-real-comparison --input (also ordinary
contract inspect) always reports historical-only authority; an optional --root
checks current identities without running Lean. replay-real-comparison --input
--root performs both admissions and the relation again under one shared deadline
(default and maximum 600 seconds, fixed 12 GiB RSS). A limited fresh result stays
unresolved and emits no native comparison artifacts. Stale implementations need
new plans/admissions. Stored native results never acquire fresh authority from a
saved wrapper. Source theorem bodies and the paper-norm bridge remain separate.


`check-real-bound-prefix --stronger high.json --weaker low.json --root PROJECT`
checks an explicit higher-to-lower input-prefix implication after fresh admission
replay. All other typed context, endpoints, guards and constant scope must agree.
Lean rechecks the live source order expressions, re-elaborates the exact admission
proof and applies its OrderPrefix law with a checked inequality. Reversing an
unequal pair stays unresolved. The result is ordinary JSON with rule
`order-prefix-v1`; it proves only the input-predicate implication, not either
source theorem body or a paper-norm bridge. The same shared 600-second deadline
and 12 GiB cap apply.

Use `check-real-bound-prefix-proofir` with the same stronger/weaker arguments to
persist the checked directional edge. Its native payload retains exact ordered
owners and a separate proof check-run; it never labels an implication equivalent.
`inspect-real-prefix --input` (or ordinary inspect) validates historical evidence
without fresh authority; optional `--root` checks identities without Lean.
`replay-real-prefix --input ... --root ...` freshly replays both admissions and
the directional proof under one deadline. Saved success cannot override a failed
fresh check. Historical inspection survives checker drift; fresh reuse requires
current plans/admissions. Conditional transfer composition is a separate route below.

`check-real-bound-coefficient --input admitted.json --root PROJECT --output NEW`
freshly replays one admission and checks pointwise output weakening from the
actual source product to `L*C`, conditional on `K ≤ L` and `0 ≤ C`. It retains
the exact predicate parameters, output object, set and order, including any
dependence on the original `K`. Both predicate admission and scalar equality
proofs are re-elaborated. Never infer a uniform coefficient or a source theorem
from this law. The result is ordinary JSON, with
`scope:pointwise-fixed-output-context`. Use `check-real-bound-coefficient-proofir`
for native evidence, `inspect-real-coefficient --input` for history and
`replay-real-coefficient --input ... --root ...` for fresh checking. There is no
coefficient edge support in the sequence API. One shared maximum 600-second deadline and
the 12 GiB worker cap apply; unresolved checks have no authority. Saved receipts
do not replace a new execution, and source/checker drift requires current inputs.

`compose-real-bounds --left ... --right ... --root PROJECT` checks a conditional
composition law derived from two compatible source applications. The `-proofir`
variant persists the ordered owners and actual conditional goal; use
`inspect-real-transfer` for history and `replay-real-transfer` for fresh checking.
The route requires matching source context and telescope roles, checks exact
middle predicate/object/set/order/bound applications in Lean, preserves data
dependencies and consumes the actual scalar equalities and sign guards.
Unsupported dependent substitutions stay unresolved. Both transfer steps remain
explicit assumptions: report `transferPremises:assumed`, source theorem proof
unchecked, coefficient uniformity not inferred and paper-norm bridge unresolved.
Do not describe this as a new admitted estimate or use it as an identity/prefix
chain edge. Each public operation shares the same 600-second/12 GiB bounds;
saved evidence has no fresh authority or authentication.

`propagate-real-bounds-proofir` takes ordered `--production` paths and one `--rule`
(`identity-v1` or `order-prefix-v1`) for each adjacent pair. It admits every
position once and independently checks each edge; adjacent edges retain the
exact same middle evidence owner. The native chain preserves these per-edge
proofs, not a separately elaborated endpoint theorem or transfer-composition
proof. Inputs are bounded to 2–128 positions and 32 MiB, with one shared maximum
600-second deadline and fixed 12 GiB worker cap. Those limits may admit fewer
positions in practice. Repeated positions do not skip checks.

`inspect-real-chain --input` (or ordinary inspect) reports historical-only
authority; optional `--root` checks current identities without Lean.
`replay-real-chain --input ... --root ...` rechecks all admissions and edges.
A failed edge preserves earlier checked evidence in an unresolved result;
deadline expiry records its phase. Neither publishes a complete native chain.
Keep the source-theorem and paper-norm bridge obligations separate.

## Attributed Real prose readings and exact connections

For these opt-in development operations, read `docs/REAL_PROSE_NATIVE.md` in the
selected Ladon checkout and its observation/recognition guides. Confirm command
availability with help; use that checkout rather than an older pip executable.
`observe-prose-bound` elaborates the attributed proposition value without proving
it. `recognize-prose-bound` preserves global or explicit set scope, every typed
binder/guard and coefficient dependency; checked aliases retain their owners.
`produce-real-prose-bound` creates the separately versioned authored native
record with unresolved admission and unreviewed fidelity. Existing extracted
Real and Nat consumers keep their own meanings and may reject this profile.

`connect-real-prose-bound` needs `--formal`, `--authored`, `--formal-root`,
`--prose-root` and `--request`. The request contains schema
`ladon-real-prose-connection-request-v1`, an isolated Lean `term` and ordered
`premises` naming distinct local Prop definitions. The initial adapter requires
the authored source context to exactly prefix-extend the formal source and both
pinned Lean executables to agree. A successful connection proves only
`formalType → premise₁ → … → authoredValue`. Retain every formal premise,
coefficient permission, norm bridge and extra condition; source theorem proof
and prose fidelity remain separate.

New `ladon-real-prose-connection-v2` results require a trusted independent
target commitment in the original captured scope/import environment, synchronous
kernel checking of the submitted term, completion and independent replay.
Legacy v1 history lacks target-owner binding. `report-real-prose-connection`
and generic inspection grant no fresh authority or evidence authentication.
`replay-real-prose-connection` needs the saved snapshot, both original input
records and both roots; newer equivalent records cannot silently replace those
inputs. Replay shares the configured absolute deadline and RSS/output caps.
Connection transport preserves canonical v1 bytes when they fit and uses a
separately versioned bounded ASCII/zlib envelope only when needed. Keep the
existing 8 MiB wire, 32 MiB expanded, graph/string and native artifact limits;
decompression is bounded before DAG validation. An unavailable aggregate result
is an operational stop: retain inputs and the failed cap, report it, and stop
dependent checks without truncation or raised limits. Saved compressed-output
digest reproduction is currently tied to the local zlib implementation, so
cross-version history validation is not established. Consult the guide for
current qualification blockers.
An unresolved route is not mathematical falsity; a conditional connection is not
NL fidelity, unconditional admission, whole-proof certification or discovery.
Count observations, formal admissions, conditional connections and unresolved
routes separately, and check the guide's current qualification evidence before
claiming general support.

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
