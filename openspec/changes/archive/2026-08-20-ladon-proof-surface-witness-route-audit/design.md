## Context

Pipeline-math demonstrates a useful proof-surface governance pattern: public
theorem statements are frozen as `Theorems.lean` stubs, proof-backed endpoints
are exposed from `Solution.lean`, and `Discharge.lean` contains identity gates
such as `example : @Frozen = @Proof := rfl`. Project-local verifier scripts add
source hash pins, banned-keyword scans, build checks, and `#print axioms`
footprints. Current Ladon sees pieces of this as module fan-in, root closure,
and lexical `sorry` markers, but it cannot distinguish a quarantined frozen spec
stub from a proof-backed endpoint or an undisclosed proof hole.

The existing claim-authority route audit already separates source attachment
from proof authority. This change extends that route-audit surface with a
compact proof-surface witness so Ladon can route review away from spec stubs and
toward proof endpoints, without becoming the Lean verifier.

## Goals / Non-Goals

**Goals:**

- Normalize a compact `proof-surface-witness` artifact into stable rows for
  spec stubs, proof endpoints, no-drift gates, source pins, axiom audits, and
  proof-hole quarantine.
- Join witness rows to claim routes and Ladon declaration/source evidence using
  source hash/range/declaration attachment where available.
- Emit proof-surface route diagnostics for spec-stub overclaims, missing gates,
  missing axiom audits, suspicious axioms, clean endpoints, and frozen spec hubs.
- Keep diagnostics reviewer-facing and explicit that they are authority-route
  evidence only.
- Add portable synthetic fixtures modeled on pipeline-math but independent of
  private or vendored repositories.

**Non-Goals:**

- Ladon does not prove theorem truth, replay proof terms, validate mathematical
  scope, or certify witness adequacy.
- Core Ladon does not run `#print axioms`, `lake build`, or source hash pin
  checks by default.
- The first packet does not require an editor UI, graph database, Rust rewrite,
  or full elaborated dependency engine.
- The witness contract does not import raw ProofIR dialects or pipeline-math
  scripts; it consumes a compact normalized evidence artifact.

## Decisions

1. Consume witness JSON in core; generate witness evidence separately.

   Core Ladon should accept a compact witness input and audit it. Running
   `#print axioms` across arbitrary Lean projects is build-sensitive and can be
   expensive, so witness generation belongs in a project-local verifier or later
   opt-in helper. This keeps normal `ladon --skip-build` behavior fast and
   predictable.

   Alternative considered: make Ladon run full Lean axiom audits by default.
   That would conflate review routing with proof checking, slow ordinary module
   audits, and make failures depend on target repository build state.

2. Model proof-surface rows as route governance, not proof evidence.

   A no-drift gate row means the witness says Lean accepted an identity gate
   between a frozen statement and proof declaration under the quoted tool
   version/build context. An axiom audit row means the witness quotes an axiom
   footprint. Neither row lets Ladon decide theorem truth.

   Alternative considered: mark clean endpoints as `lean_proved` directly.
   That would overclaim Ladon's role and blur Lean-owned proof status with
   Ladon-owned attachment/route diagnostics.

3. Integrate with claim-authority audit instead of building a parallel product.

   Claim routes already track claimed status, claimed authority, endpoint scope,
   theorem surfaces, required evidence, external evidence, and nonclaims. The
   proof-surface witness should add endpoint authority context to those routes,
   producing diagnostics under a `ladon.proof_surface.*` namespace.

   Alternative considered: keep proof-surface witness as a standalone report
   only. That would make it harder to catch the practical failure: a public
   claim citing a spec stub or endpoint without gate/axiom evidence.

4. Treat `Theorems/Solution/Discharge` as a pattern, not a hard-coded project.

   The witness schema carries roles such as `lean_spec_stub`,
   `lean_proof_endpoint`, and `lean_no_drift_gate`. Ladon may provide discovery
   hints for conventional module names, but diagnostics should be driven by
   witness rows and configurable role metadata rather than hard-coded package
   names.

   Alternative considered: special-case `Theorems.lean`, `Solution.lean`, and
   `Discharge.lean` in core. That would work for pipeline-math but fail the
   generality requirement for Ladon.

5. Preserve source attachment confidence separately from route authority.

   Witness rows can carry declaration names, module names, source paths, ranges,
   content hashes, tool versions, and generated-at timestamps. Ladon should
   prefer exact source hash/range joins, then declaration/module joins, then
   weak name-only attachment. Weak attachment can still route review, but it
   must not satisfy high-confidence endpoint evidence.

   Alternative considered: accept name-only witness rows as enough to clear
   proof-surface diagnostics. That would create false confidence for renamed or
   stale theorem endpoints.

## Risks / Trade-offs

- [Risk] Witness producers drift in field names. -> Mitigation: normalize a
  small compact schema, preserve unknown fields under quoted metadata, and emit
  malformed/unsupported witness diagnostics instead of fabricating authority.
- [Risk] Users treat `clean_endpoint` as a theorem-truth statement. ->
  Mitigation: mark rows as route-governance evidence and include trust-rule text
  in reports.
- [Risk] Missing witness input makes reports noisier. -> Mitigation: only emit
  missing witness diagnostics when a claim route asks for proof-surface
  authority or when an explicit witness audit input is supplied.
- [Risk] Pipeline-math fixtures overfit a single layout. -> Mitigation: create
  synthetic fixtures with role metadata and at least one nonstandard module name
  while preserving the same governance pattern.
- [Risk] Axiom allowlists differ by project. -> Mitigation: make allowed and
  suspicious axioms witness/config fields; use conservative defaults only for
  diagnostics, not pass/fail proof claims.

## Migration Plan

1. Add proof-surface witness fixtures and schema normalization tests.
2. Add a pure proof-surface audit module or extend claim-authority audit with
   proof-surface rows.
3. Wire normalized witness metadata into ProofIR/bridge input and reviewer
   output without changing existing bridge reports when no witness is supplied.
4. Add atlas/workflow summaries and benchmark oracles for the new diagnostics.
5. Document the trust boundary and provide a pipeline-math-style witness example.

The change is additive. Existing ProofIR bridge indexes and route-audit reports
remain valid when the witness section is absent.

## Open Questions

- Should proof-surface witness input be a standalone CLI flag, embedded in
  ProofIR bridge indexes, or both?
- Which default axiom labels should be classified as allowed, suspicious, or
  unknown?
- Should witness generation live in Ladon as an opt-in helper, in Quux, or in
  project-local verifier scripts?
- How much conventional module-role discovery should Ladon perform when no
  witness is supplied?
