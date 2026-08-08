## ADDED Requirements

### Requirement: Exact and segmented name search is correct
The system SHALL use one versioned segmentation function at index and query time, perform case-folded exact lookup through an ordinary index, and union exact matches before FTS ranking.

#### Scenario: Mixed-case exact declaration
- **WHEN** a query supplies an exact declaration name with different letter case
- **THEN** the declaration appears as an `exact-name` result subject only to explicit scope filters

#### Scenario: Exact refinement is monotone
- **WHEN** a name query is refined from a prefix or segments to an exact fully qualified name
- **THEN** the exact result is not lost because of FTS tokenization or ranking

### Requirement: Query operators are explicit
Name search SHALL expose `all`, `any`, and `phrase` modes plus repeatable exclusions and deterministic ownership-aware ranking.

#### Scenario: Query mode differs
- **WHEN** the same terms are queried under `all` and `any`
- **THEN** the request metadata states the mode and results obey its documented Boolean semantics

### Requirement: Freshness is identity-bearing
The system MUST report `verified-fresh` only after comparing the current supported repository inputs with the stored generation; stored-only checks SHALL remain `unchecked`.

#### Scenario: On-disk source is omitted
- **WHEN** a requested configured source file exists but is absent from the indexed population
- **THEN** the result contains an omission or a request error and MUST NOT report a silently complete empty result

### Requirement: Result collection migration is bounded
New name-search results SHALL use `results`; the `index query` compatibility alias MAY expose `rows` only with explicit deprecation metadata during one transition.

#### Scenario: New command returns data
- **WHEN** `proof-search search name` succeeds
- **THEN** consumers can read all matches from `results` without depending on `rows`
