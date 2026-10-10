# Design

## Context

See proposal.md. Current extraction takes the first masked `:=`, including let initializers and parameter defaults. The helper identity is part of generation/freshness metadata, but incremental update currently compares only source deltas for its no-op decision. Evidence-preserving update already owns archive and atomic publication.

## Goals / Non-Goals

Keep lexical operation independent of Lean. Fix ordinary statement boundaries and make uncertain cases honest. Reuse current archive, locking, budget and validation owners; no general parser service, database version change or compiled evidence reuse.

## Decisions

- Use a bounded syntax-aware lexical boundary owner, preserving offsets from the existing comment/string mask. Track delimiters and assignment-bearing constructs instead of choosing the first assignment. Guard unsupported/ambiguous cases with visible limitations. A complete Lean parser would require a new dependency or runtime, outside this lexical operation.
- Advance the lexical helper identity and recognize exactly its predecessor for update recovery. Re-extract old cached modules instead of transferring their incomplete text. Existing metadata and generation ownership make stored-only versus verified freshness distinct.
- Feed helper recovery into the existing source/evidence-preserving publication path; old evidence is archived and cleared from current lexical projection. Unknown helpers and configuration changes require a new build path. Current no-op remains unchanged.
- Update only the consumer runbook in the concurrent mathematical project. No source, cache or shared index mutations; real regression replay uses private copies of the reported owners.

## Risks / Trade-offs

Lean allows extensible syntax; lexical extraction cannot certify arbitrary syntax. Negative controls must cover proof-token leakage, nested delimiters, comments/strings and unsupported constructs. Stop for a design adjustment if the supported scanner cannot preserve a tested case without silently guessing. Cached recovery costs a one-time re-extraction across modules; retain extraction counts and a real-owner installed replay.

## Migration Plan

Release 0.2.3 with a new extraction identity; `index update` recovers the recognized prior identity even when sources are unchanged. Preserve old evidence and current input policy. Rollback by retaining the archived original and selecting a separate old-compatible index path; do not overwrite history. Existing qualified 0.2.2 evidence remains historical.
