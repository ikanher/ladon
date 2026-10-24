# Probe-result reuse contract

Frontier: application-probe exact-result reuse (task 2.1)

## Objective

Permit a later `check_application_probe` call to reuse an earlier locally checked
goal result only when fresh planning under the same absolute monotonic deadline
reconstructs the exact same plan and the cached raw checker receipt matches the
exact goal and proof term.

## Acceptance contract

- Preserve the existing supervised worker timeout, output and RSS bounds and the
  caller's absolute shared deadline. Reuse must not start checker work after the
  deadline; preparation and freshness checks remain subject to that same deadline.
- Recompute source/context/template bindings before consulting prior goal results.
  Reuse is allowed only when the recomputed plan ID and ordered generated goals
  exactly match the cache. The identity must cover assumptions, source and
  environment identities, checker/toolchain identity, template family/version,
  direction, kind, and limits/deadline semantics.
- A reusable goal must have the same goal ID, goal text/digest and exact proof
  term as the current request; its content-addressed raw evidence must reload
  without modification and satisfy the existing accepted-check predicate, with
  the raw completion's term digest matching the exact term. The raw receipt must
  also carry the Ladon-added binding to this plan, generated goal ID/digest/text
  and term digest, so a valid reference cannot be transplanted between goals.
  Caller status fields alone confer no authority. The repository-local `.ladon`
  store is trusted input: content addressing and binding do not authenticate
  against a malicious writer with access to the same repository. Reuse must not
  consume cache data from an untrusted workspace or writer.
- Changed assumptions, selected source, source environment, checker/toolchain,
  template revision, deadline, or resource limits make the cache miss/reject; no
  cached `checked-support` status may survive that mismatch.
- Incomplete, unsupported, failed, expired, malformed, oversized, or unaccepted
  results remain non-authoritative. Each requested term not covered by a valid
  cache entry follows the existing bounded checker path.
- Cache input and published output remain under the existing 8 MiB aggregate
  cap. The command/API must expose whether an exact goal result was reused.

## Change surface and constraints

Public API: `check_application_probe`; CLI: `check-probe`. Core source: probe
runner, input validator, CLI adapter and focused tests. No schema migration,
new dependency, network use, generated source mutation, or changes to unrelated
worktree files. Root owns production edits and acceptance tests. An independent
integrated audit is required after the final edit.

## Frozen acceptance cases

1. A valid exact cache avoids only the already checked goal worker, retains its
   accepted evidence reference, reports reuse, and still performs fresh bounded
   preparation under the shared deadline.
2. A changed assumption/context, source/environment identity, template version,
   goal, proof term, deadline, or limits cannot reuse a cached result.
3. A forged status, altered/corrupt evidence reference, mismatched term digest,
   cross-goal receipt transplant, incomplete prior result, or expired deadline
   never grants checker authority within the trusted-local-store threat model.
4. A cache miss may proceed through the ordinary checker only for a caller
   supplied term and only within the remaining shared deadline and resource caps.

## Baseline

The current implementation regenerates source-bound preparation and checks every
submitted proof term. It has no cache input or reuse indicator. Relevant source
and test contents are frozen by the board's contract/test records for this
frontier; repository revision is intentionally not used as the sole baseline
because this worktree contains unrelated uncommitted changes.
