## ADDED Requirements

### Requirement: Import Region Scale Labels

Ladon SHALL distinguish small import-context regions from import-pressure
regions.

#### Scenario: small closure-only imports are context

- GIVEN root-direct-import closures all have reachable module counts below the
  hotspot threshold
- AND no import-pressure findings are present
- WHEN review regions are summarized
- THEN the import region SHALL be emitted as `import_context_region`.

#### Scenario: broad closures remain pressure

- GIVEN a root-direct-import closure reaches at least the hotspot threshold
- WHEN review regions are summarized
- THEN the import region SHALL be emitted as `import_pressure_region`.

#### Scenario: pressure findings force pressure label

- GIVEN import-pressure findings are present
- WHEN review regions are summarized
- THEN the import region SHALL be emitted as `import_pressure_region`.
