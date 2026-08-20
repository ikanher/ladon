# Proposal

Run the maintained Quux/matrix-factorization root matrix after the latest
calibration work and record what the analyzer gets right, what remains noisy,
and what should drive the next implementation packet.

# Scope

- Run `scripts/ladon_root_matrix.py --run` over the default matrix.
- Save JSON/text reports under `temp/root-matrix-evidence-pass/`.
- Summarize each root at the architecture-signal level.
- Identify concrete false positives, false negatives, or missing grouping
  opportunities.

# Non-Goals

- No target repository changes.
- No broad new smell heuristic unless the matrix exposes a repeatable signal.
- No proof-correctness claims from Ladon's conservative declaration graph.
