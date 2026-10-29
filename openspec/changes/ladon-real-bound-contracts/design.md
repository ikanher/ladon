# Design

## Context

See proposal.md. Existing `proof_contract_recognition` and `proof_contracts` implement Nat estimates, while the Lean worker already preserves full typed expressions. `PROFILE_DIGEST` is consumed by snapshots, native payloads, comparison, propagation, obligations and probes. Changing its meaning in place would invalidate historical semantics. The prior [proposal](../ladon-proof-contract-analysis-umbrella/evidence/jet-contract-frontier-20261025/PROPOSAL.md) supplies informed cases, not a predicate registry or generic admission proof.

## Goals / Non-Goals

**Goals:** reusable typed observation, evidence-bound interpretation and soundly gated Real-bound rules. Generality means arbitrary typed objects and operator/predicate identities within an explicitly supported grammar; it does not mean complete Lean interpretation.

**Non-Goals:** new paper formalization, automatic natural-language semantics, symbolic loss inference, generic tactic search, cache, broad paper audit or held-out benefit claims.

## Decisions

### Stage observation separately from meaning

First implement `investigation contract observe-bound --input FORMAL_SNAPSHOT --root ROOT`. It consumes and verifies an existing formal snapshot, preserving that snapshot unchanged, and emits a closed `ladon-real-bound-observation-v1` wrapper. `inspect` deterministically verifies the wrapper and nested snapshot. The observation profile is `real-bound-shape-v1`; reserve `real-bound-v1` for admitted semantics. No first-stage native `proofir.contract` artifact is manufactured. Existing semantic readers reject the wrapper. This avoids widening the old record validators before their consumers can handle new meaning.

The wrapper records a candidate shape or null, residuals, an unresolved admission, profile and implementation identities, and its own immutable identity. Exit code 2 indicates unresolved/unsupported semantic work even when shape capture succeeded. A raw syntax observation is not source-fidelity review or proof validation.

### Preserve typed scope and logical structure

Walk only supported outer forall/exists structure and the explicit nonnegative-constant conjunction. Retain every typed binder, including proof premises; preserve binder information, lexical scope, guards and exact input/output predicate applications with origins. Rebase expression references to ordered binder IDs for cross-depth equality, retaining nested binders and all typeclass arguments. Recognize the same predicate and its full implicit parameter application on both sides, the same set and input function, and a unary operator application with its exact fixed parameters. Restrict shifts to the direct Nat index or builtin Nat addition with a literal; do not guess symbolic values. Do not search arbitrary subexpressions for convenient estimates under negation or disjunction. Real arithmetic applications remain evidence to be checked, not an admission by name.

Finite work limits cover expression nodes/depth, outer binders and serialized data. Reuse existing 12 GiB process supervision and frozen source snapshots; observation adds no compiler process. Malformed or bounded-out input is distinct from a supported candidate with unresolved semantics.

### Admission is a reusable checked interface

Next add a separately versioned closed Real contract variant. Its predicate application is opaque until Lean checks a bridge to a declared bound family and the actual laws needed by its consumers. The reusable family interface abstracts over object, parameter/index domain and bound predicate; derivative-prefix bounds are one adapter. Generic prefix and Real monotonicity/composition laws are checked independently of a paper. Capture exact source, compiled imports, toolchain, helper, profile, definitions, applications and law receipts. Do not accept caller assertions of admission or a Boolean flag. The first derivative adapter preserves all j≤r, p∈S and point quantifiers, joint derivatives and the norm carrier. A conventional paper C^m interpretation is a separate obligation.

### Derive a fixed joint-derivative measure in Lean

The derivative plan uses a separate closed schema and fixed adapter profile.
Its internal builder derives P, Y and Z from the live predicate object type
P × Y → Z, and synthesizes the necessary real normed-space instances only in
the actual source context. It adds no assumptions for missing instances.
The fixed measure is the norm of iteratedFDeriv Real j f(p,y), preserving the
full joint multilinear-map carrier and all prefix/set/point quantifiers.

The shared live-bound builder performs the same exact statement comparison,
predicate-prefix match, used-context closure and retained-proof rejection for
both named-measure and derivative routes. Refactoring it changes helper/checker
identities and requires fresh direct-consumer replay; old packets remain history.
The public derivative checker returns a separate derivativeAdmission result,
while full contract admission and the paper-norm bridge remain unresolved.

### Compose at explicit endpoints and bounds

