## Context

A capsule becomes credible only when Lean accepts it without access to the source
checkout. Replay consumes the immutable materialized manifest and source tree. It
must distinguish content validation, package resolution, Lean compilation, theorem
identity, dependency/trust comparison, and environmental isolation so a failure is
actionable.

V1 verifies a locked/rebuildable capsule. External packages may be obtained through
normal Lake mechanisms if the caller permits network/cache access, but any such
frontier is disclosed. Replay is the explicit phase that runs target toolchain code
under Ladon's existing time, memory, process, and output supervision.

## Goals / Non-Goals

**Goals:**

- Replay from a fresh directory with the original checkout unavailable.
- Validate all capsule bytes and locked inputs before invoking Lean.
- Ask the pinned Lean environment to confirm the exact theorem and compare
  toolchain-scoped structural and trust evidence.
- Detect missing, changed, or undeclared repository inputs.
- Emit a machine-readable receipt that supports diagnosis and independent audit.

**Non-Goals:**

- No proof checking independent of Lean.
- No claim that successful replay proves axiom freedom unless the recorded trust
  frontier supports it.
- No default execution of a capsule while it can still resolve the original tree.
- No offline/system-hermetic guarantee.
- No automatic repair, dependency fetch policy, or source mutation after failure.

## Decisions

### 1. Make replay explicit and compose it with extraction

`ladon theorem replay <capsule>` verifies an existing capsule.
`ladon theorem extract <name> --output <path> --verify` composes plan,
materialization, and the same replay service. Human text reports progress on the
diagnostic channel and the selected final representation uses the existing CLI
contract.

Alternative considered: call every materialized capsule verified. That confuses a
copy operation with independent Lean evidence.

### 2. Validate content before executing target-controlled tools

Replay first validates manifest schema, path safety, file inventory and hashes,
toolchain/lock identity, and absence of undeclared files that affect resolution. A
content failure starts no Lean/Lake process. The validated capsule is then copied or
mounted into a fresh replay root whose paths do not reference the original checkout.

### 3. Define observable clean-room invariants

The original repository path is absent from the replay command, working directory,
Lean path, Lake environment, generated configuration, and allowed filesystem roots.
Fixtures make the original checkout unreadable or rename it during replay and
include a negative proof that succeeds only when an undeclared original file leaks
in. Platform-specific sandboxing can strengthen these invariants but is not the
sole evidence.

Alternative considered: merely use a different current working directory. Lean or
Lake environment variables could still reach the original tree.

### 4. Let Lean confirm identity with versioned structural fingerprints

The pinned toolchain compiles the capsule target and a helper queries the exact
fully qualified declaration. Replay compares declaration kind, normalized
toolchain-scoped type fingerprint, value fingerprint when the toolchain exposes
one, direct/closure dependency records, and trust facts against the plan. Pretty
text may aid diagnostics but is not the identity authority. Unsupported fingerprint
facets are explicit and cannot be silently treated as equal.

Alternative considered: compare theorem name and successful exit only. A relocated
package could resolve a different declaration under the same spelling.

### 5. Supervise every process and record a bounded receipt

The existing process supervisor applies time, memory, process-tree, and output
limits. `checks/replay.json` records capsule/plan/toolchain identities, isolation
facts, ordered stages, sanitized commands, exit classifications, bounded output
digests/excerpts, dependency acquisition facts, theorem comparisons, trust
frontier, timestamps/durations where nondeterministic fields are excluded from the
receipt identity, and final status. Secrets and host-specific absolute paths are
redacted or represented by roles.

### 6. Separate replay status from proof claims

Statuses include content-invalid, environment-unavailable, dependency-unavailable,
unsupported-facet, resource-limit, Lean-rejected, identity-mismatch, isolation-
violation, and verified. `verified` means the specified capsule replay checks
succeeded under the recorded Lean toolchain; it does not mean Ladon independently
proved the theorem or that the capsule is globally minimal/hermetic.

## Risks / Trade-offs

- [External resolution can make replay nondeterministic] → Pin lock/toolchain
  identity, record acquisition/cache facts, and distinguish unavailable from Lean
  rejection.
- [OS-level isolation is not uniform] → Enforce portable environment/path invariants
  and expose the achieved isolation level in the receipt.
- [Structural fingerprints can change with Lean] → Version algorithms by exact
  toolchain and compare only compatible identities.
- [Target builds can exhaust resources or fork descendants] → Use the shared
  supervisor and make limit outcomes terminal and explicit.
- [Receipts can leak host paths or tokens] → Sanitize commands/environment and test
  redaction with adversarial fixtures.

## Migration Plan

1. Land content validation, replay models, and failure taxonomy.
2. Land fresh-root isolation and supervised package/Lean execution.
3. Land exact theorem/fingerprint comparison and receipts.
4. Integrate `--verify` with extraction after standalone replay gates pass.
5. Rollback disables replay commands without changing capsule source bytes or
   existing analyzer behavior.

## Open Questions

- What portable isolation level should be required for the initial `verified`
  status versus reported as an optional stronger level?
- Should network access default to denied with an explicit opt-in for locked
  dependency acquisition?
