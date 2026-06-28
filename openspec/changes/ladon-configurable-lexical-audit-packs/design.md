## Context

The generic source-pattern engine exists. This packet makes it reusable through
policy pack examples and fixtures.

## Goals / Non-Goals

**Goals:**

- Provide reusable pack shapes for stale terms, trust markers, TODO classes, and
  banned prose.
- Preserve zero-match coverage reporting.
- Keep generated filtering configurable.

**Non-Goals:**

- No bundled project-specific stale term defaults.
- No semantic proof interpretation from text matches.

## Decisions

- Packs are JSON data, not analyzer constants.
- Pattern summaries distinguish total matches from reported capped matches.

## Risks / Trade-offs

- Policy packs can be mistaken for defaults -> Require explicit policy source
  and docs.
