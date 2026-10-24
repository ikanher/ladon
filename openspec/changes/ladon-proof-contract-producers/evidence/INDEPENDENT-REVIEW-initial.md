# Independent producer audit (18 Oct 2026)

Role: auditor `/root/producer_audit`. Scope: exact source/environment/helper audit of the integrated formal producer, with scratch negatives only. No product, test, fixture, task, or generated-file edits were made. The only code artifacts here are isolated scratch Lean sources.

## High-severity falsification: Lean source can forge the worker receipt

The helper runs `Elab.runFrontend` on the selected source file. That frontend executes source `#eval` commands. The protocol parser then scans stdout for the first `{"version"` and parses the entire remaining stdout as the worker record (`src/ladon/proof_contract_worker.py:92-104`). The helper's actual record is printed only after frontend execution (`src/ladon/lean/ladon_formal_contract_helper.lean:90-95, 101+`).

Scratch `ForgedWorker.lean` contains a true source declaration with offset 1, followed by `#eval IO.println` of a synthetic worker object whose normalized expression reports offset 99, then `#eval (IO.Process.exit 0 : IO Unit)`. This exits the worker before the helper prints its own record. The current producer returns `status=extracted`, `offset=99`, and no residual. This is a source-backed false extraction, not a mere parser robustness concern. The synthetic object reuses the authentic `typeExpr`, changes the normalized expression and fingerprint, and matches the request identity. This demonstrates that identity fields and process receipts do not authenticate the observed expression.

Reproduction:

```sh
PYTHONPATH=src .venv/bin/python - <<'PY'
from pathlib import Path
from ladon.proof_contract_production import produce_formal_contract
r = produce_formal_contract(Path('.codex/state/proof-contract-analysis/producer-audit'),
  'ForgedWorker.lean', 'ForgedWorker', 'ForgedWorker.actual_offset_one')
print(r['status'], r['contract']['features']['regularity']['offset'])
PY
```

Observed output: `extracted 99`; source says `s + 1`. Any production receipt protocol must prevent source-controlled stdout from becoming a trusted worker record. A separate descriptor/pipe not writable by Lean source, or a worker that returns a value only after verifying the frontend completed without source-controlled output, would avoid this specific channel. Also validate expression fingerprints against returned expressions, though that alone would not stop a fully forged record.

## Feature origin collision

Scratch `OriginCollision.lean` declares `M s (f x) ≤ c * M (s + 1) x`. Extraction correctly reports offset 1, but `featureOrigins.regularity` resolves to the first `M` occurrence in the left-hand estimate, rather than the right-hand scale carrying the offset. `_feature_origins` searches the whole expression by constant name (`src/ladon/proof_contract_production.py`, `_feature_origins`); same-named operators make the origin ambiguous. Carry exact expression-node paths from recognition (including the right scale subtree) instead of rediscovering by name.

## Identity and verification

Pinned Lean release: `4.32.1`; worker environment identity: `sha256:2d3d6a0a3c155acce4bd884ee428869ca25ebf8718f90fdd2a9f3d596b231801`; helper SHA-256: `140551ecb03cd4065dda0bc231cec5f4595470c617545d2a099ab33f346bdd11`. Worker parser SHA-256: `b8abf605b40c4862810ec73db41ed71e64eeeaba91f50ba2364a4384a888332a`; production orchestration SHA-256: `9e53cd8659fa7c2b322e7e8d990a7e920673f451657d0d22898953d12f9f4433`.

Scratch hashes:
- `OriginCollision.lean`: `353abac8d116b24f1aa0fc1c20316c697b0d71ca6c168c33439e15823c3b7c58`
- `ForgedWorker.lean`: `e5fcea411631d487749d65ea8a5938b7a4564295ea8179bd52cf1d5a3479d78b`

Commands run: direct bounded producer invocations for both scratch declarations; direct `elan run leanprover/lean4:v4.32.1 lean ...` check of the exit-command behavior. These scratch probes are not tests and do not establish the focused suite or full suite. I did not access sibling repositories, external models, or reference answers. Root remains sole product mutator. Remaining gate: fix/falsify stdout forgery path and re-audit; verify origin-path specificity; root-owned focused suite and full suite remain outside this audit.
