## MODIFIED Requirements

### Requirement: Ladon's clean core SHALL preserve tested module-DAG reporting

The clean core SHALL preserve a tested smoke path for Lean module discovery,
module-DAG analysis, and JSON/text report rendering.

#### Scenario: Tiny Lean fixture report is generated

- **WHEN** equivalent CLI smoke invocations analyze a local tiny Lean fixture without `--build`, selecting JSON and text separately
- **THEN** JSON output contains metadata and a module-DAG summary
- **AND** text output contains a concise module-DAG section
- **AND** no Lake invocation is required for this smoke path
