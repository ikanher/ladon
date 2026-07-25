## Context

`ladon` currently prints JSON and text to stdout in the same invocation, accepts
`--skip-build` without carrying it into the run context, and maps nearly every
runtime error to exit 1. Optional phases can disappear, and there is no distinct
exit for an explicitly configured finding gate. The command is used directly
by people and automation, so shell behavior is part of the product contract.

## Goals / Non-Goals

**Goals:**

- Define one caller-independent execution contract across supported public
  entrypoints, with unambiguous output, build, phase, and exit behavior.
- Keep findings advisory unless the caller explicitly enables a failure policy.
- Emit a structured partial report whenever analysis produced trustworthy
  results before an operational failure.
- Exercise the installed console script in subprocess tests.

**Non-Goals:**

- Create caller-specific commands, hidden modes, or alternate analysis.
- Consolidate or remove general-purpose entrypoints merely to force one
  executable name.
- Own report field definitions, Lean-helper extraction mechanics, or finding
  algorithms.
- Automatically repair Lean code.
- Move the supported ProofIR bridge auxiliary command under a different command
  hierarchy during this alpha milestone.

## Decisions

1. **Default to no target build and bound explicit builds.** `ladon` performs
   text analysis without running target code. `--build` explicitly runs the
   repository's ordinary `lake build`; this is permitted with text analysis as
   a build-check phase and precedes Lean-backed extraction when selected. A
   finite default plus `--build-timeout` controls a shared target-process
   supervisor that handles process groups, output draining, cancellation, and
   escalation. The no-op `--skip-build` flag is removed because its absence
   already means no build. Silently or unboundedly building was rejected.

2. **Use one selected renderer per stdout stream.** The canonical shape is
   `--format text|json`, `--output PATH|-`, and
   `--report-version v2|v1`, with text/v2 to stdout by default. Report version
   selects a JSON schema: v1 is valid only when JSON is the sole
   representation; text always renders the canonical v2 model, so v1 with text
   or legacy dual output is invocation error 2. For one alpha
   compatibility release, legacy `--json PATH` and `--text PATH` map to their
   renderers; both may be supplied only with two regular file paths. Legacy
   flags cannot be mixed with canonical output flags and never send two formats
   to stdout. Invalid combinations return 2. Diagnostics and deprecation
   warnings go to stderr. After that release, legacy flags return 2.

3. **Publish four exit classes.**

   - `0`: requested analysis completed; ordinary findings are advisory.
   - `1`: input, filesystem, toolchain, build, extraction, timeout, or output
     failure.
   - `2`: invalid invocation, configuration, or unsupported option.
   - `3`: analysis completed but an explicit `--fail-on` selector matched.

   Required requested phases are marked in report v2. A required `partial` or
   `failed` phase is operational exit 1; intentional optional skips remain 0
   unless an explicit phase selector rejects them. Operational failure takes
   precedence over policy rejection. POSIX signal termination preserves the
   conventional signal-derived status instead of being remapped to 1.

4. **Make `--fail-on` small and exact.** The repeatable, case-sensitive grammar
   is `kind:<finding-kind>`, `severity:<minimum>`, or
   `phase:<name>:<skipped|partial>`. Severity order is
   `info < warning < error`; repeated selectors use OR semantics. Unknown or
   malformed selectors return 2 before analysis. Matches are ordered first by
   selector input and then stable report key, appear in metadata, and are named
   on stderr. No selector means no policy-caused failure.

5. **Preflight and classify input failures.** Build/Lean modes check repository
   existence, Lake manifest, toolchain availability, requested root, and
   writable output. Missing compiled state without `--build` yields an
   actionable operational diagnostic. Invalid option/selector syntax or
   schema-invalid Ladon configuration/policy is exit 2; missing/unreadable paths
   and OS/toolchain failures are exit 1. Malformed optional evidence that its
   phase can normalize remains an advisory diagnostic unless an explicit policy
   rejects it.

6. **Retain partial evidence on failed required phases.** Completed text phases
   and normalized build/extraction diagnostics are serialized before returning
   exit 1. A failure before any valid report can be constructed emits only a
   concise stderr diagnostic.

7. **Keep the ProofIR bridge as a supported general auxiliary entrypoint.**
   `ladon-proofir-bridge` follows the shared help, stream, invocation,
   operational-error, and signal rules where applicable. Analyzer-only
   `--build`, `--fail-on`, and report-version options are not invented for it.
   Consolidation can be proposed separately based on product value, never
   caller type.

8. **Reconcile historical flag requirements first.** Before code removal, the
   state-reconciliation packet archives the source additions first and then
   archives its explicit `ladon-python-quality` and `ladon-root-matrix`
   MODIFIED deltas. CLI integration waits for the archive-aware
   `canonicalized-legacy-cli-deltas` milestone, which validates the resulting
   canonical specs. Declaring a contradictory flag contract while canonical
   requirements still prescribed `--skip-build` was rejected.

## Risks / Trade-offs

- **Breaking flag/output behavior surprises scripts** → Provide a migration
  table, compatibility tests, and at most one bounded legacy adapter release.
- **Partial reports are mistaken for success** → Report v2 records failed
  phases, and exit 1 remains mandatory.
- **Build executes untrusted code** → Require explicit `--build` and print the
  security boundary in help/docs.
- **Failure-policy syntax grows complex** → Keep the three exact selector forms
  and defer expression languages.

## Migration Plan

Reconcile historical requirements, introduce the new renderer/report-version
selector and exit mapping behind report v2, migrate internal root-matrix
commands and docs, add installed-wheel subprocess tests, then remove
`--skip-build`. Keep legacy file-renderer flags for exactly one alpha
compatibility release. Rollback keeps default no-build behavior and may restore
aliases without restoring mixed stdout.

## Open Questions

None. Numeric timeout defaults are conservative implementation constants that
the benchmark packet may tune in a later change.
