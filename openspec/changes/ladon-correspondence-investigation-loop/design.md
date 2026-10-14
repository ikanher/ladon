# Design

## Context

The installed entrypoint lazily dispatches command families; Ladon has no investigation controller. Existing correspondence documents expose omissions but the retest used only three detailed comparisons, no frozen local goals, and stopped well before its ceiling. See proposal.md and the immutable failed report identified in evidence/baseline.json.

## Goals / Non-Goals

Implement a small dependency-free, source-bound queue with a finalization check. Preserve existing proof-IR/result schemas. Automatic extraction of semantic propositions, automatic diagnosis, and a new model evaluation are outside this change; an auditor authors mathematical records.

## Decisions

1. Add a separate lazy `investigation` family with init/status/next/finish. Init exclusively creates an editable versioned JSON plan; the other operations are read-only. This avoids another database, shared-state mutations and build coupling. Auditors save numbered plan snapshots before revisions; original goals and repairs remain separate.
2. Init splits all selected text lines into bounded units. Source units require attributed inventory notes including unnumbered assertions. Claims bind exact quote spans; compared claims require both local contract interpretations and a formal source span. Digests, quoted spans and scope coverage are checked. A name/type search hit alone is not a reviewed contract.
3. Schedule pending inventory, missing source contracts, missing formal comparisons and unresolved follow-ups in deterministic source order. A batch is bounded. A recorded unresolved judgment remains actionable unless a concrete blocker explains why progress cannot be made. Blocked work stays visible while other work proceeds.
4. Finalization uses a recorded UTC start plus a finite budget. Before the deadline actionable work yields exit 2. All scoped work reviewed yields recorded-work-complete; exhaustion or only evidenced blockers yields explicit incomplete status. Clock values and authored blocker reasons are not independently attested. User cancellation takes precedence; it saves an interrupted checkpoint, not a clean completion.
5. Plans and source reads are size/count bounded, root-constrained and digest-checked. JSON parsing rejects duplicate keys/nonfinite values. No arbitrary command execution, Lean invocation or network calls occur. The result exposes attribution and nonclaims so presence checks cannot be mistaken for a detector.
6. Preserve failed run digests, update the generic procedure and Ladon skill, and export a new primary-source workspace with no prior run files or diagnoses. The source CLI must be reachable via installed help; operational examples use the new namespace only. The actual full-exposition retest belongs to a genuinely fresh context after delivery.

## Risks / Trade-offs

- Auditors can write inaccurate contracts or falsely label an inventory/blocker → explicit attribution, source bindings, exact quantities and review controls; no semantic certification.
- A stronger stop gate merely prolongs an unproductive audit → regression tests must show new exact-contract actions, not elapsed-time waiting; report detection benefit as unmeasured.
- Unit boundaries split mathematics → auditor adjusts contiguous source units before review and reads neighboring context; scope coverage must remain intact.
- Local clock changes or edited start time → reject future/nonfinite values and preserve initial plan snapshots; not a tamper-proof time accounting service.

## Migration Plan

Existing manifests and prior pilots stay unchanged. New module/CLI can be removed with its dispatcher branch to roll back; user plans remain ordinary JSON. No dependencies, global registry or production Quux changes.
