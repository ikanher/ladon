## Context

Ladon already has most of the evidence needed to explain where a Lean theorem
lives: a lexical declaration index with exact command ranges, a canonical module
import DAG, elaborated type/value constant rows, source and configuration
fingerprints, process supervision, and installed CLI contracts. Those components
were designed for bounded analysis reports, however. A portable extraction cannot
treat a capped dependency list, a lexical name match, or a copied source tree as a
completeness witness.

The requested artifact is called a **theorem capsule**. Its dependency structure is
a DAG, not a single path back to the start of a proof. It has two related but
different closures:

- the semantic declaration closure, including type dependencies, proof-value
  dependencies, compiler-generated auxiliaries, instances, and trust facts; and
- the build closure, including source modules, source roots, Lake metadata,
  toolchain identity, locked external packages, and declared resources.

The umbrella coordinates three changes. Existing capability owners remain
authoritative at their seams:

- `ladon-declaration-source-evidence` owns lexical source and command boundaries;
- `ladon-elaborated-declaration-surface` owns Lean-confirmed declaration evidence;
- `ladon-analysis-root-and-scope-contract` and the canonical module DAG own module
  identity and import closure;
- `ladon-report-coverage-and-snapshot-integrity` owns input fingerprints and drift;
- `ladon-lean-extraction-runtime-hardening` owns helper supervision;
- `ladon-cli-execution-contract` owns installed streams, exits, and representations;
  and
- `ladon-portable-benchmark-fixtures-and-signal-oracles` owns portable acceptance
  fixtures.

## Goals / Non-Goals

**Goals:**

- Extract a fully qualified theorem through ordinary, caller-neutral CLI commands.
- Produce a closure-complete, locked/rebuildable capsule with auditable inclusion
  reasons.
- Preserve the theorem's actual preceding source context without attempting an
  unsound declaration rewrite.
- Verify the capsule with the pinned Lean toolchain while the original checkout is
  unavailable.
- Fail explicitly when exact closure, safe materialization, or replay evidence is
  unavailable.
- Keep planning, materialization, and replay separately testable and resumable while
  offering a convenient extract-and-verify flow.

**Non-Goals:**

- No LLM-facing command, model-specific defaults, or hidden prompt protocol.
- No globally minimum or declaration-minimum package claim.
- No automatic proof repair, import minimization, source normalization, or theorem
  rewriting.
- No offline vendoring guarantee or system-hermetic/native toolchain bundle in v1.
- No theorem-truth claim by Ladon; Lean remains the proof checker.
- No target-specific Matrix-Factorization names, paths, or project policy.

## Decisions

### 1. Deliver one workflow as three ordered child packets

The implementation order is:

```text
exact planning -> deterministic materialization -> isolated replay
```

Planning defines the evidence and compatibility contract. Materialization consumes
that immutable plan and creates bytes. Replay consumes only the resulting capsule
and demonstrates that it is independent of the source checkout. The public CLI
offers phase commands plus an `extract --verify` convenience flow; these are
ordinary human-usable commands, not a separate automation surface.

Alternative considered: implement extraction as one opaque command. That makes
drift diagnosis, safe retries, and phase-specific acceptance substantially harder.

### 2. Make the first guarantee closure-complete and locked/rebuildable

V1 packages all repository-owned modules in the required import closure and pins
external Lake dependencies with the original toolchain and lock metadata. It does
not claim the smallest possible source set, offline availability, or freedom from
OS/native dependencies. The manifest states this guarantee level and every
nonclaim.

Alternative considered: require fully vendored or declaration-minimal output.
Either would delay the useful core behind separate dependency-acquisition and
source-transformation research problems.

### 3. Treat semantic and build closures as different evidence graphs

The semantic graph preserves type and value edge kinds and reaches repository and
external declarations. The build graph preserves module imports, source roots,
package ownership, toolchain/config inputs, and resources. Capsule completeness
requires both graphs and a coverage status for every frontier. Neither graph is
silently substituted for the other.

Alternative considered: infer required files from declaration constants alone.
That misses elaboration context, initializers, syntax, scoped instances, generated
auxiliaries, and build metadata.

### 4. Preserve the owner-module prefix through the theorem command

The capsule copies the target module from byte zero through the exact parser command
end of the Lean-confirmed theorem. That retains namespaces, sections, variables,
notations, attributes, options, opens, local instances, macros, and other context.
Imported modules are copied whole in v1.

Alternative considered: synthesize a new file containing only recursively selected
declarations. Without re-elaboration and minimization, that can change name
resolution, implicit context, attributes, and elaborator behavior.

### 5. Require independent Lean replay for the word self-contained

Materialization alone produces an unverified capsule. A verified capsule has a
successful receipt from a fresh replay directory where the original checkout is
made unavailable. Replay checks the exact theorem name and toolchain-scoped
structural fingerprints, not pretty-printed text alone. Ladon reports Lean's result
and does not promote it into a separate proof authority.

Alternative considered: accept matching file hashes and a successful copy as
verification. Those checks cannot establish that the package resolves and builds.

### 6. Reuse existing authorities and add only capsule-specific orchestration

The planner reuses the canonical Lake layout and lexical scanner through a
capsule-specific streaming locator, without constructing the report-facing
declaration index. The pinned Lean environment confirms the fully qualified name,
declaration kind, and exact dependency evidence. It uses a dedicated complete
protocol rather than the report-oriented `MAX_DEPENDENCIES` rows. Snapshot and
process mechanisms remain shared.

Alternative considered: relax report caps globally. Report bounds are useful and
changing them would not create an explicit completeness protocol.

### 7. Fail closed at dynamic or unsafe boundaries

Unknown custom Lake behavior, undeclared filesystem reads, native plugins, unsafe
links, path escapes, collisions, missing locked dependencies, or truncated helper
results prevent the corresponding completeness or replay claim. Planning remains
read-only and does not execute target-controlled build initializers merely to
discover inputs. Explicit replay is the phase authorized to invoke the target
toolchain under supervision.

## Risks / Trade-offs

- [Module-prefix capsules can be larger than necessary] → Label them
  closure-complete rather than minimal and retain a future minimization lane.
- [Lean APIs expose dependencies differently across toolchains] → Version the helper
  protocol and structural fingerprint by Lean/toolchain identity and fail on
  incompatible evidence.
- [Custom Lake/native behavior can escape a pure source manifest] → Classify these
  facets explicitly and refuse unsupported guarantee levels.
- [External packages can disappear from the network] → Preserve lock data and state
  that v1 is rebuildable, not offline-vendored.
- [Clean-room isolation differs across platforms] → Define observable isolation
  invariants and portable fixtures; stronger OS sandboxing can be an additive lane.
- [Four packets can drift semantically] → Keep child specs byte-equivalent in the
  umbrella and gate the dependency ledger and strict validation.

## Migration Plan

1. Land plan schemas and exact helper evidence behind explicit theorem commands.
2. Land deterministic materialization after planning fixtures are stable.
3. Land isolated replay and then expose the combined extract-and-verify flow.
4. Keep existing analyzer invocations backward compatible throughout.
5. Roll back by disabling theorem commands; no existing report schema or target
   repository content is mutated.

## Open Questions

- Which supported Lean versions can expose a stable proof-value fingerprint without
  normalization artifacts?
- Which isolation mechanism provides the strongest portable proof that the original
  checkout was unavailable?
- Should an offline-vendored capsule be the next guarantee level, or should
  deterministic declaration minimization come first?
