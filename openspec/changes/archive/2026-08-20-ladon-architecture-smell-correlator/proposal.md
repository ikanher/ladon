# Ladon Architecture Smell Correlator

## Why

Single graph metrics are useful, but they are noisy. The architecture-smell and
static-analysis literature recommends looking for correlated signals before
raising review pressure.

Ladon now has enough clean-core signals to do a deterministic first slice:
module fan-in/out, root import closure size, facade counts, declaration-family
rows, and chosen-root reachability.

## What

- Add composite architecture-pressure findings derived from multiple existing
  signals.
- Cite the component signals in each finding payload.
- Keep messages descriptive and non-accusatory.

## Non-Goals

- No classifier.
- No defect prediction.
- No graph clustering yet.
- No dependency on LLM interpretation.
