## Context

The current report is assembled from `dict[str, Any]`, conditionally omits many
sections, records a skipped reason as its character count, and labels all
additive growth `clean-core-1`. The renderer also injects a current timestamp by
default, making otherwise identical runs differ.

## Goals / Non-Goals

**Goals:**

- Publish a machine-valid schema and a typed internal report boundary.
- Distinguish empty, skipped, partial, and failed phases with preserved reasons.
- Make default serialization deterministic.
- Keep text and JSON semantically aligned.
- Provide a bounded transition from v1.

**Non-Goals:**

- Redesign every internal analysis data structure at once.
- Define CLI exit mapping or extraction algorithms.
- Remove optional evidence families.
- Add caller-specific report variants.

## Decisions

1. **Make v2 the canonical in-memory model.** Frozen dataclasses or equivalent
   typed DTOs own metadata, phases, findings, evidence, and extensions. Existing
   pure analyses may still return internal dictionaries initially, but adapters
   validate them at the phase boundary. Typing the serializer alone was
   rejected because malformed state would still travel through the pipeline.

2. **Use a discriminated phase envelope.** Every registered phase has one of
   `complete`, `skipped`, `partial`, or `failed`, plus elapsed time, counters,
   textual reason/diagnostics, provenance, and typed data when available. Empty
   successful data is `complete`, not absent.

3. **Check in and package JSON Schema.** The schema identifier and report
   version are `ladon-report-v2`; every emitted JSON report validates in tests.
   Additive fields require optional schema properties, while removed/renamed or
   semantic changes require a new major report version.

   Artifact inclusion is proved through the clean baseline's constrained
   candidate gate using the logical resource
   `ladon:schemas/ladon-report-v2.schema.json`; this packet does not run a raw
   build command.

4. **Make volatility explicit.** Collections use documented stable sort keys.
   A generated timestamp is absent/null unless supplied by the caller; runtime
   timings remain present but may be excluded from byte-determinism comparisons
   through a documented normalization. Silently inserting wall-clock time was
   rejected.

5. **Render both formats from the same model.** Text sections consume typed
   phase/finding objects, not a separately assembled summary. Compact text may
   omit detailed rows, but it reports full selected totals and omitted counts;
   every rendered row preserves its JSON identifier, severity, authority, and
   phase state.

6. **Provide a one-release JSON-only v1 adapter.** Canonical analysis builds v2
   first; when JSON is the sole selected representation, a requested
   compatibility serializer emits `clean-core-1` where representable and warns
   about information loss. Text always renders the canonical v2 model, and v1
   with text or legacy dual output is rejected. Mutating the old schema in place
   was rejected.

7. **Own only the generic extension mechanism.** This packet defines the
   registered namespace envelope, version dispatch, and authority/provenance
   hooks. Witness, atlas, and elaborated-declaration owners define their
   concrete namespace names and payload schemas. Owning those payloads here was
   rejected because it would duplicate child ownership.

## Risks / Trade-offs

- **Large migration touches many consumers** → Add adapters phase by phase and
  keep contract tests around atlas, SQLite, diff, and workflow readers.
- **Schema becomes too rigid for alpha iteration** → Permit additive,
  namespaced optional fields while requiring explicit versions.
- **Deterministic reports lose useful timestamps** → Allow opt-in timestamps and
  keep timing telemetry clearly volatile.
- **v1 adapter masks migration bugs** → Test it against fixed fixtures and set a
  removal milestone.

## Migration Plan

Introduce models/schema and validate existing payloads, move phase status first,
migrate renderers/readers, switch default output to v2, then enable declaration
extensions. Rollback selects the v1 serializer while retaining typed phase
records internally.

## Open Questions

None. The compatibility adapter lasts one published v2 alpha as specified by
the shared CLI contract.
