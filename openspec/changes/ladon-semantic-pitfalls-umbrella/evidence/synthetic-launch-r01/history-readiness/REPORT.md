# Ready to launch — synthetic comparison r01

All ten workspaces are prepared and verified. No mathematical audit has started;
all outputs are empty and all clocks are unactivated. The launch order, per-unit
manifest hashes and verification outcomes are in [READINESS.json](READINESS.json).

Use the [launcher handoff](LAUNCH-HANDOFF.md), also available at
`/home/codex/projects/ladon-evaluations/synthetic-r01/START-HERE.md`.
Launch one fresh Luna-medium auditor at a time, supplying only its PROMPT.md.
Each auditor activates CHECK.py before reading mathematical source; this records
its actual start and deadline. A readiness receipt cannot predate that future
clock event. Stop preparation here until audits are requested.

## Verified delivery

Each workspace contains its one neutral projection, original five-module Lean
capsule, complete independently copied dependency/build tree, frozen recipe,
matched arm prompt, runner and LAUNCH.json. All 141,467 prepared project files
per workspace were checked against the common inventory, including file hashes
and symlink identities. Regular file inodes differ from the prepared tree.
Projection, recipe, prompt and runner hashes were separately verified. The
common inventory is retained locally as PREPARED-FILES.json; its digest is bound
in each manifest. No original proof or frozen case was changed.

RUNTIME.json records this checkout's source hashes, Python package versions,
dirty state and pinned Lean/Lake binaries. Those runtime identities were
reverified before finalization. The helper uses this checkout's src and .venv;
no pip-installed Ladon is used. Source and dependency use must remain within the
registered paths. Isolation and network prohibition are procedural instructions,
not OS-enforced claims.

## Qualified execution

CHECK.py uses Ladon's existing process supervisor. The audit window is twenty
minutes; each checking command gets at most 600 seconds and the stricter
remaining deadline, with 12 GiB RSS and 16 MiB captured-output caps. The runner
records numbered requests/results, rejects concurrent or extra submissions and
fails closed after an incomplete receipt. Interrupted commands require a
custodian incident record; they are not silently retried. Top-level batch
accounting still requires transcript reconciliation under policy v2; child Lean
counts remain descriptive and may be unavailable.

RUNNER-PROBES.json binds the exact qualified script and nine passing synthetic
checks: preactivation refusal, activation, reactivation refusal, parallel refusal,
failed-command recording, command-21 refusal, expired-deadline refusal,
deadline-clamped child termination, and incomplete-receipt refusal.
RUNNER-ACCEPTANCE.md records independent review. These probes used ordinary
/bin commands, not mathematical cases or Lean counterexamples.

## Preparation costs and history

The fresh common project build passed in 12.69 seconds with sampled peak RSS
about 6.10 GiB. WORKSPACE-COPY.json records the resumed ten-workspace copy batch
at about 614 seconds; full subsequent byte verification was additional work.
Complete preparation/review time, tokens and copy memory are unavailable.
SETUP.json identifies pinned dependency/cache reuse and its unmeasured costs.
Original build outputs, runtime and setup receipts are retained.

The earlier checksum failure was caused by invoking a relative-path checksum
list from the wrong directory. The original hashes passed when checked in the
packet directory. User-authorized policy v2 removed the proposed lifetime Lean
child-process quota. Earlier preflight reports and policies remain under the
history directories. Those historical blockers do not describe current readiness.

No audit score, new mathematical finding, or detection advantage is claimed.
The next action is actual launch using the registered order and fresh contexts,
followed by frozen first reports and independent blind adjudication.
