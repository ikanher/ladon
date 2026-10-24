# Probe packet archive verification

The original packet was accepted at
`openspec/changes/ladon-proof-contract-probes`. Its frozen manifests and
producer scripts contain paths tied to that location and directory depth.
Moving the packet must not rewrite those accepted bytes or regenerate their
manifests.

`ARCHIVE-INVENTORY.json` records every original file's relative path, size and
SHA-256 before relocation. `ARCHIVE-MIGRATION.json` binds that inventory, this
guide and the added `verify_archive.py` adapter. The adapter maps only the
historical change-directory prefix to its current directory. Inputs outside
the packet retain their original repository bindings. It checks all original
file bytes, all 14 frozen manifests and the unchanged task 3 report assertions.

After archiving, run from the repository root:

```sh
uv run --locked python openspec/changes/archive/2026-10-19-ladon-proof-contract-probes/verify_archive.py
```

The adapter works before and after the move. Historical verifiers and rebuild
scripts remain preserved as evidence; use the adapter for archived verification.
Rebuilding the historical experiments requires their original layout and
runtime inputs in a separate workspace, rather than overwriting this archive.

This check does not replay Lean, repeat the 30-minute experiment or establish a
new independent mathematical result. It requires the recorded source inputs
and current reporting implementation in this checkout, and detects their drift.
The inventory is a local preservation record, not a signature authenticating a
malicious writer. Historical reports and relative links retain their original
context; the active umbrella's links identify the archive's current location.

The main capability spec is `openspec/specs/ladon-contract-probes/spec.md`.
The parent work remains in `openspec/changes/ladon-proof-contract-analysis-umbrella`;
completing this child does not complete its integration or evaluation gates.
