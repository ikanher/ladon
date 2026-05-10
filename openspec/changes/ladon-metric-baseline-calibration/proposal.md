# Ladon Metric Baseline Calibration

## Why

Ladon currently reports graph hotspots using fixed thresholds. Those thresholds
are useful for smoke triage, but they do not say whether a row is ordinary for
this repository or exceptional inside the current proof/code graph.

The literature review under `paper/ladon-code-quality/` points toward a safer
first step: report project-local metric distributions and calibrate findings
against those distributions before making stronger claims.

## What

- Add a pure quality-baseline analysis over existing module and declaration
  graph summaries.
- Include baseline metric summaries in JSON and text reports.
- Annotate findings with percentile/rank metadata when the finding maps to a
  known baseline metric.

## Non-Goals

- No defect prediction model.
- No machine-learning score.
- No new Lean extraction route.
- No claim that a high percentile is a bug by itself.
