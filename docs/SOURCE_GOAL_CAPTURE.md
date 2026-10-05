# Source-goal capture feasibility profile

The Python API in `ladon.source_goal_capture` observes one goal at a source position. It supplies the observation used by the source-bound completion CLI. It does not apply a candidate, replay a term, check a theorem, or replace existing handwritten candidate/discovery input.

Create a `SourceGoalCaptureRequest` with a repository-relative regular `.lean` file, its module, a line and column, and an explicit `LeanToolchainContext` resolved from that repository's pin and selected Lean/Lake binaries. Lines are one-based; columns are zero-based Unicode scalar counts as in Lean's `FileMap`, rather than UTF-8 bytes or LSP UTF-16 units. A `goal_ordinal` is zero-based and required when the position has multiple goals. `expected_source_digest` accepts a lowercase `sha256:` digest and rejects stale source before target execution.

`capture_source_goal(request)` returns `ladon-source-goal-capture-result-v1`. The success status is `captured`, with a content-addressed capture containing:

- Exact source digest, byte length, requested position, raw tactic syntax range and cursor selection range. The latter includes the trailing trivia/EOF positions accepted by Lean's `goalsAt?`; its end is inclusive, whereas the raw syntax end is exclusive.
- The selected goal's raw identity, elaborated type and ordered local declarations, including binder information, types, available values, dependencies and implementation-detail roles.
- The selected `InfoTree` context's namespace, open declarations, options and actual imported closure.
- The observed Lean executable/version/commit and its pinned execution context, helper identity, and hashes of imported primary files and known sidecars.

The source is copied unchanged to an owned temporary directory and elaborated with its original repository-relative filename. No commands are inserted into it. An unfinished proof can supply a goal even when the full file has unsolved-goal errors. That observation does not establish the unfinished theorem.

The implementation first observes the import closure, hashes it, then repeats the source observation and verifies the same goal/context and disk inventory afterward. Known `.olean.server`, `.olean.private`, `.ir` and `.ir.sig` sidecars, including their absence, participate in the inventory. This establishes stable files around the observations in a trusted repository; it is not loader authentication against a hostile writer that swaps and restores files during execution.

Internal declarations, such as Lean's current `_example` local, remain explicitly marked. Capture does not turn them into extra user hypotheses or declare the context safe to reconstruct for replay. The later completion operation must establish its own forwarding and checking boundary.

The initial profile uses ordinary non-modular source with default frontend setup. It records source-local options and scopes but does not obtain Lake setup options, plugins or editor configuration. Modular source is unsupported. Missing/ambiguous compiled imports, unknown compiler commits, overlapping tactic contexts, no selected goal, malformed protocol data and changed inputs fail explicitly. No handwritten goal is substituted.

Every non-captured result has `capture: null`. Ambiguity, unavailability, staleness, timeout, memory limit, output limit and process failure remain distinct. Failed processes expose bounded diagnostic excerpts with truncation flags and retain stream digests. Receipts record actual commands, supervised helper time and RSS; operation wall time also includes inventory work. Default limits are 60 seconds per helper, 8 MiB helper output and 32 GiB helper process-tree RSS. These finite execution/input bounds are separate from uncapped saved reports.

The source helper uses the closed `ladon-lean-source-goal-v1/capture` protocol. Existing semantic-v3 checker protocols, receipts and exploratory acceptance labels are unchanged. Historical feasibility qualification alone does not establish CLI completion or comparative reader benefit; the separate completion report records its current gates.

## Ordinary CLI handoff

The CLI exposes `ladon proof-search goal capture` and `goal diagnostic` through the same source-capture API above.

The capture command selects the source module and position explicitly:

```sh
ladon proof-search goal capture \
  --repo-root /path/to/lean-project --source Owner.lean --module Owner \
  --line 2 --column 6 \
  --lean-path /absolute/pinned/bin/lean --lake-path /absolute/pinned/bin/lake \
  --format json --output /path/outside-the-project/goal.json
```

`--goal-ordinal` selects a zero-based goal when several goals share the position. `--expected-source-digest sha256:...` detects stale bytes before source elaboration. Both binaries must match the repository's `lean-toolchain`; this route has no ambient-toolchain fallback. Source capture uses the documented default frontend profile, not an inferred editor session or Lake setup.

The new source routes keep saved reports outside the target repository, or write to stdout. They reject destinations inside it and collisions with selected executable/helper/diagnostic inputs. This keeps report writing from changing the source inputs after capture. Existing handwritten candidate operations retain their output contract.

A diagnostic query takes a UTF-8 text file containing a supported ordinary Lean type mismatch:

```sh
ladon proof-search goal diagnostic \
  --repo-root /path/to/lean-project --diagnostic-file /path/to/lean-errors.txt \
  --module Owner --lean-path /absolute/pinned/bin/lean \
  --lake-path /absolute/pinned/bin/lake --format json
```

The initial text parser recognizes located `error: Type mismatch` records with indented expression, `has type`, and `but is expected to have type` blocks. Multiple matching records require `--diagnostic-ordinal`; it does not silently choose the first. Unsupported layouts fail explicitly. Lean's printed line is one-based and column is already zero-based in Unicode scalar units, so it is passed unchanged to capture. The diagnostic file's hash identifies the supplied text, not the Lean source file.

`queryEvidence` retains the parsed expression/types/location as `caller-supplied-compiler-text`. `captureResult` separately records an attempted elaboration at that source position. A constructor-field error may have no tactic goal there; its parsed expected type remains available, but does not become an observed goal. Source/module mismatch, unsafe paths, stale source, ambiguity and unsupported contexts retain their failure status.

JSON retains the complete capture and its evidence. Text foregrounds the selected goal and ordered local declarations, including available let values and explicitly marked internal locals, then shows source/environment identity and references into the complete JSON. A captured goal is an observation with replay `not-run`. None of these commands applies a theorem or establishes completion.

The new source route returns exit 0 only for `captured`, exit 1 for capture/selection/execution failure with its structured result, exit 2 for invalid invocation and exit 130 for interruption. `--progress` emits separate stderr records. The default helper bounds remain 60 seconds, 8 MiB output and 32 GiB process-tree RSS; saved reports are uncapped. Text parsing has a finite input bound, separate from saved-report size.

For a proposed full term, see the separate [explicit completion contract](SOURCE_GOAL_COMPLETION.md).
