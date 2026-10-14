# Planning sources and overlap boundaries

This file is operator/developer context, not a blind auditor input packet. It
contains known-case locations. The umbrella was planned from local source and
preserved run evidence without online research. No reference-answer match for
the target paper is claimed.

## Existing implementation

- `src/ladon/investigation.py`, `investigation_derivation.py`,
  `investigation_cli.py`, and `rational_witness.py`: current authored contract,
  independent challenge, queue, and exact arithmetic boundaries.
- `src/ladon/source_goal_capture.py`, `source_goal_completion.py`,
  `lean/ladon_source_goal_helper.lean`, `lean/ladon_expr_graph.lean`, and
  `lean/ladon_semantic_candidate_helper.lean`: source contexts, actual
  applications, shared expression serialization, and checker observations.
- `src/ladon/proofir_v3.py`, `proofir_v3_payloads.py`,
  `proofir_derivation.py`, and `proofir_sqlite_v3.py`: closed kinds, structural
  proof graphs, validation, and disposable projection owners.
- `src/ladon/report_declaration_compaction.py`, `report_projection.py`,
  `entrypoint.py`, and `cli.py`: candidates for reproducing observed report and
  option-routing failures; no root cause was established during planning.
- `tests/test_source_goal_completion_lean.py`, source-goal capture/CLI tests,
  `test_expr_graph_protocol.py`, native-v3/derivation tests, investigation tests,
  and declaration-compaction tests: existing real and portable consumer controls.

## Specifications and neighboring changes

The main specs `proofir-v3-native-schema-and-canonicalization`,
`proofir-content-environment-and-subject-identity`,
`proofir-observation-authority-and-coverage-core`, and
`proofir-derivation-hypergraph-semantics` were read including scenarios. They
remain the core authority contract; the new capabilities extend consuming
behavior without redefining graph satisfaction as theorem truth.

`ladon-binder-aware-proof-difference` and
`ladon-premise-difference-and-adapter-routing` address candidate comparison and
routing. Their current implementation can be reused, but lexical analysis is
not a substitute for the new exact correspondence obligations. No task in those
changes is closed by this plan. The completed discovery, investigation-loop,
local-derivation, and source-goal changes are baselines, not promises of research
error detection. The older v3 umbrella's remaining qualification tasks stay
separate from this bounded new path.

Generic current documentation inspected: `docs/PROOF_CORRESPONDENCE_AUDIT.md`,
`CORRESPONDENCE_DISCOVERY.md`, `DERIVATION_CHALLENGES.md`,
`SOURCE_GOAL_CAPTURE.md`, `SOURCE_GOAL_COMPLETION.md`, and the native-v3 review
and identity contracts. Their command examples must be invoked from the current
checkout when qualifying new implementation, not through an older pip package.

## Known development evidence

- `/home/codex/projects/navier-stokes-retest-4/runs/independent-01/FINDINGS.md`:
  qualified page-3 direction finding, independent review, incomplete 90-minute
  audit, four reviewed comparisons, and concrete tool failures.
- The same run's
  `final-outline-check/pressure-fresh-review/FIRST-RESPONSE.md` and
  `final-outline-check/PRESSURE-RECONCILIATION.md`: independently reproduced
  calculation and explicit source-interpretation limitations. This is attributed
  conventional evidence, not a Lean-checked counterexample.
- `/home/codex/projects/navier-stokes-retest-4/formalization/NavierStokes/PressureDatum.lean`:
  actual applications in `NavierStokes.PressureDatum.deriv_pressure_pos` and
  `NavierStokes.PressureDatum.deriv_pressure_pos_of_active`; the local selected
  source uses the pinned `leanprover/lean4:v4.34.0-rc2` environment.
- `/home/codex/projects/navier-stokes-retest-3/runs/harder-fragments-20261010/REPORT.md`
  and its `SCORE-CORRECTION.md`: constructed-fragment success, preserved local
  conditional-label correction, formal-counterpart incompleteness, and the
  append-only correction to inconsistent per-case scoring flags.

These paths are optional external evidence, not portable runtime dependencies.
At implementation start, freeze only the minimal needed source/evidence excerpts
with their identities and provenance into the new packet's evidence directory.
Preserve original reports and manifests. Actual real-target extraction should
use the exact external source/environment or an explicitly derived isolated
snapshot; never label a reconstructed miniature as that extraction.

## Quux boundary

Quux's `docs/PROOF-IR-LOCAL-BASELINE.md`, statement extractor, and
subset/subtype-transport design informed the authority and scope discussion.
Its current statement probe does not extract full proofs. Ladon's portable
acceptance and runtime do not import Quux. A future Quux experiment requires its
own separately scoped work; this umbrella makes no change there.
