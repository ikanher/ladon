# Memory profiling for internal development

Start with external tools. No new Ladon module or command is required.
Use the Python interpreter in the selected Ladon checkout, where the profiling
packages are installed. These are optional developer tools, not core dependencies.
From Ladon's root:

```bash
.venv/bin/python -m pip install memray psutil
.venv/bin/python -c 'import memray, psutil; print(psutil.__version__)'
```

If this virtual environment does not include pip, use
`uv pip install --python .venv/bin/python memray psutil`.
Use `.venv/bin/python` directly for profiling: environment synchronization can remove
packages installed outside the lockfile. From matrix-factorization, its path is
`../../ladon/.venv/bin/python`.

## Python allocation attribution with Memray

Insert Memray before the existing Ladon invocation. Replace the declaration and
repository below with the query being diagnosed:

```bash
mkdir -p temp/memory-profile
.venv/bin/python -m memray run --quiet --native --aggregate \
  -o temp/memory-profile/allocations.bin \
  -m ladon.entrypoint theorem lineage Fully.Qualified.theorem \
  --repo-root /path/to/project --refresh never --view summary \
  --format json --output temp/memory-profile/result.json

.venv/bin/python -m memray summary temp/memory-profile/allocations.bin
.venv/bin/python -m memray flamegraph \
  -o temp/memory-profile/flamegraph.html temp/memory-profile/allocations.bin
```

Memray refuses an existing capture filename by default; choose a fresh path for each
run. `--quiet` suppresses profiler chatter without suppressing Ladon's diagnostics.
`--native` adds native-extension stack frames; omit it when that detail is unnecessary.
`--aggregate` reduces capture detail/size. With the qualified Memray 1.20.0,
`summary` and `flamegraph` accept this format; `stats` does **not**. Omit `--aggregate`
when a full event capture and `memray stats` are needed.

Memray measures allocations inside its Python interpreter, including native extensions.
It does not attribute allocations inside a separately executed Lean or Lake binary.
Its tracked allocation peak is also different from RSS. Tracing changes memory use
and runtime, so retain a separate uninstrumented measurement before comparing changes.
For long runs, use the target command's resource limits and keep captures on a filesystem
with enough space. An interrupted capture may not be readable.

## Parent and subprocess memory with psutil

psutil provides a measurement API. Sample the target PID and
`Process(pid).children(recursive=True)` externally, writing each sample immediately
to JSONL. Record process identities and root/child measurements separately:

- RSS from `memory_info()` is cheap. Summed RSS can count shared pages repeatedly.
- On Linux, PSS apportions shared pages; USS measures private pages. With psutil 7,
  read them through `memory_full_info()`. With psutil 8, use `memory_footprint()`.
- PSS/USS reads cost more and may fail due to permissions. Record unavailable readings;
  do not silently turn them into zero memory use.
- Sampling can miss short peaks, short-lived processes and reparented descendants.
  Reads across processes are sequential, not an atomic snapshot. Label peaks as sampled.
- Record the sample interval, sample count and sampling time. Keep the sampler outside
  the measured tree and bound the observation duration.

The [qualified local exercise](../openspec/changes/ladon-memory-profiling/evidence/external-tools-r01/REPORT.md)
includes a one-off harness and its exact query. It samples every 100 ms, retains the
raw process rows, and uses a 120-second deadline. It is a diagnostic example tied to
that exercise, not a supported general process supervisor. Ladon's existing watchdog
RSS limits and process-observation receipts remain the enforcement path.

## What the first measurement established

The stored-lineage query returned the same semantic payload with and without Memray.
The psutil-sampled run used about 130 MiB peak RSS; native Memray plus sampling used
166 MiB. Observed elapsed times were 5.78 and 11.95 seconds respectively. These are
one-off instrumented observations, not a benchmark or an estimate of pure profiler overhead.

A separate Python child-allocation control confirmed that parent and child readings
were distinguished. The actual stored query had no observed children; this exercise
has not qualified memory attribution inside a Lean process.

External Memray already identifies allocation stacks, and psutil already observes
process memory. No missing operation requiring a new Ladon module was established.
