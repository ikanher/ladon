## Context

Ladon has three supported internal workflows—architecture review, declaration discovery, and evidence/lineage inspection—but external review showed that the discovery and authority contracts are not yet aligned with their presentation. Five executable probes against commit `35b7a85` demonstrated: name-versus-type comparison in `explain`; ignored type-search scope; echoed-but-unverified freshness; preflight/worker environment divergence; and ambient/absent-to-pinned authority promotion. The same audit found a dead recursive slice implementation beside the new iterative traversal.

The product decision is to make verified proof discovery the primary user workflow, architecture review secondary, and ProofIR/lineage the audit substrate. The implementation decision is more conservative: repair contracts first, establish a release gate over both correctness and authority, then build one vertical discovery slice before changing broad architecture or adding features.

Constraints include caller-neutral installed CLI behavior, no implicit Lean execution, bounded local resource use, no network requirement, target repositories that may execute initializers when Lean loads modules, disposable SQLite projections, Python 3.11/3.12 support, and no public distribution without an owner-granted license.

## Goals / Non-Goals

**Goals:**

- Convert every reproduced defect into a failing portable and installed regression before production edits.
- Make declaration explanation operate on attributable candidate-type evidence or return unavailable.
- Give lexical type-text discovery an honest name and enforce every accepted scope and freshness request.
- Bind toolchain preflight and worker execution to one immutable sanitized execution context.
- Represent execution binding, observation state, operation outcome, source freshness, environment match, authority basis, and analysis completeness independently.
- Define and test total non-escalation transitions through live results, artifacts, SQLite, dossiers, aggregates, and renderers.
- Provide one compact public evidence receipt backed by richer internal ProofIR evidence.
- Deliver and externally evaluate one goal-and-context-to-compiled-application discovery workflow.
- Establish capability readiness levels whose promotion requires installed, adversarial, resource, and external outcome evidence.

**Non-Goals:**

- New ProofIR artifact families, legacy ProofIR adapters, or a new wire major.
- New Rust ownership or parity claims, a long-lived daemon, editor protocol, or network service.
- A broad service-class rewrite before the vertical discovery contract exists.
- Expansion of atlas, runset/reportset, capsule, bridge, packet-governance, or architecture-smell surfaces.
- Treating lexical matching, scratch-source generation, or Ladon receipts as theorem truth.
- A cross-platform sandbox implementation in this umbrella; the release must instead expose execution posture and fail closed where policy requires isolation.

## Decisions

### 1. Five children execute in four dependency waves

Wave 1 contains independent `ladon-proof-discovery-correctness-repairs` and `ladon-execution-authority-integrity` children. Wave 2 is the small `ladon-authority-safe-release-gate`, which cannot exit until both Wave 1 children pass. Wave 3 delivers `ladon-verified-discovery-loop`. Wave 4 delivers `ladon-capability-readiness-and-external-evaluation`.

Correctness and authority repairs share a release invariant but remain separate implementation owners because their source, tests, and rollback boundaries differ. The dependency ledger is normative and must be machine-validated.

### 2. Explanation requires attributable candidate-type evidence

`explain` continues to accept a qualified candidate name for lookup, but comparison input comes from the selected declaration row, never from that name. The row must carry nonempty type text, an allowed type-status authority, and `typeTextTruncated = false`. Missing, ambiguous, stale when verification was requested, unavailable, or truncated evidence produces a stable unavailable/indeterminate result with the exact reason.

The lexical analyzer may peel binders and compare a stored conclusion, but it must label that result structural. Lean application checking remains the only semantic applicability surface. Falling back from absent type evidence to the declaration name is forbidden.

### 3. Lexical type discovery gets an honest versioned command

The ordinary command becomes `proof-search search type-text` (final spelling may be `signature` only if selected consistently before implementation). The old unqualified `search type` command exits with a stable migration diagnostic rather than silently aliasing the old semantics.

Repository scope is always supported. Other scopes are accepted only when the query has the roots and graph data needed to constrain the candidate population exactly; otherwise parsing or request validation rejects them before SQLite access. `freshness=verify` must call the same generation/source verification owner as name search and expose the verified generation identity. `freshness=stored` is explicitly labeled stored metadata. Merely echoing either value is forbidden.

### 4. One execution context owns resolution, preflight, and launch

