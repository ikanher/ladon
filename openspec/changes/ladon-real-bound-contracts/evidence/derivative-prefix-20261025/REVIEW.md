# Derivative-prefix integration audit

Scope: source review of assignment #1639 against contract #1625 and synthesis #1637; static review plus root-supplied run artifacts. No canonical edits or Lean/build execution. This does not claim independent kernel replay.

## Verdict

SUPPORTED for the source-level fixed derivative adapter and bounded first-case evidence. No consequential defect found in the reviewed implementation. Full independent compatibility verification remains pending: the supplied evidence contains derivative examples, while no v1 direct-consumer rerun was available in this audit. The root synthesis correctly says affected consumers must be rerun after the shared helper identity changes.

## Findings

- `src/ladon/lean/LadonRealBoundDerivative.lean:7-13` fixes the measure to `‖iteratedFDeriv Real j f (p,y)‖`, with universes and the required real normed-space instances polymorphic. This is the full Frechet derivative over `P × Y`; its output norm is the continuous-multilinear-map norm. It does not encode the paper's norm or regularity interpretation.
- `src/ladon/lean/LadonRealBoundDerivative.lean:20-42` derives P, Y, and Z from the live predicate's object function type, rejects non-product domains and dependent codomains, and asks Lean to synthesize measure instances within the source-owned local-instance context. It adds no assumptions. Combined with `LadonRealBoundBinding.lean:50-67,92-101`, the generated law is closed over used telescope locals, checks all used proposition-valued locals are absent, and compares the normalized live declaration against the observed expression before constructing Admission.
- `src/ladon/derivative_prefix.py:24-48` uses a separate closed v1 derivative plan schema and hashes family, shared binding, and derivative helper sources; it exposes no caller-selected measure or Lean callback. `real_bound_binding_check.py:21-34` recomputes the exact plan and `:15-22` binds all helper/checker source bytes into checker identity. Worker `:49-54,70-75,95-115` compiles and checks the exact helper source, rejects reserved helper modules, and revalidates source/checker identity after execution. The derivative path returns `derivativeAdmission=checked` only after accepted evidence and trust inventory validation (`:57-68`); paper bridge remains unresolved.
- CLI wiring is a separate pair of operations in `proof_contract_cli.py:109-110` and exact plan-schema matching is enforced by `real_bound_binding_cli.py:24-50`. The legacy bound-prefix plan path remains explicitly selected and retains its measure input (`real_bound_binding_cli.py:18-21,30-35`). Source inspection supports intended v1 compatibility, but actual v1 consumer replay was outside available audit evidence.
- The provided `.codex/state/derivative-prefix/generic-first` and matrix artifacts show a checked generic seven-loss case and unresolved parameter-only and restricted-point near misses. The latter fail exact definitional equality to the fixed full-joint `PrefixBound`; these are useful negatives, not a complete matrix. Root remains owner of matrix completion and original fixed-loss replay.
- The helper-only frozen test refactor's `quality-refactor/EQUIVALENCE.json` records AST identity after helper expansion, unchanged assertions (11) and test functions; proposal and preserved original are present. This supports no changed test expectations at source level.

## Limits and follow-up

No paper norm bridge, semantic contract activation, or independent kernel replay is established here. Before considering task 2.3 complete, root should finish the running matrix, rerun the original fixed-loss cases and direct v1 consumers under the new binding identity, and retain their fresh outputs. Existing historical receipts must not be treated as fresh evidence.
