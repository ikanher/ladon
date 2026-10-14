# Paired field measurements

Equivalent checked work: True. Observed arithmetic target: True. **Full performance qualification remains open.**

Independent audit426 confirmed every trial and all120checked links, but found an external compilation overlapped the run. Its original report is preserved in INDEPENDENT-QUALIFICATION.md and INDEPENDENT-AUDIT.json. QUALIFICATION.json distinguishes valid observed gains from the unmet clean-concurrency performance gate. A clean repeat is blocked by the other ongoing compilation recorded in ../clean-repeat-feasibility.json.

All trials use the frozen public entrypoint, exact subjects/terms/source/environment and original qualified contexts in `FREEZE.json`. Root ran builds/tests/replays serially and introduced no overlapping work during measurement. A process-list snapshot in CONCURRENCY-OBSERVATION.json observed an unrelated Lean job from another session. External activity and CPU frequency were not continuously measured or controlled; benchmark-hardware-02.json records the hardware scope. Python interpreter startup and harness freezing are excluded; per-check and end-to-end entrypoint timings remain separately recorded. Existing compiled checkout/OS caches and a warmed Python process were used. First-use setup is visible in each trial process/stage accounting.

| Workload | Ordinary median s | Request median s | Reduction |
|---|---:|---:|---:|
| cone | 342.886 | 232.659 | 32.1% |
| numeric | 302.179 | 246.849 | 18.3% |
| scoped | 503.238 | 401.846 | 20.1% |

| Workload | Pair | Mode | Wall s | Processes | Peak RSS MiB | Bundle bytes | Qualified |
|---|---:|---|---:|---:|---:|---:|---|
| cone | 1 | ordinary | 352.362 | 124 | 4681.3 | 9125963 | True |
| cone | 1 | request | 232.659 | 145 | 4633.5 | 9136418 | True |
| cone | 2 | ordinary | 341.461 | 124 | 4682.8 | 9125967 | True |
| cone | 2 | request | 232.356 | 145 | 4643.7 | 9136439 | True |
| cone | 3 | ordinary | 342.886 | 124 | 4682.1 | 9125967 | True |
| cone | 3 | request | 232.733 | 145 | 4633.4 | 9136427 | True |
| numeric | 1 | ordinary | 301.910 | 124 | 5136.7 | 10876790 | True |
| numeric | 1 | request | 244.975 | 145 | 5107.8 | 10887900 | True |
| numeric | 2 | ordinary | 302.179 | 124 | 5141.7 | 10876793 | True |
| numeric | 2 | request | 246.849 | 145 | 5112.1 | 10887902 | True |
| numeric | 3 | ordinary | 305.508 | 124 | 5131.9 | 10876805 | True |
| numeric | 3 | request | 248.228 | 145 | 5114.8 | 10887881 | True |
| scoped | 1 | ordinary | 512.487 | 158 | 5625.7 | 14371803 | True |
| scoped | 1 | request | 411.296 | 185 | 5576.8 | 14382126 | True |
| scoped | 2 | ordinary | 501.411 | 158 | 5631.9 | 14371805 | True |
| scoped | 2 | request | 401.846 | 185 | 5572.5 | 14382130 | True |
| scoped | 3 | ordinary | 503.238 | 158 | 5631.9 | 14371810 | True |
| scoped | 3 | request | 349.025 | 185 | 5576.9 | 14382120 | True |

Every trial retains its complete checked bundle, CLI log and timing/accounting record. Qualification requires all original links, no residuals, accepted independent replay and complete no-placeholder trust. Additional `SUBJECT-EQUIVALENCE.json` verifies exact whole closed subjects across all six trials per workload and against each captured goal. The summary rejects missing/duplicated trial slots and cross-run changes to exact goals, modes, outcomes or observed axiom policy/coverage/dependencies.

Peak RSS is the maximum observed supervised process group, not total machine memory. Stage wall times are inclusive and overlap; they must not be added. Counters distinguish one prose subject from its repeated typing/substantive link checks.

The gain describes these frozen operational workloads. It establishes no paper-error detection, theorem truth, prose fidelity or advantage over an ordinary auditor. Ordinary checking remains the default; reuse is explicit opt-in.

## Check populations and phase data

