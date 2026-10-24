# Scoped prose and actual Lean applications

Ladon can extract a selected application from an elaborated Lean theorem and
check the implications needed to connect it to an attributed prose
interpretation. A successful Lean build establishes neither the interpretation
of the prose nor the validity of its described method.

The M1 profile is declaration-scoped application extraction. It records the
actual application, implicit arguments, leading lambda/let context, ordered proof arguments,
and declaration range. Premise providers are visible expressions with explicit
`provider-unexpanded` frontiers. This profile does not extract an entire proof
argument or assign a source location to every elaborated subterm. The opt-in
scoped profile below retains nested contexts and provider closures; it still
observes selected applications rather than a full proof.

## Reproduce the portable controls

Run the development checkout explicitly, using an installed pinned toolchain.
The fixture uses Lean 4.32.1. No download or Lake build occurs automatically.
Choose a new output directory; existing first receipts are never overwritten.

```sh
PYTHONPATH="$PWD/src" uv run --project "$PWD" python scripts/demo_correspondence.py \
  --output .ladon/m1-example
```

The script copies the fixture into its output directory and uses the ordinary
public commands for both cases. `commands.json` records commands, status,
elapsed time, and diagnostic output. The faithful positive interpretation must
close every generated implication. The false interpretation must have a checked
negation of the original conclusion-transfer goal. The actual formal
conditional must independently replay in both cases. These checks assert their
outcomes; an unsuccessful tactic does not satisfy the negative control.

The equivalent individual commands, with `REPO` set to the copied fixture and
`OUT` to a new working directory, are:

```sh
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint proof-search proof slice \
  --repo "$REPO" --source Proof.lean --module Proof \
  --declaration Correspondence.term --application Correspondence.bridge \
  --output "$OUT/slice.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation interpret \
  --record "$REPO/positive.json" --root "$REPO" --slice "$OUT/slice.json" \
  --output "$OUT/interpretation.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation align \
  --interpretation "$OUT/interpretation.json" --slice "$OUT/slice.json" \
  --map "$REPO/map.json" --root "$REPO" --output "$OUT/plan.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation check \
  --plan "$OUT/plan.json" --terms "$REPO/positive-terms.json" \
  --repo "$REPO" --root "$REPO" --output "$OUT/result.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation inspect \
  --plan "$OUT/result.json" --output "$OUT/inspection.json"
```

The proof-slice selector accepts ordinary qualified names. An unqualified
application name is resolved in the selected declaration's namespace. Use the
qualified name for an application from another namespace. `--occurrence`
selects a zero-based occurrence in the bounded traversal; repeated occurrences
retain their ordered arguments. Unsupported selections return diagnostics and
failed process receipts, never a hand-authored substitute for extraction.

## Author once, then inspect the generated obligations

An interpretation record has exactly `id`, `source`, `formula`, and `symbols`.
The source contains a repository-relative UTF-8 path, one-based start/end lines,
the exact joined quote, and a bare SHA-256 digest of the entire file. Line
splitting includes Unicode/form-feed boundaries. Native source maps bind actual
UTF-8 byte offsets as well as lines; a PDF must first have a separate, identified
text extraction. The text extraction's provenance remains the author's
responsibility.

Formula tags are `var`, `const`, `app`, `forall`, `exists`, `implies`, `and`,
`eq`, `lt`, `le`, `not`, and `opaque`. Bound variables use scoped identities;
printed names do not carry semantics. Quantifier order is preserved. A declared
symbol names a Lean declaration with an authored Lean type, checked in the
selected environment. Global symbols are explicitly rooted to prevent capture
by generated binders. Unknown fields, escaped variables, stale source, and
undeclared symbols are rejected. An opaque root is retained as an unsupported
interpretation, with its original text and reason.

The object map maps formal local names to outer universal binder identities,
or to a declared representation function applied to those identities:
`{"n": {"symbol": "val", "args": ["i"]}}` with `val` declared as
`Fin.val : Fin 5 → Nat`. Arbitrary authored Lean terms are not object maps.
Mapped objects become typed local definitions in the generated obligations.
Their types must elaborate. Local values must depend only on mapped or earlier
available objects. A proof assumption cannot be passed as an object map. Missing
maps and proof-dependent types remain explicit residuals.

