# Uncapped review-report diagnostic

The user requested removal of the report and capture byte caps. Both runs used the installed r37 candidate, the text backend, no build/cache, review JSON projection, an empty subprocess environment and a network-disabled namespace. The analyzer deadline remained 300 seconds, the supervisor deadline 310 seconds, and each target retained a 32 GiB sampled RSS bound. No product code changed.

| Target | Complete report bytes | MiB | Sampled peak RSS (GiB) | Seconds | Report status |
| --- | ---: | ---: | ---: | ---: | --- |
| matrix-calibration | 2,164,781 | 2.06 | 0.88 | 290.59 | schema-valid-terminal |
| mathlib-heldout | 1,999,055 | 1.91 | 0.75 | 97.48 | schema-valid-terminal |

Both packaged report-v3 schema checks passed. Each report records `requested.reportBytes: null`, no crossed resource limit, and a stable terminal snapshot. Full stdout/stderr and command/measurement records are retained without truncation and copied to the content-addressed capture bundle referenced by [the execution record](architecture-diagnostic-execution-v3.json).

Matrix exceeds the former 2 MiB report cap by 67,629 bytes (3.22%). Mathlib fits below it. The matrix run spent 285.61 seconds in source discovery. Its inventory grew from 7,702 modules at initial progress to 7,705 in the terminal report; the earlier v2 run indexed 7,701. The selected source, toolchain, project manifest and Git commit matched the registered identities before and after this run. This is a size diagnostic against an evolving external workspace, not a controlled timing comparison.

| Target | Declaration-integrity content bytes | Coverage content bytes | Combined share of report bytes |
| --- | ---: | ---: | ---: |
| matrix-calibration | 1,547,121 | 358,725 | 88.0% |
| mathlib-heldout | 1,328,700 | 388,902 | 85.9% |

Component values use compact UTF-8 JSON, excluding their enclosing keys/separators. Actual stdout byte counts are authoritative. Most output is declaration-integrity and coverage data, even though the review projection analyzes only two matrix modules or four mathlib modules.

The deterministic matrix sample contains one informational lexical match for the semantic-qualifier inventory at `Mf/DP/GaussianDP.lean:704`. This is a textual inventory finding, not a theorem-correctness or architecture-quality judgment. Mathlib has only the excluded no-policy information. Independent correctness/actionability labels remain absent; precision and actionability remain null. Umbrella tasks 6.8 and 7.1 remain open, with 74/76 tasks complete.

The preregistered v1 study, capped v2 diagnostic, frozen candidate qualification, and r38 local review packet remain separate historical records. This diagnostic grants no umbrella or internal-alpha acceptance.
