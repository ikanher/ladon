# Ladon CLI contract

Ladon's installed commands are ordinary command-line tools. The same public
options and process behavior apply whether a person, shell script, editor, or
model invokes them. There is no caller-specific analysis mode.

## Analyzer command

Default analysis does not execute Lake, Lean, or target initializers. It writes
one compact text report to standard output:

```bash
ladon --repo-root /path/to/project --root Project/Owner.lean
```

Select JSON or a regular output file explicitly:

```bash
ladon --repo-root /path/to/project --root Project/Owner.lean \
  --format json --output -

ladon --repo-root /path/to/project --root Project/Owner.lean \
  --format json --output report.json
```

`--format` accepts `text` or `json`; `--output` accepts a file path or `-` for
standard output. One invocation sends at most one representation to standard
output. Report bytes use standard output or the selected file, while
deprecations and diagnostics use standard error.

For one alpha compatibility release, `--json PATH`/`--output-json PATH` and
`--text PATH`/`--output-text PATH` remain file-output aliases. Supplying both
legacy flags writes two distinct regular files from one analysis result. They
cannot be mixed with `--format` or `--output`, cannot name `-`, and emit a
deprecation diagnostic on standard error.

JSON defaults to report v3 with the `review` projection. V3 stores each phase
payload once, records deterministic omission metadata, and streams regular-file
output through the report-byte limit. Use `--projection summary|review|full` to
select detail without rerunning analysis.

`--report-version v2` remains an explicit compatibility writer and warns about
its duplicated large-payload cost. The bounded `v1` adapter is available only
when JSON is the sole representation; neither older writer selects a different
analysis. Text renders directly from the typed analysis model and does not
construct canonical JSON bytes.

## Proof-search index

Proof-navigation indexing is an explicit ordinary CLI operation:

```bash
ladon proof-search index build --repo-root /path/to/project \
  --format json --output -
ladon proof-search index status --repo-root /path/to/project
ladon proof-search index query --repo-root /path/to/project \
  --text integrable --scope closure --root Project.Owner --limit 20
```

Without `--index PATH`, an explicit build writes the generated database to
`<repo>/.ladon/index/proof-search.sqlite`. Ladon does not edit ignore files;
projects should ignore `.ladon/index/`. An external path supports read-only
checkouts and CI. Status and query operations never build the project or run
Lean. Version one labels its declaration and import rows as lexical navigation
evidence and exposes unavailable Lean-backed populations rather than treating
them as empty. Results use `--format text|json` and `--output PATH|-`; bounded
queries always report scope, omissions, generation identity, and truncation.
Builds are published atomically only after SQLite integrity and foreign-key
checks pass. `--max-index-mib` sets the database ceiling and defaults to 512;
the previous generation remains intact if the new build exceeds it. Stored
lexical signatures are capped at 16 KiB and query limits are capped at 1,000.

### Stored ProofIR evidence

After an index build, ordinary read-only queries inspect project-local ProofIR
evidence without invoking Lean or replay tools:

```bash
ladon proof-search evidence theorem Quux.Problems.Example --repo-root /path/to/project --format json
ladon proof-search evidence artifact proofir/surface.json --repo-root /path/to/project --format text
ladon proof-search evidence route route-id --dag dag.id --start fact.id --end claim.id --repo-root /path/to/project --format json
ladon proof-search evidence triage all --repo-root /path/to/project --format json
```

The theorem result keeps Lean attachment, quoted surfaces/claims, replay,
obligation context, lineage, diagnostics, coverage, and nonclaims separate.
Missing, stale, ambiguous, unsupported, and unconfigured evidence are not
collapsed into theorem failure. Use the explicit index build command to refresh.

## Theorem lineage

Use the project-local index for exact compiled dependency lineage:

```bash
ladon theorem lineage Fully.Qualified.theorem --repo-root /path/to/project \
  --refresh missing --view routes --from trust --format json --output -
```

The default `missing` policy plans and ingests only an absent closure. `never`
forbids Lean refresh, while `stale` and `always` permit it. The bounded views
are `routes`, `graph`, `tree` (a DAG unfolding with shared references), and
`bottlenecks`; `spines` is a routes alias. Filters include trust/project,
external/package/declaration roots, type/value/all edges, generated-node policy,
and finite depth/node/edge/route/output caps. Results identify freshness,
authority, closure identity, omissions, and truncation. They describe
dependencies of one compiled proof term; they do not enumerate all proofs,
alternative proofs, or a natural-language proof.

## Build and execution security

Target building is opt-in:

```bash
ladon --repo-root /path/to/project --root Project/Owner.lean --build
```

`--build` runs the target repository's ordinary `lake build`. This can execute
arbitrary target-controlled build scripts and code with the invoking user's
permissions. Ladon checks the repository, Lake manifest, toolchain, requested
root, and output destination, then supervises the build in a separate process
group with a finite `--build-timeout`. Timeout or interruption terminates and
reaps the group.

The removed `--skip-build` option is unnecessary: omitting `--build` preserves
the no-build default.

## Finding policy

Findings are advisory unless `--fail-on` is supplied. The option is repeatable,
case-sensitive, and uses OR semantics:

| Selector | Meaning |
| --- | --- |
| `kind:<finding-kind>` | Match that exact finding kind. |
| `severity:<minimum>` | Match that severity or higher using `info < warning < error`. |
| `phase:<name>:skipped` | Match an explicitly skipped optional phase. |
| `phase:<name>:partial` | Match an accepted partial optional phase. |

Selectors and deterministic matches are recorded in report metadata. An
operationally incomplete required phase takes precedence over a policy match.

## Exit status

