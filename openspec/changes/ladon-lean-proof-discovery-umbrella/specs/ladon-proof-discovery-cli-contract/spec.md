## ADDED Requirements

### Requirement: Ordinary proof-search command family
Ladon SHALL expose proof discovery through the installed caller-neutral CLI and
SHALL reuse the canonical output, stream, report-version, and exit contracts.

#### Scenario: Installed help
- **WHEN** a caller runs `ladon proof-search --help` from an installed candidate
- **THEN** the command exits zero and lists the maintained proof-search operations without caller-specific or hidden model options

#### Scenario: No-build query default
- **WHEN** a caller runs an index-backed proof-search query without an explicit refresh or Lean probe
- **THEN** Ladon SHALL NOT run Lake build or silently switch the query into architecture analysis

### Requirement: Canonical output options
Proof-search commands MUST use `--format`, `--output`, and explicit report-version
selection consistently with the existing CLI authority.

#### Scenario: JSON stdout
- **WHEN** JSON format and `-` output are selected
- **THEN** stdout contains one versioned JSON document and diagnostics remain on stderr

#### Scenario: Removed compatibility examples
- **WHEN** maintained docs and skills are checked
- **THEN** they contain no active example using `--skip-build`, `--output-json`, or `--output-text`

### Requirement: Compact proof-work presentation
The CLI SHALL provide a compact proof-search presentation that omits architecture
smells unless the caller explicitly requests architecture context.

#### Scenario: Default proof-search text
- **WHEN** a type, semantic, consumer, or field query completes in text mode
- **THEN** the output prioritizes candidates, match routes, premises, source links, scope, and freshness rather than repository-wide naming findings

### Requirement: Maintained documentation and skill parity
Ladon SHALL keep `README.md`, `docs/CLI.md`, proof-discovery documentation, and the
distributed Codex Ladon skill consistent with installed help and SHALL include one
maintained proof query.

#### Scenario: Installed example gate
- **WHEN** the documentation conformance test executes each maintained proof-search example against an installed wheel
- **THEN** every command parses with the documented behavior and uses the same public entrypoint available to human callers
