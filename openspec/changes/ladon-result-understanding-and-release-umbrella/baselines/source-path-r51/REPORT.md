# Source-path filtering repair — r51

Source-path filtering is **34% faster on installed Python 3.11 and 29% faster on
installed Python 3.12** over the frozen real-project corpus. Selected paths and
the full source digest remain identical. The repair constructs one `Path` per
validation instead of reparsing its normalized text twice. All source/toolchain
rechecks, safety bounds, classification, ordering and hashing remain in place.

Candidate `668dc2ad5b13625a5149b746cf1c926f1020905a` passes 2,950 maintained tests,
29 installed CLI contracts, strict quality/package gates and 915 relevant
installed tests on each supported runtime. Real matrix discovery still compiles
the valid application and preserves the missing prerequisite in the partial one.
This qualifies a bounded cost repair, not mathematical usefulness or general
search superiority. Umbrella accounting remains **33/50**.

## Frozen contract and implementation

The [r50 profile](../core-discovery-r50/profile-summary.json) identified six
source-tree identity calculations and substantial source filtering cost. Those
checks protect different boundaries; this repair preserves every call rather
than caching identity by path or modification time. The [contract](contract.json)
requires at least 20% lower median filtering time, exact selected outputs/errors,
unchanged mutation detection, supported installed runtimes and real A/B replay.

The [implementation diff](implementation.patch) is confined to the existing
validator. It reuses `Path(relative)` for `as_posix`, `parts` and `is_absolute`.
Filtering still validates all raw paths before classification. Fallback traversal
still yields root files before child files; no global sorting was introduced.
The package and source inventories show one runtime/build/tooling change:
`ladon/lean_toolchain.py`. Wheel `RECORD` changes accordingly; the remaining
349 runtime members are byte-identical to r49. No dependency or schema changed.
See [package parity](package-parity.json) and [source parity](source-parity.json).

Independent red, scout and falsifier workers established error precedence,
normalization boundaries, fallback ordering and symlink identity behavior before
implementation. Twelve new characterization cases passed on the baseline. The
unchanged implementation then failed the frozen performance gate with only 1.22%
apparent improvement; that is the performance red result, not a correctness bug.
Tests, corpus identities, baseline and timing harness were frozen before green
work. The green proposal confirmed the parsing opportunity; root selected the
smaller existing-function repair rather than adding helpers. A distinct auditor
found no actionable defect, and root reran its differential probe: 69,942 path
strings and 64 filter pairs produced identical accepted outputs or exception
types/messages. The audit probe's escaped backslash-x00 is not actual NUL;
[supplemental probes](supplemental.json) separately cover actual NUL, leading
slashes and depth bounds while preserving legacy behavior. These are Linux
observations on the supported Python versions, not an exhaustive platform proof.
The [portfolio](portfolio.jsonl) records assignments, adjudication, the worker
registration correction and audit. [All 50 active frozen files](frozen-tests-verification.json)
retain their hashes.

## Performance and source identity

The corpus was captured through the existing source-enumeration owner in the
trusted matrix-factorization environment: 108,553 raw paths and 10,981 selected
paths. Only its [summary and hashes](paths-summary.json) are exported; the raw
names remain in `/home/codex/.cache/ladon-source-path-r51/paths.json`.
The [timing harness](reproduce/benchmark_source_filter.py) verifies those identities,
then alternates baseline/candidate order for five pairs in the same interpreter.
It imports the candidate module from the installed wheel, outside the checkout.
No timing assertion was added to ordinary CI.

| Installed interpreter | Baseline median | Repaired median | Reduction |
| --- | ---: | ---: | ---: |
| CPython 3.11.15 | 0.840 s | 0.554 s | 33.99% |
| CPython 3.12.12 | 0.826 s | 0.585 s | 29.17% |

[3.11 samples](py311-performance.json) and [3.12 samples](py312-performance.json)
retain the complete vectors and ordering. Qualification work shared the host;
these small, paired filtering measurements establish the scoped gate rather
than a statistical productivity benchmark. The initial integrated source run
also passed at 34.64%; worker timings are not substituted for installed evidence.

The full digest over the frozen selection was computed with baseline, installed
candidate, then baseline again. All three equal
`sha256:1f117a8be448768318eb658cd370c4f5d4f5e3088f04a177c4e372de363b7b74`,
matching the original capture. See [identity parity](source-identity-parity.json)
and its [reproduction script](reproduce/compare_source_identity.py). This is
identity equality over the frozen inputs; the live project acquired another
source during subsequent index work and is not claimed to remain unchanged.

## Ordinary real-project replay

The r49/r50 goal, ordered local contexts, module and literal type-text pattern
were reused without supplying a candidate name. Commands used the installed
CLI, explicit Lean/Lake 4.33.0, freshness verification and 32 GiB RSS limits.
The first discovery rejected the retained r50 index as stale. A new isolated
index build rejected `Mf/DP/Profile/RationalPolicyLogarithm.lean` changing during
the build; its failure remains recorded. A bounded retry succeeded in 92.33 s,
about 111 MiB peak tree RSS. No freshness check was weakened and the existing
r50/shared indices were preserved.

| Replay | Outcome | Command time | Peak tree RSS |
| --- | --- | ---: | ---: |
| A | Propagation lemma accepted and scratch compiled; three rejects | 25.54 s | 8.37 GiB |
| B | Exact boundary-gap residual; three rejects | 19.72 s | 8.36 GiB |

B retains `0 ≤ Mf.DP.fixedEpochCenterGap point h boundary`; it does not infer
that the goal is false. All four names, exact theorem source identities,
application terms, discharged premises, substitutions, residuals and scratch
statuses match the r50 mathematical outcome projection. Full receipt/environment
identities are not claimed byte-identical across a changing live project.
[Observations](observations.json) bind all five commands, including both failed
setup attempts, streams, limits and telemetry. No run hit resource limits.
These root-operated replays are not fresh-reader experiments. The historical
r50 command times differ, but they do not form a controlled overall speed test.

## Qualification, retained errors and next decision

[Qualification](qualified-candidate.json) binds the immutable candidate, wheel,
all commands/log hashes, installed origins and test counts. The clean gate
covers strict quality, full maintained tests, collection parity, locked build,
wheel/sdist/resource consistency and installed CLI contracts. Separate isolated
3.11/3.12 gates cover semantic, discovery, result and toolchain/path consumers.
[Final artifact verification](verification.json) rechecks all retained command/log
bytes, installed production parity, frozen tests, unchanged historical records
and root Git guards. The independent audit reviewed the focused patch and differential behavior;
it did not run these package gates. Root HEAD/index remain unchanged; only a
cache-local qualification snapshot was committed. No global install, neighbor
source/build edit, archive or publication was performed.

Retained harness failures include the initial capture field typo, a focused
command naming nonexistent `test_source_enumeration.py` (no tests collected),
and report projection calling `.get` on absent scratch evidence. The corrected
filename/context suite passed 20 cases; the other focused suites passed 61.
[capture-error.txt](capture-error.txt) and [report-harness-error.txt](report-harness-error.txt)
classify reporting/setup errors separately from product rejection. Failed
attempts were not counted as passes. Earlier r48/r49/r50 records remain history.

Next, profile semantic delivery on the repaired candidate. If repeated envelope
validation remains material, test reuse of an owned, validated immutable result
inside one request, retaining complete-input validation and exact identities.
Do not infer that persistent caching or more result-layer features are needed.
The compact partial-applicability reader hypothesis and r49 usefulness gate
remain untested/unmet; provenance, community profiles and quantitative reader
metrics remain deferred. No additional umbrella task is closed by this repair.
