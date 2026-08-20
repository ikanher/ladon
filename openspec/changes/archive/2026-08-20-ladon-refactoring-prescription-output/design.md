## Context

Architecture smells and code smells are indicators. Prescriptions should guide
review work without applying edits or hiding evidence.

## Goals / Non-Goals

**Goals:**
- Convert findings into action taxonomy rows.
- Preserve evidence, confidence, priority, and nonclaims.

**Non-Goals:**
- Do not auto-refactor source.
- Do not reduce findings to a single quality score.

## Decisions

- Keep prescriptions in a separate `refactoring_prescriptions` namespace.
- Prioritize direct core boundary violations above lower-impact naming smells.

## Risks / Trade-offs

- Prescriptions can be wrong without domain context; mitigate with evidence and
  confidence fields.