Generated local names currently accept ASCII letters, digits and underscores,
plus Greek letters. Common Lean names with Unicode subscripts, such as `h₁`,
produce `unsupported-local-names` residuals. The actual formal conditional can
still replay, while premise supply and conclusion transfer remain unresolved.
Inspect each printed goal before supplying a proof: outer universal binders and
mapped `let` definitions precede the implication hypotheses. A term that
introduces too few binders can fail on a valid correspondence; rejection of that
attempt does not refute the goal.

For prose assumptions `H`, formal premises `P`, formal conclusion `C`, and prose
conclusion `N`, `align` generates the original `H → P` and `H → C → N` goals,
under the scoped objects and typed map. It also generates interpretation typing,
object-map elaboration, and actual formal conditional obligations. These are
**generated correspondence goals**, rather than claims that Lean observed an
original prose-proof goal. `inspect` prints these obligations and queries their
native SQLite projection without promoting stored labels to proof authority.

A supplied term record has exactly `obligation`, `term`, and `mode` (`prove` or
`refute`). Refutation checks `¬ (original generated goal)`. The caller cannot
replace the goal, introduce additional hypotheses into its contract, or reuse
an altered plan. A conditional proof is obtained from the actual extracted
application automatically. The checked module copies the original source, resets its command scope,
checks declared symbol types, captures each generated goal, elaborates the
term, and independently recompiles/replays it. Generated goals cannot inherit
ambient section hypotheses, namespace aliases, or attributes. Capture rejects
unexpected ordinary locals; completion rejects use of implementation-detail
locals, including a synthetic declaration used as its own proof. Only replay with complete axiom
coverage under `lean-standard-no-placeholders-v1` supplies support; `sorryAx`
and other unapproved axioms are rejected.

## Keep the outcomes separate

| Dimension | What the M1 result establishes |
| --- | --- |
| `conditionalValidity` | Replay of the actual selected formal application with its hypotheses |
| `premiseEstablishment` | The required generated premise-supply implications; external prose predecessors remain a separate review obligation |
| `parentSupport` | All required links support the attributed interpretation, a link is checked false, or the correspondence remains unresolved |
| `interpretationFidelity` | `attributed-unreviewed`; mathematical checking does not certify the author's reading |
| `methodCorrespondence` | `unreviewed`; the same endpoint does not establish the described method |
| `extractionCompleteness` | `selected-application`, including explicit unexpanded providers |
| `checkerAuthority` | Actual Lean worker authority for completed generated-goal checks |

Native `proofir.interpretation` and `proofir.correspondence` artifacts share exact,
owner-qualified references with source maps, attempt logs, and check runs. The
plan binds its native interpretation into its identity and must be replayed with
the original validated batch. One authored record supplies the artifact and
goal views. Serialized artifacts remain portable evidence claims: validation
checks structure and references; acceptance at the checking boundary requires
fresh extraction and replay. The environment may have an unresolved native
manifest; it is never guessed from another artifact. The full source/toolchain
and compiled import identities remain bound to the extraction and raw receipts.

SQLite schema 9 adds these native rows. Older disposable projections require
explicit rebuilding. Existing nine-kind canonical identities are unchanged.
The Rust validator does not support the two added kinds; this guide makes no
cross-language parity claim for them.

## Bounds and provenance

Each compiler/helper process has a 60-second deadline, 12-GiB RSS cap, and
8-MiB output cap, with process-group cleanup. Traversal permits 8192 visited
nodes and depth 64; each serialized expression is limited to 1 MiB. Formal
source is limited to 8 MiB. Interpretation lowering retains its separate 4096-node,
64-depth, 1-MiB text bounds. A check accepts at most sixteen supplied terms,
with one term per obligation, and replays at most sixteen supplied and automatic
terms in total. Remaining obligations receive explicit attempt-limit residuals.
Correspondence command JSON inputs have a
32-MiB bound; legacy investigation input limits remain unchanged. The executable
example adds a 15-minute outer deadline per public command.

