# Design

## Context

See proposal.md. Existing native interpretation artifacts already bind the
original span, authored AST, symbol map and lowered proposition. The Nat prose
producer additionally calls `validate_contract`, which requires `norm-scale-v1`.
The extracted `real-bound-v1` record instead owns Lean declaration observations
and two historical admission checks. Reusing either unchanged cannot produce
an authored Real semantic contract.

The typed Real recognizer currently requires four predicate arguments
(function, set, order, bound), direct builtin order addition and Real product.
The selected interpretation uses three predicate arguments and named scalar
operations. The [feasibility evidence](evidence/proposition-feasibility-20261027/REPORT.md)
is the implementation starting point; it is not a released producer.

## Goals / Non-Goals

**Goals:** a bounded typed route from an authored interpretation to an exact,
qualified Real connection. Preserve original statements and all evidence owners.

**Non-Goals:** automatic NL parsing, arbitrary theorem synthesis, generic AND/OR
frontiers, symbolic loss solving, whole-paper analysis, removing norm ambiguity,
changing historical schemas or asserting a source proposition as a theorem.

## Decisions

### Reuse interpretation ownership; elaborate its proposition value

Use the existing source-map/interpretation pair. A new closed observation wrapper
records attribution, the exact original formula and lowering profile, selected
context and implementation identities, process outcome and typed proposition.
No new duplicate source-map format is needed. The provisional command is
`investigation contract observe-prose-bound --interpretation RECORD --root ROOT
--context REQUEST`; context includes the selected source/module and exact scope.
The implemented CLI must freeze these arguments before acceptance tests.

Elaborate the lowered formula as a value of type Prop in the selected source
context, checking that type explicitly. A local generated definition can hold
that value, with source ranges and generated/original ownership distinguished.
Do not produce an axiom or a theorem with `sorry`; do not read the type `Prop`
of the definition as the estimate itself. The scratch observer demonstrates the
mechanism but lacks the production request validator, custody, structured error
contract and finite renderer limits; it must not be shipped unchanged.

### Observe global bounds explicitly

Extend recognition via a separately versioned profile with global versus
set-indexed scope, not a nullable patch to `real-bound-v1`. The global form is
`J f (n+d) C -> J (A f) n (K*C)`; the set-indexed form retains its actual set
binder. Both preserve the complete telescope and coefficient permission order.
A missing set is semantically meaningful. Synthetic Unit/universal-set adapters
are explicit Lean bridges with owners and check evidence, never source rewrites.

Keep the old recognizer and old payload validation unchanged. Shared extraction
logic may be factored only under regression checks and new implementation
identities. Do not inspect theorem names or recognize specific derivative losses.

### Check local aliases before abstracting them

Typed syntax can preserve `shift n` without knowing its offset. Derive a literal
shift or canonical product only by a bounded fresh Lean equivalence check at the
exact expression and context. Record both original and canonical expressions
and the equivalence owner. Avoid whole-statement unfolding, which would destroy
predicate identity or expand full analytic definitions. Unsupported aliases and
symbolic losses remain residuals; they are not assigned guessed numeric values.

### Separate authoring, admission and connection

A new authored record refers to the exact interpretation and typed observation;
its features have their formula origins and unresolved/admitted states. An
extracted record cannot be fabricated from it. New native profile dispatch must
be inventoried across envelope validation, batch ownership, SQLite, report,
inspection, replay and older semantic consumers before activating the record.

Connection consumes two exact propositions and explicit bridge terms. Fresh
checks must validate any local specialization, predicate/norm bridge, constant
change and final implication, keeping all assumptions. Existing zero-parameter
and coordinate-norm lemmas are test inputs, not runtime built-ins. Order-dependent
multipliers remain typed expressions and quantified where the original theorem
permits them; do not flatten them into a scalar metadata field. Saved checks
remain history, and inspected equality of syntax alone confers no proof authority.

A rejected four-order application is a selected-route gap. A later different
four-order proof could establish the endpoint without validating the original
route; both dimensions remain reportable independently.

## Risks / Trade-offs

- A wrapper may succeed while its consuming grammar still rejects the pair →
  test the exact elaborated reading and unrelated grammar controls first. The
  initial selected reading fails the existing bound-predicate grammar; this
  stops wrapper-only expansion and motivates the explicit global variant.
- Local alias normalization may erase relevant context → retain exact original
  expressions and require checked equivalence rather than text substitution.
- A source-context declaration may be confused with a proved theorem → observe
  only its Prop value, reject non-Prop values, and test theorem/axiom inputs as
  negative controls for this particular value-observation path.
- New profile consumers may silently grant old authority → separate versioned
  dispatch and test every direct persistence/report/replay consumer before use.
- This can become another broad analysis framework → stop at one exact checked
  connection and its generic controls. General graph propagation remains separate.

The feasibility experiment shares one 600-second absolute deadline, 12 GiB RSS
and 8 MiB output allowance. Preserve all failed attempts and resource stops.
Production tests must additionally exercise bounded rendering, cancellation and
source/context mutation; scratch success is insufficient for runtime activation.

## Migration Plan

Keep all old identities and validators. Add new formats and explicit unsupported
paths first, then opt-in production/connection commands. Rollback removes new
command dispatch while retaining stored artifacts as historical data. No database
rewrite, dependency upgrade, automatic source repair or old-record relabeling.

### Bound aggregate connection-job transport separately

The internal connection job uses a separately versioned canonical JSON DAG,
with opaque string values and no inspection of nested authored-history chunks.
The exact informed formal/authored pair exceeds 8 MiB as ordinary JSON but fits
below 8 MiB in this generic representation. Wire size remains capped at 8 MiB;
expanded canonical ASCII JSON is capped at 32 MiB, matching the existing bounded
aggregate-job convention. This is an in-memory aggregate footprint, not a new
native artifact allowance or a process-memory limit. Existing artifact, string,
scalar, process RSS and output limits keep their meanings.

The profile additionally bounds depth (272), per-string/key UTF-8 bytes (1 MiB),
unique DAG nodes (100,000), edges (500,000) and expanded value occurrences
(1,000,000). Callers may narrow these limits. Encoder identity traversal and
bottom-up metrics reject cycles and over-expanding shared Python structures
before expanded serialization. Decoder validates the bounded wire, closed
schema, strict backward references, unique canonical postorder nodes, reachability
and bottom-up expanded metrics before allocating a value tree. Expanded digest
verification streams canonical tokens before fresh-container materialization;
repeated references never alias distinct mutable decoded owners.

This transport grants no semantic authority. Original native envelopes, owners,
source freshness, imports and admissions still require their existing validators.
It adds no CLI or persistence schema. Some valid aggregate jobs will exceed the
wire cap even after interning; they must fail explicitly rather than be truncated
or trigger an automatic cap increase.
