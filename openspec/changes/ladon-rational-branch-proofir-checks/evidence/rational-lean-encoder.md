# Rational AST to Lean encoder evidence

The bounded `ladon.rational_lean.encode_rational_goal` encoder first calls the existing exact Python rational checker. It then emits one closed `decide` proposition for each premise and the conclusion, with exact rational literals and the checker's expected Boolean result. No caller-provided Lean expression is accepted. Python rejects unsupported AST nodes, malformed assignments, resource-bound violations, and evaluated division by zero before the function returns an encoding.

Validation in `/home/codex/projects/ladon`:

- `pytest -q tests/test_rational_lean_encoder_v2.py` — 16 passed.
- `ruff check src/ladon/rational_lean.py tests/test_rational_lean_encoder_v2.py` — passed.
- `radon cc -s -a src/ladon/rational_lean.py` — all functions A/B (maximum complexity 7).
- `vulture src/ladon/rational_lean.py tests/test_rational_lean_encoder_v2.py` — passed.

The actual 15 proposition strings returned by the encoder were wrapped in `example : ... := by norm_num` declarations and compiled using `lake env lean /home/codex/projects/ladon/.codex/state/lean-rational-encoder-generated.lean` from `/home/codex/projects/lean/matrix-factorization` (Lean 4.32.1 with its existing Mathlib). The matrix exercised all seven expression operators (`add`, `sub`, `mul`, `div`, `neg`, `abs`, `pow`), all six comparisons, and both true and false expected outcomes. Compilation succeeded without diagnostics.

This validates goal rendering and Mathlib normalization for the exercised matrix only. It does not create a ProofIR artifact, run a bounded Ladon Lean worker, bind a branch or receipt, establish source formula fidelity, or prove a universal claim. The encoder currently has no workspace capability probe; that remains required before a public route can claim support.
