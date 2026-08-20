## Context

Ladon already emits direct policy findings. This packet improves triage by
making each row say what to inspect first and why.

## Goals / Non-Goals

**Goals:**

- Add pair, file, context, and suggested-action metadata.
- Render text reports summary-first.
- Preserve full detail in JSON.

**Non-Goals:**

- No automatic refactor.
- No claim that a suggested action is the unique correct design.

## Decisions

- Compute summaries from findings to keep JSON detail and text summaries
  consistent.
- Use generic context classifiers with project override hooks.

## Risks / Trade-offs

- Suggestions can sound too strong -> Use review-oriented wording and source
  evidence in every row.
