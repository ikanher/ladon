## Context

Ladon currently has strong clean-core review signals: text-backed module DAGs,
repo-local architecture policies, generated/facade metadata, source-pattern
packs, declaration/source evidence, ProofIR joins, claim-authority route audit,
and proof-surface witness route audit. The recent literature review adds five
directions that fit Ladon's role as a Lean review assistant:

- Lean's module system makes public/private import and declaration boundaries
  central to scalability and library design.
- Lean/Lake already own import minimization and linting evidence; Ladon should
  route and compare that evidence rather than invent a competing authority.
- The proof-surface witness audit already covers claim/trust diagnostics; the
  missing piece is an opt-in verifier handoff that produces better witness rows.
- InfoTree/LeanDojo/Pantograph-style elaborated data is useful for proof-shape
  review only if authority levels stay explicit.
- General refactoring guidance says smells are indicators, so Ladon findings
  should lead to small, source-evidenced refactoring prescriptions rather than
  ungrounded quality scores.

## Goals / Non-Goals

**Goals:**

- Define the next Lean-specific review-intelligence umbrella without duplicating
  already-completed proof-surface/claim-authority work.
- Make module-system readiness and import diet first-class review surfaces.
- Specify how optional Lean-owned verifier outputs flow into existing route
  audits.
- Stage proof x-ray enrichment behind explicit elaborated-backend metadata.
- Convert findings into prioritized, evidence-backed refactoring prescriptions.

**Non-Goals:**

- Do not make Ladon a proof checker, theorem prover, import minimizer, or Lake
  replacement.
- Do not run expensive Lean elaboration, `lake shake`, or `#print axioms` by
  default.
- Do not infer proof dependencies from parser candidates.
- Do not add project-specific rules to analyzer code.
- Do not create automatic refactoring rewrites in this umbrella.

## Decisions

1. **Model Lean-owned outputs as optional witnesses.**

   Ladon should consume import-diet and proof-surface/verifier witness artifacts
   with tool name, version, command, source hash, and confidence fields. This
   keeps Lean/Lake/project scripts authoritative for build-sensitive facts while
   still making Ladon the review router.

   Alternative considered: have Ladon directly run all Lean checks by default.
   Rejected because large Lean projects vary in build cost, toolchain state,
   cache availability, and verifier conventions.

2. **Separate module path, namespace, and public API evidence.**

   Lean source paths determine import names, while namespaces are orthogonal to
   modules. Module-readiness analysis should therefore report path/module
   topology, namespace declarations, facade shape, public/private hints, and
   module-system witness rows separately.

   Alternative considered: treat namespace and module alignment as mandatory.
   Rejected because Lean permits deliberate cross-namespace declarations.

3. **Treat trust audit as existing and extend only the handoff.**

   The proof-surface witness route audit already emits missing gate, missing
   axiom, suspicious axiom, spec-stub authority, clean endpoint, and frozen hub
   diagnostics. This umbrella should not redefine those diagnostics. It should
   define how optional verifier scripts can generate richer witness rows and how
   other workflows can surface route-evidence completeness.

   Alternative considered: create a second trust-audit subsystem. Rejected to
   avoid duplicated authority rules and divergent reviewer output.

4. **Proof x-ray rows require authority labels.**

   Every tactic skeleton, proof-state shape, premise, axiom/sorry/unsafe
   footprint, or dependency row must identify whether it is parser-observed,
   Lean-elaborated, external-tool quoted, or unknown. Reviewer cards may rank
   proof-shape pressure, but they must not promote those rows to theorem truth.

   Alternative considered: fold x-ray rows into the declaration graph directly.
   Rejected because parser references and elaborated proof metadata have
   different authority and false-positive boundaries.

5. **Prescriptions are review actions, not automatic edits.**

   A prescription should say which refactor direction is plausible and why:
   extract common lower layer, move bridge glue, split large owner, promote a
   facade, demote implementation imports, clean generator output, run import
   diet, or add missing witness evidence. It should include source evidence,
   confidence, and non-claim wording.

   Alternative considered: emit a single maintainability score. Rejected because
   composite scores hide the evidence that maintainers need to review.

## Risks / Trade-offs

- **Witness drift**: external witness formats may change. Mitigation: normalize
  compact schemas, preserve unknown fields as quoted metadata, and emit
  malformed/unsupported diagnostics instead of failing hard.
- **False confidence from Lean-adjacent evidence**: source hashes, import
  minimization, or axiom audits may be read as proof truth. Mitigation: repeat
  trust-boundary text in schemas, reports, and reviewer cards.
- **Noise in module-readiness output**: namespace/module drift can be
  intentional. Mitigation: classify as review pressure, allow policy suppressions
  or explicit facade/bridge/common roles, and benchmark positive/negative
  fixtures.
- **Expensive elaborated extraction**: proof x-ray can be slow on large repos.
  Mitigation: keep it opt-in, cacheable, root-scoped, and absent-safe.
- **Prescription overreach**: a suggested refactor can be wrong without domain
  context. Mitigation: attach evidence, confidence, and alternatives; never
  auto-rewrite from this umbrella.
