## ADDED Requirements

### Requirement: Lean-Backed Owner Matrix Entries

Ladon SHALL keep concrete calibration owner roots Lean-backed when declaration
graphs add useful review signal.

#### Scenario: selected owner roots use Lean extraction

- GIVEN the maintained root matrix
- WHEN entries for Quux BIFR RMSE, MF GaussianCore, MF BSRFactorCore, and MF
  FTRL are selected
- THEN their commands SHALL include `--extraction-backend lean`.

#### Scenario: project roots remain text-backed

- GIVEN the maintained root matrix
- WHEN project-level roots such as `quux-project` and `mf-project` are selected
- THEN their commands SHALL continue to use `--skip-build`.
