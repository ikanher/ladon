# Runner acceptance — synthetic launch r01 / policy v2

## Assessment

The final `CHECK.py` is acceptable for the registered experiment-only role.
It requires the manifest's exact Python executable, loads the shared
`ladon.process_supervisor` from the manifest's source root, requires an
activated session before accepting checking commands, serializes submissions,
charges each request before execution, and refuses command 21. It recomputes
remaining unit time before each supervised call and supplies the stricter of
that deadline and 600 seconds, with 12 GiB RSS and 16 MiB captured-output
limits. Its result receipt retains the supervisor's process and resource
outcomes.

`RUNNER-PROBES.json` records passing synthetic `/bin` probes for activation,
reactivation, parallel submission refusal, failed-command recording, the
twenty-command limit, expired deadlines, timeout of a child at the remaining
deadline, and refusal after an incomplete receipt. These probes used no case
prose, Lean attempts, or auditors. The runner uses only the existing shared
supervisor interface; the control receives no native Ladon interfaces.

The planned `finalize_launch.py` delivery procedure checks the registration
checksums, runtime source and tool hashes, prepared project inventory, copied
project bytes and independent file inodes, per-unit allowlisted inputs and
recipe, and empty output directories. It writes per-unit manifests binding
the Python and source paths, runner and delivered input hashes, registration,
runtime, setup and project inventory identities, resource limits, and
activation instructions. Its operational prompt directs each fresh auditor to
activate through the registered Python runner before reading context or
mathematical project sources. Isolation and communication/network restrictions
are accurately described as procedural rather than OS-enforced.

## Limits retained by policy

- The twenty-command budget is enforced over runner submissions. A shell,
  script, or batch may perform multiple top-level checking calls under one
  submission, so the numbered auditor log must be reconciled to available
  transcripts. Verified overruns and unknown accounting remain unqualified as
  the registration specifies.
- Network denial, filesystem access boundaries, and no cross-auditor
  communication are procedural controls. The delivery manifest discloses
  this; the runner does not claim OS isolation.
- Underlying Lean starts are descriptive telemetry. Incomplete child counts
  remain unavailable (and sampled observations must be labeled sampled).
- An incomplete request/result pair stops further runner use. The custodian
  records the incident and preserves available partial outputs; readiness
  remains invalid until that incident is reviewed, with no silent retry.
- The timeout is recalculated immediately before the supervisor call. The
  supervisor timeout begins at child launch, leaving only the small runner to
  child-start interval at the absolute deadline boundary.

These are the registered procedural and telemetry limits, not additional
runner acceptance gates. No case content was opened and no audit was run for
this acceptance review.

## Evidence-state note

At review time, `RUNNER-PROBES.json` is present, but the packet's
`CURRENT.json` still reports the earlier `prelaunch-incomplete` staging state;
the `READINESS.json` output described by `finalize_launch.py` is not yet
present. Therefore this document accepts the runner and the finalizer's
delivery design; it does not certify that final workspace finalization has
already completed. The extant launch status should be taken from the
finalizer-generated readiness receipt once the documented staging procedure
has run.
