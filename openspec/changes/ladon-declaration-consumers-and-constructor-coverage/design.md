## Context

The elaborated dependency surface already records forward declaration dependencies.
The index can invert those edges and instantiate structure field types, but coverage
status requires the premise-difference authority rather than basename matching.

## Goals / Non-Goals

**Goals:** exact reverse consumers, field coverage matrices, supplier strength/range
classification, qualitative/quantitative separation, and leakage diagnostics.

**Non-Goals:** no proof of architectural necessity, constructor synthesis, or claim
that an unprobed supplier fills a field.

## Decisions

- Invert only Lean-observed dependency edges for confirmed consumers; parser/text
  candidates remain a separate optional hint class.
- Elaborate structure parameters from the constructor goal before deriving field
  target types, so coverage is request-specific rather than generic-name based.
- For each field, run type search and premise difference, then classify exact,
  stronger-premise, restricted-range, adapter-dependent, or unmatched.
- Let repository policy annotate quantitative versus qualitative roles while always
  retaining the actual field type.
- Flag certificate leakage only when a constructor premise is definitionally equal or
  Lean-equivalent through a bounded transparent wrapper to the target field.

## Risks / Trade-offs

- [Reverse dependencies are incomplete] → State backend/coverage and never mix
  parser hints into confirmed consumers.
- [Field instantiation fails] → Emit the unresolved parameters and stop classification.
- [Leakage warnings are misread] → Label as review diagnostics with exact evidence.

## Migration Plan

Add reverse queries first, then instantiated field inventory, then coverage/leakage
rows. Keep existing declaration graph unchanged.
