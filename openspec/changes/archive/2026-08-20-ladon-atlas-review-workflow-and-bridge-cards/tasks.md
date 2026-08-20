## 1. Workflow Model

- [x] 1.1 Define the atlas review workflow input set for report roots, optional before/after roots, optional packet evidence, and optional ProofIR bridge reports.
- [x] 1.2 Define workflow output sections for changed rows, recurring hotspots, review-priority roots, low-confidence joins, and incomplete or stale evidence.
- [x] 1.3 Preserve atlas JSON as the canonical machine-readable surface.

## 2. Reviewer Cards

- [x] 2.1 Extend reviewer-card extraction with packet-evidence and bridge diagnostic summaries when present.
- [x] 2.2 Render known non-claims and trust notes on cards.
- [x] 2.3 Add tests for cards with and without optional ProofIR bridge data.

## 3. Queries And Diffs

- [x] 3.1 Add or update canned SQLite queries for recurring hotspots, proof-family pressure, packet evidence gaps, and low-confidence joins.
- [x] 3.2 Add or update atlas diff categories for bridge diagnostics and evidence status changes.
- [x] 3.3 Add deterministic fixture tests for each workflow question.

## 4. Scripts And Validation

- [x] 4.1 Extend atlas scripts or add a thin workflow script for the combined reviewer output.
- [x] 4.2 Run `openspec validate ladon-atlas-review-workflow-and-bridge-cards --strict`.
- [x] 4.3 Run `uv run pytest -q tests`.
- [x] 4.4 Run `uv run python scripts/python_quality.py --strict`.
