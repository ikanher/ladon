# Source-bound investigation loop

`ladon investigation` schedules an authored correspondence audit. It binds quotations to local source bytes and refuses premature completion. It does not discover assertions, compare mathematical meanings, run Lean, or certify an exposition.

Extract a UTF-8 text view of the primary document and preserve the original PDF. Choose the root containing both text and formal sources. Initialize once, at the actual start of the investigation:

```sh
mkdir -p runs/current
pdftotext -layout exposition.pdf runs/current/exposition.txt
ladon investigation init --text runs/current/exposition.txt --root . \
  --output runs/current/plan.json --minutes 90 --unit-lines 80
ladon investigation next --plan runs/current/plan.json --root .
```

For disputed derivations, use `init --derivations` and [local derivation challenges](DERIVATION_CHALLENGES.md). Version two prioritizes missing step reviews before unrelated inventory and can replay exact rational witnesses. The default version-one behavior described below remains compatible.

The initialized plan partitions all selected lines into pending units. Examine each unit, recording stated results, intermediate assertions and applications, including displayed mathematics. Mark its inventory `done` only after recording those claims, with an attributed `note` explaining the inventory or why no assertions were identified. The controller cannot verify that this inventory is complete.

Author the plan as JSON and save numbered snapshots after each batch. Every claim has a unique `id`, an existing `unit`, inclusive `startLine` and `endLine`, a `quote` equal to those complete source lines joined by newlines without a trailing newline, and a `state`. States advance as follows:

- `captured`: write the exact local contract next.
- `contract`: find and compare exact formal support next.
- `reviewed`: keep investigating if either statement or method judgment is `unresolved`.
- `blocked`: retain evidence, the next action and the condition needed to resume.

A `contract` is an object with seven nonempty text fields: `objects`, `assumptions`, `domains`, `quantifiers`, `conclusion`, `dependencies`, `neededImplication`. Both the source interpretation and formal counterpart need these fields. Preserve formulas, parameter ranges and dependencies explicitly; a summary such as “an estimate” is inadequate. These are attributed mathematical interpretations; the controller only checks their presence.

A reviewed claim additionally contains:

```json
{
  "formal": {
    "path": "formalization/Example.lean",
    "sha256": "actual SHA-256 of the complete file bytes",
    "startLine": 10,
    "endLine": 14,
    "statement": "exact complete lines 10 through 14, joined with newlines",
    "contract": {
      "objects": "...", "assumptions": "...", "domains": "...",
      "quantifiers": "...", "conclusion": "...", "dependencies": "...",
      "neededImplication": "..."
    }
  },
  "judgment": {
    "statement": "aligned",
    "method": "same",
    "evidence": "specific comparison and proof-body evidence"
  }
}
```

Statement judgments are `aligned`, `mismatch`, or `unresolved`; method judgments are `same`, `different`, or `unresolved`. They answer separate questions. Missing support remains unresolved or blocked; do not invent a counterpart to make the gate pass. A blocker needs nonempty `kind`, `evidence`, `nextAction` and `unblockCondition`. One blocked claim does not stop actionable work elsewhere.

After each batch, use `next` and work on the returned queue. Pending source inventory comes first, then local obligations in source order. `--limit` bounds the displayed next batch (1–100); `nextOmitted` reports hidden queue entries. The full queue is reconstructed from the preserved plan. Read relevant formal definitions and proof bodies, and check the implication needed at the actual application. Reserve enough budget for comparisons across the inventory before deep proof engineering.

Before ending the investigation, run:

```sh
ladon investigation finish --plan runs/current/plan.json --root .
```

A `continue` result exits 2: useful recorded work remains before the deadline, so continue. After budget exhaustion, remaining work yields `incomplete-budget`. If all remaining claims have evidenced blockers and inventory is done, the result is `incomplete-blocked`. These outcomes allow a final report but preserve its incompleteness. `recorded-work-complete` means only that the authored records have resolved judgments. It says nothing about mathematical truth or assertions omitted from the inventory. An explicit user cancellation overrides this workflow; record that intervention.

