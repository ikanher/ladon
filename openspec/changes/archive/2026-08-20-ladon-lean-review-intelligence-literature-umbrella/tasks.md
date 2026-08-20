## 1. Umbrella Setup And Child Packets

- [x] 1.1 Create a focused child packet for `ladon-lean-module-readiness-audit`.
- [x] 1.2 Create a focused child packet for `ladon-lean-import-diet-witnesses`.
- [x] 1.3 Create a focused child packet for `ladon-proof-surface-witness-generation-handoff` that explicitly reuses the existing proof-surface route audit.
- [x] 1.4 Create a focused child packet for `ladon-proof-xray-staging`.
- [x] 1.5 Create a focused child packet for `ladon-refactoring-prescription-output`.
- [x] 1.6 Record in each child packet that Ladon routes review evidence and does not prove theorem truth.

## 2. Module Readiness Audit

- [x] 2.1 Add synthetic Lean fixtures covering public facade, implementation module, bridge module, common module, generated aggregation, and namespace/module drift cases.
- [x] 2.2 Add module-readiness report rows derived from module DAG metadata, facade subtype, generated tags, root closure, and declaration namespace evidence when available.
- [x] 2.3 Add optional module-system witness normalization with backend, tool version, command, source hash, confidence, and public/private/exposed status fields.
- [x] 2.4 Add tests proving absent module-system witnesses are skipped safely and do not suppress text-backed readiness rows.
- [x] 2.5 Add text/JSON rendering for module-readiness findings with nonclaim wording.

## 3. Import Diet Witnesses

- [x] 3.1 Define a compact import-diet witness schema for Lean/Lake-owned minimized-import evidence.
- [x] 3.2 Add witness normalization that preserves unknown fields and emits malformed/stale/unsupported diagnostics without failing the core report.
- [x] 3.3 Compare fresh witness imports against Ladon's observed import sites and report redundant-import candidates with source path, line, import text, witness command, and confidence.
- [x] 3.4 Add stale witness tests for mismatched source hash, module name, and inventory metadata.
- [x] 3.5 Rank import-diet candidates by fan-in, fan-out, root closure, generated status, and facade role.
- [x] 3.6 Document how to generate import-diet witnesses from Lean/Lake tools without making those tools mandatory in clean-core runs.

## 4. Proof-Surface Witness Handoff

- [x] 4.1 Confirm the existing proof-surface witness route audit remains the single implementation for spec-stub, missing-gate, missing-axiom, suspicious-axiom, clean-endpoint, frozen-hub, and escaped-proof-hole diagnostics.
- [x] 4.2 Define verifier handoff metadata for build command, source pin command, no-drift command, axiom audit command, tool version, replay boundary, and content hash.
- [x] 4.3 Add fixtures showing project-local verifier output feeding existing `proof_surface_witness` normalization.
- [x] 4.4 Add route-evidence completeness summaries that point to existing proof-surface diagnostics rather than creating duplicate trust rules.
- [x] 4.5 Add docs distinguishing proof-surface witness generation from Ladon's route audit consumption.

## 5. Proof X-Ray Staging

- [x] 5.1 Define optional proof-xray row schemas for tactic skeletons, proof-state shape, automation hotspots, premise/dependency rows, and axiom/sorry/unsafe footprint metadata.
- [x] 5.2 Require backend, tool version, command or extraction method, source attachment, confidence, and authority label on every proof-xray row.
- [x] 5.3 Add fixtures proving parser-observed rows and Lean-elaborated rows remain separate when they disagree.
- [x] 5.4 Add absent-backend tests proving proof-xray status is unavailable rather than inferred.
- [x] 5.5 Add reviewer-card output for proof-shape pressure that does not claim theorem truth or elaborated proof dependency unless supplied by the backend.

## 6. Refactoring Prescription Output

- [x] 6.1 Define a stable prescription action taxonomy covering extract common layer, move bridge, declare explicit bridge policy, split large owner, promote public facade, demote implementation import, clean generator output, move generated parameters to manifest, run import diet, and add proof-surface witness evidence.
- [x] 6.2 Map architecture policy findings and shared-dependency candidates to extraction, bridge, facade, and obsolete-import prescriptions.
- [x] 6.3 Map generated naming, generated duplicate import, large module, and facade subtype findings to generator and split-owner prescriptions.
- [x] 6.4 Map missing route evidence diagnostics to `add_proof_surface_witness_evidence` prescriptions without duplicating trust-audit logic.
- [x] 6.5 Add prioritization tests proving direct core boundary violations outrank lower-impact naming-only findings.
- [x] 6.6 Render prescriptions in JSON, text, atlas, and reviewer-card surfaces with evidence, confidence, alternatives, and nonclaim text.

## 7. Benchmarks, Documentation, And Gates

- [x] 7.1 Add benchmark-oracle predicates for every new promoted signal instead of whole-report snapshot comparisons.
- [x] 7.2 Add positive and negative fixtures for intentional namespace drift, intentional facades, true common layers, stale import witnesses, weak proof x-ray rows, and correct proof-surface handoff usage.
- [x] 7.3 Update architecture and trust-boundary docs to mention module readiness, import-diet witnesses, proof-xray staging, and refactoring prescriptions.
- [x] 7.4 Run `openspec validate ladon-lean-review-intelligence-literature-umbrella --strict`.
- [x] 7.5 For each child implementation packet, run focused tests and `uv run python scripts/python_quality.py --strict` before marking tasks complete.
