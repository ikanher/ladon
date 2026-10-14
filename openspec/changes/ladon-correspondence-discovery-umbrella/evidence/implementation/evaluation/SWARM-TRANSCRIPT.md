# Ultra Code Swarm: task:correspondence-discovery

## Board

- **acceptance_contract:** Frozen two-arm inputs; enforce answer exclusion; record first attempts and unavailable outcomes; no detection claim without supported scores
- **baseline:** 14/22 packet tasks, no scored runs
- **coordinator_pid:** 2265885
- **created_by:** root
- **current_target:** Isolated paired evaluation of frozen authored cases
- **dependency_policy:** Existing installed tools only; no production runtime changes; no online answers
- **frontier_id:** pilot
- **max_agents:** 4
- **objective:** Complete correspondence discovery evaluation honestly
- **run_id:** task:correspondence-discovery
- **schema_version:** 3

## Participants

| Author | Active | Nickname | Handle | Role | Model | Reasoning | Task |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pilot/isolation | yes | isolation | /root/pilot_isolation | contract_auditor | gpt-6-luna | medium | pilot_isolation |
| pilot/final-audit | no | final-audit | /root/pilot_final_audit | integration_auditor | gpt-6-luna | medium | pilot_final_audit |

## Notification Routing

- Pending wakes: 1

## Assignments

### Post #1: pilot_isolation [completed]
- Worker: `pilot/isolation`
- 2026-10-10T10:29:25.233Z `posted` by `root`: atomic dispatch
- 2026-10-10T10:29:35.787Z `spawned` by `root`: Accepted Luna medium sidecar; shared filesystem, not a scored auditor
- 2026-10-10T10:30:42.465Z `completed` by `pilot/isolation`: Read-only feasibility audit and negative filesystem probe posted as #3.

### Post #5: pilot_final_audit [completed]
- Worker: `pilot/final-audit`
- 2026-10-10T10:41:43.625Z `posted` by `root`: atomic dispatch
- 2026-10-10T10:41:54.198Z `spawned` by `root`: Accepted Luna medium independent read-only integration audit
- 2026-10-10T10:45:27.444Z `completed` by `root`: result post #7; peer gate waived: sidecar mode; independent integrated audit of frozen reports and final consuming guide; root verified counts and identities

## Posts

### #1 pilot/isolation [assignment / active]
- Author: `root` (root)
- Communication: `Root -> isolation`
- Created: 2026-10-10T10:29:25.233Z
- Recipient: `pilot/isolation`
- Tags: `frontier:pilot`

assignment_contract:
  frontier: pilot
  role: contract_auditor
  deliverable: independent read-only audit of namespace evaluator feasibility and a concrete minimal command proposal
  relevant_threads: none
  forbidden_shortcuts: [claiming fresh context alone excludes readable labels, exposing secrets, running an answer-bearing case, editing production or OpenSpec files]
  soft_evidence_deadline: 5 minutes
  hard_cancellation_deadline: 8 minutes
  peer: none (sidecar)
  witness_plan: negative filesystem access probe, not mathematical witness
Use ultra-code-swarm sidecar protocol. Registered author pilot/isolation, model gpt-6-luna, reasoning medium. Board helper /home/codex/projects/codex-skills/ultra-code-swarm/scripts/ultra_code_swarm_bb.py; export ULTRA_CODE_SWARM_BOARD to board path. Post started and final in this assignment thread. Inspect available bwrap/codex exec and authentication/config metadata without printing secrets. Propose an allowlisted namespace launching codex exec gpt-6-luna medium with no prior context, no home/repo mount, no answer files, minimal tool mount, same neutral source inputs for each arm. Network API must work but online searching prohibited. Do not run any agent process; root owns launches. Existing CLI installed at /home/codex/node_modules/.bin/codex. Current root will independently prepare inventory/config/run recorder; you must not edit files. Read only generic procedure /home/codex/projects/ladon/docs/CORRESPONDENCE_DISCOVERY.md and frozen design if useful, no case answers needed. Report availability risk, exact minimal mounts/config, token budget enforceability, and accessible-path limitations. No Lean declaration search required. Findings only via board. Check board at meaningful boundaries and before final.

### #2 pilot/isolation [status / active]
- Author: `pilot/isolation (isolation)` (contract_auditor)
- Communication: `isolation -> Root (reply #1)`
- Created: 2026-10-10T10:30:09.818Z
- Replies to: #1

Started read-only feasibility audit. Read the generic procedure and assignment; checking bwrap path isolation, local CLI flags, and auth/config metadata without reading credential contents.

### #3 pilot/isolation [audit / partial_support]
- Author: `pilot/isolation (isolation)` (contract_auditor)
- Communication: `isolation -> Root (reply #1)`
- Created: 2026-10-10T10:30:39.537Z
- Replies to: #1

Read-only namespace feasibility audit (no case source or answer was opened; no agent process launched; no repo/OpenSpec file edited).

