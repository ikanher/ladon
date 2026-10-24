# Protocol-v2 independent follow-up (18 Oct 2026)

Role: auditor `/root/producer_audit`, assigned by board post 141. Scope remained bounded to the stdout/result-channel fix, exact feature-origin paths, and associated formal snapshot/CLI behavior. Root retained sole product and test ownership; no product/test/fixture/task files were edited by this auditor. Scratch evidence remains in this directory.

## Review result

The previous stdout spoof is closed for the tested attack. `produce_formal_contract` ignores source stdout as a worker response and reads a result JSON from the helper's private `statement.json`; the helper writes it only after `Elab.runFrontend` returns. The persisted `ForgedWorker.lean` prints a synthetic worker-shaped object and exits before helper completion. It now returns `status=unavailable`, `contract=None`, residual `helper-result-missing`, and no extracted offset. This confirms source stdout alone cannot impersonate helper completion.

The exact-origin fix is also confirmed. On `OriginCollision.lean`, `M s (f x) ≤ c * M (s + 1) x` extracts offset 1 and points regularity at `/normalizedTypeExpr/forallE/body/forallE/body/app/1/app/1`, which resolves to the right-hand `M` scale application containing `HAdd.hAdd`; it no longer points at the left-hand `M`.

The helper result channel does not claim to sandbox adversarial Lean source. Lean source IO runs in the same process and filesystem context; the private temporary result file is a protocol boundary against stdout spoofing, not an authenticated or privilege-separated receipt. Keep that limitation explicit. Inspection replay is deterministic self-consistency against the retained observation and current source/environment/helper identity; it does not cryptographically authenticate a caller-edited observation or re-elaborate a proof body, consistent with the docs' snapshot-hash limitation.

## Verification

Command:

```sh
PYTHONPATH=src .venv/bin/pytest -q --tb=short \
  tests/test_proof_contract_protocol.py \
  tests/test_proof_contract_formal_snapshot.py \
  tests/test_proof_contract_formal_cli.py
```

Result: `9 passed in 9.65s`. This is a targeted protocol/snapshot/CLI check; no full suite was run.

Direct scratch producer results: forged stdout + early exit -> unavailable with `helper-result-missing`; colliding scale/operator name -> extracted offset 1 with exact right-scale origin. Pinned Lean `4.32.1`; environment identity `sha256:2d3d6a0a3c155acce4bd884ee428869ca25ebf8718f90fdd2a9f3d596b231801`; helper/protocol `ladon-formal-contract-observation-v2`; helper SHA-256 `c4f5b31403ab9056ef21cd8132645fe9e7895e993673e92819935d2cbe0dd645`.

Current production artifact hashes:
- `src/ladon/proof_contract_production.py`: `5c9f5c86b5381439871078b62c594a31b399e4ca92960420b906bd0b143a1aed`
- `src/ladon/proof_contract_recognition.py`: `9677cce39fc959ab5596678ffaf3d82b79bf9e0f8aab0ae470aaab92a41912a8`
- `src/ladon/proof_contract_worker.py`: `3a6677f6ed482d5ffbf2933e165b8e28a5e635827d3553e76c3694255eea3e1b`
- `src/ladon/proof_contract_formal.py`: `c24697c6ab256cf243b3af5697edc38ec9a7e8049d0e7f6d8dcd60a6cab26d97`
- `src/ladon/lean/ladon_formal_contract_helper.lean`: `c4f5b31403ab9056ef21cd8132645fe9e7895e993673e92819935d2cbe0dd645`
- `tests/test_proof_contract_protocol.py`: `21668b053c194de011d349435d2ef134112415f0ff06aaf830305453438f3685`
- `tests/fixtures/proof_contract_protocol/ForgedWorker.lean`: `e5fcea411631d487749d65ea8a5938b7a4564295ea8179bd52cf1d5a3479d78b`
- `tests/fixtures/proof_contract_protocol/OriginCollision.lean`: `353abac8d116b24f1aa0fc1c20316c697b0d71ca6c168c33439e15823c3b7c58`

Remaining gate: the two original concrete findings are fixed for their stated cases. Preserve the explicit arbitrary-Lean-IO and unauthenticated-snapshot limits; root owns compatibility and broader verification. No full-suite or theorem-fidelity claim.
