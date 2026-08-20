## 1. Roadmap Artifacts

- [x] 1.1 Review the pro-review packet recommendations and keep the top-level posture wording in sync.
- [x] 1.2 Add child packet briefs for the benchmark, declaration-evidence, and atlas-workflow packets.
- [x] 1.3 Validate this roadmap umbrella with `openspec validate ladon-architecture-review-evidence-routing-roadmap --strict`.

## 2. Child Packet Sequencing

- [x] 2.1 Apply child 1: `ladon-portable-benchmark-fixtures-and-signal-oracles`.
- [x] 2.2 Apply child 2: `ladon-declaration-table-source-evidence-contract`.
- [x] 2.3 Apply child 3: `ladon-atlas-review-workflow-and-bridge-cards`.
- [x] 2.4 Reassess deferred directions after child 1-3 are complete.

## 3. Closeout

- [x] 3.1 Update README and architecture docs with the final trust-boundary wording after child results are known.
- [x] 3.2 Run `uv run pytest -q tests`.
- [x] 3.3 Run `uv run python scripts/python_quality.py --strict`.
- [x] 3.4 Archive or mark the umbrella complete only after child packet outcomes are recorded.
