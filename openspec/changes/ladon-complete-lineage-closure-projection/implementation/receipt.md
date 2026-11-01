# Implementation replay receipt

## Synthetic contract

- Frozen closure contract tests: 6/6 passed after implementation. The independent fixture
  uses a 20-layer two-wide graph (41 nodes, 80 typed edges, over one million
  simple cycles in the test construction), plus disconnected, typed-parallel,
  SCC/self-loop, generated-filter, exact-cap, and cap-plus-one cases.
- Frozen route tests: 3/3 passed. Distinct-node expansion reached 41 nodes and
  examined no more than the fixture's 80 typed adjacency rows. Separate tests
  cover a depth cutoff versus exhausted frontier, generated-node blocking,
  traversal-work cap, reverse-direction cycles, and route-cap independence.
- Frozen test hashes are recorded in
  `.codex/state/ultra-lineage-closure.sqlite3`; the final verification is
  recorded below after the integrated gates.

The integrated focused lineage/store/query/projection/CLI/history/hardening run
passed 57 tests. Static checks over every changed Python source and test file
passed strict Radon/Vulture, Ruff, and compileall. The closure test freeze was
superseded twice with board-recorded reasons: splitting a complex cap test to
meet the complexity gate, then normalizing imports. All current frozen hashes
verify. Added regression groups cover insertion-order determinism, historical
closure fingerprints, route-cap accounting, and route reachability.

Independent integrated audit found and verified two fixes: route-edge cap
accounting excludes the extra route used only to detect route truncation, and
historical coverage mutation recomputes the closure fingerprint. The final
follow-up audit passed those regression tests and the offline history suite
(12 tests total).

## Retained gradient field closure

The retained index is at
`/home/codex/projects/lean/matrix-factorization/.ladon/index/proof-search.sqlite`.
Its active target closure is `cf24ba311d3c8b649ad45455c5927423453c04164390f6793f877c5d1d34feeb`,
with source fingerprint
`47f7f0d115275ef4bc3e1c65ac9c0e7808e8bdcc87d79981566dd55e837e29a3`,
configuration fingerprint
`4c49aee41c413824400f4cb4080546b765502dcf66e0570ce98f4f762ade81d0`,
and toolchain `leanprover/lean4:v4.33.0`. The target checkout is at
`77d23ca9cad8a491f435646fcbce0e7ffbe687cc`; current untracked inputs make its
present source snapshot differ from the stored one.

The ordinary current-mode CLI was tried with `--refresh never`. It failed closed
with `status=unavailable`, `reason=stale-source`, exit 1, and did not change the
index size or modification time. No Lean/Lake execution or refresh was used.

For the retained historical observation, the replay helper obtains the identity
from the stored closure row, opens the index with SQLite `mode=ro`, projects with
`--max-nodes 100000 --max-edges 200000 --max-output-bytes 33554432`, and marks
the result historical before rendering. Command, from the Ladon repository root:

```bash
PYTHONPATH="$PWD/src" python openspec/changes/ladon-complete-lineage-closure-projection/implementation/replay_field_case.py \
  --index /home/codex/projects/lean/matrix-factorization/.ladon/index/proof-search.sqlite \
  --output /tmp/ladon-lineage-closure-field-replay-historical.json \
  --max-nodes 100000 --max-edges 200000 --max-output-bytes 33554432
```

Exit status: 0. Result: `status=available`, historical source freshness
`not-assessed`, current association `not-established`, source extraction and
selected graph coverage `complete`, `truncated=false`, exact match of all 2,242
stored nodes and all 47,533 typed edges (zero missing or extra rows), returned
counts equal payload lengths, and a 13,132,747-byte output under the 33,554,432
byte cap. Historical coverage and the projection fingerprint were independently
checked against the final serialized payload. `/usr/bin/time` measured 1.09
seconds elapsed and 119,564 KiB peak RSS.

For the prior route projection, the frozen field result hit the 10,000 recursive
row ceiling and returned 1,072 nodes, 23 distinct untyped pairs, and 73 route-edge
occurrences. Running the new route acquisition against the same stored identity
expanded 2,242 distinct nodes and examined 47,533 typed adjacency rows; node,
depth, and work limits were not reached. It returned 20 representative routes;
only the route population was truncated. This is a stored-field comparison, not
a new acquisition or a theorem check.

## Command status

| Gate | Command | Status |
| --- | --- | --- |
| Field packet verifier | `python openspec/changes/ladon-complete-lineage-closure-projection/evidence/verify.py` | PASS before implementation replay |
| Focused lineage/history suite | `python -m pytest -q tests/test_theorem_lineage_closure.py tests/test_theorem_lineage_closure_filters.py tests/test_theorem_lineage_closure_determinism.py tests/test_theorem_lineage_history_fingerprint.py tests/test_theorem_lineage_reachability.py tests/test_theorem_lineage_reachability_caps.py tests/test_theorem_lineage_query.py tests/test_theorem_lineage_projection.py tests/test_theorem_lineage_hardening.py tests/test_theorem_lineage_cli.py tests/test_theorem_lineage_integration.py tests/test_index_history_offline.py` | PASS, 57 passed |
| Changed-file strict Radon/Vulture, Ruff, compileall | scripted checks over changed Python files | PASS |
| Repository strict Python quality | `python scripts/python_quality.py --strict --target ...` (runs all `tests/`) | FAIL after 4,423.72s: 5,579 passed, 86 skipped, 3 unrelated failures |
| Strict OpenSpec validation | `openspec validate ladon-complete-lineage-closure-projection --strict` | PASS |

The three broad-suite failures were rerun individually and reproduce outside
the changed files. Two proof-contract scratch tests fail because their worker
shim calls `_block_at_capture` with the now-required `workspace_parent`
argument omitted (`test_outer_stage_timeout_recovers_a_delegated_goal_without_deleting_its_bytes`
and `test_timeout_after_real_goal_write_cleans_only_the_owned_goal_tree`). The
third is the repository quality self-test, which currently reports ten C-or-
worse Radon findings in `real_bound_native_analysis.py`,
`real_bound_native_relation_worker.py`, and related real-bound tests. Strict
Radon/Vulture, Ruff, and compileall pass on all changed Python files, and the
57-test focused lineage suite passes. No lineage test failed in the full run.
