# Ladon product scope

Ladon's governing objective is to help AI-assisted mathematics become
understandable, checkable, attributable and reusable by the mathematical community.
An explanation a reader can question and correct matters more than whether an
assistant chooses a particular command. Model-independent reading and ordinary
verification are design requirements; software status is not human understanding.

Ladon's near-term product has three intended workflows. Candidate-specific
execution evidence determines their readiness. The [measured alpha profile](MEASURED_ALPHA_PROFILE.md)
records the qualified contracts, external observations, and remaining gaps.
Other command surfaces are optional layers outside this compatibility boundary.

The responsible-mathematics work is motivated by AGMAI's September 29, 2026
recommendations. The [source and selected focus](../openspec/changes/ladon-result-understanding-and-release-umbrella/sources.md#selected-focus-for-the-current-milestone)
identify clearer proof exposition and honest informal/formal coverage as the
current contributions. Goal capture and application checking support those
contributions; their engineering qualification alone does not demonstrate
improved exposition or human understanding.

The returned r05 review and [checked offset bridge](../openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/offset-bridge-r63/REPORT.md)
narrow the active investment to preserving the intended claim and its exposition
alongside ordinary Lean tools. Direct consumption of guides, manifests and
assessments as files is supported. Further standalone search/application/exposition,
extractor and release-feature expansion is frozen; retain existing commands and
checking guarantees while consolidating their documented use. The matched bridge
attempts establish mathematical progress but no concrete Ladon contribution.
Shared artifact-maintenance value remains unmeasured. No third uptake challenge
is planned to select a favorable command-use result.

## Current direction

The r08 review accepts [r68 maintenance](../openspec/changes/ladon-request-canonical-validation-reuse/evidence/r68/REPORT.md)
and closes that optimization cycle. Existing command/format compatibility and
checking boundaries remain maintained. No next optimization target is implied.

The [proof explanation and correction round](PROOF_EXPLANATION_AND_CORRECTION.md)
used a real fixed-epoch divergence question. The r09 review accepts a narrow
editorial contribution; the [refined companion](../openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/proof-companion-r69/COMPANION.md)
and manuscript transition remain reviewed proposals, with adoption pending.
This cycle is closed. The [mathematical handoff](ORDINARY_LEAN_HANDOFF.md) also
remains proposed and is not a software prerequisite. No new runtime package is
justified. Interface/extractor/release expansion remains frozen. A substantive
new question, material claim/support change or concrete costly/error-prone handoff
in actual use should determine further work; routine edits need no new pro review.

The supplied proof-correspondence paper led to a bounded [local audit workflow](PROOF_CORRESPONDENCE_AUDIT.md). Three elementary cases and faithful controls have new ordinary Lean evidence; one pinned published derivative comparison has source-local evidence and an unresolved stronger-estimate bridge. The investigation closes with readable findings and unadopted corrections. Existing tools suffice; this adds no runtime feature and does not reopen the r09 editorial or r68 optimization cycles.

The existing engineering/ordinary-proof results do not establish comparative
reader benefit or artifact-maintenance advantage. The umbrella benefit gate stays
unmet/deferred; neither a bundle nor a recorded review certifies understanding.

## Retained product workflows

### 1. Declaration discovery and proposition verification

Use the disposable proof-search index for bounded lexical/type-text shortlists.
Index construction is lexical and does not invoke Lean. These search commands
have candidate-specific installed contract gates and do not establish Lean
applicability. Readiness requires the corresponding execution evidence.
`search type-text` replaces the retired `search type` spelling and emits
`ladon-proof-search-type-text-result-v2`. Literal matching uses SQLite's ASCII
case folding. Field contributions and population coverage describe the
bounded lexical query; omitted rows and lower-bound counts remain explicit.
Stored freshness does not inspect current sources; verified freshness checks
index generation, not theorem truth. `explain` requires a unique, nonempty,
untruncated Lean-rendered indexed type and retains owner and generation
evidence. A normal lexical index has no such type. Alternatively, select
`explain --check-artifact <artifactRef> --check-local-id <localId>` from a
stored check in the same evidence store. This returns its bounded rendered
type and stored receipt without invoking Lean. Structural comparison never
establishes applicability to the supplied goal.

```bash
ladon proof-search index build --repo-root /path/to/project
ladon proof-search search type-text --repo-root /path/to/project --pattern 'Nat → Nat'
ladon proof-search check candidate --repo-root /path/to/project \
  --module Project.Owner --goal 'True' --candidate Project.Owner.goal
```

The explicit candidate checker is an experimental proposition-only profile for
trusted repositories under a selected toolchain. Repeat `proof-search discover --local NAME:TYPE` for ordered typed hypotheses,
including dependent propositions. Names and types are validated before
toolchain selection; Lean elaborates them in the selected module. The default compact
`llm` result registers full ProofIR outside the target repository, returns only
artifact-qualified evidence references, and remains bounded to 8 KiB for a
direct check or 32 KiB for discovery. `--projection audit` returns the unchanged
full artifact payload. Scratch replay is disabled by default;
`--scratch-mode advisory` attempts it at most once per discovery operation and
does not promote candidate authority. Non-terminal batch prefixes remain
provisional process observations and cannot be counted, ranked, or replayed as
semantic outcomes. Exact request bytes are digest-bound to Lean's structural
goal subject; display spelling is non-authoritative. Shortlist rows remain
discovery evidence, not elaboration results or proofs.

### 2. Architecture review

Run the ordinary analyzer to inspect module ownership, imports, declaration
structure, architecture-policy violations, review regions, and calibrated
quality signals. Text-only analysis is the safe default; target builds and Lean
extraction remain explicit operations.

```bash
ladon --repo-root /path/to/project --root Project/Owner.lean \
  --architecture-policy docs/ladon-architecture-policy.json \
  --format json --output report.json
```

### 3. Evidence and lineage inspection

Use read-only ProofIR dossier, route, slice, alternative, and triage queries for
stored evidence. Use theorem lineage for an exact compiled proof-value
dependency closure when a pinned Lean environment is available.

```bash
ladon proof-search evidence theorem Project.Owner.goal --repo-root /path/to/project
ladon theorem lineage Project.Owner.goal --repo-root /path/to/project \
  --refresh missing --view routes
```

Stored evidence, structural routes, and lineage dependencies do not become
unqualified theorem-truth claims.

## Optional layers

- Experimental `ladon result validate` checks supplied claim manifests and
  revision-bound review observations without loading canonical Lean evidence.
  See [Result manifests](RESULT_MANIFEST.md). Dossier integration and full
  release readiness remain gated separately.

- Reportsets, runsets, atlas JSON/SQLite, atlas diffs, and reviewer cards are
  optional multi-report review projections.
- Theorem capsules are optional packaging and clean-room replay machinery.
- ProofIR bridge adapters and external snapshot importers are compatibility
  edges, not the native-v3 semantic core.
- Benchmark, calibration, review-packet, and governance commands are maintainer
  workflows rather than the primary user product.

Optional layers may have narrower portability or stronger environment needs.
They must not weaken the three core workflows, become implicit dependencies of
them, or redefine their authority boundaries.

The generated [supported-feature matrix](SUPPORTED_FEATURE_MATRIX.md) records
the executable tests that gate each supported or optional workflow.

Candidate-specific integration qualification is described in
[Authority-safe integration](AUTHORITY_SAFE_INTEGRATION.md). Passing the two child receipts alone
does not close integration or the experimental verified-discovery exit.

Candidate evidence admission and the registered evaluation policy are described
in [Readiness and evaluation](READINESS_EVALUATION.md).
