## 1. Baseline And Ledger

- [x] 1.1 Capture `openspec list --json`, strict validation, backlog analysis, status hygiene, canonical specs, and archive state before mutation.
- [x] 1.2 Add a tracked reconciliation ledger schema and one row for every pre-program active candidate, invalid completed packet, or reviewed archive batch; reference rather than duplicate the alpha dependency ledger.
- [x] 1.3 Record source, test, gate, replacement, conflict, and disposition evidence for each candidate status change.
- [x] 1.4 Make the ledger reject a completion disposition with uncovered requirements.

## 2. Seven Legacy Candidate Packets

- [x] 2.1 Reconcile common-layer/facade, configurable lexical packs, fix-oriented triage, and policy-persistence packets against source/tests and their completed umbrella.
- [x] 2.2 Reconcile generated-artifact attribution and transfer residual generated-importer fan-in behavior to `ladon-signal-correctness-hardening` before recording superseded-with-residuals.
- [x] 2.3 Reconcile `ladon-proof-xray-roadmap`: apply this change's `ladon-proof-xray-staging` MODIFIED requirement for quoted witness/trust rows, assign direct Lean-observed statement/type/value dependency and axiom/sorry/unsafe facts to the alpha declaration child, and retain/narrow the roadmap as owner of any future tactic-skeleton/InfoTree evidence contract without inventing a native-generation requirement.
- [x] 2.4 Reconcile `ladon-review-signal-benchmarks` against completed portable oracle work and transfer uncovered positive/negative fixtures—especially source-pattern and claim-authority boundaries—plus metric/drift obligations to `ladon-signal-benchmark-harness` before recording superseded-with-residuals.
- [x] 2.5 Mark tasks complete or narrow residual tasks only after each ledger row has requirement-level evidence.

## 3. Remaining Future Lane

- [x] 3.1 Keep `ladon-review-radar-semantic-changelog-roadmap` as a planning umbrella outside alpha and strip implementation tasks from it.
- [x] 3.2 Narrow `ladon-theorem-surface-changelog` into the bounded child that consumes the alpha declaration surface rather than duplicating extraction.
- [x] 3.3 Record the future ownership chain `ladon-elaborated-declaration-surface` → theorem-surface changelog child → a later Review Radar MVP child, and remove or reassign duplicate proof-xray/theorem-extraction checkboxes.
- [x] 3.4 Split/reassign the planning umbrella's delta specs: move concrete `ladon-semantic-theorem-changelog` requirements into the bounded theorem child, narrow `ladon-proof-xray-enrichment` to optional consumer availability/nonclaims that reference its extraction owners, and validate that every residual future requirement has exactly one authoritative packet.

## 4. Validation And Automation Repair

- [x] 4.1 Repair or record a validated superseding route for `ladon-proofir-bridge-mvp`.
- [x] 4.2 Repair or record a validated superseding route for `ladon-proofir-bridge-real-report-smoke`.
- [x] 4.3 Add missing strict-validation and relevant verification commands to retained packet automation metadata.
- [x] 4.4 Add `scripts/openspec_canonical_gate.py --profile legacy-cli`; in active mode it verifies the explicit `ladon-python-quality`/`ladon-root-matrix` deltas and the pipeline-base → source-addition → reconciliation ordering, while `--require-canonical` verifies after reconciliation archive that no canonical scenario positively prescribes `--skip-build`.

## 5. Conflict-Aware Archive

- [x] 5.1 Group completed changes by capability/dependency, preflight conflicts, and archive in the required base chain: `ladon-pipeline-phase-boundaries-timing`, `ladon-clean-core-radon-gate`, `ladon-root-matrix-lean-expansion`, then `ladon-proof-xray-staging`, before preparing reconciliation's own archive.
- [x] 5.2 Archive one reviewed batch at a time and verify the active source moved, exactly one dated archive exists, and expected canonical requirements appeared; record each result instead of trusting the archive command's exit status alone.
- [x] 5.3 Stop and resolve incompatible delta requirements before archiving the conflicting batch.
- [x] 5.4 Strictly validate canonical specs, active changes, and archive state after every batch.
- [x] 5.5 Preserve superseded packet artifacts and discoverable replacement links, then write a self-archive handoff that requires reconciliation to archive last and requires umbrella readiness to run canonical-spec validation plus `openspec_canonical_gate.py --profile legacy-cli --require-canonical`.

## 6. Documentation And Gates

- [x] 6.1 Correct current-state and roadmap documentation only; leave contract-specific CLI, report, runtime, declaration, signal, support-matrix, and release documentation to their owning alpha children.
- [x] 6.2 Extend backlog/status hygiene tests for invalid completed packets, verified-shipped unchecked tasks, and unowned requirements.
- [x] 6.3 Run `uv run --locked pytest -q tests/test_openspec_backlog.py tests/test_openspec_hygiene.py`.
- [x] 6.4 Run `uv run --locked python scripts/ladon_openspec_backlog.py --openspec-root openspec --check`.
- [x] 6.5 Run `uv run --locked python scripts/ladon_openspec_hygiene.py --openspec-root openspec --check`.
- [x] 6.6 Run strict non-interactive validation for all active changes and canonical specs.
- [x] 6.7 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 6.8 Run `openspec validate ladon-openspec-state-reconciliation --strict`.
