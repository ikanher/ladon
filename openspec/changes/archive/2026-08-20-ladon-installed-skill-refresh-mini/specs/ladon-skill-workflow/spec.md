## ADDED Requirements

### Requirement: Installed Skill Matches Current Ladon CLI

The installed Ladon Codex skill SHALL describe the current shared CLI workflow.

#### Scenario: Lean declaration graph workflow is documented

- GIVEN a Codex instance reads the installed Ladon skill
- WHEN it needs root declaration graph triage
- THEN the skill SHALL show `--extraction-backend lean` with root scope.

#### Scenario: cache workflow is documented

- GIVEN a Codex instance reads the installed Ladon skill
- WHEN it repeats Lean-backed root runs
- THEN the skill SHALL show `--lean-cache-dir`.

#### Scenario: declaration graph limitations are documented

- GIVEN a Codex instance reads a declaration graph report
- WHEN it interprets references and unresolved candidates
- THEN the skill SHALL warn that these are conservative parser candidates rather
  than elaborated proof dependencies.
