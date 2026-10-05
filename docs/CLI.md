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

The theorem dossier exposes native check runs in a bounded `checks` section.
Each available receipt is a stored reader view of the canonical check; it retains
historical binding, outcome, authority, freshness, and completeness. The dossier's
own query receipt reports `not-run` because reading evidence does not run a check.
Older artifacts without receipts expose null receipt availability.

Stored semantic receipts are also checked against canonical typed inputs,
results, and application shapes. Rehashing a receipt does not allow it to change
the canonical goal, candidate, outcome, or completeness. Unsupported receipt
operations and contradictions return an operational invalid-receipt diagnostic.

Stored `evidence route|slice|alternatives` output includes a separate reader
receipt bound to the artifact content, operation, typed input references, and
bounds. Structural completion does not imply checking: its checking outcome is
`not-run`, and environment match and checking completeness are `not-assessed`.
Invalid targets have failed observation state. Content/lookup owner mismatches
are rejected before traversal; the query never executes Lean.

Stored lineage queries and their graph/summary projections expose the same
receipt axes. They report no executed theorem check, even when the dependency
closure is fresh. `lineage:` references identify existing closures without
reinterpreting opaque IDs as digests. Text output includes the seven dimensions
and exact receipt identity alongside the bounded result.

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

## Bounded declaration search and explanation

Proof-search uses the same installed CLI surface as a human operator. Its
bounded search commands are `search name`, `search type-text`, `explain`,
`consumers`, and `constructor`; `index query` remains a compatibility adapter.
Use `--format json` for machine-readable results and inspect `authority`,
`freshness`, `coverage`, `bounds`, and `omissions` before treating a row as
actionable.

`search type-text` uses the JSON schema
[`ladon-proof-search-type-text-result-v2`](../src/ladon/schemas/ladon-proof-search-type-text-result-v2.schema.json).
The old `search type` spelling fails with a stable migration diagnostic before
index access. Matching is literal substring matching with SQLite's ASCII case
folding, including literal `%` and `_`. Each row reports the contributing type
fields; coverage includes returned-row contribution counts, population and
row-evidence completeness, omissions, caps, and a matched lower bound.
`matchedExact=false` means the bounded query did not count all matching rows.
`--limit` accepts 1–1000; `--diagnostic-limit` accepts 0–1000. Diagnostics do not
establish Lean verification. Scope-specific roots are required before index
access. `--freshness verify` checks canonical source, configuration, schema,
helper, toolchain and stored/current generation identities; stale or
unavailable indexes fail closed. Stored queries remain explicitly stored.

`explain --candidate <name> --goal <goal>` looks up exact indexed names.
`--module <owner>` filters candidate ownership; it is not a goal-environment
selection. Bounded matches retain name, type bytes/truncation, authority,
module/namespace/package, path/line and stored generation evidence. One unique,
nonempty, untruncated `lean-rendered` type permits structural comparison.
Missing, ambiguous, lexical-only, empty, truncated or stale evidence produces
an unavailable result. Structural results and route cards do not establish
Lean applicability; use explicit `check candidate` or `discover` for that
operation. These commands execute code from the selected trusted repository.

`explain --check-artifact <artifactRef> --check-local-id <localId>` selects
one declaration type from a validated stored check, using `--evidence-store`
from that check. It requires stored freshness and no `--module` owner filter.
The exact declaration name and structural fingerprint must agree. A normal
lexical index has no Lean-rendered type; this explicit stored-check path can
provide one without running Lean. Its receipt remains stored and its route
card does not claim applicability to the new goal.

## Runsets and report sets

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
  --timeout-seconds 120 --max-output-mib 8 --max-rss-mib 32768 \
  --format json
