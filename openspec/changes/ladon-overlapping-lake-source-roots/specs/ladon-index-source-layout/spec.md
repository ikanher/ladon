# Source ownership in the lexical index

## Purpose

Keep lexical indexes usable and module identities accurate when Lake library source roots overlap. Surface ownership conflicts where the caller can resolve them.

## ADDED Requirements

### Requirement: Resolved overlapping roots preserve canonical module ownership

The lexical index SHALL use confirmed module ownership when overlapping roots give a source multiple candidate module names. The same ownership SHALL apply to build, update, freshness, and scoped queries.

#### Scenario: A nested library owns a source inside a broader library directory

- **WHEN** a supported layout or explicit ownership selection identifies the nested library as the canonical owner of the shared source
- **THEN** the index publishes the source under its confirmed module name and the broader library's unaffected modules remain searchable
- **AND** the discarded candidate does not appear as a second owning module
- **AND** an unchanged source status check reports the published generation as current

### Requirement: Unresolved source ownership has an actionable diagnostic

The lexical index SHALL report unresolved source ownership before publication. The diagnostic SHALL identify the source path, the competing module names, and how to resolve the conflict. Any previously published generation SHALL remain available.

#### Scenario: Overlapping roots give a source two names without a confirmed owner

- **WHEN** a build or update encounters overlapping candidate ownership and cannot determine the canonical owner
- **THEN** it reports the conflicting source and both candidate names with resolution guidance
- **AND** it preserves any prior published generation and publishes no replacement for the failed attempt
