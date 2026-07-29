# Theorem capsules

Ladon can package one fully qualified Lean theorem as a
locked/rebuildable module-prefix capsule and ask the pinned Lean toolchain to
replay it away from the original checkout. This is an ordinary CLI workflow;
people, scripts, editors, and model-driven callers use the same commands and
artifact contracts.

## Operational boundary

Planning invokes the target repository's Lake/Lean environment. The repository
must have a pinned `lean-toolchain`, supported Lake configuration, and compiled
project state. Loading Lean modules can execute imported initializers, so theorem
planning and replay are not safe operations for an untrusted repository.

Planning is read-only with respect to the target checkout. Materialization is
required to write outside that checkout. Replay validates the capsule before
executing target tools, copies it into a fresh temporary repository, removes
checkout-specific Lean/Lake environment paths, applies finite process deadlines
and output limits, and never writes build products back into the capsule.

## Workflow

Create a canonical plan:

```bash
ladon theorem plan Fully.Qualified.theorem \
  --repo-root /path/to/project \
  --format json --output /tmp/theorem-plan.json
```

Materialize the reviewed plan:

```bash
ladon theorem materialize \
  --plan /tmp/theorem-plan.json \
  --output /tmp/theorem-capsule
```

Replay the capsule:

```bash
ladon theorem replay /tmp/theorem-capsule \
  --format json --output /tmp/replay-receipt.json
```

The combined flow uses the same three services:

```bash
ladon theorem extract Fully.Qualified.theorem \
  --repo-root /path/to/project \
  --output /tmp/theorem-capsule \
  --verify
```

Use `--network allow` during replay only when locked external Lake packages must
be acquired. The default is `--network deny`. A `.tar`, `.tar.gz`, or `.tgz`
output path requests a reproducible archive instead of a directory.

## What is planned

A planner-specific streaming locator reuses Ladon's Lake layout and lexical
declaration scanner to nominate an exact source candidate and command boundary.
It does not construct or retain the report-facing declaration index, and it is
not the final declaration authority. A target-specific Lean helper confirms the
fully qualified theorem, kind, owner module, structural type/value fingerprints,
and dependency records under the pinned toolchain.

The plan keeps two graphs:

- The semantic graph recursively covers repository-owned type and proof-value
  dependencies and records direct external declaration frontiers, generated
  auxiliaries, axioms, `sorryAx`, and unsafe declarations separately.
- The build graph covers the repository import closure, source roots, pinned
  toolchain, supported Lake configuration, lock metadata, and external import
  frontiers.

The helper protocol is independent of the dependency limit used by human-facing
declaration reports. It emits an explicit completion record with a node count and
checksum. Helper output is file-backed and capped; exceeding that finite limit
fails planning instead of publishing a partial complete plan.
`--max-rss-mib` optionally adds a supported process-tree resident-memory ceiling
to planning and replay.

## Capsule layout and verification

The target module is copied from byte zero through the end of the theorem command.
This preserves preceding namespaces, sections, options, variables, notations,
attributes, macros, and local instances. Later commands are excluded. Every other
repository module in the build closure is copied whole and retains its
source-root-relative path.

`capsule.json` accounts for every copied/generated payload file with its role,
inclusion reason, origin, byte count, normalized mode, and SHA-256 hash.
`plan.json` preserves the planning evidence. Materialization rechecks the
module-layout fingerprint and every selected source/configuration hash, rejects
unsafe paths and links, builds in a staging directory, and publishes
transactionally.

Replay first verifies the manifest and exact file inventory. It then runs
`lake build <target-module>` in a fresh copy and queries the exact theorem again.
A `verified` receipt means that:

- the capsule content matched its manifest;
- the fresh replay did not use the original checkout in its command or sanitized
  environment;
- the pinned Lean build succeeded;
- the exact name, declaration kind, Lean version, structural type/value
  fingerprints, repository semantic closure, and recorded trust frontier matched.

Lean is the proof checker. Ladon records and compares Lean evidence.

## Explicit nonclaims

V1 capsules are closure-complete at the documented repository/external-frontier
boundary and are locked/rebuildable. They are not claimed to be:

- globally or declaration-level minimal;
- offline-vendored;
- system-hermetic across native and operating-system dependencies;
- axiom-free unless the recorded trust frontier supports that statement; or
- independently proved correct by Ladon.

Custom `lakefile.lean` behavior, native/custom Lake facets, source symlinks, path
escapes, collisions, undeclared files, stale inputs, incompatible protocols, and
unsupported structural comparisons fail closed.
