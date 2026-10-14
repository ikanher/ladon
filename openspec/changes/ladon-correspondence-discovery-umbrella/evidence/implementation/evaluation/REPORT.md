# Frozen correspondence-discovery pilot

All 28 first attempts completed in fresh Luna-medium contexts with individual case inputs and filesystem exclusion of reference answers, earlier reports and development workspaces. No reruns, tuning or case-level interventions occurred. The two namespaces supplied the same primary source and ordinary tools; the assisted arm also received the generic audit procedure and installed Ladon source.

**The pilot benefit criterion was unmet.** Both arms localized all eight predeclared discrepancies (including one valid method difference), made no false accusations on six controls, and abstained on the same underspecified control. The assisted arm used more observed time and tokens. This is evidence about fourteen elementary authored inputs, not research-paper fault discovery.

## Paired totals

| Observation | Ordinary tools | Ladon assisted |
| --- | ---: | ---: |
| Excerpt discrepancies localized (out of 6) | 6 | 6 |
| Multi-assertion discrepancies localized (out of 2) | 2 | 2 |
| False alarms on faithful controls (out of 6) | 0 | 0 |
| Faithful controls accepted (out of 6) | 5 | 5 |
| Abstentions | 1 | 1 |
| Missed reference discrepancies | 0 | 0 |
| Multi-assertion claims examined (out of 11) | 11 | 11 |
| Sum of per-run elapsed seconds | 194.81 | 285.09 |
| Accounted input + output tokens | 333138 | 419530 |
| Completed tool items | 14 | 19 |

The assisted totals were 46.35% higher in elapsed time and 25.93% higher in accounted tokens. Elapsed totals sum individual process durations, including API latency; two processes ran concurrently. Tokens include cached input and are CLI telemetry, not a billing measurement. No token, time or sampled-RSS bound was exceeded. Token allowance is checked after the turn, not a hard API cap. Shared preparation stayed below its 60-minute limit and reused compiled Lean dependencies without rebuilding them.

## Case-level decisions

| Case | Reference | Ordinary | Assisted | Ordinary seconds / tokens | Assisted seconds / tokens |
| --- | --- | --- | --- | ---: | ---: |
| [e10](cases/e10/INPUT.md) | faithful | [faithful](runs/e10-ordinary-tools/first-report.json) | [faithful](runs/e10-ladon-assisted/first-report.json) | 12.43 / 23329 | 11.96 / 24428 |
| [l01](cases/l01/INPUT.md) | discrepancy | [localized; correctly classified](runs/l01-ordinary-tools/first-report.json) | [localized; correctly classified](runs/l01-ladon-assisted/first-report.json) | 12.24 / 24007 | 33.59 / 25519 |
| [e12](cases/e12/INPUT.md) | faithful | [abstained](runs/e12-ordinary-tools/first-report.json) | [abstained](runs/e12-ladon-assisted/first-report.json) | 11.37 / 23910 | 21.94 / 24813 |
| [e02](cases/e02/INPUT.md) | discrepancy | [localized; correctly classified](runs/e02-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e02-ladon-assisted/first-report.json) | 11.03 / 23768 | 19.91 / 24693 |
| [e09](cases/e09/INPUT.md) | faithful | [faithful](runs/e09-ordinary-tools/first-report.json) | [faithful](runs/e09-ladon-assisted/first-report.json) | 12.92 / 23335 | 16.84 / 53292 |
| [e08](cases/e08/INPUT.md) | faithful | [faithful](runs/e08-ordinary-tools/first-report.json) | [faithful](runs/e08-ladon-assisted/first-report.json) | 14.01 / 23356 | 18.14 / 38907 |
| [e03](cases/e03/INPUT.md) | discrepancy | [localized; correctly classified](runs/e03-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e03-ladon-assisted/first-report.json) | 10.06 / 23638 | 20.87 / 24766 |
| [e07](cases/e07/INPUT.md) | faithful | [faithful](runs/e07-ordinary-tools/first-report.json) | [faithful](runs/e07-ladon-assisted/first-report.json) | 10.44 / 23721 | 9.36 / 24438 |
| [l02](cases/l02/INPUT.md) | discrepancy | [localized; correctly classified](runs/l02-ordinary-tools/first-report.json) | [localized; correctly classified](runs/l02-ladon-assisted/first-report.json) | 17.73 / 24710 | 28.83 / 25260 |
| [e05](cases/e05/INPUT.md) | discrepancy | [localized; correctly classified](runs/e05-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e05-ladon-assisted/first-report.json) | 12.98 / 23975 | 11.72 / 24691 |
| [e01](cases/e01/INPUT.md) | discrepancy | [localized; correctly classified](runs/e01-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e01-ladon-assisted/first-report.json) | 23.31 / 23948 | 25.28 / 24980 |
| [e11](cases/e11/INPUT.md) | faithful | [faithful](runs/e11-ordinary-tools/first-report.json) | [faithful](runs/e11-ladon-assisted/first-report.json) | 17.50 / 23516 | 7.88 / 24308 |
| [e04](cases/e04/INPUT.md) | discrepancy | [localized; correctly classified](runs/e04-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e04-ladon-assisted/first-report.json) | 12.77 / 23926 | 40.29 / 40184 |
| [e06](cases/e06/INPUT.md) | valid method difference | [localized; correctly classified](runs/e06-ordinary-tools/first-report.json) | [localized; correctly classified](runs/e06-ladon-assisted/first-report.json) | 16.04 / 23999 | 18.49 / 39251 |

