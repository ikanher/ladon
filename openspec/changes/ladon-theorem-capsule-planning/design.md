## Context

Ladon's Lake layout and lexical declaration scanner can locate a candidate, and
the elaborated helper already emits direct type/value constants, source ranges,
and module dependencies. The normalized report surface deliberately retains a
large declaration-rich index and caps dependency lists. That is appropriate for
inspection but is unnecessarily expensive and cannot support a capsule
completeness claim.
Planning therefore needs a dedicated exact protocol and recursive closure algorithm
while reusing existing source, module, snapshot, and process authorities.

The planner is read-only. It may invoke Lean to inspect an existing repository, but
it does not create capsule sources, write inside the repository, or run arbitrary
project build initializers to infer hidden inputs.

## Goals / Non-Goals

**Goals:**

- Resolve one fully qualified theorem with the repository's pinned Lean environment.
- Record exact command boundaries and complete semantic and build dependency DAGs.
- Preserve type, value, generated, trust, module, package, and external-frontier
  distinctions.
- Emit a deterministic versioned plan with enough fingerprints to reject drift.
- Give every partial, ambiguous, unsupported, or unavailable result an actionable
  machine-readable reason.

**Non-Goals:**

- No materialized source tree or archive.
- No lexical-only theorem identity claim.
- No dependence on bounded declaration-report rows.
- No execution of target-controlled initializers merely to discover dependencies.
- No package minimization, proof repair, or external dependency vendoring.

## Decisions

### 1. Add theorem phase commands without changing analyzer semantics

The installed CLI will accept caller-neutral operations shaped as
`ladon theorem plan <fully-qualified-name>` and
`ladon theorem extract <fully-qualified-name> ...`; this packet implements the
planning portion and a stable Python service beneath it. Existing analyzer
invocations keep their current meaning. JSON is the canonical plan representation;
human text is a projection.

Alternative considered: expose only a Python API. That would violate the product's
CLI-first use model and make clean installed-distribution testing harder.

### 2. Use lexical lookup only to nominate an owner, then ask Lean

A planner-specific streaming locator reuses the canonical Lake layout and lexical
scanner to supply candidate module/source anchors without constructing the
report-facing declaration index. It byte-prefilters source files, parses only
plausible candidates, and retains only the selected import closure. A versioned
Lean helper loads the relevant module under the pinned project environment and
confirms exact fully qualified name, declaration kind, source ownership, type
identity, and value availability. Not-found, multiple-owner, non-theorem, and
source/Lean disagreement are terminal planning outcomes.

Alternative considered: accept the first lexical suffix match. Namespace aliases,
generated declarations, reexports, and duplicate short names make that unsafe.

### 3. Introduce a complete dependency stream

The helper protocol emits deterministic records for every direct constant in a
declaration's type and value, plus generated auxiliaries and trust facts, with an
explicit end record and counts/checksum. Python recursively requests or consumes
records until the reachable closure is closed, condenses cycles into SCCs, and
rejects missing end markers, count mismatches, incompatible schemas, or any
truncation indicator. Report caps remain unchanged.

Alternative considered: raise `MAX_DEPENDENCIES`. Any finite presentation cap can
still silently invalidate a package plan.

### 4. Keep two typed closure graphs

The semantic graph records declaration nodes with `type`, `value`,
`generated/auxiliary`, and trust-frontier relationships. The build graph records
module imports, source-root mappings, package ownership, toolchain and Lake files,
locked external packages, and declared resources. The plan links declaration nodes
to owning modules but does not collapse the graphs.

Alternative considered: copy modules reached by constants. Imports and elaboration
context are not recoverable from that relation alone.

### 5. Bind the plan to exact inputs

The plan contains a schema/protocol version, repository-relative normalized paths,
source byte hashes, source-inventory, module-layout, and module-DAG fingerprints,
toolchain contents, Lake configuration/manifest hashes, target structural
fingerprints, closure coverage, and guarantee/nonclaim fields. Canonical sorting
and JSON serialization make equivalent plans byte-stable. Absolute source paths
are diagnostic metadata, not materialization identities.

Alternative considered: bind only to a Git commit. Dirty trees and non-Git inputs
would remain ambiguous.

### 6. Classify unsupported facets before materialization

The planner statically records custom `lakefile.lean`, native libraries/plugins,
external resources, symlinks, and other dynamic inputs when observable. A facet is
either supported with evidence, external with a locked frontier, or unsupported
with a reason. Unknown is not equivalent to absent.

## Risks / Trade-offs

- [Recursive declaration closure is large] → Stream records, deduplicate by exact
  name and environment identity, condense SCCs, and retain deterministic counts.
- [Source ownership is missing for generated declarations] → Keep them in the
  semantic graph and link to their generating/owning module evidence when available.
- [Custom build logic hides inputs] → Fail closed for the locked/rebuildable claim
  instead of executing discovery code during planning.
- [Repository changes during helper runs] → Capture before/after fingerprints and
  publish no valid plan on drift.
- [Structural hashes vary by Lean version] → Scope algorithms and values to exact
  toolchain and helper protocol versions.

## Migration Plan

1. Add plan models/schema and pure validation.
2. Add the exact Lean helper protocol and closure collector.
3. Join source/module/config evidence and expose the plan CLI.
4. Gate against portable large-closure, ambiguity, drift, and unsupported-facet
   fixtures.
5. No existing report row changes are required; rollback removes the new command.

## Open Questions

- Can all supported Lean versions expose generated auxiliary ownership uniformly?
- Should the first protocol request dependencies declaration-by-declaration or emit a
  module-wide stream filtered in Python?