Extraction privately compiles the selected source and observes the loaded
module closure. It then recompiles and observes again inside a checked stable
inventory interval. Every primary compiled module and present/absent sidecar is
fingerprinted; ambiguous, stale, or unexpected paths are rejected. Source,
helper, executable and context identities are checked too. Source, helper,
compiled inventory, limits, frontiers, local context, and actual application
facts contribute to slice identity. Timing and temporary paths do not.

Checking re-extracts before and after the obligations and rebuilds the original
plan. Generated temporary modules are removed after their receipts are saved.
Successful extraction receipts retain actual output digests and sizes instead
of duplicating the helper's full JSON frame. Failed output is retained within
its explicit diagnostic bound. Unavailable tooling and resource exhaustion
remain unresolved outcomes.

The checker captures its implementation identity when loaded and verifies that
identity before and after replay. A changed checker requires a new process;
it cannot label an old loaded implementation with the new source identity.
New checked bundles retain this identity as `implementationDigest`. Historical
bundles remain inspectable as stored evidence without acquiring fresh authority.

The real development passage/application run is qualified: the pressure-datum
application proves a one-dimensional derivative sign conditional on its exact
premises. Its physical coordinate/pressure correspondence, vicinity of the
axis, and quantifier scope are not supplied by that application. The native
result retains the unsupported physical reading; it does not certify the
sentence or identify the undisclosed historical exposition fault. Independent
source-fidelity review is retained separately from mathematical replay.

## Scoped local providers

Add `--scoped` to `proof-search proof slice` to select
`scoped-local-argument-v1`. The default profile and its existing identities are
unchanged. Scoped extraction traverses the actual theorem value, opening each
lambda and let in its own local context. A have-proof's right-hand side cannot
see later facts. Separate branch occurrences retain separate contexts; a nested
witness cannot be mapped to an outer prose object.

Every ordered proof argument records a boundary assumption, local proof value,
or proof expression, together with its closed type and proof. `align` adds a
`provider-N` obligation of kind `premise-provider-validity` for each one. `check`
replays these closures automatically. Its extra `providerValidity` result is
`conditionally-supported`, `refuted`, or `unresolved`. A supported closure is
conditional on its observed hypotheses: it does not establish their truth or
the original prose predecessors. Provider obligations and their individual
statuses survive native projection; the existing seven native result dimensions
retain their schema.

The executable scoped example refutes a missing premise while preserving the
downstream conditional and provider support:

```sh
PYTHONPATH="$PWD/src" uv run --project "$PWD" python scripts/demo_correspondence_review.py \
  --output .ladon/scoped-review-example
```

This uses actual Lean extraction and replay, then the ordinary review commands.
It preserves a first response and stores a correction separately. The demo's
reviewer label is explicitly an author's attribution, with no independent
reviewer launched. Its unfinished formal links keep `finish` at exit 2.
`commands.json` retains command results and timings.

Scoped extraction supports bounded elaborated lambda/let/application and
projection expressions, including witnesses and branch functions. Lexical scope
paths describe the traversal; they do not assign exact prose correspondence or
subterm source ranges. A source with no exposed theorem value, unavailable
application, unsupported expression, or exhausted bound remains unavailable or
incomplete with a frontier. Selected extraction never certifies full argument
coverage or the validity of an analytic derivation outside available replay.

## Immutable version-three review

`investigation init --correspondence` opts into v3; default v1 and
`--derivations` v2 remain available. Attach an existing interpretation, prepared
correspondence, or checked native bundle. This reuses its source-bound record
and original generated goals; no second contract transcription is needed.

