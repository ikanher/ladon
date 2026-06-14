## 1. Route Model And Fixtures

- [x] 1.1 Add portable route-audit JSON fixtures for closed-with-imported-evidence, endpoint-scope overclaim, all-Lean scalar replay overclaim, scoped sampled/null positive, and honestly labeled imported seam cases.
- [x] 1.2 Add tiny Lean declaration-surface fixtures for primary theorem attachment, weak basename attachment, and final-sounding conditional theorem signatures.
- [x] 1.3 Define route-audit dataclasses or typed rows for claim id, claimed status, claimed authority, endpoint scope, theorem surfaces, required evidence authorities, allowed external evidence, and nonclaims.
- [x] 1.4 Add fixture assertions that source attachment confidence is tested separately from proof authority.

## 2. Pure Claim Authority Audit

- [x] 2.1 Create a pure analysis module for claim authority route auditing with no filesystem, subprocess, CLI, or bridge side effects.
- [x] 2.2 Implement `ladon.claim.closed_with_imported_evidence` for closed or Lean-closed claims with unallowed imported or external required evidence.
- [x] 2.3 Implement `ladon.claim.endpoint_scope_overclaim` for configured stronger claimed scopes such as arbitrary-neighbor event DP over sampled-null primary theorem routes.
- [x] 2.4 Implement `ladon.evidence.authority_mismatch` for production or fully proved artifacts whose evidence rows contain diagnostic, smoke, unchecked, interval-certified, imported numeric, or external certificate authority.
- [x] 2.5 Implement `ladon.claim.missing_primary_theorem_surface` for public claims without joined primary theorem surfaces or with only helper/background theorem surfaces.
- [x] 2.6 Ensure every route-audit diagnostic states that Ladon found an authority/evidence mismatch, not theorem falsehood or proof invalidity.

## 3. ProofIR Route Authority Contract

- [x] 3.1 Extend compact ProofIR input normalization to preserve `claimedAuthority`, `endpointScope`, `primaryTheoremSurfaces`, `supportingTheoremSurfaces`, `backgroundTheoremSurfaces`, `requiredEvidenceAuthorities`, `allowedExternalEvidence`, and `nonclaims`.
- [x] 3.2 Normalize string/list/map authority fields without mutating input and preserve unknown labels with an unknown-authority diagnostic.
- [x] 3.3 Add bridge report fields that keep source attachment confidence separate from route authority metadata.
- [x] 3.4 Add reviewer-card and atlas workflow rows for route audit diagnostics under a route or ProofIR namespace without promoting ProofIR status.

## 4. Conditional Signature Heuristics

- [x] 4.1 Add warning-only detection for final, production, maintained, closed, theorem, or eventDP-like declaration names with high-risk conditional premises.
- [x] 4.2 Cover baseline premise tokens: `EvidenceAt`, `Certificate`, `Package`, `falsePkg`, `hForwardCDF`, `hReverseCDF`, `hcountMassEvidence`, `haggregateEvidence`, `imported`, and generic row evidence.
- [x] 4.3 Suppress or lower heuristic output when explicit route metadata honestly labels the claim as conditional on imported evidence.
- [x] 4.4 Add tests proving the heuristic never emits high-confidence proof-authority mismatch diagnostics by itself.

## 5. Packet Validation Clarity

- [x] 5.1 Update review-packet validation summaries to separate skipped source repository paths from forbidden archive entries.
- [x] 5.2 Add tests showing skipped `__pycache__` or `.pytest_cache` source paths do not imply archive contamination.
- [x] 5.3 Add tests showing actual forbidden archive entries are reported distinctly and fail validation.

## 6. Documentation And Review Surfaces

- [x] 6.1 Update ProofIR bridge docs with the route authority contract and the nonclaim that Ladon audits authority alignment only.
- [x] 6.2 Update architecture or README roadmap text to make claim authority audit Priority 1 ahead of new graph heuristics.
- [x] 6.3 Add example reviewer output for closed-with-imported-evidence, endpoint-scope overclaim, missing primary theorem surface, and honest conditional imported seam cases.
- [x] 6.4 Create a source-first pro review packet after implementation if public review surfaces or ProofIR bridge contracts change.

## 7. Validation

- [x] 7.1 Run targeted tests for route audit, ProofIR route normalization, signature heuristics, atlas/reviewer-card summaries, and packet validation clarity.
- [x] 7.2 Run `uv run pytest -q tests`.
- [x] 7.3 Run `uv run python scripts/python_quality.py --strict`.
- [x] 7.4 Confirm OpenSpec status reports this change complete before implementation handoff or archive.