Scores are attributed mathematical judgments with reasons and immutable report bindings in [scores.json](scores.json). The reference inventory has six claims for l01 and five for l02. Both auditors address all eleven, including combined discussion of positivity and the upper bound; the denominator is not their supplied component count. Excerpts use one grouped reference item each and do not establish fine-grained source inventory completeness. e06 counts as localized even though both verdicts say faithful: each report separately identifies the valid method difference and neither labels the theorem false.

## Limits and retained disagreements

- All fourteen cases are authored and elementary. The two multi-assertion selections are single paragraphs, not realistic long mathematical texts. Zero naturally occurring cases were included. Pretraining familiarity with standard mathematics is possible; no general accuracy claim follows.
- Formal counterparts are rendered summaries, not Lean modules. No scored run invoked Lean checking. Only e06-assisted opened Ladon help; no run used Ladon proof search or candidate checking. This comparison primarily exercises the added procedure, not a runtime detector.
- e12 was curated as faithful, but its formal summary omits an exact proposition. Both auditors reasonably abstained. Keep the original reference and expose this ambiguity; do not retrospectively repair or replace the scored input.
- Both l02 reports additionally note a true assertion omitted by the supplied formal summary. That supported omission is reported separately from the predeclared false inference, not counted as a false alarm or an extra scored success.
- The ordinary l01 report incorrectly says the first harmonic term was omitted. Its displayed block argument still proves divergence. Other minor domain and method wording qualifications are retained in scores.json.
- Answer files were excluded through bubblewrap mount/PID/user namespaces, including host-root access through proc. The runtime/API smoke test and negative path probe passed. The authentication profile contained no conversation history. Shared provider prefix caching does not add earlier answers to a new context.
- Web search was disabled, and shell searches were procedurally prohibited; API networking remained enabled without an egress filter. Retained tool events show only local reads/help and local report writes, with no online or answer-file access observed. Filesystem exclusion is enforced; absence of hidden service-side exposure is not independently attested.
- Model request and reasoning were identical (`gpt-6-luna`, medium). Backend identity is not independently attested. Token limits are post-turn accounting. No budget overrun, contamination or intervention was observed in any retained attempt.
- Reference answers and scoring are Codex-attributed conventional mathematical judgments, without independent human adjudication. Artifact validation checks identities and arithmetic, not semantic truth.

## Decision and next question

The strengthened workflow is implemented and exercised. This pilot provides no comparative detection advantage and no reason to add a speculative semantic-diff runtime. Stop this evaluation here. The next concrete question is whether a fresh, answer-excluded audit can localize the user-reported issue in the full Navier–Stokes exposition using the new workflow. That separately prepared retest is a previously used target and has no result yet; it is not an unseen-paper accuracy study.
