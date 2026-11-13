# Runner review — synthetic launch r01 / policy v2

Scope: `CHECK.py` and policy-v2 `synthetic-comparison-r01/REGISTRATION.md`,
with a read-only check of the existing `ladon.process_supervisor` interface.
No case projections, custody material, or answers were read. No cases or audits
were run.

## Findings

1. **Activation does not yet gate source loading/inspection.** `CHECK.py`
   imports `ladon.process_supervisor` and reads `LAUNCH.json` before processing
   `--activate`. The registration requires activation before source inspection
   and starts the unit clock at first source inspection. Invoke the runner with
   the pinned environment, but defer checkout imports and source-dependent
   manifest resolution until after activation; record a distinct inspection
   start/deadline immediately before the first permitted source read. If the
   runner itself is considered source inspection, its current session timestamp
   should be described as the start and the ordering requirement made explicit.

2. **The 20-command limit is a request-file count, not verified top-level
   accounting.** Counting `command-*.request.json` usefully charges failed
   submissions, but any submitted shell/script/batch can invoke multiple
   checking tools and consume only one slot. This is explicitly procedural in
   the registration, so preserve the auditor numbered log and reconcile it to
   transcripts before qualifying a unit. Reject shell interpreters and
   multi-call wrappers where practical; otherwise retain the registered
   overrun/unknown-accounting invalidation rule. A crash after the request file
   is created correctly consumes a command, but currently leaves no structured
   result receipt.

3. **Deadline timeout is based on a stale snapshot.** `remaining` is computed
   before lock acquisition, receipt creation, environment setup and supervisor
   startup. Recompute `max(0, deadline - time.time())` immediately before each
   supervisor call, refuse if zero, and pass `min(600, remaining_now)`. This
   makes the cap stricter through startup overhead as specified.

4. **Error receipts are incomplete.** Exceptions from manifest/session reads,
   environment setup, supervisor startup, or result-file writes can leave a
   request with no final receipt; the `finally` block removes the lock, so a
   subsequent invocation can continue with ambiguous state. Catch operational
   exceptions after request creation, write a bounded structured error result
   (phase, exception type/message, submitted argv and timestamp), retain partial
   stdout/stderr if available, and stop the unit on incomplete receipt rather
   than retrying. Keep stale-lock refusal as an incident requiring custodian
   reconciliation.

5. **Runner interpreter / runtime binding is implicit.** The script imports
   the checkout supervisor before it applies manifest `PYTHONPATH`, while the
   registration requires the checkout `.venv` Python and pinned runtime. Make
   the launch command use the recorded `.venv/bin/python` and verify the
   resolved interpreter, checkout source root and runtime identity against the
   frozen manifest before allowing checking commands. The in-process
   `PYTHONPATH` adjustment then remains useful for target children.

## Confirmed alignment

- The existing supervisor accepts `timeout_seconds`, `max_rss_bytes`,
  `max_output_bytes`, `env`, and `observe_resources`; the runner supplies
  `min(600, remaining)`, 12 GiB, 16 MiB, and resource observation. This is the
  registered interface and does not require native Ladon interfaces in the
  control.
- The exclusive `ACTIVE` file serializes concurrent submitted commands, and
  request creation precedes process launch so failed submissions are charged.
- `ProcessResult` exposes timeout, output-limit, memory-limit, return code,
  elapsed time, peak RSS, and resource observations for the result receipt.
- Registration correctly treats the command limit as procedural, requires
  transcript reconciliation, accounts retries, and preserves invalid or
  unknown accounting as unqualified rather than silently accepted.

## Recommended disposition

Fix findings 1, 3, 4 and 5 before mathematical launches. Finding 2 is a
registration-consistent procedural boundary, but command-log reconciliation
must be part of qualification; add launcher-side rejection of obvious shell
chains/wrappers if feasible. No native navigation/extraction/checking
interface should be added to the control runner.
