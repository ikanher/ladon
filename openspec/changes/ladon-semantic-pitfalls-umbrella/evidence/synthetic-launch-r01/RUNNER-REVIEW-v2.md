# Runner review v2 — synthetic launch r01 / policy v2

Scope: revised `CHECK.py` and the policy-v2 `REGISTRATION.md`, with a read-only
check of the existing supervisor interface. The first review is preserved in
`RUNNER-REVIEW.md`. No case projections, custody material, or answers were read;
no cases or audits were run.

## Re-review findings

1. **Activation ordering is now acceptable under the launcher's stated
   interpretation.** The script still reads `LAUNCH.json` and imports the
   supervisor before `--activate`, but this is limited to launch/runtime
   metadata and the shared process supervisor, not mathematical case source.
   The root's launch procedure activates before the first mathematical source
   inspection, matching the registration's clock definition. Keep that
   ordering explicit in each unit's launch receipt.

2. **Deadline enforcement is corrected.** The runner recomputes remaining time
   after request creation and environment setup, refuses execution if the
   deadline has passed, and passes `min(600, remaining)` to the supervisor.
   The short interval between this calculation and process startup is
   unavoidable call overhead; the supervisor's timeout starts at process
   launch, so the effective cutoff can exceed the absolute deadline by that
   overhead. If strict wall-clock cutoff is required, account for the measured
   runner-to-child startup gap or place a deadline-aware wrapper around the
   child. This is a small residual boundary, not a launch blocker at a 20-minute
   unit scale.

3. **Incomplete receipts now fail closed, but do not provide a structured
   failure receipt.** Before accepting another command, the runner detects any
   request lacking a `.result.json` and stops. This prevents silent retries or
   continuation after an interrupted/failed write. The custodian must record
   that incident outside the runner output because exceptions after request
   creation still do not generate a structured error result; preserve any
   partial stdout/stderr and do not relaunch that unit as though the request
   had not occurred.

4. **Runtime binding is improved and needs a frozen manifest check.** The
   runner resolves `ladonSourceRoot`, prepends it to `sys.path` before importing
   the supervisor, and rejects a differing `sys.executable` when
   `pythonExecutable` is present. The launcher states all delivered manifests
   will include that field, so require it and bind it plus the source root to
   the frozen runtime manifest before launch. Without that external binding,
   the runner only checks self-consistency against whatever `LAUNCH.json`
   contains.

5. **Top-level command accounting remains procedural.** Request-file counting
   charges failed requests and enforces twenty runner submissions, but cannot
   distinguish one direct checking command from a shell/script/batch making
   multiple top-level tool calls. The registration explicitly sets this as a
   procedural budget. Reconcile numbered auditor logs to complete transcripts;
   preserve any overrun or unknown accounting as unqualified. The runner does
   not need native Ladon interfaces in the control.

## Confirmed alignment

- The existing supervisor API matches the runner's `timeout_seconds`,
  `max_rss_bytes`, `max_output_bytes`, `env` and `observe_resources` arguments.
  Values are capped at 600 seconds, 12 GiB RSS and 16 MiB captured output, with
  resource observations enabled.
- The exclusive active lock serializes runner submissions. Request files are
  written before execution, and incomplete requests prevent subsequent use.
- The result serializes `ProcessResult`, including timeout/output/memory limit
  states, return code, elapsed time, peak RSS and resource observations.

## Disposition

The revision resolves the original stale-timeout issue and the activation-order
concern under the documented launch interpretation. Before mathematical launch,
bind the required interpreter and source root to the frozen runtime manifest,
and establish the custodian's incident procedure for incomplete receipts.
Procedural command-log/transcript reconciliation remains required by policy.
