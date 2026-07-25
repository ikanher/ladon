## Why

Several currently promoted Ladon findings have reproducible false negatives or
misleading labels. An alpha review tool must fix known correctness defects and
calibrate existing signals before expanding its heuristic catalog.

## What Changes

- Fix missing-internal-import detection so the selected owner root does not
  hide missing sibling modules within the repository namespace.
- Make handwritten fan-in counts exclude generated importers as well as
  generated targets, and make labels state the population actually counted.
- Replace the narrow declaration regex path with comment/string-aware text
  extraction that recognizes Lean declaration modifiers and kinds used by
  facade classification.
- Treat ordinary file/namespace layouts as expected and report namespace drift
  only when evidence crosses an explicit, tested boundary.
- Prevent proof-family similarity from reaching high confidence solely through
  shared coarse unresolved-reference classes.
- Deduplicate overlapping promoted findings while preserving their raw metric
  populations and selection metadata.
- Correct and authority-label raw missing-import and text `sorry`/axiom
  evidence; defer any new default finding family to the benchmark-backed
  promotion process.

## Capabilities

### New Capabilities

- `ladon-signal-correctness`: Correctness and calibration requirements for
  existing module, declaration, namespace, and similarity signals.

### Modified Capabilities

None.

## Impact

- Affected code: text extraction, module DAG analysis, findings,
  module-readiness analysis, proof-family similarity, and rendering.
- Affected tests: focused regression fixtures plus positive and intentional
  negative cases for every repaired signal.
- Observable finding counts and ordering may change because duplicate and
  falsely promoted rows will be removed.