| Status | Meaning |
| --- | --- |
| `0` | Requested analysis completed; advisory findings may be present. |
| `1` | Input, filesystem, toolchain, build, extraction, timeout, or output failure. |
| `2` | Invalid invocation, option combination, selector, or Ladon configuration. |
| `3` | Analysis completed and an explicit `--fail-on` selector matched. |

When the process is terminated by a POSIX signal, Ladon cleans up supervised
children and preserves the conventional signal-derived status.

## Partial reports

If trustworthy discovery or analysis phases finish before an operational
failure, Ladon writes the selected report with completed evidence and a
`partial` or `failed` required phase, then returns status 1. A failure before a
valid report can be constructed produces only a concise standard-error
diagnostic. Consumers must inspect both process status and phase envelopes;
report existence alone does not mean the requested run completed.

## Scope preview and finding inspection

`preview` resolves roots and populations before a full analysis:

```bash
ladon preview --repo-root /path/to/project \
  --scope multi-root --root Project.Owner --root Project.SecondOwner \
  --format json --output -
```

It reports resolved roots, primary/context populations, truncation, cache
expectations, estimated Lean batches, selected policy identities, and requested
wall-time, RSS, report-byte, and Lean-helper limits. Policy content participates
in the source-index and scope fingerprint. Preview reads source and policy
inputs but does not start Lake, Lean helpers, target initializers, or VCS
commands; observed resource use and limit crossings therefore remain absent.

Project-generated classification is opt-in through a versioned policy such as
[`generated-family-policy.example.json`](policies/generated-family-policy.example.json).
Only an explicit per-family `reviewThreshold` can promote
`generated_family_review_pressure`; large or generated-looking names alone do
not. The finding is review pressure, not evidence of a generator defect,
staleness, proof failure, or theorem truth.

`findings` inspects an existing supported report without rerunning analysis:

```bash
ladon findings --report report.json --filter severity=warning
ladon findings --report report.json --id ladon.finding.<stable-id>
```

Filters are exact and limited to `id`, `kind`, `severity`, `scope`,
`authority`, `confidence`, `priority`, `population`, and `path`. Exact lookup
returns typed canonical-row, aggregate, artifact, or source evidence when the
producing analysis supplied it; an explicit unavailable reason is retained
otherwise. Finding inspection rejects malformed or dangling local evidence
pointers instead of returning an apparently actionable row.

## Runsets and report sets

Proof-search uses the same installed CLI surface as a human operator. Its
bounded search commands are `search name`, `search type`, `explain`,
`consumers`, and `constructor`; `index query` remains a compatibility adapter.
Use `--format json` for machine-readable results and inspect `authority`,
`freshness`, `coverage`, `bounds`, and `omissions` before treating a row as
actionable.

`runset` executes a versioned manifest of ordinary Ladon analyses and publishes
a resumable bundle:

```bash
ladon runset --manifest analysis-runset.json \
  --bundle-dir /tmp/ladon-bundle --format json --output -
```

Entries run serially by default, retain distinct reports, and reuse only
fingerprint-compatible indexes or Lean caches. Resume validates the manifest,
entry fingerprint, report version, projection, content hash, and terminal
state before accepting a zero-launch hit.

Installed report-set operations consume supported reports or a validated
bundle:

```bash
ladon atlas --bundle /tmp/ladon-bundle/bundle.json \
  --output-sqlite /tmp/ladon-atlas.sqlite \
  --format json --output /tmp/ladon-atlas.json
ladon query --db /tmp/ladon-atlas.sqlite --query hotspots
ladon cards --atlas /tmp/ladon-atlas.json
ladon diff --before before-atlas.json --after /tmp/ladon-atlas.json
ladon workflow --atlas /tmp/ladon-atlas.json --before before-atlas.json
```

Bundle ingestion resolves only manifest-declared relative members and verifies
their versions, hashes, sizes, metadata, and entry states. These operations
preserve quoted authority, confidence, partial state, and nonclaim fields; they
do not perform theorem comparison or upgrade review evidence into proof facts.
If a failed, skipped, interrupted, or cancelled runset entry has no canonical
report, `atlas --bundle` preserves the bundle-owned state, reason, and nonclaim
under `workflowDiagnostics`; it does not synthesize a report or analysis
evidence. The `workflow` command routes those rows through its matching
`workflowDiagnostics` and `incompleteOrStaleEvidence` sections.

## Auxiliary ProofIR bridge

`ladon-proofir-bridge` remains a supported general-purpose auxiliary command.
Its help, report/diagnostic channel separation, invocation errors, operational
errors, and signal behavior follow the same process rules where applicable.
Analyzer-only build, finding-policy, and report-version options are not added to
the bridge merely to make its option list identical.

## Proof-search baseline evidence

The portable baseline command records identity-bearing, observational timings
without overwriting an accepted file:

```bash
python scripts/proof_search_baseline.py \
  --repo-root /path/to/project \
  --output .ladon/baselines/proof-search.json \
  --probe python -c 'print("probe")'
```

Baseline timing, database-size, and peak-RSS measurements are observational and
must be compared on the same fingerprinted host. Public-contract predicates,
deterministic ordering, authority/freshness fields, bounds, and omission
semantics are release gates; a fast measurement never upgrades heuristic or
lexical evidence into Lean authority.

## Migration summary

| Earlier invocation | Current invocation |
| --- | --- |
| `ladon ... --skip-build` | `ladon ...` |
| `ladon ... --output-json report.json` | `ladon ... --format json --output report.json` |
| `ladon ... --output-text report.txt` | `ladon ... --format text --output report.txt` |
| JSON and text printed together | Select one stdout format, or use the bounded two-file legacy adapter. |
