## Why

Ladon declaration graph reports and ProofIR bridge joins need auditable source
evidence. A stable declaration table with path, range, hash, backend, method,
and confidence gives reviewers stronger attachment context without claiming
proof truth.

## What Changes

- Add `declaration_graph.declarations` rows to reports when declaration IR is
  available.
- Include declaration identity, source evidence, extraction backend, extractor
  version, name-resolution method, and confidence.
- Update ProofIR bridge join precedence to prefer source hash and range evidence
  before module/name or basename matches.
- Render and document that source attachment confidence is not theorem truth.

## Capabilities

### New Capabilities

- `ladon-declaration-source-evidence`: Defines declaration source-evidence rows,
  confidence levels, and bridge join behavior.

### Modified Capabilities

None.

## Impact

- Affected code: `src/ladon/ir.py`, `src/ladon/lean_extraction.py`,
  `src/ladon/pipeline.py`, `src/ladon/render.py`, `src/ladon/proofir_bridge.py`,
  atlas exports, tests, and fixtures.
- Affected report schema: additive `declaration_graph.declarations` rows.
- Affected downstream consumers: ProofIR bridge and atlas can use higher
  confidence joins when source evidence is present.