```sh
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation init \
  --correspondence --text "$REPO/claim.txt" --root "$REPO" --output "$OUT/review.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation attach \
  --plan "$OUT/review.json" --bundle "$OUT/result.json" --root "$REPO" \
  --output "$OUT/attached.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation challenge \
  --plan "$OUT/attached.json" --claim "$SUBJECT" --root "$REPO" \
  --output "$OUT/challenge.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation ingest \
  --plan "$OUT/attached.json" --packet "$OUT/challenge.json" \
  --response "$OUT/response.json" --root "$REPO" --output "$OUT/reviewed.json"
PYTHONPATH="$PWD/src" uv run python -m ladon.entrypoint investigation inspect \
  --plan "$OUT/reviewed.json" --root "$REPO" --output "$OUT/queue.json"
```

For a formal bundle, `SUBJECT` is its `planId`; for an interpretation without a
counterpart it is the native interpretation artifact ID. Distinct readings and
applications are independent subjects. Source units still need an attributed
inventory; attaching a bundle does not clear unexamined source.

A response has exactly `reviewer`, `subject`, `challengeDigest`,
`classification` (`aligned`, `mismatch`, `unresolved`), `method` (`same`,
`different`, `unresolved`), `sourceFidelity` (`faithful`, `ambiguous`,
`unresolved`), and a nonempty `evidence` explanation. Copy the subject and
challenge digest from the exported packet. The packet contains source inputs,
observed context and original goals; it excludes prior checks, verdicts and
repair proposals. Launch independent reviewers separately under the applicable
authorization and preserve their first reports before reconciliation.

`sourceFidelity` describes whether the attributed interpretation represents the
quoted source. It is separate from whether that interpretation matches the
formal argument; a faithful reading can receive a `mismatch` classification.

To correct a response, use `reconcile` with the same arguments as `ingest` plus
`--first FIRST_RESPONSE_ID`, writing a new plan. The first response remains
unchanged and the correction is stored separately. A changed source, map,
interpretation or observed context requires a new subject/challenge and new
review; a prior digest cannot carry its acceptance forward.

Status prioritizes discrepancies and missing formal links before inventory
expansion. Mathematical review and formal correspondence have separate
completion dimensions. No counterpart, unresolved source, exhausted budget and
unsupported interpretation remain visible. `complete-attributed` mathematical
review can coexist with `incomplete-no-counterpart`; it cannot finalize the
formal work. Recorded complete native links are labeled
`recorded-links-complete-unreplayed`: ingestion and status do not run Lean again
or verify reviewer identity. V3 rational `witness` commands are explicitly
unsupported; use the v2 derivation workflow for that operation.

Current development writes `typed-operators-v2` lowering and
`ladon-correspondence-plan-v2` preparation. A declared operator such as
`HDiv.hDiv : Real → Real → Real` is annotated at the application site, so
numeral-only arguments elaborate in Real. Declaring the same operator at
`Nat → Nat → Nat` intentionally keeps truncated natural division. Nested
applications carry their own signatures. Dependent operator signatures outside
this instantiated fragment reject explicitly. The actual generated-goal check
records the closed elaborated expression and each applied operator/operand type;
inspection and sanitized review expose this evidence. The `interpretation`
obligation P → P is a typing check and does not establish P or prose fidelity.

Missing native lowering-profile metadata denotes historical untyped lowering.
Its canonical native bytes remain structurally readable; current checks require
fresh typed interpretation artifacts, newly prepared plans and new reviews.
Unknown profiles reject. Checksums bind stored evidence but do not authenticate
an arbitrary caller's bundle or replace fresh Lean execution.

Scoped extraction now uses `scoped-identity-transport-v2`. The Lean helper
reconstructs an ordered fresh context by fvar identity, substitutes dependent
types and local let values, and checks the closed application/proof roundtrip.
Original observed source locals and provider identities remain in the slice.
A map can use exact observed IDs:

```json
{"profile":"local-identity-v1","entries":{"OBSERVED_LOCAL_ID":"NL_BINDER_ID"}}
```

Use the actual `localContext[].localId`, never invent an ID from its display
name. Raw old maps remain usable when each display name resolves uniquely.
Ambiguous names, proof hypotheses, lets and escaped nested witnesses reject as
object-map references. Maps express attributed correspondence; generated
premise-supply and conclusion-transfer implications still need actual proofs.
Preserve the primary source path and its full qualified module identity.
Private extraction stages canonical sibling imports so a temporary namespace
directory does not hide the original project's compiled dependencies.

