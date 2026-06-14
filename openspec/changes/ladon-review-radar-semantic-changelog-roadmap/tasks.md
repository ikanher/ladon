## 1. Schema And Fixtures

- [ ] 1.1 Add Review Radar report schema fixtures covering after-only and before/after inputs.
- [ ] 1.2 Add semantic theorem-surface changelog fixtures for added/removed declarations, proof-only changes, added assumptions, conclusion drift, rename candidates, and missing source evidence.
- [ ] 1.3 Add fixture assertions that Review Radar and changelog rows preserve source path, range, content hash, backend, version, name-resolution method, and confidence where available.
- [ ] 1.4 Add nonclaim regression assertions for structural observations, source-evidence joins, quoted ProofIR evidence, and optional x-ray rows.

## 2. Semantic Changelog Core

- [ ] 2.1 Create a pure comparison module for before/after declaration rows without filesystem or subprocess side effects.
- [ ] 2.2 Implement declaration add/remove/change classification with confidence labels and source-evidence diagnostics.
- [ ] 2.3 Implement initial theorem-surface classes for stable-type proof-only change, theorem-type change, added/removed assumption, heuristic conclusion drift, rename candidate, and doc/comment-only change.
- [ ] 2.4 Expose raw before/after surfaces alongside heuristic semantic classes so reviewers can inspect the evidence.

## 3. Review Radar Workflow

- [ ] 3.1 Create a Review Radar builder that accepts before/after reports or atlas surfaces and emits changed modules, changed declarations, import-pressure deltas, evidence attachment deltas, review-priority roots, and nonclaims.
- [ ] 3.2 Reuse atlas diff/workflow and ProofIR bridge summaries rather than introducing a new storage backend.
- [ ] 3.3 Render machine-readable JSON and compact Markdown reviewer cards from the same Review Radar payload.
- [ ] 3.4 Add configurable CI failure rules that default to advisory success and fail only for explicitly enabled severe regressions.

## 4. CLI And Documentation

- [ ] 4.1 Add a CLI surface for Review Radar that can run from precomputed before/after report paths before adding git-ref orchestration.
- [ ] 4.2 Document the command, output schema, severity rules, and trust boundary in README or architecture docs.
- [ ] 4.3 Record examples showing that high review priority is routing pressure, not a quality score or proof-truth claim.
- [ ] 4.4 Keep unsupported git/ref or elaborated-backend options explicit until implemented with tests.

## 5. Optional Proof X-Ray Enrichment

- [ ] 5.1 Define an additive x-ray namespace for elaborated-backend metadata with backend, tool version, source hash, and confidence fields.
- [ ] 5.2 Add tests proving parser reference candidates and elaborated dependency metadata remain separate rows with separate authority labels.
- [ ] 5.3 Add x-ray unavailable-state handling so Review Radar and semantic changelog outputs remain valid without elaborated extraction.
- [ ] 5.4 Gate any tactic skeleton, dependency, axiom, sorry, or unsafe footprint rows behind explicit backend-supplied metadata.

## 6. Validation

- [ ] 6.1 Run targeted tests for semantic changelog, Review Radar workflow, and optional x-ray unavailable/enabled states.
- [ ] 6.2 Run `uv run pytest -q tests`.
- [ ] 6.3 Run `uv run python scripts/python_quality.py --strict`.
- [ ] 6.4 Create a source-first pro review packet after implementation if the roadmap changes public review behavior.
