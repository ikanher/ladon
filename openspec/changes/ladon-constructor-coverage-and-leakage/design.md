## Context

Constructor coverage combines semantic structure inspection, instantiated dependent fields, type search, difference analysis, and dependency evidence.

## Goals / Non-Goals

**Goals:** exactly one row per unresolved field, batched matching, conservative categories, quantitative/adapter labels, and three explicit leakage classes.

**Non-Goals:** treating heuristic field categories as proof facts or requiring editor goal capture for the P0 API.

## Decisions

1. P0 accepts explicit module, structure, parameters, and assumptions; later goal capture feeds the same engine.
2. Instantiate fields in declaration order and batch SQL/Lean checks across all fields.
3. Leakage checks separate definitionally equivalent field inputs, direct projection dependencies, and alias/reducible projection dependencies.
4. Heuristic quantitative/adapter classification is labelled `heuristic_classification`; registry-backed labels retain their rule authority.

## Risks / Trade-offs

- [Dependent fields are mis-instantiated] → Lean helper owns instantiation and fixture covers dependencies/inheritance.
- [Leakage false positives] → exact binder/dependency evidence and verification state per finding.
