## Context

The proof-surface audit already emits spec-stub, missing-gate, missing-axiom,
suspicious-axiom, clean-endpoint, frozen-hub, and escaped-proof-hole diagnostics.

## Goals / Non-Goals

**Goals:**
- Reuse the existing proof-surface route audit.
- Preserve verifier metadata from handoff rows.
- Summarize completeness without duplicating trust rules.

**Non-Goals:**
- Do not add a second proof trust subsystem.
- Do not run Lean checks by default.
- Do not validate theorem truth.

## Decisions

- Add handoff fields to normalized witness rows.
- Add route completeness as derived metadata inside `proofSurface`.

## Risks / Trade-offs

- Completeness may be mistaken for proof truth; mitigate by keeping
  `routeGovernanceOnly` and nonclaim text.
