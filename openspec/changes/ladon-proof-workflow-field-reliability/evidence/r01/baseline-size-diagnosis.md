# Ladon source-goal capture-size diagnosis

## Finding

The exact frozen late-goal source is reproducible under the repository's pinned Lean 4.33.0 and existing compiled import closure. Running the unmodified source-goal helper with output streamed to a 66 MiB cap crosses the cap after 69,271,552 bytes (the final read can exceed the cap by one 64 KiB chunk), exits by SIGKILL (Python return code -9), and takes about 11 seconds. `/usr/bin/time` reports 9,471,268 KiB maximum RSS. The retained early capture is 3,595,007 bytes and its selected goal plus locals total only about 9 KB.

A temporary instrumented copy of the helper reports the late goal has 16 locals. `he.valueStructural` is 108,297,084 UTF-8 bytes by itself; `he.valueDisplay` is 109,471 bytes. The next largest structural value is `hA.valueStructural` at 278,492 bytes. The goal type is only 345 bytes structurally; import-path JSON is about 2,019,712 bytes. The underlying source declares `he` as a function proof at lines 208–221; later local `hf`/`he` are consumed by the selected goal at line 236. This establishes repeated expansion in `repr Expr` for a retained local proof value as the cause of frame growth. The measurement does not identify which subexpression pattern in `he` causes the Expr expansion.

The helper builds `valueStructural := (repr value).pretty` in `localRow`, then compresses the complete `Observation` into one JSON string. The frame contains both the human `valueDisplay` and the recursive structural rendering. The line 236 capture is therefore a true output-size failure, not an import inventory growth or source-size issue. The high RSS is also material: it is almost 9.5 GiB despite the 108 MB final structural string, so a serializer fix should avoid first building another fully expanded representation.

## Reduced fixture status

I attempted a core-Lean `replicateTerm n` macro that expands a shared recursive child twice, then bound it as a local. The fixture source is `repeated-source.lean`; the instrumented helper run emitted a 424,306-byte frame at 2.8 seconds / 3.68 GiB RSS. However, `goalsAt?` selected the enclosing `by` block and the captured context omitted the `repeated` local, so this is not a valid witness for the capture path. I did not find the smallest synthetic failing witness within this pass. The exact frozen field case is conclusive for diagnosis; the synthetic minimality gate remains open.

## Representation and diagnostics

A representation that preserves meaning should encode Lean `Expr` as a shared graph: a node table with explicit constructors and child references, plus root references for each local type/value and goal type. Preserve binder names/info, de Bruijn indices, fvar IDs, constant names and universe levels, literals, projections, metadata, and let values. Keep `valueDisplay` as a human view, but do not make the expanded pretty or `repr` string the sole structural authority. Intern shared subexpressions while walking the `Expr` graph and reference their node IDs. This preserves exact local references and proof values while preventing repeated serialization of shared subtrees. Validate graph bounds, root existence, acyclicity/order constraints, and local dependency references in the protocol. Version the frame/capture schema because the current closed v1 contract requires both strings.

For frame-size diagnostics, compute and report a bounded preflight estimate before constructing the final compressed frame: per-goal/local UTF-8 field lengths, cumulative encoded size, largest field path (for this case `goals[0].localContext[11].valueStructural`, local name `he`), and configured output budget. Emit a small explicit `frame-too-large` diagnostic frame with these metrics, or stderr metadata under a separate tightly bounded channel, so the caller can distinguish a known oversized observation from generic process output truncation. The preflight itself must be streaming or graph-based; calling `Json.compress` on the expanded frame just to count bytes repeats the allocation problem.

## Consumers to account for

- `src/ladon/_source_goal_protocol.py`: closed frame/local field sets, string validation, and ordered local dependency validation.
- `src/ladon/source_goal_capture.py`: capture identity and persisted `goal.localContext`; the capture is later canonicalized and digest-bound.
- `src/ladon/_source_goal_completion_inputs.py`: validates captured goals and canonical `captureId`; a new representation must remain identity-bound.
- `src/ladon/lean/ladon_source_goal_completion_helper.lean`: independently builds the same local rows for residual goals using duplicated `repr` serialization.
- `src/ladon/lean/ladon_semantic_candidate_helper.lean`, `src/ladon/semantic_candidate_protocol.py`, and `src/ladon/semantic_local_context.py`: semantic local-context values participate in protocol validation and context identity. If the shared representation is adopted here, update all these producers/consumers together; otherwise the field schema can diverge.
- Public projection/presentation paths should continue exposing concise display text and avoid accidentally expanding the graph into a giant string.

## Reproduction and exits

Working directory: `/home/codex/projects/ladon`; compiled import closure: `/home/codex/projects/lean/matrix-factorization`; pinned executable: `/home/codex/.elan/bin/elan run leanprover/lean4:v4.33.0 lean`.

The exact request is retained in `request-late-exact.json`, the frozen source in `capture-source.lean`, the instrumented copy in `helper-instrumented.lean`, and the bounded runner in `run_exact_capped.py`. Run:

```sh
python temp/field-reliability-falsifier/run_exact_capped.py
```

Observed runner report: `bytes=69271552`, `rc=-9`, `killed_at_cap=true`, `wall_s=10.97`; outer `/usr/bin/time`: exit 0 for the Python wrapper, 10.98 seconds, 9,471,268 KiB max RSS. The wrapper intentionally kills the child after crossing its 66 MiB cap. The instrumented child writes per-local byte counts to `late.instrumented.stderr` before the oversized frame is serialized.

The core fixture was also run with the same pinned helper and exited 0, but it failed to expose the local in the selected context as described above. No repository build or production/test file was changed. All created files are under this directory.
