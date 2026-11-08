# Capsule memory hypothesis experiment — 2026-11-08

Confirmed: concurrent Lake compiler jobs amplify aggregate process-tree RSS and can exhaust the replay cap. Ordered builds eliminate that overlap on the measured inputs.

| Workload | Scheduling | Maximum Lean processes | Peak tree RSS | Result |
| --- | --- | ---: | ---: | --- |
| Three independent modules importing Lean, each with a 3-second sleep | Lake default | 3 | 4,834,533,376 bytes (4.50 GiB) | Passed |
| Same source graph, fresh separate directory | Ordered module builds | 1 | 1,743,028,224 bytes (1.62 GiB) | Passed |
| Actual reported capsule, clean project output, locked external dependencies | Lake default target build | 3 observed | 7,590,899,712 bytes (7.07 GiB) | Killed by 6 GiB RSS limit |
| Same three real modules observed in the concurrent build | Ordered module builds | 1 | 4,627,197,952 bytes (4.31 GiB) | All three passed in 15.17 seconds |

The small default build took 4.29 seconds; its ordered control took 11.35 seconds. A complete stable concurrent sample showed aggregate tree RSS 4,832,559,104 bytes and summed compiler PSS 1,788,746,752 bytes (1.67 GiB). RSS and PSS are distinct measures: the configured replay limit is aggregate RSS and includes shared pages once per mapping/process. Do not silently reinterpret that limit as unique physical memory. The exact highest-RSS sample had a process-exit race; the PSS claim uses a separate complete three-compiler sample.

Pinned toolchain: leanprover/lean4:v4.33.0. Machine: 12 logical/allowed CPUs. Small experiments used a 6 GiB cap and 60-second shared deadline per policy. Actual setup used a 6 GiB cap and 180-second deadline; build used the same cap with a 30-second deadline. Ordered real builds shared a 120-second deadline and the 6 GiB cap. Existing Ladon process-group supervision and sanitized replay environment were used throughout. One earlier public replay attempt timed out during dependency resolution at 60 seconds and did not reach the build.

The actual diagnostic builds ran in a temporary copy of the exact retained capsule sources. The original checkout and capsule were not modified. Dependencies were resolved by lake update in the temporary tree; no project compiled artifacts were copied from the original checkout. Source hashes for the three compared real modules are in source-checks.json. The first default actual build was terminated while its first three compiler jobs were loading imports; those modules were then built individually in the same tree. No outputs for those three modules were successfully built by the terminated default run. This is an early-frontier control, not a full 459-module scheduling evaluation.

No full capsule replay verification was achieved or claimed. The original 32/48 GiB failures were not reproduced at those caps; the diagnostic reproduced concurrent compiler amplification at a lower cap. Other modules could exceed this cap individually. Product code and OpenSpec artifacts were not changed. Scripts, raw samples, module-build receipts, and summaries are retained beside this report.
