# LLM usage feedback

This is qualitative development evidence. Record failures and workarounds as
well as useful results. Do not infer measured improvement or independent human
review from this report.

- Date and Ladon candidate identity:
- Agent/model identity as available; state if the implementation agent is also the reviewer:
- Task and intended decision:
- Exact input artifacts/revisions:
- Exact commands and relevant stdout/stderr (exclude private material explicitly):
- Observed result and interpretation:
- Missing, confusing, misleading, or unnecessarily verbose information:
- Workaround or other tools/source consulted:
- Suggested concrete change:
- Reproduction status: observed once / reproduced / unresolved:
- Finding kind: usability / suspected correctness / confirmed correctness:
- Source or Lean evidence for a correctness finding:
- What was not assessed:

Initial development scenarios:

1. Validate the finite-map example and distinguish declared mappings from actual Lean checking.
2. Explain why the example leaves a component unmapped and retains an additional-assumption review.
3. Edit a subject and recompute its revisions without updating the old review; observe historical review binding.
4. Try a malformed or oversized artifact and inspect the diagnostic and exit status.
5. Record canonical evidence resolution as unavailable until that integration exists; do not invent a successful check.

Later scenarios add actual canonical evidence, reusable lemmas, reading guides,
attribution support, and incomplete attempt populations as those features land.

The [matrix-factorization fixed-epoch field report](field-feedback-matrix-fixed-epoch.md)
adds a real-project navigation scenario: locate the article's main theorem and
counterexample, compare the pinned coverage addendum, and preserve compiled
resource failures. It is preparatory feedback, not completion of the later
core dossier/guide/bundle scenario.

The [completed exposition baseline v1](baselines/fixed-epoch-v1/README.md)
extends that report with frozen manuscript inputs, an explicit partial claim
map, model-attributed differences, and reproducible installed CLI scenarios.
Use its retained limitations and expected unavailable outcomes when comparing
later candidates; do not count them as implemented dossier/guide features.