The separate LadonRealBoundComposition module uses a pointwise TransferAt,
with input/output objects, common set, both orders, input bound and coefficient
all explicit. Composition requires the exact intermediate predicate, object,
set, order and scaled bound; it retains the product of the actual factors.
Callers may quantify this proposition in their original context. This avoids
inferring uniformity in an object or input bound when a coefficient depends on
it. Prefix and coefficient weakening take the actual predicate laws as premises.
The checked law library remains distinct from native rule activation. Generic
kernel counterexamples to missing sign guards and pointwise-to-uniform exchange
are distinct from controls that merely reject incompatible applications.

### Consumer dispatch before semantic activation

Keep Nat meanings and digest bytes unchanged. Version new closed payloads when references cannot fit historical records. Inventory and gate validators, SQLite/report projection, compare/propagate, obligation/probe consumers and snapshot replay before activation. Unsupported consumers reject the new profile. Direct comparison requires exact compatible contexts and checked laws. Enable only individually proved propagation rules; unresolved bridges remain visible. An opaque dictionary of semantic extensions is not an acceptable shortcut.

### Activate input-prefix weakening separately from equivalence

The explicit `check-real-bound-prefix` operation accepts ordered stronger/weaker
production wrappers. It freshly replays both admissions and allows candidate
contexts to differ only in literal input loss, the input-order expression, and
the terminal input-premise type. Other data types, predicate/operator identities,
sets, guards, constant scope and interpretation must agree. This candidate gate
is insufficient for acceptance.

A separate Lean helper re-observes both full source types, aligns data binders
without the original input-proof witness, and rejects retained proof-valued data
dependencies. It verifies actual orders against the observed base order and
literal shifts. The exact weaker admission proof is re-elaborated in that fresh
context; its OrderPrefix law and a kernel-checked Nat inequality prove the
requested higher-to-lower implication. This is a bounded rule template, not a
generic tactic search. Reverse requests stay unresolved.

The result has its own ordinary-JSON schema and states only an input-predicate
implication. Its native producer records a separate `ladon-real-bound-prefix-bundle-v1`
wrapper and closed `analysisKind:real-bound-prefix-v1` payload in the existing
comparison storage stage. Existing native Iff history remains unchanged. The
payload retains exact ordered owners, the deterministic source-derived request,
proof and admission terms, and a separate prefix check-run. Historical validation
compares the recorded checker with both recorded admissions, not today's checker;
it cannot authenticate saved execution. Fresh replay separately requires current
identities and checks both admissions and the directional proof under one shared
deadline. Coefficient/composition rules and theorem-body implications remain
separate work. Fresh checker identity includes
the new helper, so old runtime packets require new planning/admission for reuse.

### Persist exact ordered predicate edges

The bounded sequence API uses an explicit rule per adjacent pair: identity-v1
or order-prefix-v1. It freshly admits every position once, preserves exact
semantic owners and reuses the same middle admission on both incident edges.
Each relation is checked separately under a shared maximum 600-second deadline.
Failure stops expansion, preserves prior checked edge evidence, and cannot
publish a complete native sequence. Deadline checks cover admission preflight,
per-edge work, final source reads and artifact publication.

A separate closed `real-bound-chain-v1` payload uses the existing propagation
stage, retaining ordered contract, check-run and edge-analysis references. Its
flat bundle reuses existing single-edge native artifacts. Exact shared contract
owners and decoded middle replay productions are checked by native batch
validation. Repeated positions are allowed without skipping admission or edges;
nested chains are not individual-edge evidence. Historical reconstruction is
distinct from fresh checking.

SQLite keeps contract positions and generic external-reference closure. Only
this exact Real variant omits the derivation-goal projection row: no endpoint
theorem was separately elaborated. No schema migration, normalized chain query
API, full graph traversal or transfer-composition proof is introduced. Existing
Nat graph propagation and historical Real single-edge meanings remain unchanged.

### Weaken only the output scalar in its original pointwise context

The separate `check-real-bound-coefficient` operation takes one admitted source
owner. It freshly replays predicate/scalar admission and checks a law over the
exact observed output: for original data and new `L`, `K ≤ L` and `0 ≤ C` imply
that the actual source output bound can be replaced by `L*C`. Predicate
parameters, output object, set and order retain their original values, including
any dependence on `K`. No existential witnesses are extracted or compared.

The Lean helper shares the existing scalar source walker, preserving the old
admission goal. It rejects retained proof-dependent data, specializes the exact
Admission term, and uses the scalar proof's product equality before applying
bound monotonicity. Thus a merely propositional product equality is sufficient
for the helper; the current observation grammar remains unchanged.

