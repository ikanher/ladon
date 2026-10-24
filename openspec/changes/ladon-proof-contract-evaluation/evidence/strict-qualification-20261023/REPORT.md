# Strict qualification of current working tree

Date: 2026-10-23

## Command and outcome

Command:

```text
timeout --signal=INT --kill-after=30s 7200 uv run --locked --offline python scripts/python_quality.py --strict
```

The run exited 1 after 2,571.21 seconds. Strict Radon/Vulture checks passed, Ruff passed, and `compileall` passed. Pytest reported **4,819 passed, 43 failed, 1 skipped**.

All 43 failures came from the repeated rational-branch plan acceptance files (`tests/test_rational_branch_plan_v3.py` through `v8.py`). The plan workflow fails closed because its configured Lean workspace lacks the tracked source file `Mf/DP/Training/BMinSep/AccountantProfileComparison.lean`. The file is marked deleted in the current `../lean/matrix-factorization` working tree; a similarly named file exists under the separate `../lean/dpadam-release-e192b83a` checkout, which is not the configured workspace. Tests expecting a successful plan consequently receive `unsupported`, then fail their planned-result assertions.

This is an environment/source-workspace identity failure, not a successful functional qualification. The fail-closed response is correct for a missing source identity input; substituting a file from another checkout would change the evaluated workspace. The strict gate therefore does **not** authorize freezing the enhanced runtime or claiming the evaluation arms are ready.

## Decision

Leave evaluation task 3.1 open. Before retrying qualification, restore the expected tracked source in the configured Lean workspace or revise the acceptance fixtures to use an independently frozen, exact source workspace. Do not alter the frozen evaluation protocol or treat the 4,819 passing tests as a complete pass.
