# Ladon Report Contract v2 (compatibility)

`ladon-report-v2` is the explicit compatibility JSON format backed by Ladon's
typed analysis model. Canonical JSON output now uses
[`ladon-report-v3`](REPORT_CONTRACT_V3.md), which owns large payloads once and
supports bounded projections. Compact text renders directly from the typed
model. The public command remains the ordinary `ladon` command; the report
contract does not define a caller-specific mode.

## v1 inventory

The former `clean-core-1` report was assembled as a dictionary with these
top-level sections:

| Section | v1 presence | v2 state |
| --- | --- | --- |
| `metadata` | always | typed metadata, always present |
| `warnings` | always | always present; Ladon-authored warning text |
| `module_dag` | always | `phases.module_dag`, complete or failed |
| `declaration_graph` | Lean extraction only | explicit complete or skipped phase |
| `module_readiness` | when produced | explicit phase |
| `architecture_policy` | when produced | explicit phase |
| `source_patterns` | policy only | explicit complete or skipped phase |
| `import_diet` | witness only | explicit complete or skipped phase |
| `proof_xray` | witness only | explicit phase and registered extension |
| `quality_baseline` | when produced | explicit phase |
| `refactoring_prescriptions` | when produced | explicit phase |
| `findings` | always after pipeline execution | typed findings, always present |
| `packet_evidence` | non-empty only | explicit phase and registered extension |
| `review_regions` | non-empty only | explicit phase |
| `pipeline.timings` | pipeline reports only | compatibility projection of `phases` |

The current renderers and readers are:

- `ladon.render`: canonical JSON serialization and compact text rendering.
- `ladon.atlas`: report-directory reader and atlas renderer.
- `ladon.atlas_diff`: atlas reader and deterministic diff renderer.
- `ladon.atlas_sqlite`: atlas and bridge-report reader.
- `ladon.atlas_workflow`: current/before atlas and bridge-report reader.
- `ladon.proofir_bridge`: Ladon report reader used for optional ProofIR joins.
- `ladon.calibration`: report reader used by calibration predicates.
- `scripts/ladon_atlas_export.py` and `scripts/ladon_atlas_workflow.py`: file
  loaders for those library readers.

In v1, optional phases were represented by a missing top-level key. A skipped
phase stored the character count of its reason in
`pipeline.timings.<phase>.counters.reason`; the reason text was lost. The
renderer generated `metadata.generated_at_utc` from the wall clock when no
timestamp was supplied.

## Canonical v2 shape

Every registered phase is present in `phases` with an explicit `required`
selection bit and exactly one state:
`complete`, `skipped`, `partial`, or `failed`. An empty successful result is
`complete` with empty data. Skipped, partial, and failed phases preserve a
textual reason and structured diagnostics. The `pipeline.timings` and known
top-level analysis sections are bounded compatibility projections; new
capabilities must not add arbitrary top-level keys.

Registered extension namespaces are:

| Namespace | Owner | Base-contract responsibility |
| --- | --- | --- |
| `proof_xray` | proof-xray capability | version, state, authority, provenance envelope |
| `packet_evidence` | packet-evidence capability | version, state, authority, provenance envelope |
| `atlas` | atlas capability | version, state, authority, provenance envelope |
| `elaborated_declarations` | declaration-surface capability | version, state, authority, provenance envelope |

The owning capability defines each concrete extension payload. The base report
schema only validates the generic envelope and JSON value boundary.

## Stable ordering and volatility

Canonical JSON uses UTF-8, two-space indentation, sorted object keys, and a
trailing newline. Collection sort keys are:

| Collection | Stable key |
| --- | --- |
| phase mapping | registered phase order, serialized as sorted object keys |
| findings | `(kind, subject, identifier)` |
| diagnostics | `(phase, severity, identifier, subject, message)` |
| extensions | namespace |
| provenance | `(authority, source, backend, version)` |
| phase counters | counter name |

Analysis-owned lists retain their owner-defined deterministic order. An owner
that introduces an unordered collection must define its sort key in that
capability's schema.

`metadata.generated_at_utc` is nullable and is never synthesized. If the caller
provides a timestamp it is preserved verbatim. `elapsed_seconds` is useful
runtime telemetry but volatile; normalized-byte determinism tests replace it
with zero before comparison. No other field is normalized away.

## Version policy and reader dispatch

- `ladon-report-v3` is the current JSON interchange contract.
- `ladon-report-v2` remains an explicit compatibility writer and reader.
- Additive optional properties and registered extension payload versions may
  evolve without changing the report major.
- A removed or renamed field, a changed field meaning, or a changed required
  state requires a new report major.
- Readers explicitly accept `ladon-report-v2` and the bounded
  `clean-core-1` compatibility input. Unknown majors fail with an actionable
  diagnostic naming the consumer, received version, and supported versions.
- The enriched typed model and report v3 record terminal phase dispositions.
  The unchanged v2 wire shape cannot represent selector- or strict-mode
  dispositions, so its explicit writer reports that information loss. Every
  public dictionary tagged `ladon-report-v2` keeps the frozen schema shape;
  callers needing current disposition evidence must retain the typed model or
  request report v3 directly.
- The v1 serializer is JSON-only. Text always renders the canonical v2 model.

The `clean-core-1` serializer remains for one published v2 alpha release. It
projects representable canonical data, restores v1's omitted-section behavior,
and emits an information-loss warning because phase states, structured
diagnostics, extension envelopes, identifiers, authority, and provenance are
not fully representable. Remove the adapter at the first release following
that v2 alpha compatibility window.

## Field and state migration

| v1 field/state | v2 field/state | Compatibility behavior |
| --- | --- | --- |
| `metadata.report_version = clean-core-1` | `metadata.report_version = ladon-report-v2` | v1 serializer restores the old label |
| generated `metadata.generated_at_utc` | nullable caller-supplied value | v1 output omits it when unavailable |
| missing optional section | `phases.<name>.status = skipped` | v1 serializer omits the section |
| successful empty section | `status = complete`, empty `data` | retained as an empty v1 section where representable |
| numeric `counters.reason` | textual `reason` | v1 cannot reconstruct the old numeric artifact |
| `status = ok` | `status = complete` | v1 timing projection maps back to `ok` |
| exception-only failure | `status = failed` plus diagnostics | v1 warning records information loss |
| rows plus module failures | `status = partial` plus diagnostics | v1 warning records information loss |
| untyped finding dictionary | typed finding with `id`, `severity`, `authority`, and `evidence_count` | extra v2 fields are omitted only when required for fixed v1 fixtures |
| optional owner top-level key | registered `extensions.<namespace>` envelope | concrete payload remains owner-defined |
