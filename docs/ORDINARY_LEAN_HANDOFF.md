# Ordinary Lean maintenance handoff

Use ordinary Lean source inspection, editing, compilation and axiom inspection
first. Ladon retains compatible claim-and-evidence utilities alongside that route;
comparative usefulness remains unestablished. Standalone search/application,
extractor and release-feature expansion is frozen.

The concrete fixed-epoch example lives in `../lean/matrix-factorization`:

```bash
cd ../lean/matrix-factorization
lake build Mf.DP.PoissonFixedEpochOffset Mf.DP.PoissonFixedEpochOffsetAudit Mf.DP.PoissonFixedEpochLargeBatchOptimality Mf.DP.PoissonFixedEpochLargeBatchOptimalityAudit
lake env lean Mf/DP/PoissonFixedEpochOffset.lean
lake env lean Mf/DP/PoissonFixedEpochOffsetAudit.lean
```

Read `docs/POISSON-FIXED-EPOCH-OFFSET-CORRESPONDENCE.md` there for exact conditions,
version bindings and limitations. This is a proposed handoff pending human adoption. The normal build and all
commands in the recipe passed from the documented root, with permitted axioms.
The [handoff record](../openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/offset-handoff-r64/REPORT.md)
retains both earlier failures and the successful final receipt. No private experimental workspace is required.

When original-goal identity matters, the optional existing route is:

```bash
ladon proof-search goal complete --help
ladon proof-search goal complete \
  --repo-root /path/to/lean-project --capture-file /path/to/captured-goal.json \
  --term 'candidate argument premise' \
  --lean-path /absolute/pinned/bin/lean --lake-path /absolute/pinned/bin/lake \
  --max-rss-mib 32768 --format json --output /path/to/completion.json
```

The goal capture must be genuine and current; this is not a runnable application
without its task-specific inputs. See [source-goal completion](SOURCE_GOAL_COMPLETION.md).
The corrected command spelling and flags were checked against the explicitly
selected r63 qualified installed candidate; no mathematical Ladon operation was
performed for this handoff. Existing commands, formats and checking boundaries
remain supported. New software investment requires a concrete user need.
