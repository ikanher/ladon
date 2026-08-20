## 1. Umbrella Artifacts

- [x] 1.1 Review the Quux ProofIR surface and bridge artifact examples recorded in this packet.
- [x] 1.2 Keep the ProofIR trust boundary synchronized with Ladon architecture and bridge docs.
- [x] 1.3 Validate this roadmap umbrella with `openspec validate ladon-proofir-quux-input-normalization-roadmap --strict`.

## 2. Child Packet Sequencing

- [x] 2.1 Open child 1: `ladon-proofir-quux-surface-bundle-adapter-mini`.
- [x] 2.2 Apply child 1 with frozen `proof_ir_lean_surface_bundle` fixtures and adapter tests.
- [x] 2.3 Open child 2: `ladon-proofir-quux-source-anchor-normalization-mini`.
- [x] 2.4 Apply child 2 with `sourceHash` alias tests and nested `sourceAnchor` downgrade tests.
- [x] 2.5 Open child 3: `ladon-proofir-quux-bridge-snapshot-atlas-import-mini`.
- [x] 2.6 Apply child 3 with optional atlas import tests for `ladon_proofir_bridge_snapshot`.

## 3. Closeout

- [x] 3.1 Confirm unsupported raw ProofIR dialects fail or warn without fabricated evidence.
- [x] 3.2 Confirm bridge and atlas outputs state that attachment confidence is not proof truth.
- [x] 3.3 Run `uv run pytest -q tests`.
- [x] 3.4 Run `uv run python scripts/python_quality.py --strict`.
- [x] 3.5 Archive or mark the umbrella complete only after child packet outcomes are recorded.
