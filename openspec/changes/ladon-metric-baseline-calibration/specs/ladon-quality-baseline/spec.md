## ADDED Requirements

### Requirement: Project-Local Quality Baseline

Ladon SHALL compute project-local distributions for selected graph metrics
already present in the clean-core report.

#### Scenario: module and declaration distributions

- GIVEN module and declaration graph summaries
- WHEN the quality baseline is summarized
- THEN the baseline SHALL include module fan-in, module fan-out, root import
  closure, declaration fan-in, and declaration fan-out metric summaries where
  source data is available.

#### Scenario: finding calibration metadata

- GIVEN a finding whose count maps to a known baseline metric
- WHEN findings are summarized with a quality baseline
- THEN the finding SHALL include percentile, descending rank, and population
  metadata for that metric.

#### Scenario: report payload exposes baseline

- GIVEN a pipeline run
- WHEN the JSON report payload is built
- THEN the payload SHALL include a `quality_baseline` object.

#### Scenario: text report summarizes baseline

- GIVEN a report payload with a quality baseline
- WHEN the text renderer runs
- THEN the text report SHALL include a quality-baseline section and calibrated
  finding metadata where available.

#### Scenario: missing baseline remains non-blocking

- GIVEN no quality baseline is supplied to the renderer or finding summarizer
- WHEN reports are generated
- THEN existing behavior SHALL remain valid without calibration metadata.
