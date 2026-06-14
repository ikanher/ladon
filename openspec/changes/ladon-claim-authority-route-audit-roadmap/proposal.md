## Why

External review found that the starter packet is honest and useful, but current
Ladon would not reliably catch the most important failure mode: a packet or
review note claims Lean-closed proof status while the actual route still depends
on imported certificates, interval-certified rows, side-condition packages, or a
narrower endpoint scope. Ladon's next priority should therefore be proof-claim
authority and evidence-route auditing, not additional graph heuristics.

## What Changes

- Define a first-class claim authority audit layer that compares claimed status,
  claimed authority, endpoint scope, primary theorem surfaces, required premise
  authorities, external evidence rows, and nonclaims.
- Add diagnostics for the specific overclaim classes called out in review:
  - `ladon.claim.closed_with_imported_evidence`
  - `ladon.claim.endpoint_scope_overclaim`
  - `ladon.theorem.final_name_conditional_statement`
  - `ladon.evidence.authority_mismatch`
  - `ladon.claim.missing_primary_theorem_surface`
- Extend the compact ProofIR/Ladon bridge contract with route and authority
  fields such as `claimedAuthority`, `endpointScope`,
  `primaryTheoremSurfaces`, `supportingTheoremSurfaces`,
  `requiredEvidenceAuthorities`, `allowedExternalEvidence`, and `nonclaims`.
- Add route-audit regression fixtures modeled on the b-min-sep failure modes:
  closed-claim-with-imported-finite-window evidence, arbitrary-neighbor
  overclaim, all-Lean scalar replay overclaim, scoped sampled/null positive
  route, and honestly labeled imported seams.
- Add warning-only theorem signature heuristics for final/production/closed-like
  declaration names whose statements still expose high-risk premises such as
  `EvidenceAt`, `Certificate`, `Package`, `falsePkg`, `hForwardCDF`,
  `hReverseCDF`, `hcountMassEvidence`, `haggregateEvidence`, `imported`, or
  generic `row` evidence.
- Preserve the clean-core nonclaim: Ladon does not decide theorem truth. Ladon
  audits whether the claim's authority label matches the observed evidence
  route.
- Keep architecture smells, proof-family similarity, atlas diffs, and OpenSpec
  hygiene as secondary work until this authority-route audit exists.
- Improve future review-packet validation summaries so skipped source-repository
  cache paths are distinct from forbidden files actually included in an archive.

## Capabilities

### New Capabilities

- `ladon-claim-authority-route-audit`: Audits claim status, authority, endpoint
  scope, theorem-surface attachment, required evidence authorities, and
  nonclaims to produce route mismatch diagnostics.
- `ladon-proofir-route-authority-contract`: Defines the compact route/authority
  fields Ladon expects from ProofIR or Quux-style bridge inputs, without
  importing raw ProofIR dialects or promoting external proof status.
- `ladon-route-audit-fixtures`: Provides portable regression fixtures for
  claim/evidence authority mismatches, scoped positives, honest imported seams,
  and review-packet validation clarity.
- `ladon-conditional-signature-heuristics`: Adds warning-only review-routing
  heuristics for final-sounding theorem names with conditional or imported
  evidence premises in their signatures.

### Modified Capabilities

None.

## Impact

- Affected code in future child packets: ProofIR input normalization, bridge
  report generation, atlas/reviewer-card summaries, packet evidence summaries,
  declaration-surface inspection, and optional CLI/report output.
- Affected artifacts: compact ProofIR route fixtures, route-audit JSON fixtures,
  reviewer-card examples, OpenSpec child packets, and future pro review packets.
- Affected workflow: maintainers should be able to see when a public claim says
  "Lean closed" but the observed route is conditional on imported evidence, a
  narrower endpoint scope, missing primary theorem surfaces, or weak attachment.
- Affected trust model: route diagnostics are governance and review-routing
  evidence only; theorem truth, proof correctness, and witness adequacy remain
  owned by Lean or explicitly named external artifacts with their own authority.
