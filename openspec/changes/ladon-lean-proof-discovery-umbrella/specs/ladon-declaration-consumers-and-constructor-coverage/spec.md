## ADDED Requirements

### Requirement: Reverse declaration consumers
Given a declaration or structure field, Ladon SHALL list project-owned declarations
that consume it through Lean-observed dependency evidence, with source locations.

#### Scenario: Primitive authority consumers
- **WHEN** a caller queries consumers of a compiled primitive theorem or structure
- **THEN** results identify immediate project-owned consumers, owner modules, source ranges, dependency kind, and evidence backend

#### Scenario: Parser-only candidate
- **WHEN** only a parser reference suggests consumption
- **THEN** it is separated as an unconfirmed hint and not merged into Lean-confirmed consumers

### Requirement: Instantiated structure-field coverage
For an attempted constructor, Ladon SHALL instantiate every structure field in the
local parameter context and compare it with the active declaration inventory.

#### Scenario: PathBounds coverage matrix
- **WHEN** a caller supplies a `PathBounds` constructor goal and local context
- **THEN** the response lists every instantiated field type, candidate suppliers, source links, and coverage status

### Requirement: Coverage strength and role classification
Field suppliers SHALL be classified as exact, stronger-hypothesis,
restricted-range, adapter-dependent, or unmatched, while quantitative and
qualitative roles remain separately visible.

#### Scenario: Existence versus numerical bound
- **WHEN** an all-row field needs only integrability existence but a retained-row field needs a uniform quantitative bound
- **THEN** the matrix keeps the two obligations distinct and does not reject the existence supplier for lacking the stronger numerical estimate

#### Scenario: Restricted row supplier
- **WHEN** a supplier requires a row guard absent from an all-row field
- **THEN** the field is marked restricted-range with that guard as an unmatched premise

### Requirement: Certificate-leakage diagnostics
Ladon SHALL flag a proposed constructor premise that is Lean-equivalent, through the
supported transparent boundary, to the field the constructor claims to derive.

#### Scenario: Equivalent field passed through
- **WHEN** a constructor still accepts a premise definitionally equal to an unmatched target field
- **THEN** the coverage matrix reports possible certificate leakage with both source surfaces and an inspection-only nonclaim

### Requirement: No constructor-proof overclaim
Coverage status MUST distinguish indexed candidate, Lean type match, premise-closed
route, and compiled probe.

#### Scenario: Candidate not probed
- **WHEN** a field has a matching declaration but no successful application probe
- **THEN** Ladon does not label the field compiled or filled
