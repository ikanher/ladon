## External-tool qualification

- [x] 1.1 Confirm installed tools and measure a bounded representative Ladon query with psutil, preserving root/descendant memory and output evidence.
- [x] 1.2 Qualify external Memray capture and reporting on the same operation, recording instrumented cost and scope limitations.
- [x] 1.3 Document repeatable recipes and observed gaps; validate documentation and OpenSpec. Do not add a product module without demonstrated need.

## Current result

External profiling qualified; no product module needed. See
[evidence and limits](evidence/external-tools-r01/REPORT.md) and the
[user recipe](../../../docs/MEMORY_PROFILING.md). All three exercise exits were zero;
Memray summary/flamegraph and evidence arithmetic/hash/link checks passed.
`openspec validate ladon-memory-profiling --strict` and `git diff --check` passed.
No production/test/lockfile changes; no product test-suite rerun was required.
Memray stats rejected the aggregate format; this is documented, with no stats result claimed.
Remaining gap: no actual Lean-process sampling qualification, no exact peak/overhead claim.
