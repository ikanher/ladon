# Bounded compressed connection transport

## Result

The aggregate connection transport now preserves the original canonical DAG
codec and adds an ASCII-only, separately versioned zlib envelope as a fallback
when canonical v1 wire exceeds the caller's existing cap. Small records keep
their exact v1 bytes. The envelope remains subject to the 8 MiB external wire
cap; decompression is bounded at 40 MiB before the existing canonical DAG,
32 MiB expanded-value, graph, depth, occurrence and string checks run. No native
artifact limit, process cap, connection authority or theorem semantics changed.

The fallback is used at the fresh connection supervisor/worker and previous
history boundaries. When compressed output is returned, connection v3 retains its exact ASCII
wire bytes in chunks of at most 256 KiB. Saved-history checks verify the
recorded digest and decode those original bytes; aggregate chunk bytes are rejected incrementally before concatenation,
empty chunks are invalid, and stopped v3 checks cannot retain completed output.
History validation does not invoke the local compressor. Existing v1/v2
snapshot schemas and semantics are preserved. Compression is lossless; JSON-looking history values remain opaque.

## Informed runs

The informed runs use the same formal owner and applicable existing resource
limits: 550 seconds, 12 GiB RSS and 8 MiB output. Each has isolated evidence.

| Case | Status | Controller time | Connection worker time | Controller peak RSS | Snapshot JSON | Worker stdout wire |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Five-order, compression v2 | connected | 511.73 s | 441.37 s | 5.92 GiB | 15,006,598 B | 1,538,459 B, compressed |
| Four-order, compression v2 | unresolved | 434.74 s | 365.43 s | 5.92 GiB | 12,325,618 B | 8,190,237 B, canonical v1 |
| Five-order, history v3 (prior validator revision) | connected | 487.57 s | 423.48 s | 5.92 GiB | 16,544,364 B | 1,538,375 B, compressed |
| Five-order, bounded v3 history revision | connected | 496.74 s | 427.94 s | 5.93 GiB | 16,544,897 B | 1,538,395 B, compressed |

All runs avoided timeout, memory, and output limits. All snapshots pass
`validate_snapshot`. The bounded v3 five-order snapshot also validates when both
the history reconstruction helper and transport compressor are replaced with
functions that raise; this demonstrates that history validation uses retained bytes rather
than recompressing. Its recorded implementation digest matches the current
shipped Python/Lean source inventory. Its retained stdout is 1,538,395 bytes in
six chunks. The
five-order completion is a conditional connection only; it does not certify NL
fidelity, the source theorem proof, mathematical falsity or independent
discovery. The four-order status remains unresolved.

## Verification

The focused transport, connection, CLI, history, scratch and compatibility
suite on the bounded v3 history revision passed **83 tests, 30 skipped** (see
`VERIFICATION.txt` for the exact command and runtime). Ruff and targeted strict
radon/vulture/compile checks passed for the four production modules and four
frozen transport test modules. The three original transport-specific frozen suites passed **17/17**, and the
new v3 boundary suite passed **3/3**. Together they cover malformed/truncated/concatenated streams, decompression
bounds, digest tampering, ASCII subprocess transport, retained-byte history
validation without compression, and byte-compatible small v1 output. The full
strict quality command's repository suite was run before the v3 receipt addition;
it completed in 74m17s with **5,516 passed, 86 skipped and 3 failed**. No
transport test failed.
Two proof-contract worker scratch tests failed because their test shim rejects
the `workspace_parent` keyword before reaching its marker; the failing tests are
`test_outer_stage_timeout_recovers_a_delegated_goal_without_deleting_its_bytes`
and `test_timeout_after_real_goal_write_cleans_only_the_owned_goal_tree`. The
third failure is the project-wide strict-quality assertion, which found ten
radon C/D findings in other Real-bound analysis/worker and test files; none is
in the four production modules or four transport test modules covered by the
scoped strict gate. The complete list is preserved in `VERIFICATION.txt`.

The board-wide frozen-test verifier continues to report its existing unrelated
mismatch for `tests/test_rational_lean_encoder_v2.py`; the file itself matches
HEAD and was not edited or refrozen. All four active transport tests match
their frozen hashes. The first draft of the subprocess test omitted a required
output bound; it was preserved under
`.codex/state/real-prose-connection-consumer/superseded-tests/` and explicitly
superseded before test execution.

Task 2.2's compressed-history portability gate is resolved for v3: the receipt
retains exact bounded wire bytes, with aggregate bounds enforced before join,
and history verification does not depend on the local zlib compressor. The
previous compression-v2 experiment remains historical with its original schema;
the final informed run used the bounded v3 validator.
Task 3.1's overall qualification, source-pair discovery and parent propagation
remain open. The three full-suite failures are test-maintenance findings, not
mathematical results. Independent reviews and final manifest reconciliation are
recorded on the durable board. Nothing was committed or pushed.