```

Application checks now expose observed residual contexts and the selected
declaration's full parameter inventory; see [Application observations](APPLICATION_OBSERVATIONS.md)
for protocol versions, compact omissions and historical evidence limits.

Candidate checking, discovery, and explicit source association default to a
32 GiB process-tree RSS cap (`--max-rss-mib 32768`). Reports retain measured
`peakRssBytes` and configured limits; a run below the cap can still warrant
performance investigation. Compare peak memory and elapsed time with the same
operation and input baseline when assessing regressions.

Candidate checking and source association allow up to 16 GiB of primary
compiled inputs in aggregate, with a 512 MiB per-file ceiling. These are
streamed disk-input budgets, separate from the process memory cap. Source
association additionally observes up to 8 GiB of auxiliary compiled files.

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
When an artifact includes a canonical check receipt, expansion also returns an
`evidenceReceipt` for the current read with `observationState: stored`. The
embedded artifact retains its original bytes and historical receipt. A receipt
whose identity or check/environment ownership is invalid fails the read.
New rejected checks also record their ordered local context as a typed canonical
input. Live projections and stored readers reject receipt/context contradictions.
Older rejected checks without that input remain readable; their receipt context
has no independent canonical context evidence. Historical execution binding is
checked against the exact input-owned environment's recorded toolchain selection
mode and Lean worker executable identity. Ambient selection can name an elan
launcher; new environments record the actual worker digest separately. Explicit
selection additionally requires the selected Lean identity to match the worker.
Scratch and interrupted-batch process receipts bind their recorded selected
toolchain, preserving their partial process scope rather than asserting another
elaborator worker observation.
Malformed metadata or contradictions fail the
read. If that environment or its toolchain context is unavailable, the returned
receipt has `executionBinding: none` and an explicit limitation; its reported
outcome and checking scope remain unchanged. The canonical artifact keeps its
original receipt. This inspection neither consults current toolchain files nor
reconstructs the original process environment from redacted metadata.
Older ambient launcher records without an independent worker identity also
return binding `none` when the selected and observed executables differ.

Compact candidate and scratch cards apply the same historical binding checks.
Absent context or an unknown launcher/worker relation yields binding `none`;
direct cards then report a stored observation, while discovery cards report a
derived observation. The card's `executionBindingLimitation` explains the
weakening in JSON, text, and minimal output. Its `sourceReceiptIdentity` still
identifies the unchanged original receipt. Recorded contradictions fail before
display selection, including for omitted candidates. Weak failures without
canonical checks retain their attempted toolchain selection and failed,
non-checker scope. Missing or null receipts expose unknown axes; public
completeness fields cannot supply receipt authority. A present malformed receipt
fails compact population validation, including on omitted rows and unattributed
scratch failures. Stored text reads preserve the finite binding limitation.
The raw `audit` projection
remains a detached copy of the supplied canonical result, rather than a new read
receipt. Its text header identifies original observations whose execution
binding has not been revalidated for that view. None of these projections starts
Lean or inspects current executables.

This checker is an experimental proposition-goal profile for trusted target
repositories. Target initializers execute inside the bounded worker. The public
`discover` workflow accepts repeated `--local NAME:TYPE` declarations in
order, including dependent hypotheses such as `P:Prop` followed by `h:P`.
It validates the declarations before toolchain selection and retains their
order in the request and receipt. It does not claim arbitrary-`Type` discovery
and treats scratch replay as advisory process
evidence only. Scratch is disabled by default; `--scratch-mode advisory`
requests at most one replay and is bound into the discovery request identity.
Lexical/type-text shortlists are candidate populations rather
than semantic matches. For `discover --pattern`, `--module` selects the module
in which Lean checks the goal; it does not filter the shortlist. Use `--scope`
and `--root` to select candidates. For example, `--module Main --scope module
--root Helpers` searches `Helpers` and checks its candidates in `Main`.
A non-terminal batch prefix is exposed as a provisional
process observation: it is not counted as accepted or rejected and cannot
trigger scratch. Controlled testing uses explicit-pinned toolchains.

Add `--require-isolation` to `proof-search check candidate` or `proof-search
discover` when target initializer isolation is required. The current trusted
repository profile cannot provide it, so these requests return exit code 1 and
`target-isolation-unavailable` before executable preflight, target loading,
index access, or evidence publication. Inspect the requested policy with
`ladon doctor --json --require-isolation`; doctor reports availability and
`targetExecution: not-run` without executing the target.

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

Candidate-specific integration qualification is described in
[Authority-safe integration](AUTHORITY_SAFE_INTEGRATION.md). Passing the two child receipts alone
does not close integration or the experimental verified-discovery exit.

### Result inspection

`ladon result inspect MANIFEST [--artifact PATH ...] [--assessments PATH] [--lineage-inputs PATH]`
provides offline component cards and stored checking evidence. Select
`--section components|claims|targets|assessments|reviews|checking|assumptions|lineage|evidence`,
optional `--claim ID` / `--target ID`, `--limit 1..100`, and `--format json|text`.
Use the returned `--cursor` with identical inputs/options for continuation.
Both formats retain exact references and omissions under a 32 KiB page limit.
The `evidence` section queries exact subjects in the supplied canonical artifacts.
Explicit lineage selections add stored trust and frontier observations; missing
extraction remains unknown. Inspection does not run Lean or refresh evidence. See
[Result manifests](RESULT_MANIFEST.md#offline-result-inspection) for versioned
assessment inputs, independent evidence dimensions and remaining limitations.

### Proof reading guides

`ladon result guide MANIFEST [--guide-inputs PATH] [--artifact PATH ...] [--lineage-inputs PATH]`
reads ordered, attributed explanations and citations. Select
`--section steps|citations|reviews|correspondence|targets|checking|assumptions|lineage|evidence`,
exact `--claim ID` / `--target ID`, `--limit 1..100`, `--cursor`, and
`--format json|text`. Pages fit 32 KiB and preserve exact omitted-field references.
Explanation and attribution reviews bind exact revisions and remain distinct
from manifest correspondence reviews and stored checker results. The command
does not execute Lean or establish applicability to a new goal. See
[Proof reading guides](RESULT_GUIDES.md) for the companion format and reuse workflow.

## Portable result bundles

`ladon result export MANIFEST --selection SELECTION --output BUNDLE` creates a
deterministic experimental core package. `ladon result verify BUNDLE` verifies
integrity only; `--extract-to NEW_DIRECTORY` publishes verified contents.
`result inspect BUNDLE` and `result guide BUNDLE` accept the ZIP or extracted
directory using their normal selectors and continuations. External input flags
cannot be mixed with bundle inputs. See [selection, history, limits and examples](RESULT_BUNDLES.md).


## Source goals and compiler diagnostics

`ladon proof-search goal capture` observes a selected goal at an exact source position with explicit pinned Lean/Lake binaries. `goal diagnostic` parses a saved type-mismatch record and separately attempts source capture; parsed expected types remain caller-supplied evidence. Neither command applies a candidate or completes a proof. See [source selection, positions, output isolation and status contracts](SOURCE_GOAL_CAPTURE.md#ordinary-cli-handoff).

The additive [source-goal completion workflow](SOURCE_GOAL_COMPLETION.md) consumes saved JSON capture and a full term; independent replay is required for its completed status.
