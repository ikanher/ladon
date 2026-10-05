# Explicit source-goal completion

`ladon proof-search goal complete` checks a whole proposed term against a captured source goal. Independent Lean compilation and transitive axiom checking are part of the operation. The [r59 report](../openspec/changes/ladon-goal-capture-and-application-probes/evidence/application-completion-r59/REPORT.md) qualifies this completion slice. The [r60 handoff](../openspec/changes/ladon-goal-capture-and-application-probes/evidence/application-handoff-r60/REPORT.md) records fixed-epoch integration and limit controls. The [owning change](../openspec/changes/ladon-goal-capture-and-application-probes/tasks.md) is complete; exposition review remains a separate parent outcome.

Save the complete JSON output from [goal capture](SOURCE_GOAL_CAPTURE.md), then submit the exact term:

```sh
ladon proof-search goal complete \
  --repo-root /path/to/lean-project --capture-file /outside/goal.json \
  --term 'someLemma argument premise' \
  --lean-path /absolute/pinned/bin/lean --lake-path /absolute/pinned/bin/lake \
  --format json --output /outside/completion.json
```

The input must be a successful `ladon-source-goal-capture-result-v1` envelope. Text projections, bare inner captures, handwritten goals, candidate acceptance and historical scratch receipts cannot supply this CLI input. The API takes the inner capture: construct `SourceGoalCompletionRequest` with `repo_root`, `capture`, `term` and an explicit `LeanToolchainContext`, then call `complete_source_goal`.

The operation checks the capture's canonical identity before execution, re-observes the source position and compares its actual goal, ordered context, scopes, options and pinned compiled environment. It elaborates the term there. Local definitions retain their actual values; internal/self dependencies cannot become added hypotheses. Closed expressions must survive printing and parsing with empty local context before ordinary compiler replay. Temporary files stay outside the target project. Reports cannot overwrite the capture file, sources, helpers, executables or compiled artifacts.

The initial profile is ordinary non-modular source with default frontend setup. Definitions available only in the unfinished source may be unavailable to replay. This prevents completion without implying the goal is false. The operation does not insert a proof or establish the enclosing production declaration.

The schema `ladon-source-goal-completion-result-v1` separates `application`, `replay` and `trust`:

| Status | Meaning |
| --- | --- |
| `completed` | Original-goal checking, independent replay and complete permitted trust evidence all succeed. |
| `incomplete` | This application leaves actual residual goals in their observed contexts. |
| `rejected` | The proposed term fails checking. |
| `trust-rejected` | Replay succeeds but dependencies violate the policy. |
| `stale` | A captured source, context or environment binding changed. |
| `unavailable` | Required checking or dependency coverage cannot be established. |
| `timeout`, `memory-limit`, `output-limit`, `process-failed` | Supervised execution did not establish the required result. |

Policy `lean-standard-no-placeholders-v1` permits `Classical.choice`, `Quot.sound` and `propext`. It rejects `sorryAx` and other axioms. Lean's independent compiler collects the generated declaration's transitive dependencies. Compiler exit zero, lexical scans and earlier checks cannot replace that evidence. A residual is an obligation of this application, not a claim of necessity for every proof.

JSON includes goal and term identities, actual residual contexts, replay source and digests, trust observations and process receipts. Text starts with the outcome and residual propositions, then replay and trust status. Residual locals retain capture order and explicitly distinguish usable premises from internal implementation details. Available local definitions include their values as `name : type := value`; these labels do not change the authoritative capture or JSON. Mathematical outcomes (`completed`, `incomplete`, `rejected`, `trust-rejected`) return exit 0; operational failure returns exit 1; invalid invocation returns exit 2; interruption returns exit 130. Inspect the structured status for mathematical success.

Defaults are 60 seconds per process, 32GiB process-tree RSS and 8MiB process output. `--timeout-seconds`, `--max-rss-mib` and `--max-output-mib` change these execution bounds. Receipts record actual time and peak RSS, including replay; saved reports remain uncapped. Completion supports precise exposition and honest formalization scope. It does not establish prose correspondence, human understanding or comparative productivity.