`status`, `next` and `finish` read without changing the plan. `init` creates a new file exclusively. Changed digests or quotations, invalid partitions, duplicate IDs/JSON keys, future or timezone-free start times, and paths escaping the root reject with exit 2. Plans are limited to 4 MiB, individual source files to 8 MiB, distinct source bytes to 128 MiB, and units/claims to 4096 each. Sources must be regular UTF-8 files. The workflow clock and authored evidence are not tamper-proof.

The portable example at `scripts/demo_investigation.py` exercises a quantitative mismatch and a faithful counterpart through the public CLI. Run `python scripts/demo_investigation.py --output /tmp/ladon-investigation-demo` with a new output directory. It demonstrates bookkeeping and distinct attributed judgments; it is not a scored detection experiment.

For this development checkout, invoke the current source from the Ladon directory:

```sh
cd /home/codex/projects/ladon
uv run --locked python -m ladon.entrypoint investigation checkpoint \
  --plan /absolute/path/plan.json --root /absolute/path/source-root \
  --output /absolute/path/new-checkpoint.json
uv run --locked python -m ladon.entrypoint investigation finalize \
  --plan /absolute/path/plan.json --root /absolute/path/source-root \
  --output /absolute/path/new-terminal.json
```

Both operations reassess the source-bound plan. A checkpoint preserves the queue,
original `startedAt` and budget. A refused finalization prints `continue`, exits
2 and creates no terminal output. Consume that result by choosing an item from
`next`, doing the indicated source review or correspondence work, saving a new
plan, and checkpointing again. Do not reset the clock or wait idly for its budget
to expire. Plain agent prose is outside this CLI gate.

A terminal receipt permits an incomplete report when the budget has elapsed,
every remaining item has an evidenced blocker, or an actual user stop is
recorded. This permission is separate from mathematical review and formal
correspondence. Reading stored checks performs no fresh Lean replay.

Version-three plans can optionally contain `workBlockers` with profile
`work-blockers-v1` and `records` of `{workId, blocker}`. `workId` is the canonical
`ladon.proof_slice.digest` of one complete current queue item. Each blocker needs
`kind`, `evidence`, `nextAction`, and `unblockCondition`; `policy-limited` also
requires `unverifiedScope`. Only matched items leave the actionable queue. A
changed obligation rejects its stale blocker. These records retain unverified
work and do not mark its inventory or review complete.

For an actual cancellation, `finalize --stop-record FILE` accepts a closed
`ladon-investigation-user-stop-v1` record with `actor`, UTC `at`,
`instructionRef`, `reason`, `planId` (digest of the exact plan), and `scopeId`
(digest of its scope). Record the actual instruction; never invent cancellation
to pass the gate. Actor and clock fields are attributed, not authenticated.
`validate_progress_receipt` checks immutable receipt identity against the exact
plan and current source. Historical reports are not overwritten or relabeled.

The portable command regression is executable from this directory:

```sh
uv run --locked pytest -q tests/test_investigation_finalization.py \
  tests/test_investigation_stop_receipts.py tests/test_investigation_work_blockers.py
```

The bounded live continuation example performs an unresolved source
interpretation and attaches it after a refused finalization. Run it with a new
output directory; it leaves the investigation open and saves its actual CLI log:

```sh
cd /home/codex/projects/ladon
uv run --locked python scripts/demo_investigation_finalization.py \
  --output /tmp/ladon-continuation-new
uv run --locked pytest -q tests/test_investigation_continuation_driver.py
```

The deterministic test drives the same public operations at 57.65 minutes of a
90-minute budget. It records a next action while retaining 32.35 minutes;
it does not wait for the budget to expire. The unresolved interpretation has
no formal counterpart and grants no mathematical authority.
