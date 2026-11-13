# External memory profiling qualification

The installed external tools are sufficient for the first diagnostic. No Ladon source,
CLI, runtime dependencies or Lean helpers changed. See [identity](IDENTITY.json) for
source hashes, exact revisions, retained raw capture digests and paths.

Installed in `.venv`: Ladon 0.4.2, psutil 7.2.2, Memray 1.20.0.
The [one-off harness](measure.py) is an experiment, not a product module.
Each query used the current source checkout, read-only `theorem lineage` with
`--refresh never`, and the matrix-factorization proof-search index. Target and command
are retained in each summary. No source/index mutation was requested.

| Mode | Elapsed | Samples | Sampling time | Root peak RSS | Root peak PSS | Root peak USS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| psutil sampling | 5.776 s | 58 | 0.340 s | 129.54 MiB | 121.18 MiB | 118.34 MiB |
| Native Memray + psutil | 11.951 s | 120 | 0.676 s | 166.17 MiB | 156.77 MiB | 153.00 MiB |

Both target exits were zero, both query statuses were `available`, and payloads are
identical after removing `elapsedSeconds` and `acquisitionElapsedSeconds`. Stderr retains
the ordinary lineage progress events. No descendant was observed in either query;
this does not prove no transient child ran. No unavailable reads were observed.
Memory columns are separate maxima and need not occur at the same sample.

The synthetic child control allocated 16 MiB in its Python parent and 64 MiB in its
Python child and kept them alive for observation. Nine samples observed one descendant,
with parent/child RSS maxima about 26.87/72.61 MiB and tree RSS 99.48 MiB. Its exit was
zero. This qualifies parent/child separation on this control, not Lean coverage or
complete capture of process creation/reparenting races.

## Allocation report

`memray flamegraph` and `memray summary` successfully read the actual capture. The
binary capture and generated HTML remain under ignored `temp/memory-profiling-r01/`;
their identities are retained rather than committing binary or generated HTML output.
The textual report and largest tracked allocations at the high-water mark are retained.

Memray's tracked allocation peak was 109,368,848 bytes (~104.30 MiB), distinct from RSS.
The largest records' Python stacks point to `lean_paths_under_root` in
`src/ladon/lean_layout.py`, called by repository snapshot capture. This identifies a
measured allocation location; it does not establish a leak or an urgent performance
problem, and no optimization was started.

One reporting attempt failed: `memray stats --json` rejects pre-aggregated captures
in Memray 1.20.0. No stats JSON was produced. The documentation uses the qualified
summary/flamegraph path, and explains omitting `--aggregate` if stats is needed.

## Reproduction and limits

From Ladon's root, using the installed environment without resynchronizing it:

```bash
.venv/bin/python temp/memory-profiling-r01/measure.py sampled
.venv/bin/python temp/memory-profiling-r01/measure.py memray
.venv/bin/python temp/memory-profiling-r01/measure.py child-control
.venv/bin/python -m memray summary temp/memory-profiling-r01/memray/allocations.bin
.venv/bin/python -m memray flamegraph -o temp/memory-profiling-r01/memray/flamegraph.html \
  temp/memory-profiling-r01/memray/allocations.bin
```

The harness is retained here and can be copied back into a **fresh** scratch directory;
its exercise directories must not already exist. Its fixed query/project are explicit
in the script. It is not a production cleanup/signal implementation. Missing readings
are counted; aggregate peaks only cover successfully observed rows. A missing process
must not be interpreted as a certified zero footprint.

Sampling and tracing overhead is included; sampler memory is outside the measured tree.
These are single local samples with no cold/warm classification, repetitions, confidence
intervals or general overhead claim. PSS/USS sampling took substantial time relative to
this short query. Sequential process reads miss instantaneous peaks. Memray does not
profile separately executed Lean allocations. No new Lean run was necessary.

## Disposition

Document external profiling. Keep normal runtime dependencies empty. Do not introduce
a new product module or CLI command until repeated use demonstrates a missing operation.
The earlier CLI draft and expected red results remain under ignored
`.codex/state/memory-profiling/`; they are superseded, not implementation evidence.