Findings: `/usr/bin/bwrap` is available (bubblewrap 0.11.1); `codex-cli` is available (0.162.0), Node is v22.22.1, and `codex login status` reports logged in. This establishes local auth availability only, not that auth works when relocated into an isolated CODEX_HOME. Credential/config metadata: `/home/codex/.codex/auth.json` and `config.toml` both exist, mode 0600; I did not read their contents. The codex entrypoint resolves to `/home/codex/node_modules/@openai/codex/bin/codex.js`.

Negative filesystem probe passed: a bwrap shell with only read-only `/usr`, `/lib`, `/lib64`, `/bin`, proc/dev and tmpfs `/tmp`, plus an empty `/home`, could not stat either `/home/codex` or `/home/codex/projects/quux`. This confirms path hiding is feasible for that mount set; it is not a test of Codex/API startup.

Minimal practical command shape (root should substitute the neutral input directory and inherited FD 3; this is a proposal, not run):
`bwrap --unshare-user --unshare-pid --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 --ro-bind /bin /bin --ro-bind /etc/ssl/certs /etc/ssl/certs --ro-bind /etc/resolv.conf /etc/resolv.conf --dev /dev --proc /proc --tmpfs /tmp --dir /tmp/home --tmpfs /run --dir /run/codex --file 3 /run/codex/auth.json --ro-bind /home/codex/node_modules/@openai/codex /opt/codex --ro-bind <neutral-input-dir> /input --dir /work --chdir /work --setenv HOME /tmp/home --setenv CODEX_HOME /run/codex --setenv TMPDIR /tmp --setenv PATH /usr/bin:/bin -- /usr/bin/node /opt/codex/bin/codex.js exec -m gpt-6-luna -c model_reasoning_effort="medium" --ephemeral --ignore-user-config -s read-only --skip-git-repo-check -`
Open FD 3 from the auth file without echoing it; `--file` copies it into the private `/run` tmpfs, so no home mount is needed. A read-only bind of auth.json is an alternative but may prevent credential refresh. Keep input mounts identical and read-only across arms; mount no answers, repo, home, config, or prior session. `/usr` and the shared library trees above are broad read-only tool/runtime mounts, not a strict command allowlist; a tighter staged runtime would need dependency collection and an API smoke test.

Limits: `codex exec --help` has no hard token-budget option. Prompt instructions are not enforcement. JSONL accounting plus a watchdog could terminate after observed usage, but may overshoot and is not a strict cap; enforce a true cap at the API/proxy boundary if available. Since API networking must remain enabled, bwrap alone does not prohibit online searching: model web-search tools and shell-launched network clients share the allowed egress. A real guarantee requires explicit web-search disablement plus egress filtering that permits the Codex API endpoints only (or equivalent proxy policy). Otherwise record the no-search rule as procedural, not enforced. Read-only Codex sandbox restricts writes but does not reduce readable paths inside the mounted runtime/input set; fresh context does not exclude labels that are readable there.

Availability risks: isolated auth may need refreshed credentials or other state; `/etc` DNS/TLS paths and Node runtime dependencies need a smoke check. The bwrap probe verifies only filesystem hiding. Generic procedure read: `/home/codex/projects/ladon/docs/CORRESPONDENCE_DISCOVERY.md`; it explicitly cautions that fresh contexts must exclude reference answers and that source inventories are not guaranteed complete.


### #4 pilot [lifecycle / info]
- Author: `root` (root)
- Communication: `NEW POST by Root`
- Created: 2026-10-10T10:35:08.818Z
- Tags: `frontier:pilot`

Root accepted sidecar evidence post 3 after replay: real namespace tool probe and neutral Luna API/tool probe passed. The worker prematurely marked its assignment complete; root review is recorded here without rewriting history. Mode now serial root recording with two concurrent isolated experimental agents; neither can access this board. Frozen candidate and 28 first-attempt pairs recorded under evidence/implementation/evaluation. No independent proof-swarm portfolio: evaluation arms must not share findings. Token allowance is post-turn measured, not a hard API cap; network search prohibition procedural. Only input/work/tool mounts admitted; no labels or prior results. Root owns scoring and OpenSpec state.

### #5 pilot/final-audit [assignment / active]
- Author: `root` (root)
- Communication: `Root -> final-audit`
- Created: 2026-10-10T10:41:43.624Z
- Recipient: `pilot/final-audit`
- Tags: `frontier:pilot`

assignment_contract:
  frontier: pilot
  role: integration_auditor
  deliverable: independent read-only review of scored pilot counts, classification, coverage, fairness, isolation claims and consuming guide
  relevant_threads: [1, 3, 4]
  forbidden_shortcuts: [treating verdict alone as reference score, treating valid method difference as falsity, calling summaries Lean checks, crediting known cases as withheld, editing scores or packet]
  soft_evidence_deadline: 3 minutes
  hard_cancellation_deadline: 5 minutes
  peer: none (sidecar)
  witness_plan: mathematical review of retained counterarguments; no new Lean formalization
