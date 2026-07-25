# Ladon Report Contract v3

`ladon-report-v3` is Ladon's canonical JSON interchange format. The ordinary
`ladon` command analyzes once, keeps the result in the typed report model, and
then selects a JSON projection without changing analysis or finding policy.
Compact text is rendered directly from that same model.

Ladon reports architecture and review-routing evidence. Source ranges,
declaration candidates, audit commands, findings, and graph edges do not assert
theorem truth or proof correctness.

## Canonical ownership

Every phase payload has one owner under `sections`. Entries in `phases`,
`extensions`, and `pipeline.timings` carry status, scalar summaries, and local
JSON pointers such as `#/sections/module_dag`; they do not repeat the payload.
Consumers must resolve those pointers instead of looking for legacy duplicated
phase data.

Diagnostics have one canonical table under `diagnostics`. Phase envelopes
refer to rows in that table, preserving incomplete-state reasons without
copying diagnostic objects into every view.

Every phase also carries a terminal `disposition`. A partial phase is
`accepted` only when it is optional and no strict or explicit failure selector
rejects it. Required, explicit-selector, and deprecated strict-mode rejection
are distinguished as `required-rejection`, `selector-rejection`, and
`strict-rejection`. The separate `required` bit remains authoritative when
more than one rejection condition applies.

## Projections

JSON output defaults to the `review` projection:

| Projection | Collection limit | Intended use |
| --- | ---: | --- |
| `summary` | 20 | quick orientation and automation summaries |
| `review` | 100 | ordinary interactive review |
| `full` | unbounded | explicit complete evidence export |

Bounded projections record each omitted collection with its JSON pointer,
reason, and exact omitted count. An omitted population is therefore distinct
from an observed empty population. All three projections share an analysis
fingerprint computed from the unprojected analysis after only registered
runtime and cache telemetry is normalized.

## Serialization and limits

Regular-file v3 output is encoded in bounded chunks, written to a temporary
file, flushed, and atomically published. `--max-report-bytes` is checked before
publication; exceeding it leaves an existing destination unchanged. This path
does not construct a second report-sized decoded JSON string.

When progress is explicitly enabled, serialization emits start and terminal
events plus bounded byte-count updates on stderr. Source discovery similarly
emits bounded completed-module counts. Progress telemetry never becomes an
analysis-authority surface and never enters report stdout.

The packaged schema is
`src/ladon/schemas/ladon-report-v3.schema.json`. Readers reject unknown report
majors rather than guessing field locations.

## Compatibility

`--report-version v2` explicitly selects the compatibility writer. V2 repeats
large payloads in legacy locations and emits a warning about that cost.
`--report-version v1` remains a bounded JSON-only adapter with documented
information loss. Readers retain explicit dispatch for supported older majors;
older writers never select a different analysis path.

A persisted v2 document cannot be promoted losslessly into v3 because the
frozen v2 wire contract has no terminal-disposition field. The v3 builder
therefore requires the typed analysis model, or an enriched mapping that
already carries every disposition, instead of inventing selector or
strict-mode policy state.

See [CLI contract](CLI.md) for stream and exit behavior and
[Report contract v2](REPORT_CONTRACT_V2.md) for the compatibility shape.
