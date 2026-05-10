# Design

## Inputs

The first slice consumes only data Ladon already computes:

- module DAG edges and root direct-import closure rows;
- declaration graph edges;
- declaration-name family rows;
- unresolved-reference class rows.

## Baseline Shape

The report gains a `quality_baseline` object:

```json
{
  "method": "project_local_metric_distribution",
  "metrics": {
    "module_fan_in": {
      "count": 42,
      "min": 0,
      "median": 1,
      "p90": 4,
      "p95": 6,
      "p99": 9,
      "max": 12,
      "values": [0, 0, 1]
    }
  }
}
```

The `values` field is intentionally retained in JSON for now. It keeps
calibration deterministic and inspectable. Text rendering summarizes only the
headline distribution fields.

## Finding Calibration

Findings whose count corresponds to a baseline metric receive:

```json
{
  "baseline": {
    "metric": "module_fan_in",
    "percentile": 99.7,
    "rank_desc": 1,
    "population": 370
  }
}
```

This is descriptive. It means "this row is high relative to the current
repository distribution", not "this row is wrong".
