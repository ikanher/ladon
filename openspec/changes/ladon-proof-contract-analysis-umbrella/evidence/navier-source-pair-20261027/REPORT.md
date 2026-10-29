# Navier–Stokes source pair and checked specialization

The original excerpt now has independently frozen prose readings, an explicitly
chosen typed interpretation, and a checked connection to the existing formal
theorem. **The parameter mismatch is resolved for the selected parameter-free
comparison.** The formal route still supplies five extra derivatives; applying
it to the four-order reading fails at the input bound. This is known-target
integration evidence, not fresh discovery or a refutation of the paper.

Task 2.1 remains open: the paper-norm interpretation and native Real
production/propagation connection are not complete. The umbrella remains 8/12.
The user explicitly selected this existing excerpt after the earlier
[feasibility pass](../source-pair-feasibility-20261027/REPORT.md). An original
known pair is eligible for development integration; it need not be unfamiliar
to the root. The held-out discovery rules are unchanged.

## Original source and independent reading

The unchanged paper is Lemma 8.6, equation (8.19), pages 95–96, with the fixed
direction from (6.2). Its SHA-256 is
`0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`.
[PAIR.json](PAIR.json) links the canonical original PDF, source excerpt,
existing native formal contract and selected declaration. No source was edited.

Two fresh Luna-medium readers received only the original paper text/PDF and
source-reading assignments. Their first readings were frozen before seeing peer
reports or formal mappings: [primary reading](navier_prose_46/source-reading.md)
and [independent audit](navier_prose_47/source-audit.md), board 1844/1845.
The root already knew this target; the experiment is not blind. The workers'
access boundary is an instructed review boundary, not a filesystem sandbox.

Both readings retain the fixed temporal direction, the unit two-torus, smooth
zero-Haar-mean scalar input, every integer order including zero, and a constant
depending on the order and fixed direction rather than the source function.
They separate the displayed estimate from existence/uniqueness and later
velocity/chart assertions. Neither located an explicit definition of the torus
`C_y^m` norm. The peer challenge retained that ambiguity while noting that common
max/sum and exact-order/all-order conventions can give equivalent estimates on
the zero-mean space with order-dependent constants. This is ordinary mathematical
review, not a new Lean norm-equivalence theorem.

## Authored interpretation and new bridge

The [structured reading](interpretation-record.json) chooses full real Fréchet
derivative prefix bounds on the universal cover as an explicit convention.
It preserves zero mean, periodicity, smoothness, a nonnegative input bound, and
the coefficient chosen before the function and bound. Its input order is `n+4`;
the direction is fixed to temporal. The scalar vocabulary uses complex functions;
the original prose's scalar convention and real-valued restriction remain
qualified. This reading covers the estimate only.

The public `investigation interpret` command produced
[native interpretation artifacts](interpretation-native.json). That command
performs structured lowering and source binding, not truth checking. Separately,
Lean compiled [PaperVocabulary.lean](project/PaperVocabulary.lean), containing the
lowered four-order proposition as a **definition of Prop**, with no axiom or
proof asserting it. This establishes a well-typed chosen interpretation, not
that the interpretation is the paper's unique meaning or that its claim holds.

[ParameterFreeBridge.lean](ParameterFreeBridge.lean) supplies a small checked adapter:

- `eraseParameter` is a linear isometry from `(Fin 0 → ℝ) × Plane` to `Plane`.
- `norm_liftSource` preserves every full iterated Fréchet derivative operator
  norm exactly; `bound_equiv` identifies the two prefix-bound predicates.
- `lift_inverse` is definitional equality between the lifted existing family
  inverse and the same plane Fourier inverse.
- `plane_inverse_five` specializes the existing `inverse_finiteJets` theorem
  through those identities, preserving five-order loss and a coefficient chosen
  before the input function and bound.

This removes the dummy parameter exactly. It does not infer slow-parameter
derivative bounds from torus-only data, define the paper's norm, prove an improved
inverse estimate, or establish existence/uniqueness. Mean zero is preserved in
the source reading and test goals even though the formal bound does not need it.

## Fresh public checks

