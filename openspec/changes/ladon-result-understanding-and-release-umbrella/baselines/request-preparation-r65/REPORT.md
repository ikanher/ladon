# r65 bundled view preparation maintenance

Bundled inspection and guide requests now retain their complete, validated dossier
in the private bundle snapshot instead of preparing it twice. The snapshot lives
only inside the existing bundle context. Selected checking cards project the
already validated receipt population through the checking owner. Public explicit
entrypoints retain their signatures and complete validation; private renderers
retain selector/limit validation. No schema, CLI, persistent cache/session,
checking authority, network/Lean operation, dependency or page-limit change.

## Evidence

The new six-case regression suite first reported **2 failed, 4 passed**: both
bundled operations prepared twice, while parity and malformed-unselected-receipt
controls passed. After integration, the focused owner/consumer suite passed
**30 tests**. Frozen assertions remain unchanged after import sorting.

The real r49 bundle produced byte-identical output, including binding and cursor:

| Selected operation | Before | After | Output bytes |
|---|---:|---:|---:|
| Component inspection | 9.13s | 4.80s | 18,305 |
| Checking guide | 9.39s | 4.87s | 28,863 |

These are two one-shot operations on a shared host, not statistical measurements
or evidence of mathematical reader benefit. Maximum process RSS remained around
222–226 MiB. [Comparison](real-bundle-comparison.json) and time records retain scope.

An explicit complete current-input snapshot was built into a wheel/sdist and
passed the installed distribution smoke. All **289 result tests** passed against
the installed wheel on Python 3.11 and 3.12 from `/tmp`. The initial `worktree`
materializer rejected inherited untracked required inputs; a directory snapshot
included them without staging or changing Git state. The initial `python -m ladon`
measurement invocation failed because there is no package `__main__`; actual
measurements use the normal `.venv/bin/ladon` entrypoint. Both setup failures
remain recorded, not counted as product failures or successful commands.

## Portfolio and limits

Three real Luna medium roles were dispatched on the canonical evidence board:
red author, green proposer and distinct source auditor. Red reproduced the
failure. The green assignment requested a patch only, but its edits appeared in
shared source; root interrupted it, corrected omitted selector validation and
selected-target initialization, and ran verification itself. No worker-reported
green qualification is credited. The independent audit found no actionable issue;
it performed source inspection, not test execution. Relevant posts:931–947 in
`.codex/state/ultra-result-evidence.sqlite3`. All workers are retired.

No mathematical-project files were changed during this maintenance. The checked
r64 handoff stays proposed; the user moved on to improving Ladon. Umbrella task9.1
remains unmet/deferred, and this repair adds no comparative usefulness claim.

## Final acceptance

**Accepted bounded maintenance.** The full strict gate passed: radon/vulture,
Ruff, compileall and **3,173 maintained tests** (333.75 seconds). OpenSpec strict
validation and scoped whitespace checks passed. Packaged real-bundle inspect on
Python 3.11 and guide on Python 3.12 from `/tmp` also match the original bytes.
[Installed origins](installed-origins.json) confirm virtual-environment
site-packages and identical module bytes to the selected snapshot;
[acceptance](acceptance.json) binds the wheel and full snapshot inventory.

Final report assembly initially dereferenced the venv Python symlink and ran its
base interpreter, producing ModuleNotFoundError in the origin-inspection harness.
Correcting the executable spelling preserved the venv and verified installed
origins. This was an assembly failure, not a product/test failure; board949 was
premature and superseded by the final corrected record.

This qualifies the maintenance slice, not every historical runtime qualification
or the full umbrella. No source or index changes were staged or committed.
