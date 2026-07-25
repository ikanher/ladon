## Context

The pre-program snapshot contained nine active packets and 81 unchecked tasks.
Creating the alpha-hardening umbrella and eight children intentionally changed
the live snapshot to 18 active packets and 311 unchecked tasks. Of the nine
legacy packets, seven appear implemented, partly superseded, or stale, while
the remaining Review Radar and theorem-surface packets duplicate part of each
other's scope. Two completed ProofIR packets fail strict validation, multiple
historical packets lack automation metadata, and canonical specs/archive
directories do not represent the large completed history.

Existing `ladon_openspec_backlog.py` and `ladon_openspec_hygiene.py` already
detect parts of this drift. Reconciliation should use and strengthen those
surfaces instead of introducing another inventory system.

## Goals / Non-Goals

**Goals:**

- Establish an evidence ledger for every active/completed status change.
- Give each residual capability one authoritative packet.
- Strictly validate and archive completed work in conflict-aware batches.
- Make current-state/roadmap docs and backlog reports agree with shipped source.

**Non-Goals:**

- Implement Review Radar or semantic changelog behavior.
- Mark work complete solely because an umbrella checkbox says so.
- Rewrite historical proposals or discard conflicting specs without review.
- Archive the new alpha children before implementation.
- Duplicate lifecycle ordering already owned by the alpha dependency ledger.

## Decisions

1. **Create a tracked legacy reconciliation ledger.** For each pre-program
   active candidate, invalid completed packet, or reviewed archive batch it
   records disposition (`complete`, `superseded-with-residuals`, `retained`, or
   `blocked`), source/test/gate evidence, authoritative replacement, residual
   owner, spec conflicts, and archive result. The alpha umbrella's typed
   dependency ledger remains the sole lifecycle authority for its new children.
   A raw task-count normalization was rejected because checkboxes can drift in
   either direction.

2. **Classify seven stale candidates only with evidence.** Common-layer/facade,
   lexical packs, fix triage, generated attribution, policy persistence, proof
   x-ray roadmap, and review-signal benchmarks are checked against their
   completed umbrella/replacement and current tests. Generated attribution and
   review-signal benchmarks can be superseded only after their residual
   positive/negative predicate oracles—including source-pattern and
   claim-authority boundaries—and metric/drift obligations move to the alpha
   signal and benchmark owners. Proof-xray is split: completed staging keeps
   quoted witness/trust rows, the alpha declaration child owns direct
   Lean-observed statement/type/value dependency and axiom/sorry/unsafe facts,
   and `ladon-proof-xray-roadmap` remains narrowed to any future
   tactic-skeleton/InfoTree evidence contract. Native generation is not claimed
   as an existing legacy requirement.

3. **Narrow the remaining future lane.** The Review Radar change remains a
   planning umbrella, not an implementation packet. The ownership chain is
   alpha elaborated-declaration surface → bounded theorem-surface changelog
   child → future Review Radar MVP child. The changelog consumes declaration
   output and cannot define a parallel extractor. Review Radar implementation
   checkboxes are removed from the planning umbrella and may be introduced only
   in that later bounded MVP child. Completed proof-xray staging remains the
   authority for quoted-witness normalization, not all future proof analysis.
   The planning umbrella's delta specs are rewritten: concrete semantic
   changelog requirements move to the theorem-surface child, while optional
   proof-xray enrichment retains only consumer availability/nonclaim behavior
   and references its extraction owners.

4. **Archive in dependency/conflict batches.** Validate a packet, compare its
   delta requirements with canonical/current replacements, archive, then
   validate canonical specs before continuing. Bulk-moving all completed
   directories was rejected because duplicate capability specs could overwrite
   one another. `ladon-pipeline-phase-boundaries-timing` is archived first
   because `ladon-clean-core-radon-gate` modifies its `ladon-pipeline`
   capability. The clean-core packet then creates `ladon-python-quality`,
   followed by the `ladon-root-matrix` and `ladon-proof-xray-staging` source
   additions. Only then is this reconciliation packet archived so its MODIFIED
   deltas become canonical; the umbrella's archive-aware readiness gate
   validates those canonical postconditions.

5. **Repair process metadata at the source.** Add missing validation commands
   and automation files where a packet remains part of the historical record;
   fix the two invalid completed ProofIR packets or document a safe superseding
   archive route.

6. **Strengthen existing hygiene gates.** Required output distinguishes active
   implementation work, completed-unarchived work, superseded work, invalid
   packets, and status metadata drift. CI fails on newly introduced drift after
   the baseline is reconciled.

7. **Keep documentation ownership local to the changing contract.**
   Reconciliation corrects current-state and roadmap claims only. The dedicated
   alpha children own CLI, report, runtime, declaration, signal, support-matrix,
   and release-gate documentation. All caller wording describes one shared,
   caller-independent contract across supported public entrypoints.

8. **Migrate legacy flag requirements with new deltas.** This reconciliation
   change owns modified `ladon-python-quality` and `ladon-root-matrix`
   requirements that replace `--skip-build` with omission of explicit
   `--build`. Historical packet text remains untouched. The `ladon-pipeline`
   prerequisite and then their source additions are canonicalized first;
   archiving this reconciliation packet then applies the MODIFIED deltas. The
   CLI may integrate flag removal only after the archive-aware canonical
   milestone passes. Merely editing old proposals or hoping unspecified archive
   order resolves the conflict was rejected.

## Risks / Trade-offs

- **Historical specs conflict** → Stop the batch, record the conflict, and choose
  one authoritative requirement before archive.
- **Evidence is insufficient for a stale packet** → Keep it active with narrowed
  residual tasks; never infer completion.
- **Mass archive creates an unreadable diff** → Use reviewed batches and a
  machine-readable ledger.
- **Documentation cleanup changes product claims** → Cross-check source, tests,
  and the authority boundary; avoid aspirational wording.

## Migration Plan

Capture the pre-reconciliation inventory, resolve active packets, repair strict
validation blockers, archive base additions and other completed changes in
batches, regenerate the backlog report, and update docs. Prepare a self-archive
handoff, then let the umbrella archive reconciliation last and verify its
canonical deltas. Rollback restores a batch from version control; the ledger
preserves the reason for every move.

## Open Questions

- Conflicting canonical spec choices are resolved during implementation and
  recorded in the ledger rather than predetermined here.
