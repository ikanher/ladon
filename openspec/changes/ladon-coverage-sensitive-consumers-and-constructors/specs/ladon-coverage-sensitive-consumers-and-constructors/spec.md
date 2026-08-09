## ADDED Requirements

### Requirement: Consumer status follows semantic dependency coverage
`consumers` SHALL report `complete` only when the selected declaration population has authoritative complete dependency coverage. Empty or partial populations SHALL report `unavailable` or `partial` with reason and counts.

#### Scenario: Dependency table has zero authoritative rows
- **WHEN** a known declaration is queried in a lexical generation
- **THEN** the result reports `not-populated` rather than claiming that the declaration has no consumers

#### Scenario: Complete population has no reverse users
- **WHEN** complete semantic coverage is recorded and no matching edges exist
- **THEN** the result reports a complete empty consumer set with the covered population identity

### Requirement: Constructor queries use stored structure evidence
The constructor CLI SHALL resolve the requested structure, load ordered stored fields and supplied arguments, and distinguish missing structure, absent field extraction, partial fields, a known zero-field structure, and complete nonempty fields.

#### Scenario: Known structure has no indexed field population
- **WHEN** the structures table contains the owner but field coverage is unavailable
- **THEN** the result reports `structure-fields-not-indexed` and MUST NOT report an available zero-field structure

### Requirement: Coverage payloads expose populations and omissions
Consumer and constructor results SHALL include generation identity, freshness, evidence authority, total indexed declarations/dependencies/structures/fields, selected-scope counts, caps, truncation, and actionable omissions.

#### Scenario: Result is partial
- **WHEN** only some modules have semantic extraction
- **THEN** the response names or bounds omitted modules and does not silently generalize observed absence

### Requirement: Compatibility is explicit
Coverage-sensitive responses SHALL use a new versioned result schema or explicit compatibility metadata; old fields MUST NOT retain misleading semantics under the old version identifier.

#### Scenario: Existing caller reads the old schema
- **WHEN** compatibility output is requested during transition
- **THEN** deprecated status semantics are labeled and the new coverage object remains available
