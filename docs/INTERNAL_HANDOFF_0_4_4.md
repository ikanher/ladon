# Internal Ladon 0.4.4 handoff

From `lean/matrix-factorization`, select the current Ladon checkout:

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint version --json
git -C ../../ladon rev-parse HEAD
git -C ../../ladon status --short
```

Record target revision/dirty state as well. Replace the relative checkout path
for other layouts. [Release notes](RELEASE_0_4_4.md) own qualification and limits.
Use the selected checkout rather than an older pip-installed executable.

For one current-generation check:

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint \
  proof-search index freshness --repo-root . --format json
```

For several known queries, save ordinary argument lists to `queries.json`:

```json
[["name", "--text", "stepUpper_optimal"], ["type-text", "--pattern", "Summable"]]
```

```bash
uv run --project ../../ladon --locked python -m ladon.entrypoint \
  proof-search search batch --repo-root . --queries queries.json \
  --format json --output batch-results.json
```

Workers can share the results with their generation and validation identities.
Two captures bracket one read transaction; observed edits/replacement withhold
rows. Later live queries need a new validation window. A batch is lexical
discovery, not Lean checking. See [CLI bounds and examples](CLI.md).

Ordinary `index update` now discards stale derived cache observations and creates
no historical backup. Save useful audit outputs explicitly. `--archive-history`
is opt-in. Update phase timings help identify future bottlenecks. Old archives
can be removed through a saved `history-cleanup` preview; inspect its paths,
bytes and consequences before explicitly applying it.

For exposition review, follow [the short recipe](PROOF_CORRESPONDENCE_AUDIT.md#quick-review-tex-and-a-named-lean-theorem).
Slice limits are configurable; a memory-limit result requires reporting back
before a higher-cap retry. Read theorem definitions, assumptions and conclusion
transfer. Matching theorem statements do not establish matching proof methods.
Historical stored context does not establish current source freshness.

Feedback should retain runtime/checkout/target identities, exact commands and
inputs, expected versus observed results, JSON/stderr, generation/validation
scope, resource limits and timings. Separate lookup, freshness, resource,
interpretation and mathematical issues. Retain justified findings and incomplete
coverage without upgrading lexical or stored evidence to checked proof authority.
