## ADDED Requirements

### Requirement: Elaborated type-pattern search
Ladon SHALL accept an elaborated target type or partial type pattern with explicit
wildcards and search declarations in the selected indexed scope.

#### Scenario: Partial integrability pattern
- **WHEN** a query supplies an anchored `Integrable` proposition with wildcarded parameters and implicit arguments
- **THEN** Ladon returns declarations whose Lean-elaborated types match and reports the wildcard substitutions

#### Scenario: Pattern cannot elaborate
- **WHEN** the query pattern cannot elaborate in the selected namespace/import context
- **THEN** the command returns an operational query diagnostic and does not fall back silently to substring search

### Requirement: Ordered bounded match routes
Matches MUST be classified and ranked in the order direct unification, equality
symmetry, bounded definitional reduction, registered coercion, and explicitly named
adapter route.

#### Scenario: Direct match outranks transformed match
- **WHEN** one declaration unifies directly and another needs symmetry or an adapter
- **THEN** the direct declaration ranks first and each row identifies its distinct match route

#### Scenario: Search budget exhausted
- **WHEN** candidate, reduction, adapter, or time limits are reached
- **THEN** the response is explicitly truncated and does not claim complete search results

### Requirement: Source-complete result evidence
Every result SHALL include fully qualified name, kind, owner module/package,
elaborated type, source location when available, required import, substitutions,
scope, index freshness, and match authority.

#### Scenario: External declaration without source range
- **WHEN** an external indexed declaration matches but no local source range exists
- **THEN** the row retains package/module/import evidence and explicitly marks the location unavailable

### Requirement: Semantic name and signature search
Ladon SHALL search tokenized names, namespaces, docstrings, and elaborated signatures
with conjunction and exclusion filters.

#### Scenario: Semantic segmented name
- **WHEN** a caller searches `all row corrector integrable` within project-owned scope
- **THEN** segmented name/signature matches can find a declaration such as an all-state corrector integrability theorem without requiring its exact identifier

#### Scenario: Excluded collision
- **WHEN** a NOT filter or ownership restriction excludes an unrelated generated or external collision
- **THEN** the collision is omitted with the applied filter visible in query metadata

### Requirement: Family and failed-route context
Results SHALL group known theorem families, identify likely wrappers/aliases versus
mechanism-facing authorities, and preserve unchanged failed-route evidence.

#### Scenario: Previously rejected candidate
- **WHEN** a candidate has the same relevant fingerprints as a stored rejected route
- **THEN** Ladon reports the rejection reason and does not present it as a fresh unexplained recommendation