Run the current source checkout, avoiding any pip-installed Ladon:

```sh
cd /path/to/ladon
uv run --locked pytest -q tests/test_correspondence_typed_lowering.py \
  tests/test_correspondence_identity_transport.py \
  tests/test_proof_slice_namespace_overlay.py
```

These are actual portable Lean checks, with distinct arithmetic, context and
import-path guarantees. Passing them is development qualification; it does not
claim an exposition error was detected.

Historical v3 investigations remain readable under their original profile,
including original reviews and reconciliations. Status adds a
`refresh-semantic-profile` queue item for an untyped subject and reports
`incomplete-semantic-migration` on that subject. This preserves old observations
while requiring fresh typed checks and reviews for current guarantees. Historical
recorded-time validation does not supply current termination permission.


For repeated links in the admitted public-source fragment, opt into request-local
preparation using the same ordinary checking command:

```sh
cd /path/to/ladon
uv run --locked python -m ladon.entrypoint investigation check \
  --plan prepared.json --terms terms.json --repo /absolute/formalization \
  --root /absolute/source-root --preparation request --output checked.json
```

The selected source is compiled once in an owned temporary module inside its
already pinned canonical compiled root. Every link still runs actual capture,
completion, independent replay and complete no-placeholder axiom inspection.
Original compiled-import reads can be reused only inside this request, with
file/directory fingerprint checks at every lookup and full uncached hashes at
entry and exit. A changed source, helper, import or sidecar permanently invalidates
the owner, even after restoring its bytes. Cleanup removes only unchanged files
owned by that request. Source containing `private` or `local` keywords declines preparation and uses
the ordinary route; `preparationMode` records the route actually used.

`executionAccounting` reports all supervised process calls while checking,
per-stage wall time, process bounds, observed peak process-group RSS, input sizes
and the complete published bundle size. Nested stage wall times overlap and
must not be added. Peak RSS is the maximum observed supervised process group;
it does not measure total machine memory. CLI parsing and publication lie outside
its checking timer. Paired benchmarks additionally measure the complete public
entrypoint and disclose cache state and operator-controlled concurrency.

Preparation allows at most 8 GiB of selected compiled import/sidecar snapshots;
source, helper, frame and process output retain their 8 MiB bounds. A preparation
limit failure publishes a bounded diagnostic with the exact plan and unattempted
obligation frontier, leaving every failed link unresolved. Complete ordinary
JSON bundles use compact encoding and retain the 32 MiB consumer cap. An output
over that cap fails before creating the output file.

Request preparation now declines source text containing a `local` or `private`
keyword (including comments, conservatively). Every admitted reused obligation
still observes its closed proposition in the original copied source. Its exact
structural expression must equal Lean's separately captured prepared goal before
proof completion; a mismatch remains unresolved with
`prepared-goal-subject-mismatch`. This checks proposition identity per goal,
without asserting equality of all command, notation or tactic state.

The final paired field observation retained all 18 successful public trials
and their complete subject/replay/trust evidence. Observed median check time decreased
32.1% on the cone workload, 18.3% on numeric and 20.1% on scoped checks. These
are observations for the frozen inputs and measured machine, with warmed process
and checkout caches. An unrelated Lean job was observed on the host; external
load was not controlled, so full performance qualification remains open pending
a clean repeat. See the [full measurements and command](../openspec/changes/ladon-correspondence-field-hardening-umbrella/evidence/paired-benchmark-02/REPORT.md).
Ordinary checking remains the default; the command above opts into request reuse.
These measurements establish no improvement in detecting mathematical errors.

For authored correspondence observations without a successful extracted slice,
use the [observation capture and reporting path](INVESTIGATION_FINDINGS.md).
Version-three plans accept optional immutable `observations`; review completion,
source fidelity, formal support and mathematical falsity remain separate.
Status retains reviewed native classifications and corrected first-response
history. Supplementary reporting exposes conflicting reviews and pending branch
work without resetting the clock or replaying stored checks.