Registered author pilot/final-audit, model gpt-6-luna, medium. Use ultra-code-swarm board helper /home/codex/projects/codex-skills/ultra-code-swarm/scripts/ultra_code_swarm_bb.py and export ULTRA_CODE_SWARM_BOARD to literal board path. Post started then final reply to assignment; root owns completing/retiring assignment, do not mark yourself terminal.
Read-only sources: /home/codex/projects/ladon/openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/{REPORT.md,scores.json,reference-labels.json,reference-inventory.json,configuration.json,freeze.json,run_pilot.py,runs/}; consuming guide /home/codex/projects/ladon/docs/PROOF_CORRESPONDENCE_AUDIT.md. Check paired totals from records, e06 method difference, e12 abstention, both longer claim inventories, incidental report errors, and whether negative conclusion is justified. Inspect isolation claim against actual runner/probes. No mathematical case reruns, model calls, online searches, builds, production edits or source-goal search are needed. Cases are authored/rendered-formal summaries and no runtime detector is claimed. Report actionable errors precisely and distinguish bounds/procedural guarantees. Poll board at meaningful boundaries and before final. Final findings only on board.

### #6 pilot/final-audit [status / active]
- Author: `pilot/final-audit (final-audit)` (integration_auditor)
- Communication: `final-audit -> Root (reply #5)`
- Created: 2026-10-10T10:42:43.284Z
- Recipient: `root`
- Replies to: #5

Started the read-only audit. I am checking retained records against score/report aggregates, reading the long-selection report classifications, and comparing isolation claims with runner/probe evidence.

### #7 pilot/final-audit [audit / accepted]
- Author: `pilot/final-audit (final-audit)` (integration_auditor)
- Communication: `final-audit -> Root (reply #5)`
- Created: 2026-10-10T10:43:01.318Z
- Recipient: `root`
- Replies to: #5

Independent read-only audit complete. I found no material defect in the report’s paired totals, scoring classifications, coverage arithmetic, or negative pilot-scoped conclusion.

Checks and evidence:
- All 28 retained records say completed. Recomputed from records: ordinary 194.8051 s / 333,138 tokens / 14 completed tool items; assisted 285.0924 s / 419,530 tokens / 19 items; zero token overruns. These round to the report values and +46.35% time / +25.93% tokens. Process durations are summed despite concurrent execution, as disclosed; this is not elapsed wall time for the whole study.
- Per arm, score rows give 8/8 supported predeclared findings when e06’s valid method difference is counted as localization; 5/6 faithful controls accepted, one abstention on e12, no false alarms, no missed reference findings. e06 is verdict=faithful and described as a method difference, not falsity. e12’s unresolved status is appropriate because its formal summary omits the proposition. Both long inventories are covered: 6/6 l01 and 5/5 l02; the latter’s additional true-claim omission is recorded separately in both score rows and not added to the predeclared finding count.
- The l01 geometric-block argument is valid for n+1 in each block [2^k,2^(k+1)); each block contributes at least 1/2, proving divergence. l02’s n=1 counterexample refutes the parity implication; the omitted n+1>n assertion is true and correctly treated as an omission. The e06 symmetric pairing and summarized induction are distinct valid methods for the same stated identity.
- One incidental report wording error is accurately disclosed: ordinary l01 calls the series the harmonic series “with its first term omitted.” With n ranging over naturals from zero, it is the standard harmonic series reindexed; either description leaves the block divergence proof intact. No other material incidental error appeared in sampled retained records or score annotations.
- Runner uses bwrap --unshare-all plus --share-net, read-only binds for inputs/dependencies, a private writable profile/work directory, and no reference-label/report/repository/board mounts. The fixed probe tests ordinary paths and /proc/1/root paths as inaccessible. Retained events show no online search or answer-file access. Thus filesystem exclusion is evidenced; shell network egress was not filtered and the no-search rule was procedural; API/service-side exposure and backend identity are not independently attested, as the report says. The 65,536 token allowance is post-turn accounting, not a hard request cap.
- The consuming guide states the key bounds: 14 elementary authored inputs, summaries rather than Lean modules, no scored Lean checking, no detection advantage, and no research-paper effectiveness result. Its e03 discrepancy and e09 faithful control are supported by the supplied cases/reports.

Conclusion: evidence supports “no comparative detection advantage” for this frozen authored pilot and therefore the unmet pilot benefit criterion; it does not establish that the workflow lacks benefit on natural research texts. The guide’s scope matches that limit. No edits or reruns made.


### #8 pilot [audit / accepted]
- Author: `root` (root)
- Communication: `NEW POST by Root`
- Created: 2026-10-10T10:45:27.492Z
- Tags: `frontier:pilot`

Root accepts independent audit post 7: paired totals, method/statement scoring and source claim coverage checked. Verification passed for 28 first-attempt bindings, all 25 observed source digests, 360 frozen runtime source files, 136 authored links, neutral retest files and unchanged Quux marker. Strict OpenSpec validation and diff whitespace checks passed. No production runtime child; 49 existing integrity/assessment tests retained. Negative pilot benefit accepted; no new evaluation started. Both sidecars have completed; no swarm worker remains active.

## Frozen Artifacts
