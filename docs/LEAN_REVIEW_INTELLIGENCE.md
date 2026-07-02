# Lean Review Intelligence

Ladon is a Lean review-routing assistant. These optional review-intelligence
surfaces help maintainers decide what to inspect first while keeping Lean,
Lake, and project-local verifier scripts authoritative for build-sensitive or
proof-sensitive facts.

## Module Readiness

`module_readiness` rows summarize module/API boundary pressure:

- public facade or barrel pressure;
- implementation modules with high fan-in;
- generated aggregation exposed as public surface;
- namespace/module drift when declaration evidence is available;
- optional module-system witness rows with backend/version/command/hash
  metadata.

These rows do not claim Lean module-system correctness. They are review hints
for API design, rebuild-scope risk, and source organization.

## Import Diet

`import_diet` consumes optional witness JSON from Lean/Lake-owned import
minimization tools. A fresh witness can identify source imports that look
redundant relative to the quoted minimized-import set. A stale or malformed
witness produces diagnostics instead of removal advice.

Ladon does not remove imports and does not prove removability. Replay the named
Lean/Lake command before changing source.

## Proof X-Ray

`proof_xray` is optional proof-shape context. Rows must carry an authority
label:

- `parser_observed`
- `lean_elaborated`
- `external_tool_quoted`
- `unknown`

Tactic skeletons, automation hotspots, dependencies, axiom footprints, sorry
footprints, and unsafe footprints remain reviewer context. Parser-observed rows
are never promoted to elaborated proof dependencies.

## Refactoring Prescriptions

`refactoring_prescriptions` turns existing evidence into concrete review
actions:

- `extract_common_lower_layer`
- `move_bridge_to_neutral_namespace`
- `declare_explicit_bridge_policy`
- `split_large_owner`
- `promote_public_facade`
- `demote_implementation_import`
- `clean_generator_output`
- `move_generated_parameters_to_manifest`
- `run_import_diet`
- `add_proof_surface_witness_evidence`

Prescriptions are not automatic rewrites. They preserve the evidence, priority,
confidence, and nonclaim text so maintainers can decide whether the suggested
refactor is actually appropriate.
