# R05 field follow-up: build passed; final dependency output hit16MiB

Documentation-only handoff from the historical ordinary-Adam lineage owner.
No Ladon implementation or acceptance decision is changed by this note.
The existing ordered-build fix worked for the full434-module closure.

## Exact observed outcome

Installed Ladon0.4.1 identity:
`sha256:3deb6351266fb8d2f0bb4cd72c1c89077b281472a1d6f694edfd3be50683e186`.
Target:
`Mf.Optimization.StochasticApproximation.Adam.ordinaryGaussian_expectedNorm_tendsto_zero`.
Capsule identity:
`sha256:4dc6ae17a9ddaf34a06d0ca47fde3527bafa8a7fbf15c529508be6b069542658`.
Plan identity:
`sha256:49eefd580d5e927402e897131d12c4b6aa9423b5eb14534059186a1de0570c9a`.

R05 ran4636.07seconds with a5250-second outer deadline and48GiB aggregate RSS
ceiling. Sampled process-tree peak was10809917440bytes. Locked dependency
resolution passed. All868ordered build steps passed:434dependency checks and
434project lean-artifact steps. Isolation checks passed.

The last `theorem_query` failed with `outputLimited=true`, `timedOut=false`,
`memoryLimited=false`, returncode−15. The installed output cap is16777216bytes.
Replay status is `resource-limit`; `comparisons` is empty. The stdout excerpt
starts a `ladon-theorem-capsule-stream-v1` response whose status is complete,
but this partial excerpt is not a complete comparison or an axiom audit.
Do not promote434artifacts or the truncated helper response to verified replay.

## Reproduction and retained inputs

Owning checkout: `/home/codex/projects/lean/matrix-factorization`.
Pinned capsule: `/tmp/historical-adam-convergence-r04-capsule` (temporary;
retain or rematerialize from its recorded capsule/plan before deleting it).
The source-side records are:

- `openspec/changes/historical-stochastic-approximation-proof-umbrella/evidence/adam-replay-r05/capsule-replay.json`
- adjacent `driver-result.json`, `summary.json`, `inputs.json`, `installed-version.json`
- R04 adjacent `capsule-manifest.json`.

Executed command from the source checkout:

```bash
ladon theorem replay /tmp/historical-adam-convergence-r04-capsule \
  --build-policy ordered --network allow --timeout 5250 --max-rss-mib 49152 \
  --format json --output <evidence>/capsule-replay.json
```

The source-side outer driver also enforces the complete-operation deadline and
process-tree memory cap; it is retained at
`temp/historical-adam-replay-r05/run-replay.py`.
The successful isolated build root was
`/tmp/ladon-capsule-replay-_46fbwnz/repository`; verify whether the replay context
has cleaned it before attempting any resume. Do not assume it survives.

## Narrow owner investigation

`src/ladon/theorem_capsule_replay.py` passes the fixed
`PROCESS_OUTPUT_LIMIT_BYTES` (16MiB) into `_run_replay_helper` at the final
query. Public `ladon theorem replay --help` exposes timeout, RSS and build
policy, but no output-size or final-query resume option. This identifies the
observed transport gate, not a claim about the best fix.

Suggested acceptance tests for the Ladon owner:

1. Retain a small synthetic over-cap dependency-output regression independent
   of this expensive434-module fixture.
2. Support a bounded complete stream/projection/comparison strategy, or an
   explicit supported output budget with diagnostics. Never truncate and accept.
3. Retain final type/value/dependency/trust identity comparisons, isolation,
   cancellation and finite time/RSS/output controls.
4. If adding reuse of a completed isolated build, bind every reused source,
   lock, compiler and artifact before resuming. Do not rerun the hour-long build
   merely to test JSON transport if a safe smaller reproduction suffices.
5. Re-run the actual selected target only with an explicit resource allowance;
   the research owner has not started a new whole replay.

This note requests investigation by the Ladon owner. It neither raises the
existing output cap nor patches the installed package. The research theorem
remains built locally and in isolation, with independent replay acceptance open.
