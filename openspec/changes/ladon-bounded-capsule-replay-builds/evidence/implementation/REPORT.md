# Ordered capsule replay implementation — 2026-11-08

The public replay service and CLI now support `build_policy="ordered"` /
`--build-policy ordered`. The compatibility default remains `lake-default`.
Ordered replay validates and topologically sorts the project import graph, then
runs a no-build dependency preflight and an exact module build in sequence.
Missing compiled imports or unsupported Lake facets fail explicitly; no
unrestricted build fallback runs. All module calls share one finite build-stage
deadline. Content/isolation checks and final identity/trust comparisons remain.

## Measured scheduling result

The [hypothesis experiment](hypothesis-check/REPORT.md) retains raw traces,
source hashes and scripts. Pinned Lean 4.33 default scheduling launched three
compilers (4.50 GiB aggregate RSS); ordered requests for the same small graph
peaked at 1.62 GiB with one compiler. The reported capsule's initial frontier
also failed a 6 GiB aggregate cap with three compilers; those same three modules
all built individually below that cap. RSS and PSS were measured separately;
the RSS bound was not reinterpreted as physical memory.

Pinned Lake's `--no-build build +Module:deps` was additionally checked on a
missing-import fixture: it returned code 3 without compiling the missing module.
The leaf's own dependency preflight succeeded, its exact `+Module:leanArts`
build succeeded, and the parent's preflight/build then succeeded.

## Public large-capsule integration

One implementation attempt used the actual retained capsule, a fresh replay
root, `build_policy="ordered"`, `network="allow"`, a 6 GiB process-tree RSS cap,
and 180 seconds for each of dependency resolution, the entire build stage, and
the final helper. Exact source identities and limits are in
[actual-inputs.json](actual-inputs.json), with the full classified
[receipt](actual-ordered.json) and [summary](actual-summary.json).

Dependency resolution succeeded. Two project modules built. The next module,
`Mf.DP.GaussianPrivacyLoss`, exceeded the cap with only one observed Lean process:

- Aggregate peak: 6,539,939,840 bytes (6.09079 GiB).
- Individual Lean peak: 5,403,742,208 bytes (5.03 GiB).
- Memory limit reached; no timeout; process-group return code -15.
- Total replay wall time: 111.36 seconds.
- The final theorem/dependency comparison was not reached.

This is a resource-limit outcome, not verified or mathematically rejected.
No retry with a larger memory limit was made. The user subsequently authorized a 12 GiB trial; its outcome is recorded in
the follow-up below.

The attempt preceded review fixes rejecting non-finite timeouts and oversized
edge populations and correcting descendant counts to exclude the supervised
root. Its exact code hashes are retained. These guard/count-label changes do
not alter the valid 180-second graph scheduling or its measured Lean-process
count; the raw pre-review `maxDescendantProcesses` values include the root and
must not be interpreted using the corrected final definition. Final source
hashes are in [final-source-identity.json](final-source-identity.json).

## Verification

Baseline revision: `fa7e409ffe81b5fe5652697ab75046067b6db755`.
The independent test author's initial ten service/CLI/DAG/budget tests failed
because the policy did not exist. Three observer tests likewise failed for the
missing observation interface. Frozen acceptance tests are tracked in
`.codex/state/ultra-capsule-build.sqlite3`; later unused-argument lint changes
preserved all cases/assertions and were explicitly superseded/refrozen.
Existing RSS/timeout/descendant cleanup behavior was reused; its established
regressions and new observation-enabled cleanup tests were retained, rather
than making a correct existing cleanup path fail artificially.

Final command:

```bash
python -m pytest -q tests/test_capsule*.py tests/test_theorem_capsule*.py \
  tests/test_process_supervisor*.py tests/test_installed_theorem_cli_contract.py
```

Result: **80 passed in 60.08 seconds**, exit 0. This includes pinned 4.33
module-diamond materialization/replay after renaming the original checkout,
mutation rejection, post-build identity mismatch rejection, invalid invocation,
shared deadline exhaustion, memory exhaustion, and descendant cleanup.

Changed Python sources/tests pass Ruff, strict Radon/Vulture and compileall.
The frozen test hashes verify. The wheel was built offline with
`uv build --wheel --offline --out-dir /tmp/ladon-capsule-policy-wheel`, installed
without dependencies into an isolated target, and its replay/extract help was
checked against documented flags. The installed distribution identity is in
[installed-version.json](installed-version.json). Shared Ladon skill validation
passed. Repository-wide unrelated suites were not rerun.

Independent red, scheduling-scout, implementation and final audit workers were
used. The auditor's three findings (non-finite timeout, edge-count bound, root
included in descendant count) were fixed and reviewed; its final four non-Lean
suites passed 24 tests with no further actionable findings.

No schemas or stored evidence require migration. The existing replay receipt
schema receives additive `buildPolicy`, `resourceLimits` and observation fields,
each versioned independently; historical receipts are unchanged. Removing the
new policy path restores legacy scheduling without deleting capsule data.

## Authorized 12 GiB default and 0.4.1 follow-up

The user authorized 12 GiB and requested a version bump. The shared product
default was already 12 GiB; the prior 6 GiB experiments explicitly overrode it.
The default is now protected by CLI/parser/service-forwarding regression tests,
and the package/lockfile are bumped to **0.4.1**. The isolated 0.4.1 wheel and
`uv run --locked --offline ladon --version` both report the new version. The
installed replay API default is 12,884,901,888 bytes and the CLI default is
12,288 MiB. Seven focused default/version checks pass; no runtime implementation
changed in this follow-up.

One further public ordered replay used the service default (no explicit RSS
argument), `network="allow"`, and the existing 180-second stage budgets.
It passed `Mf.DP.GaussianPrivacyLoss` and completed **19** module builds before
exhausting the shared build deadline during `Mf.DP.BNB.BNBTraceLaw`.
The build peak was **8,159,080,448 bytes (7.60 GiB)**, `memoryLimited=false`,
`timedOut=true`, with at most one sampled Lean process. Total replay wall time
was 267.94 seconds including dependency setup. Final theorem comparison was
not reached; this is a timeout result, not a verified capsule. The remaining
large-case gate is enough build time for the full closure; the unbuilt remainder
has not been qualified under this memory cap.

The new [input identity](default-12gib-0.4.1/inputs.json),
[receipt](default-12gib-0.4.1/receipt.json),
[summary](default-12gib-0.4.1/summary.json),
[installed version](default-12gib-0.4.1/installed-version.json), and
[release checks](default-12gib-0.4.1/release-checks.json) preserve this outcome
separately from the historical 6/32/48 GiB runs. The cap and timeout were not
raised further after the timeout.
