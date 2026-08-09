## ADDED Requirements

### Requirement: Conceptual ranking rewards concentrated segment matches
`any` search SHALL downweight versioned generic theorem tokens, reward multiple distinct query segments in one candidate basename, preserve exact and phrase precedence, and use deterministic ownership/name/source tie breaks.

#### Scenario: Specific path-theta candidate competes with generic bound names
- **WHEN** the query contains `path theta displacement bound`
- **THEN** candidates matching multiple specific basename segments rank ahead of candidates matching only generic `bound` or `path`

### Requirement: Ranking evidence is inspectable
JSON results SHALL expose normalized query segments, ignored/downweighted terms, per-candidate matched segments, contribution classes, minimum-match policy, and ranking identity.

#### Scenario: Caller questions an ordering
- **WHEN** two results have different scores
- **THEN** their contribution evidence explains the deterministic ordering without exposing an undocumented opaque score

### Requirement: Any-mode breadth is caller-bounded
The CLI SHALL provide a finite minimum matched-segment control whose default prevents one generic segment from dominating multi-term conceptual queries while preserving an explicit broad mode.

#### Scenario: Four-term query uses the default
- **WHEN** only one generic term matches a candidate
- **THEN** that candidate is omitted or ranked in a separately labeled broad fallback population

### Requirement: Owner projection is focused by default
Owner analysis SHALL render selected and co-reachable graph evidence first, summarize repository-global integrity counts compactly, and omit global candidate samples unless an explicit global projection is requested.

#### Scenario: Selected graph contains two modules
- **WHEN** repository-global integrity inventory contains tens of thousands of candidates
- **THEN** default text output remains bounded to owner evidence plus compact global counts

### Requirement: Report bounds and omissions are explicit
Every projection SHALL report selected/global populations, per-section caps, truncation, omitted sample classes, and the flag needed to request wider evidence.

#### Scenario: Global samples are suppressed
- **WHEN** default owner projection omits them
- **THEN** the result reports their counts and omission reason rather than implying they do not exist