The caller environment is an input to context construction, not an execution environment. Ladon first captures immutable allowlisted selection inputs, preserving locale presence and values. It resolves executables using those inputs, derives existing compiled-library roots, and freezes the final process map with constructed `PATH` and `LEAN_PATH` before any version or source-enumeration process. Version checks, auxiliary Git enumeration, and worker launch use that exact final map and repository root. Selected Git has its own bound absolute executable identity; later verification does not reread the host environment or reselect tools. Root-list mutation and mismatched worker repositories fail closed. This binds search paths, not every compiled library file.

The receipt records a canonical digest of non-secret execution-context data: allowed key names and values after an explicit redaction policy, executable identities, repository root identity, pin content digest, selection mode, and worker adapter identity. Raw secrets and arbitrary caller variables are never serialized. A version result that depends on a discarded variable therefore fails preflight under the actual worker environment.

### 5. Evidence axes and their transitions are explicit and total

The public model separates:

- `executionBinding`: `explicit-pinned`, `ambient-observed`, or `none`;
- `observationState`: `live`, `stored`, `derived`, `absent`, or `failed`;
- `operationOutcome`: `accepted`, `rejected`, `failed`, or `not-run`;
- `sourceFreshness`: `fresh`, `stale`, `unknown`, or `not-assessed`;
- `environmentMatch`: `exact`, `mismatched`, `unknown`, or `not-assessed`;
- `authorityBasis`: the existing closed ProofIR basis vocabulary;
- `analysisCompleteness`: `complete`, `partial`, `invalid`, or `not-assessed`.

Every parent-to-child projection is governed by an explicit transition table. Reload converts live to stored; aggregation converts source observations to derived where applicable; absence remains absent; ambient or none cannot become explicit-pinned; stale or mismatched input cannot become fresh/exact; failed/not-run cannot become accepted; and completeness cannot increase. Invalid combinations fail validation rather than being normalized heuristically.

The table registers live-result, canonical-artifact, SQLite-row, dossier,
aggregate, JSON-renderer, and text-renderer boundaries. SQLite and dossier
readers cannot emit live observations, and aggregates emit derived, failed, or
absent observations. Receipt projection revalidates canonical shape and identity
before applying these transitions. Artifact expansion presents its reader receipt
beside the immutable canonical artifact rather than rewriting historical bytes.

Required initializer isolation is an explicit CLI/API policy. The current
trusted-repository profile exposes its absence and rejects the requirement before
toolchain preflight or any target work. Doctor uses the same read-only posture
owner to report the requested policy. Resource bounds and toolchain pinning do
not satisfy an initializer-isolation requirement.

### 6. The compact receipt is a projection, not a second evidence system

Candidate checks, dossiers, lineage results, and renderers expose one versioned `evidenceReceipt` projection over canonical internal evidence. It contains the axes above, environment/check references, limitations, and exact subject identity. Rich ProofIR artifacts and normalized SQLite rows remain the source of detailed audit evidence.

The receipt subject has three closed profiles. Application-check subjects retain
exact module, candidate, goal, and ordered local context. Stored theorem query
subjects contain exactly `queryKind`, `theorem`, and `sourceRef`; supported kinds
are `theorem-evidence` and `theorem-lineage`. Lineage source references preserve
the existing closure ID as `lineage:<id>`; they do not assert that opaque IDs are
content digests. A missing closure keeps `sourceRef` null.

Stored derivation reader subjects contain exactly `queryKind=derivation`,
`artifactRef`, and `queryIdentity`. Both identities are content digests. The
query digest binds the operation, exact owner, typed target/start references,
and applied bounds. The SQLite lookup owner must match validated artifact
content before traversal. Complete structural results remain not-run and
not-assessed for theorem checking; invalid targets have failed observation
state. Native graph APIs retain their structural-only result contract.

Stored-query subjects cannot claim executed checks: binding is none, outcome is
not-run, environment match is not-assessed, and environment/check references are
null. Their receipt completeness does not imply complete theorem checking.
Freshness comes only from the existing closure identity comparison; source
staleness does not turn into an environment-match assertion. Dependency rows
retain their original acquisition authority separately.

The theorem dossier has a bounded, owner-qualified `checks` section in addition
to generic `observations`. Native check receipts are validated against their
canonical check/environment/authority owner and projected as stored; canonical
artifact bytes remain unchanged. Artifacts without receipts return null rather
than receiving inferred historical execution authority. Aggregate lineage graph
and summary receipts become derived. JSON and text use the shared transition
owner, and text includes all seven axes and the exact receipt identity.

Compact discovery views project each candidate and scratch receipt separately
as derived. They retain both the projected `receiptIdentity` and original
`sourceReceiptIdentity` alongside all axes and exact check/environment expansion
references. Missing receipts remain missing. No discovery-wide accepted receipt
is synthesized from successful children. Byte fitting retains these fields for
every visible card and reports omitted candidates through population coverage;
the complete population is validated before selection.

