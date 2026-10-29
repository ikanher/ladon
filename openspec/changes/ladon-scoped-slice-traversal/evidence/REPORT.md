# Configurable proof-slice traversal and cache measurement

The public extractor now accepts `--max-nodes N` (Python: `max_nodes=N`) for
both profiles, defaulting to **131,072**, with valid integer range
**1–1,048,576**. It validates the budget before filesystem/compiler setup,
records it in slice identity, and preserves it at both correspondence freshness
replays. Independent 60-second process, 12-GiB RSS, depth-64 and output/expression
bounds remain unchanged. No cache optimization was retained.

## Measured reason for the default

The original scoped traversal takes **109,620 visits** to find one application
in the selected theorem. A negative-subtree cache reduces that to 10,711 visits,
but the elapsed-time benefit is small on this workload. Three paired executions
used the same compiled owner context, allowance of 131,072 and process bounds;
order alternated between pairs. No shared builds ran concurrently.

| Measurement | Original traversal | Proposed negative cache |
| --- | ---: | ---: |
| Visits | 109,620 | 10,711 |
| Median traversal time | 98.0 ms | 24.9 ms |
| Median complete measurement-process time | 1.448 s | 1.390 s |
| Maximum observed process-tree RSS | 3.556 GiB | 3.559 GiB |

The process-time difference is about 58 ms, with essentially unchanged memory.
These are three-pair observations, not a general speedup claim. The comparison
includes import/startup and traversal, **not full slice serialization or provider
replay**. It uses the existing compiled owner context. Per-run receipts, exact
instrumented helpers and executed driver are in [cache-comparison](cache-comparison/).
The original raw-expression diagnostic (2,209 distinct expressions) counts a
different object from instantiated traversal visits and does not set the budget.

The earlier cache implementation and failing/passing synthetic experiment are
retained as deferred evidence. The user redirected the implementation toward
configurable allowances and measurement before optimization; board contract
posts 1489, 1493 and 1495 supersede the original fixed-budget contract in
[contract.txt](contract.txt). The final production traversal remains unchanged.

## Actual source-bound consumer

The [default-budget command](actual-default-command.json) privately compiles the
original selected source and gets past traversal. It then returns exit 2,
`status: unavailable`, `complete: false`, with:

```text
Unknown identifier `inst`
```

The failure is during elaboration of a printed closed context/proof, so stable
observation replay never completes. The command took **8.01 seconds** with
**3.63 GiB** peak RSS; it did not hit time, RSS or output limits. The
[result](actual-default.json) records the separate operational frontier.
The earlier [8,192-node cached attempt](actual-8192.json) remains unchanged.
No full slice, native correspondence certificate, mathematical refutation or
unfamiliar-source discovery is claimed. Child task 2.1 remains open; the next
engineering target is a minimal reproduction of the printed-context name failure.

## Verification

The first API/CLI regression run had 12 expected failures because the keyword
and option did not exist. The integrated implementation passed all 12 cases,
including real Lean checks through both profiles and both nondefault-budget
correspondence replays. A helper-only test refactor preserved all 10 assertion
ASTs and all 12 parameterized cases, resolving Radon complexity without changing
expectations. Original red, original green, and the earlier test snapshot are
retained here; the maintained test is `tests/test_proof_slice_limits.py`.

The final affected-consumer run passed **21 tests in 406.28 seconds** after the
last production edit and test refactor. It covers both helper profiles, custom
allowance replay, scoped occurrence ordering, local providers, Unicode identity
transport, historical profiles, untrusted observations and namespace overlays.
See [command](focused-tests-command.json) and [output](focused-tests.txt).

The current-checkout application controls also replayed unchanged: the five-loss
control is **accepted with zero residuals**; the four-loss probe has **two
residual premises**, identical to the original diagnostic. Commands took 4.62
and 4.72 seconds, respectively, with approximately 5.00 GiB peak RSS. These remain
ambient selected-application checks, not whole-closure certification or a proof
of the full prose norm statement. See [control summary](APPLICATION-SUMMARY.json).

This packet does not claim a complete repository-wide qualification. No full
suite or paper audit was rerun.

[Independent review](AUDIT.json), board post 1501, found no actionable correctness
issue in the final runtime diff. The reviewer ran no tests; execution evidence
is root-observed. The current frozen regression and deferred historical test
match their board identities. The full historical board registry still reports
an unrelated prior mismatch for `tests/test_rational_lean_encoder_v2.py`; it was
not changed by this work.

Changed Python modules and the maintained test pass Ruff and strict
Radon/maintainability/Vulture checks. Both bundled and shared Ladon skills pass
the skill validator; the new OpenSpec change passes strict validation.
[Input verification](input-verification.json) confirms 2,670 primary input files
and 21 original diagnostic artifacts unchanged. The broader umbrella's full
qualification and detection-benefit gates remain open. Nothing was pushed.