Counts below distinguish unique checked subjects from the one prose subject, typing probes and substantive links. Phase wall times are inclusive, overlap and must not be summed. An absent phase is marked not recorded rather than assigned an invented zero. Complete process/byte/resource populations and every recorded phase are retained in each trial timing.json.

| Workload | Pair | Mode | Checked subjects | Prose subjects | Typing | Substantive |
|---|---:|---|---:|---:|---:|---:|
| cone | 1 | ordinary | 6 | 1 | 1 | 5 |
| cone | 1 | request | 6 | 1 | 1 | 5 |
| cone | 2 | ordinary | 6 | 1 | 1 | 5 |
| cone | 2 | request | 6 | 1 | 1 | 5 |
| cone | 3 | ordinary | 6 | 1 | 1 | 5 |
| cone | 3 | request | 6 | 1 | 1 | 5 |
| numeric | 1 | ordinary | 6 | 1 | 1 | 5 |
| numeric | 1 | request | 6 | 1 | 1 | 5 |
| numeric | 2 | ordinary | 6 | 1 | 1 | 5 |
| numeric | 2 | request | 6 | 1 | 1 | 5 |
| numeric | 3 | ordinary | 6 | 1 | 1 | 5 |
| numeric | 3 | request | 6 | 1 | 1 | 5 |
| scoped | 1 | ordinary | 8 | 1 | 1 | 7 |
| scoped | 1 | request | 8 | 1 | 1 | 7 |
| scoped | 2 | ordinary | 8 | 1 | 1 | 7 |
| scoped | 2 | request | 8 | 1 | 1 | 7 |
| scoped | 3 | ordinary | 8 | 1 | 1 | 7 |
| scoped | 3 | request | 8 | 1 | 1 | 7 |

| Workload | Pair | Mode | Extraction s | Preparation s | Typing s | Capture s | Completion/replay/trust s | Final freshness s |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| cone | 1 | ordinary | 18.953 | not recorded | 15.463 | 107.558 | 191.795 | 14.087 |
| cone | 1 | request | 14.237 | 2.839 | 15.670 | 60.033 | 110.111 | 14.364 |
| cone | 2 | ordinary | 14.163 | not recorded | 15.276 | 107.019 | 186.525 | 13.957 |
| cone | 2 | request | 14.394 | 2.828 | 15.456 | 60.015 | 110.003 | 14.125 |
| cone | 3 | ordinary | 14.028 | not recorded | 15.488 | 107.582 | 187.220 | 14.023 |
| cone | 3 | request | 14.167 | 2.861 | 15.631 | 60.272 | 110.157 | 14.212 |
| numeric | 1 | ordinary | 14.499 | not recorded | 11.461 | 91.102 | 166.076 | 14.049 |
| numeric | 1 | request | 14.355 | 2.176 | 11.376 | 65.505 | 120.989 | 13.922 |
| numeric | 2 | ordinary | 14.294 | not recorded | 11.625 | 90.553 | 166.686 | 14.269 |
| numeric | 2 | request | 14.326 | 2.147 | 11.641 | 66.511 | 121.211 | 14.272 |
| numeric | 3 | ordinary | 14.349 | not recorded | 11.512 | 92.648 | 168.146 | 14.137 |
| numeric | 3 | request | 14.589 | 2.220 | 11.676 | 65.852 | 122.436 | 14.080 |
| scoped | 1 | ordinary | 17.380 | not recorded | 19.924 | 160.305 | 292.241 | 16.438 |
| scoped | 1 | request | 16.433 | 2.720 | 26.926 | 112.965 | 210.874 | 17.159 |
| scoped | 2 | ordinary | 16.301 | not recorded | 19.537 | 159.382 | 283.656 | 16.423 |
| scoped | 2 | request | 18.988 | 5.253 | 23.335 | 116.215 | 198.634 | 16.246 |
| scoped | 3 | ordinary | 16.465 | not recorded | 19.470 | 159.680 | 284.881 | 16.664 |
| scoped | 3 | request | 16.618 | 2.846 | 19.981 | 95.002 | 176.768 | 16.547 |

Command (from the current Ladon checkout):

```bash
uv run --locked python scripts/benchmark_correspondence_field.py --inputs openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/real-cases-attempt03 --output openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/paired-benchmark-02 --repo /home/codex/projects/navier-stokes-retest-5/formalization --root /home/codex/projects/navier-stokes-retest-5
```