The public operation checks exact fresh ownership, current helper identity,
complete proof/compilation receipts and copied source capture. Admission,
checking and final freshness share a maximum 600-second deadline and 12 GiB
worker cap. Expiry retains available evidence with unresolved status and no
authority. Its separate ordinary-JSON result states only a conditional
pointwise output-predicate implication. Native coefficient persistence uses a
separate unary replay codec and `real-bound-coefficient-v1` analysis; the
historical two-owner codec and identity/prefix chain schemas are unchanged.
It owns the exact conditional derivation goal, so the existing propagation
SQLite projection retains a goal row. Recorded checker consistency permits
offline history after helper drift; fresh replay requires current identities.

### Derive conditional composition from the two source applications

The source-bound transfer route re-observes both actual declaration types,
requires the same pinned source context and matching telescope/role layouts,
and derives the intermediate and outer applications in Lean. It shifts the
first order by the second literal loss, substitutes its output object and
actual bound into the second input, and requires the full intermediate
application to be definitionally equal. Data substitutions must preserve
their dependent types; retained proof-valued data dependencies are unsupported.
Predicate parameters and other fixed data are preserved, not guessed equal.

Both source-shaped transfer implications remain explicit premises. Exact
scalar equalities identify the actual products; nonnegative guards justify
the intermediate bound and the generic `TransferAt` composition law. The
conclusion retains the outer observed endpoints and the factor `L*K`. This
is not a proof of either source theorem body, a uniform existential estimate,
or a new admitted contract. This selected bounded route implements the
explicit-endpoint composition decision above without assuming arbitrary
theorem shapes can be interpreted.

`compose-real-bounds[-proofir]` freshly admits both inputs and checks the exact
conditional law. Native `real-bound-transfer-v1` analyses retain two ordered
owners, a separate check-run and the actual derivation goal. Historical
inspection reconstructs all evidence and reports no fresh authority or
authentication; explicit replay rechecks both admissions and the rule under
one deadline. Both native rule formats preserve unresolved paper-norm bridges,
source-theorem nonclaims and unavailable coefficient uniformity. Neither format
is accepted as an input-predicate identity/prefix chain edge. Failed admission,
checking or publication cannot yield a native success artifact; available
receipts and resource diagnostics remain in the unresolved ordinary result.

### Generality and sequencing

Freeze parser controls for unrelated names, losses 0/4/7, changed binder scopes, guards, parameters, sets, polarity, symbolic shifts and resource bounds. Synthetic AST controls establish parsing only. Run actual Lean generic examples from unrelated mathematical families before admitting the original two fixed-loss cases. A genuine observed four-loss statement must preserve four; mean removal remains its own valid endpoint. Definition mutations must fail admission, not merely compare unequal strings. Original baseline is 0/2 admitted fixed-loss contracts; observations and admissions have separate denominators throughout.

## Risks / Trade-offs

- A flexible shape parser is mistaken for semantic extraction → distinct schema/profile, no contracts, mandatory residual and negative consumer tests.
- Typed rebasing loses proof-binder shifts → exact expression paths, nested-binder tests and actual original-source replay.
- Admission laws prove only an abstract interface, not the actual predicate → require source-bound instantiation and negative definition/environment mutations.
- Generic admission is not feasible at acceptable cost → first run one generic adapter + two law checks under a shared 15-minute, 12 GiB budget; stop dependent rule activation if evidence is unavailable, retain observations and named blockers. No automatic limit increase.
- The original 15-minute gate is historical: it completed the generic positive checks but its late placeholder negative timed out. On 2026-10-25 the user authorized continued work without the aggregate budget concern. Exact-application binding uses new explicit per-check deadlines (600 seconds in qualification), retaining the fixed 12 GiB cap and the original incomplete result unchanged.
- Broad dispatch changes break old evidence → pin old profile bytes, use affected native/CLI/snapshot tests and independent audit; no redundant whole-repository or paper run.

## Migration Plan

Add observation command and schema first. Add admitted profile and per-consumer support only after admission tests pass. Keep historical records readable; reject unsupported versions explicitly. Rollback removes new entrypoints without changing stored evidence. Root owns shared edits/builds; use the existing legacy board at `/home/codex/projects/ladon/.codex/state/ultra-proof-contract.sqlite3` with its compatible ultra-code helper. Nothing is pushed.
