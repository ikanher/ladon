## ADDED Requirements

### Requirement: Root Direct Import Closure Summary

Ladon SHALL summarize transitive closure sizes for direct imports of selected
root modules.

#### Scenario: direct import closure rows are computed

- GIVEN a known root module imports two known modules
- AND those imports have different reachable transitive closures
- WHEN module-DAG analysis runs
- THEN the summary SHALL include direct-import closure rows sorted by descending
  reachable module count.

#### Scenario: text report renders root import closures

- GIVEN module-DAG summary contains direct-import closure rows
- WHEN text rendering runs
- THEN the report SHALL include a `Root Direct Import Closures` section.
