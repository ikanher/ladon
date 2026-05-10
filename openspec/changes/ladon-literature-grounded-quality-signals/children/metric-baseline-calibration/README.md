# Child 1: Metric Baseline Calibration

## Literature Basis

- `arxiv:2307.12082` Software Code Quality Measurement.
- `mccabe:1976` A Complexity Measure.
- `arxiv:2511.11265` SQuaD.
- `arxiv:2602.18270` Many Tools, Few Exploitable Vulnerabilities.

## Problem

Ladon currently uses fixed hotspot thresholds such as fan-in >= 5 or family size
>= 3. These are useful but under-justified. The literature suggests comparing
against project-local metric distributions before making stronger claims.

## Proposed First Slice

Add a `quality_baseline` analysis module that computes distribution summaries
over existing report fields:

- module fan-in and fan-out;
- root direct-import closure sizes;
- declaration fan-in and fan-out;
- declaration family sizes;
- unresolved-reference class counts.

Report percentile/rank information for findings, for example:

```text
module_fan_in_hotspot Quux.Basic: fan_in=101, percentile=99.7
```

## Acceptance Bar

- Tests over synthetic distributions.
- JSON fields for baseline summary.
- Text findings include rank/percentile where available.
- Smoke reports for Quux and matrix-factorization.