Compact candidate and scratch receipts also consume the exact recorded execution
binding result. Unsupported historical selection claims weaken to none through
the same owner used by stored readers. Because the closed model requires an
executed binding for live observations, an unbound direct renderer first takes
the stored-read transition; discovery then takes the aggregate-derived
transition. Other reported dimensions remain unchanged. A finite
`executionBindingLimitation` survives minimal output and text rendering alongside
source and projected receipt identities. The raw audit copy retains its
canonical-source contract; it is not a newly attributed read receipt.

Population validation rejects a present non-object receipt before treating a
weak candidate or scratch failure as unattributed. Absent receipts leave receipt
axes unknown, including completeness; public status metadata cannot supply the
missing receipt's completeness. Valid weak receipts retain attempted toolchain
selection and failed/non-checker scope. Stored text includes the finite historical
binding limitation. Raw audit text identifies original observations whose
execution binding has not been revalidated in that view; audit JSON keeps its
unchanged-copy and no-registry-write contract.

Receipt construction has one shared owner used by live checks and readers. Persistence round trips must demonstrate that live evidence reloads as stored without changing its recorded historical execution binding or authority basis. The receipt does not invent kernel authority and never replaces artifact validation.

Stored semantic receipts also reuse the observation contract that validates
compact discovery. Canonical results supply status, and typed declared input
references select the application shape. A validly rehashed receipt cannot
override candidate/module/goal attribution, outcomes, completeness, or available
context evidence. Scratch matching preserves the canonical caller-context
prefix; additional observed introduced variables remain permitted. Rejected
artifacts without a canonical application/context shape do not independently
establish complete context evidence. Unknown receipt operations fail closed;
legacy artifacts without receipts keep their existing read behavior.

`ladon doctor --json` reports installed distribution identity, command/schema compatibility, repository pin presence, resolved execution posture, supported Python status, and whether explicit toolchain preflight can be attempted. It is diagnostic and read-only: it does not build an index, load target modules, execute repository initializers, or convert a failed preflight into authority.

### 7. Derivation slicing has one implementation

The recursive `expand`/`_expand_step` path is deleted after differential fixtures prove the iterative traversal preserves ordering, occurrence routes, alternative selection, residuals, truncations, and bounds. No dormant alternate algorithm remains. The quality gate evaluates the iterative owner directly instead of suppressing complexity without decomposition evidence.

The public native query facade delegates shared graph validation, bounds, and
result envelopes to `_proofir_derivation_core`, AND/OR support search to
`_proofir_derivation_solver`, and selected slice accumulation to
`_proofir_derivation_slice`. The SCC owner consumes the same core directly.
Solver dispatch separates goal entry, alternative selection, child return, and
premise scheduling; slicing separates goal expansion from ordered slot capture.
These owners pass the quality gate without a traversal suppression. This is a
structural implementation boundary and does not supply checker acceptance.

### 8. Verified discovery is one bounded attributable Lean operation

The discovery request includes an exact goal, ordered local declarations/hypotheses, target module/environment, scope, caps, and execution context. SQLite produces a bounded shortlist with contribution evidence. One framed/batched Lean worker request checks that finite set under the exact context and returns per-candidate substitutions, discharged local hypotheses, residual premises, rejection diagnostics, and output bounds.

The selected scratch example is the source submitted to the recorded Lean check, or a byte-identical attributable derivative whose digest and relationship are explicit. Ladon does not compile an unexplained second source and call the two operations equivalent. At least one accepted candidate and one plausible rejected candidate are retained in the installed acceptance corpus.

### 9. Readiness is evidence-based and monotone

Capabilities use `experimental`, `contract-supported`, `externally-evaluated`, and `release-qualified`. Promotion requires all lower-level evidence and cannot be inferred from help output or a single happy-path unit test. Contract support requires installed smoke, adversarial semantics, resource/process cleanup, and versioned result gates. External evaluation requires held-out repositories and labeled outcomes. Release qualification additionally requires supported Python matrices, locked clean-candidate gates, documented security posture, and authority-safe integration where the capability emits authority-bearing results.

Evaluation uses a frozen goal corpus and compares Ladon with `exact?`, `apply?`, editor search where automatable, `#check`, and `rg` under recorded environments and equal resource/reporting rules. Metrics keep recall, incorrect-suggestion rate, time to first accepted candidate, scratch replay, architecture-finding precision, and maintainer actionability separate.

