# Spec Delta

## Purpose

Expose bounded, source-associated portions of actual Lean proof reasoning,
including instantiated applications and the evidence supplying their premises.

## ADDED Requirements

### Requirement: Actual application observations
A supported proof slice SHALL identify the exact source and Lean environment and expose observed application terms, instantiated arguments, conclusion, and local context. Declaration-name dependencies or authored summaries SHALL NOT substitute for an observed application.

#### Scenario: Same lemma used at two different instantiations
- **WHEN** a proof applies one lemma to distinct parameters
- **THEN** the slice retains distinct applications and their actual argument substitutions rather than merging them by declaration name

### Requirement: Complete local premise accounting
Each extracted step SHALL preserve ordered premise occurrences, implicit arguments, local-definition values, and provider references. A premise SHALL be identified as supplied by a scoped provider, an explicit boundary assumption, or an unresolved frontier. All conjunctive premise branches SHALL remain visible.

#### Scenario: Only one branch has been expanded
- **WHEN** a selected application needs two premises and extraction follows only one provider
- **THEN** the second premise remains an explicit requirement and the slice is not reported closed

### Requirement: Witness scope and branch isolation
Extraction SHALL preserve witness introduction, binder scope, branch assumptions, and earlier-context availability. It SHALL NOT allow a branch-local witness or an unavailable later fact to supply a premise outside its valid context.

#### Scenario: Witness escapes a case branch
- **WHEN** an alignment attempts to use an existential witness outside the branch that introduces it
- **THEN** the scope violation is rejected or left as an explicit unsupported obligation without checked support

### Requirement: Bounded extraction with observable residuals
Slice extraction SHALL enforce finite source selection, traversal, expression, output, process-time, and memory bounds. Missing attribution, unsupported source forms, or exhausted bounds SHALL return named omissions or operational failure without implying absence or complete coverage.

#### Scenario: Proof slice reaches the configured node bound
- **WHEN** additional premise providers remain after the node budget is consumed
- **THEN** the result identifies the unexpanded frontier and reports incomplete extraction

### Requirement: Extraction authority remains separate from replay
An observed formal slice SHALL retain its actual provenance and SHALL distinguish extraction from independent checking of any selected application. Checked evidence SHALL bind exact source, context, toolchain, dependencies, and trust results; source drift SHALL prevent reuse as current evidence.

#### Scenario: Local provider changes without changing the theorem name
- **WHEN** a local definition or proof provider changes after extraction
- **THEN** prior replay cannot establish the current application until the changed context is re-observed and checked