Both public source-goal checks used an exact copy of the complete original
`NavierStokes/SmoothFamilyTorusInverse.lean` before the adapter and observation
goal. The selected theorem was freshly compiled in this source copy; dependency
libraries were pinned and read without a Lake build. The original checkout and
compiled dependencies were not modified.

| Check | Result | Capture + completion seconds |
| --- | --- | ---: |
| Same reading with five-order input | Completed; independent compiler replay accepted; only the three standard axioms | 86.49 |
| Four-order reading, identical submitted proof term | Rejected: `hb` supplies `n+4`, but the application requires `n+5` | 82.40 |

The two goal files differ only in the selected order-shift declaration. The
[result](BRIDGE-RESULT.json), full capture/completion records, submitted term and
process receipts are retained. CLI exit zero on the rejected completion was
**not** counted as mathematical success; the result's status is `rejected`.
The failure does not refute the four-order proposition or exclude a sharper
formal route.

All Lean experiments shared one 600-second deadline and a 12 GiB process-tree
cap. Their measured process times total **176.27 seconds**, including vocabulary
compilation and the two direct adapter attempts; peak sampled RSS was
**5.117 GiB**. No timeout, memory stop or output stop occurred. The first direct
adapter attempt failed to simplify the zero-dimensional norm and reported
`sorryAx`; it remains a failed attempt. The corrected proof and fresh public
positive replay contain no forbidden axioms. No failed result was relabeled.

The existing native inverse contract also passed public historical inspection
with current source freshness. It retains loss five and `authority: none`,
`freshCheck: false`; this is not a new native semantic admission. The separate
Task 4.1 evidence remains unchanged.

## Persistent finding and review correction

The public observation workflow captured the original source, authored reading,
exact formal sources and remaining obligations. Independent bridge review at
1852/1853 agreed with the narrow proof and interpretation boundaries.

The reviewer's first response labeled the statement `aligned` because the
reading matched the prose. Root challenged this: statement relation and source
fidelity are separate fields. The reviewer corrected the former to `mismatch`
for the selected four-versus-five-order statements, retaining faithful source
reading and unresolved method. Public `ingest` and `reconcile` preserve both
[first response](reviewer/response.json) and
[correction](reviewer/response-correction.json); neither was overwritten.

The [current public report](current-report.json) retains:

- statement relation: `mismatch`, for this selected route and declared convention;
- source fidelity: `faithful`, as an attributed reading with explicit caveats;
- method relation: `unresolved`;
- formal support and mathematical falsity: `not-established`.

The [two-branch historical aggregation](public-report.json) also includes the
pre-correction plan and therefore reports a conflict. It is not the effective
current judgment. Both versions remain available. The observation publication
session's 30-minute clock starts at its actual initialization after source
preparation; it is not the Lean experiment budget or a whole-paper audit clock.
Survey units and method obligations remain pending; no terminal certification
was manufactured.

## Remaining integration work

The next runtime design can now use this pinned pair and checked specialization
instead of searching for an unfamiliar substitute. It needs an attributed Real
prose contract and a way for comparison/propagation to consume checked
specialization and representation-transport evidence without promoting it to
source fidelity or theorem proof. The existing Nat frontier still cannot consume
Real contracts; this packet does not bypass that boundary.

Keep the remaining mathematical obligations explicit: coordinate/full-operator
norm comparison with source-independent constants, the exact torus/scalar
conventions, and a route supporting the four-order estimate if correspondence is
to close. A failed five-order application is useful local evidence, not a proof
that no route exists. Any implementation must remain general across sources.

[VERIFICATION.json](VERIFICATION.json) records 610 unchanged runtime files,
2,670 unchanged protected primary files and 106 unchanged Task 4.1 artifacts.
No Ladon runtime, repository tests, dependencies, cache policy or external source
changed. No full suite, broad paper rerun, commit or push was performed. This is
one known-source development pair; it adds no A/B/C evaluation cases or measured
discovery benefit.

Final independent packet review at board **1860** accepted these scope and
authority boundaries. [REVIEW.jsonl](REVIEW.jsonl) preserves the source readings,
peer challenge, adapter audit, first-response correction and final review.
Reviewers inspected source and receipts; root executed the checks. The exact
resource counts are authoritative in VERIFICATION.json and the process receipts.