### 10. Product profiles are documentation and dependency boundaries first

The release documents `discover` as primary, `review` as secondary, `evidence` as audit substrate, and `extras` as non-critical. This umbrella does not immediately create a plugin architecture or service-class hierarchy. Production extraction follows demonstrated shared invariants; optional layers must not become dependencies of the first three profiles.

### 11. Installed adversarial evidence is authoritative for these repairs

The external reproduction script is translated into repository-owned fixtures without importing the review bundle. Each case first fails against the pre-change installed wheel and then passes through the ordinary installed CLI or public model. Source-tree unit tests supplement but cannot replace installed behavior. Exact expected statuses, fields, exits, and nonclaims are asserted; prose-only gates are insufficient.

## Risks / Trade-offs

- [Renaming `search type` disrupts callers] → emit a stable migration error, update docs/skills in the same child, and version the result schema.
- [Requiring non-truncated type evidence makes `explain` less available] → prefer an honest unavailable result and direct callers to candidate checking or index enrichment.
- [Many evidence axes burden users] → keep them canonical internally and expose one compact receipt with a review guide; never recombine axes into an ambiguous scalar.
- [Environment fingerprints expose sensitive values] → define a redacted canonical manifest, exclude arbitrary variables, and test that secrets never appear in output or digests intended for comparison across trust boundaries.
- [Batch checking increases target-code execution exposure] → require explicit execution posture, finite batch/resource limits, cancellation cleanup, and no use on untrusted repositories unless an approved isolation policy is active.
- [External baselines are difficult to automate fairly] → preregister corpus, environment, queries, labels, and metrics; report unavailable comparisons separately.
- [The vertical slice triggers premature refactoring] → make behavior and receipts the acceptance target; defer service extraction unless required by duplicated invariants.
- [Freeze delays useful optional work] → allow correctness/security maintenance but prohibit new compatibility promises until the gate exits.

## Migration Plan

1. Capture the five adversarial reproductions and current public payloads before edits.
2. Apply correctness and execution-authority children independently; either may be reverted without changing the other's storage.
3. Rebuild disposable indexes for any schema/result-version change and reject incompatible old projections explicitly.
4. Apply the authority-safe integration gate, regenerate supported-feature/readiness artifacts, and update installed documentation and skills.
5. Build the verified discovery vertical slice behind its new versioned command; do not silently change old command semantics.
6. Freeze and label an external evaluation corpus, then promote capabilities only from recorded results.

Rollback restores the previous installed command/result versions and rebuilds the disposable database. It must never reinterpret new receipts as old authority fields. Canonical native ProofIR v3 artifacts remain immutable source evidence unless a separately versioned schema change is approved.

## Open Questions

- Choose `type-text` versus `signature` as the final command spelling before the correctness child begins.
- Define which stored type statuses are sufficient for structural binder peeling and whether Lean-rendered truncated types are always unavailable.
- Environment identity policy is resolved in `docs/EXECUTION_ENVIRONMENT.md`: exact allowlisted values are privately hashed; public metadata exposes keys, selected paths, and digests.
- Select the initial held-out repositories and the minimum maintainer-label protocol without making optional external repositories required CI inputs.
- Define the minimum Linux execution posture for an internal technical alpha while a true sandbox remains out of scope.


### Historical reconstruction and installed acceptance

The original five review defects were reconstructed from exact commit `35b7a85`
after their production repairs. `historical-reproductions.json` in the result
umbrella records all five old-version behaviors on Python 3.11 and 3.12, the old
wheel bytes, import origins, probe bytes and raw capture digests. This is an
explicit historical exception to the original pre-edit chronology: it does not
establish that those tests ran before the repairs. New repairs still follow the
ledger's TDD invariant.

The authority acceptance inventory freezes the complete suite targets and
required source assertions. The installed runner records initial and final
collection, all setup/call/teardown outcomes and exact approved pytest arguments
with ambient selection and plugin autoload disabled. Candidate files and
installed package bytes are checked before and after the run. Qualification
requires both supported runtimes, no skips and every selected target.

A child receipt resolves bounded content-addressed artifacts instead of accepting
digest labels alone. The validator checks source-to-wheel-to-installation byte
equality, the suite/runtime matrix, approved producer/invocation, initial/final
collection, successful outcomes and source assertions. Quality command records
retain their bound logs. These are local integrity and coverage checks of
producer records; they do not authenticate the producer. The integration gate
requires separate compatible correctness and authority exits with the full
ledger exit-class names. Authority acceptance alone keeps that gate closed.
