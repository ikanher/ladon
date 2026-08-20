## 1. Witness Contract And Fixtures

- [x] 1.1 Add repository-local synthetic proof-surface witness fixtures for clean endpoint, spec-stub overclaim, missing gate, missing axiom audit, suspicious axiom, stale pin, weak attachment, frozen spec hub, and escaped proof-hole cases.
- [x] 1.2 Define the normalized proof-surface witness row model for artifact metadata, spec surfaces, proof endpoints, no-drift gates, axiom audits, source pins, proof-hole policy metadata, and nonclaims.
- [x] 1.3 Implement proof-surface witness normalization as a pure input-boundary module or a clearly separated sibling of ProofIR input normalization.
- [x] 1.4 Add malformed, unsupported-kind, unsupported-version, and non-dictionary input diagnostics that do not fabricate authority.
- [x] 1.5 Preserve unknown witness fields as quoted metadata so producer drift remains inspectable without changing Ladon's trust model.

## 2. Declaration Attachment

- [x] 2.1 Reuse existing declaration/source evidence join precedence for proof-surface witness rows: source hash, source range, source-line anchor, module/declaration, basename warning, unmatched.
- [x] 2.2 Mark weak name-only, line-anchor, stale-hash, and unmatched witness rows as insufficient for high-confidence proof-surface requirements.
- [x] 2.3 Add tests proving stale pins and weak attachment do not clear clean-endpoint classification.

## 3. Route Audit

- [x] 3.1 Extend claim-authority route audit inputs so claim routes can reference proof-surface witness endpoints, spec surfaces, gates, axiom audits, and nonclaims.
- [x] 3.2 Emit `ladon.proof_surface.spec_stub_used_as_authority` when a public claim cites a `lean_spec_stub` as primary proof authority.
- [x] 3.3 Emit `ladon.proof_surface.missing_no_drift_gate` when a claim requires drift protection and no clean gate links its spec surface to its proof endpoint.
- [x] 3.4 Emit `ladon.proof_surface.missing_axiom_audit` when a claim requires an axiom footprint and no accepted axiom audit row exists.
- [x] 3.5 Emit `ladon.proof_surface.suspicious_axiom` for suspicious, unknown, forbidden, or project-disallowed axiom rows.
- [x] 3.6 Expose `ladon.proof_surface.clean_endpoint` only when endpoint attachment, required gates, and required axiom audits are all acceptable.
- [x] 3.7 Expose `ladon.proof_surface.frozen_spec_hub` for intentionally quarantined spec-stub hubs without treating them as proof endpoints.
- [x] 3.8 Add tests proving proof holes outside allowed quarantine are reported and quarantined spec stubs are not treated as authority.

## 4. Bridge, Atlas, And Output

- [x] 4.1 Add CLI or bridge-input plumbing for optional proof-surface witness JSON without changing existing reports when no witness is supplied.
- [x] 4.2 Render proof-surface diagnostics and classifications in bridge reviewer output with claim id, declaration, source attachment, quoted verifier metadata, and nonclaims.
- [x] 4.3 Add atlas/workflow rows for proof-surface diagnostics so review cards can show clean endpoints, missing route evidence, suspicious axioms, and frozen spec hubs.
- [x] 4.4 Add trust-rule text stating that proof-surface witness rows are route-governance evidence only and do not validate theorem truth, proof correctness, witness adequacy, or mathematical scope.

## 5. Benchmark Oracles And Regression Tests

- [x] 5.1 Add explicit expected outcomes for every promoted proof-surface diagnostic and classification in the synthetic fixture suite.
- [x] 5.2 Add regression tests that use nonstandard module names to prove diagnostics are role-driven rather than hard-coded to pipeline-math file names.
- [x] 5.3 Add tests showing proof-surface witness auditing runs without Lean, Quux, pipeline-math, matrix-factorization, or sibling repository checkouts.
- [x] 5.4 Run focused proof-surface, ProofIR bridge, claim authority, atlas workflow, and full repository tests that are available in the local environment.

## 6. Documentation

- [x] 6.1 Document the proof-surface witness schema with a compact JSON example modeled on frozen spec stubs, proof endpoints, no-drift gates, source pins, and axiom audits.
- [x] 6.2 Document how project-local verifier scripts can generate witness rows from Lean checks such as build status, source hashes, and axiom footprints.
- [x] 6.3 Document when to use proof-surface witness audit versus ProofIR route-authority audit, and how the two evidence layers compose.
