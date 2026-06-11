## Context

Ladon already exports atlas JSON, SQLite tables, atlas diffs, and reviewer
cards. The ProofIR bridge separately emits joins, diagnostics, trust rules, and
reviewer cards. These surfaces share the same reviewer goal but are not yet a
single workflow.

## Goals / Non-Goals

**Goals:**

- Make atlas cards the default reviewer entry point for report sets.
- Answer five review questions: what changed, what recurs, which roots need
  review first, which joins are low-confidence, and which packets are incomplete
  or stale.
- Preserve machine-readable JSON and SQLite outputs.
- Integrate optional ProofIR bridge diagnostics without moving bridge logic into
  clean core.

**Non-Goals:**

- No web UI.
- No graph database dependency.
- No LLM-generated explanations.
- No theorem-truth, witness-adequacy, or ProofIR-authority promotion.

## Decisions

1. Keep atlas JSON canonical.

   SQLite, Markdown, and cards remain derived artifacts. This keeps diffs stable
   and avoids introducing a storage dependency.

2. Add bridge-aware rows only when bridge reports are supplied.

   The atlas workflow should support normal Ladon report sets and report sets
   augmented by bridge diagnostics.

3. Make reviewer cards concise and evidence-routed.

   Cards should point to strongest evidence and known non-claims, not copy full
   report tables.

4. Keep CLI scripts composable.

   Existing scripts can grow options for bridge inputs or workflow outputs
   rather than being replaced by a large command.

## Risks / Trade-offs

- Cards become too verbose -> Keep detailed rows in JSON/SQLite and summarize
  only top routes.
- Optional bridge data confuses core status -> Namespace bridge diagnostics and
  keep trust notes visible.
- Query drift -> Add tests for each canned question before broadening outputs.
