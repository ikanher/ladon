# Design

The umbrella is grounded in `paper/ladon-code-quality/`.

## Literature Mapping

- McCabe (1976), Jin et al. (2023): metric distributions and complexity
  baselines.
- Esposito et al. (2024), Han et al. (2022), code-smell SLR: smells should be
  validated against review/evidence, not treated as absolute truth.
- Garcia et al. (2015), Savidis/Savaki (2022): architecture recovery and
  dependency accuracy justify module-DAG closure attribution.
- Clone/similarity SLR and LLM clone survey: repeated proof-shape detection
  should evolve from naming heuristics to similarity features.
- Hermann et al. (2026), SQuaD (2025): analyzer precision needs benchmarks,
  not just examples.
- Code Property Graphs and LLMxCPG: graph-first extraction can later feed
  higher-level query/LLM explanations.
- Tarjan formalization, ProofGym, Goedel-Prover, Zhang/Ringer/First: proof-code
  workflows need proof-checker boundaries and structured artifacts.

## Execution Order

1. `metric-baseline-calibration`
2. `architecture-smell-correlator`
3. `proof-family-similarity`
4. `witness-packet-evidence-gate`

This order strengthens the current analyzer before rebuilding packet/witness
audits. It avoids adding evidence gates before Ladon can explain why a signal is
unusual.

## Output Shape

Each child should add:

- an OpenSpec change;
- tests before implementation;
- JSON report fields;
- concise text-rendered findings;
- a note in docs linking the signal to literature;
- smoke reports against Quux and matrix-factorization when applicable.
