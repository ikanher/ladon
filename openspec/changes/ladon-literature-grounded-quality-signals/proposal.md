# Proposal

Turn the local code-quality literature corpus into the next Ladon development
roadmap.

The literature points away from one-off smell detectors and toward calibrated,
evidence-backed review signals:

- metric distributions rather than arbitrary thresholds;
- architecture-level smells correlated with local warnings;
- clone/similarity analysis for repeated proof shapes;
- benchmark/evidence gates for analyzer precision;
- deterministic graph extraction first, LLM explanation later.

# Parent Goal

Make Ladon findings more defensible: every high-level quality signal should have
a documented evidence source, a calibrated baseline, and an explicit
false-positive boundary.

# Child Packets

1. `metric-baseline-calibration`
   - Build repo-local metric baselines from Ladon's own reports and target repo
     smoke reports.
   - Replace single hard-coded thresholds with percentile/context rows where
     practical.

2. `architecture-smell-correlator`
   - Combine module-DAG signals with declaration/local warning signals.
   - Start with deterministic correlations: high fan-in, root-import closure,
     facade count, unreachable count, declaration-family count.

3. `proof-family-similarity`
   - Extend declaration-name families into a proper repeated proof-shape module.
   - Stay deterministic first: suffix groups, token n-grams, reference-set
     overlap, and shared unresolved-class profiles.

4. `witness-packet-evidence-gate`
   - Rebuild packet/witness audit as an evidence gate.
   - Check whether review packets contain machine-readable witnesses, checkers,
     commands, and negative cases.

# Non-Goals

- No LLM-only quality scoring.
- No claim that a finding proves a defect.
- No graph clustering/atlas rewrite in the first wave.
- No Rust port before stable measurements prove a bottleneck.
