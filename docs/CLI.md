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
checks pass. `--max-index-mib` sets the database ceiling and defaults to 1024;
the previous generation remains intact if the new build exceeds it. Stored
lexical signatures are capped at 16 KiB and query limits are capped at 1,000.
Index construction is lexical-only and never invokes Lean. The former
`--mode semantic|hybrid`, `--lean-timeout`, and `--semantic-completeness`
options were removed because they labeled lexical output without producing
semantic populations. Lean-backed evidence is available only through explicit
operations whose results name the checker and exact subject.

### Stored ProofIR evidence

After an index build, ordinary read-only queries inspect project-local ProofIR
evidence without invoking Lean or replay tools:

```bash
ladon proof-search evidence theorem Example.Project.goal --repo-root /path/to/project --format json
ladon proof-search evidence artifact proofir.derivation --repo-root /path/to/project --format text
ladon proof-search evidence route sha256:<artifact-id> --start statement:premise --end statement:goal --repo-root /path/to/project --format json
ladon proof-search evidence slice sha256:<artifact-id> --end statement:goal --repo-root /path/to/project --format json
ladon proof-search evidence alternatives sha256:<artifact-id> --end statement:goal --repo-root /path/to/project --format json
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
bounded search commands are `search name`, `search type-text`, `explain`,
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

## Native ProofIR v3

Validate producer output before indexing:

```bash
ladon proofir validate ARTIFACT.json
ladon proofir canonicalize ARTIFACT.json --out ARTIFACT.canonical.json
ladon proofir inspect ARTIFACT.canonical.json
```

`validate` and `inspect` return `ladon-proofir-validate-result-v1` and
`ladon-proofir-inspect-result-v1` objects. `canonicalize` returns the canonical
native ProofIR 3.0 artifact itself. Invocation, operational, and interruption
failures use `ladon-proofir-terminal-v1` JSON on stderr with exits 2, 1, and
130. These schemas describe artifact processing; they do not establish checker
acceptance or theorem truth.

List canonical artifact paths in the repository ProofIR configuration, then
run `proof-search index build` explicitly. The database is disposable and
project-local; a stored query never starts Lean or refreshes producer output.
Former bridge, surface-bundle, replay, obligation-DAG, and witness artifacts
fail with an unsupported-legacy diagnostic. Producers must regenerate native
v3 artifacts; there is no converter or data migration command.

Reviewers must inspect `coverage`, `omissions`, `checkerAcceptance`, and
`limitations`. A claim is a producer assertion, an attachment only relates
identities, and route/slice/alternative results are structural views. Only an
explicit check-run states what a named checker observed in a named environment.

Run the explicit closed-candidate checker with the same ordinary CLI used by
human and automated callers:

```bash
ladon proof-search check candidate \
  --repo-root /path/to/lean/project \
  --module Project.Module \
  --goal 'Exact Goal' \
  --candidate Project.Module.declaration \
  --timeout-seconds 120 --max-output-mib 8 --max-rss-mib 4096 \
  --format json
```

The installed command defaults to `--projection llm`. Before stdout is
published, Ladon commits the exact ProofIR artifacts to a separate
repository-scoped user-cache SQLite registry and re-resolves every emitted
environment and check-run reference. The compact direct result is capped at
8 KiB; compact discovery is capped at 32 KiB. Select `--projection review` for
more bounded diagnostic detail or `--projection audit` for the unchanged full
embedded result. Override registry location and capacity with
`--evidence-store` and `--max-evidence-store-mib`.

Expand compact references without rebuilding the lexical index or starting
Lean:

```bash
ladon proof-search evidence semantic-artifact ARTIFACT_REF --repo-root /path/to/project
ladon proof-search evidence semantic-environment ENVIRONMENT_REF --repo-root /path/to/project
ladon proof-search evidence semantic-check CHECK_ARTIFACT_REF \
  --local-id CHECK_LOCAL_ID --repo-root /path/to/project
```

These commands revalidate stored canonical bytes. Their references locate
evidence; they do not increase its recorded authority.

This checker is an experimental proposition-goal profile for trusted target
repositories. Target initializers execute inside the bounded worker. The public
`discover` workflow rejects caller-supplied local context, does not claim
arbitrary-`Type` discovery, and treats scratch replay as advisory process
evidence only. Scratch is disabled by default; `--scratch-mode advisory`
requests at most one replay and is bound into the discovery request identity.
Lexical/type-text shortlists are candidate populations rather
than semantic matches. A non-terminal batch prefix is exposed as a provisional
process observation: it is not counted as accepted or rejected and cannot
trigger scratch. Controlled testing uses explicit-pinned toolchains.

The testing profile caps a candidate name at 4 KiB and a module or goal at
64 KiB. A child timeout cannot exceed 600 seconds, output cannot exceed
64 MiB, and RSS cannot exceed 64 GiB. Discovery also rejects a projected child
process budget above 600 seconds, attempts at most one explicitly selected
advisory scratch replay, and caps its canonical serialized result at 64 MiB.
Compact transport has the smaller 8/32 KiB limits above. These are safety
ceilings rather than performance targets; the ordinary defaults are lower.

With `--projection audit`, a closed application returns
`ladon-semantic-candidate-check-result-v1` containing a batch-closed environment
manifest, check-run, and zero-residual derivation. The default compact schema is
`ladon-semantic-candidate-projection-v1`; it carries resolvable environment and
check-run references without embedding those bodies. If
Lean applies the candidate but leaves goals, the result is
`applicable-with-residuals` and contains an incomplete attempt-log with ordered
substitution, residual-statement, and local-context references; it is not a
proof. The
environment hashes every imported `.olean` selected by Lean plus repository
toolchain/manifest inputs; expression identities use the versioned structural
Lean-expression scheme. The exact goal bytes passed to the pinned helper are
digest-bound to the returned structural goal subject; pretty-printed goal text
is explanatory and is not used as semantic identity. The supervisor—not the Lean helper—owns command,
executable, helper, output, deadline, and RSS observations and creates the
check-run identity. Timeout, rejection, malformed helper output, or a resource
limit returns no accepted artifact. This first checker intentionally checks one
declaration application against a closed goal. It does not recursively solve
residual goals or promote an incomplete attempt into a derivation.

For `proof-search`, select machine output with `--format json`. Successful JSON
results are isolated on stdout. Invocation failures, operational failures, and
caller interruption produce exactly one
`ladon-proof-search-terminal-v1` JSON record on stderr and no stdout result;
their exit codes are respectively 2, 1, and 130. A failed or interrupted
operation does not replace an existing `--output` file. These records describe
CLI execution only and confer no checker or theorem authority.

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
