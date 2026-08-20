## Context

The inventory backend invokes `lake env lean --run` once for every source file,
sequentially and without a deadline. A cold root run can take tens of seconds,
inventory runs can consume much more, and interrupted work has left large Lean
processes alive. The current cache omits toolchain, Lake, and transitive import
state. Module discovery also assumes repository-relative conventional paths.

## Goals / Non-Goals

**Goals:**

- Amortize Lean environment startup across modules.
- Bound time and process lifetime, including cancellation and failure cleanup.
- Preserve successful module rows when another module fails.
- Make cache validity and target-code execution provenance inspectable.
- Discover declared Lake library roots before falling back to conventional
  layout.

**Non-Goals:**

- Build the target implicitly.
- Extract theorem semantics beyond the transport fields required by the
  declaration child.
- Promise safe analysis of untrusted Lean projects.
- Run many unconstrained helper processes to reduce wall time.

## Decisions

1. **Use a versioned batch protocol.** Python supplies an ordered batch of module
   requests to a helper invocation; the helper emits framed, per-module JSON
   records and a terminal batch summary. Configured batch size bounds recovery
   cost. One-process-per-file was rejected because environment startup
   dominates; one process for an arbitrarily large repository was rejected
   because it makes recovery and memory unbounded.

2. **Reuse the shared target-process supervisor.** The CLI execution child owns
   the generic process-group/deadline/cancellation/output-draining mechanism for
   explicit Lake builds. Lean extraction configures the same supervisor per
   helper batch and adds helper-protocol recovery. Killing only the immediate
   process or maintaining a second supervisor was rejected because descendants
   can survive and lifecycle semantics would diverge.

3. **Treat partial results as first-class.** A malformed or failed module record
   becomes a module diagnostic; previously validated records remain available
   in deterministic order. Strict mode may reject the batch but cannot erase
   diagnostics.

4. **Version and strengthen cache fingerprints.** A key includes helper/protocol
   version, Lean version, `lean-toolchain`, Lake manifest/configuration,
   extraction options, target source, transitive local source closure, and
   identifiable compiled/external environment state. When relevant state
   cannot be fingerprinted, the cache is bypassed or explicitly marked unsafe;
   it is never silently presented as sound.

5. **Ask Lake for library layout before path fallback.** Discovery normalizes
   multiple libraries, `srcDir`, and declared generated roots into a module
   source map. Simple repositories without usable Lake metadata retain the
   existing conventional scan with a visible fallback status.

6. **Expose provenance through report v2.** Each batch records command shape
   with secrets/redacted values excluded, toolchain/helper versions, cache
   outcome, requested/completed/failed counts, elapsed time, timeout state, and
   the warning that target initializers may execute.

## Risks / Trade-offs

- **Batch helper increases Lean implementation complexity** → Keep the protocol
  small, versioned, and fixture-tested with one record type per module.
- **Strong fingerprints cost I/O** → Hash only the resolved import closure,
  reuse content hashes within a run, and measure the trade-off.
- **Lake layouts are not uniformly machine-readable** → Preserve explicit
  fallback/unsupported diagnostics rather than guessing silently.
- **Termination semantics differ by platform** → Implement a portable base and
  mandatory Linux process-group tests for the supported CI environment.

## Migration Plan

Add the protocol beside the single-root runner, migrate inventory scope, create
a new cache namespace, then migrate root scope. Retain text extraction as the
safe fallback. Rollback selects the prior root runner only; the unbounded
per-file inventory path is not restored as a default.

## Open Questions

None. Implementation SHALL choose conservative, finite, versioned batch-size
and deadline defaults with focused tests. The downstream benchmark packet may
propose tuned values later without blocking this child.
