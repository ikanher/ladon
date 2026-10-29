---
name: ladon
description: Use Ladon to find Lean declarations, compare indexed candidate types with goals, and inspect explicit candidate-check evidence in a Lean repository.
---

Use the installed CLI and its `--help` to confirm available commands. Read
[CLI contracts](../../docs/CLI.md) for invocation details and
[product scope](../../docs/PRODUCT_SCOPE.md) for current readiness limits.

Start with the repository's existing index, or build a lexical index explicitly
with `ladon proof-search index build --repo-root <repo>`. Name search and
`ladon proof-search search type-text --pattern <text>` return bounded SQLite
shortlists. The retired `search type` spelling returns a migration diagnostic.
Type-text matching is literal substring matching with SQLite's ASCII case
folding; it does not unify types or establish applicability.

Choose scope and roots before querying. Keep coverage, omissions, caps,
truncation and field contributions beside any suggestion. A matched count may
be a lower bound. `--freshness stored` reports stored evidence;
`--freshness verify` checks canonical source/index generation freshness and
does not check a candidate with Lean.

For active source editing, use `proof-search index status --changed` to inspect
added, changed and removed modules. An exact identifier miss on a stale index
does not establish current-source absence; read the exact-match summary before
lexical suggestions. `generationIdentity` names stored rows and
`currentGenerationIdentity` names newly observed supported inputs. Stored-only
queries leave the latter unchecked. For a supported index, use the
explicit `proof-search index update`; a `full-build-required` diagnostic means
the existing generation cannot be safely updated. Inspect the returned reuse,
source-change and size evidence before reporting an improvement.
After upgrading to 0.4.0, run explicit update to refresh recognized lexical
extractors v3, v4 or v5 to v6, even when sources did not change. This recovers
modifier-prefixed sections, matching compound scope ends, safe EOF-open scopes,
theorem-type `let` expressions and same-line `where` signature boundaries.
Retained evidence is preserved in history. Unknown extractor identities require
a new index path. Candidate names remain lexical; generated declarations may be
absent, and lexical type headers omit elaborated section variables and inferred
instances. Check the pinned Lean type before constructing an application.

When private indexes accumulate, run `proof-search index list`, then save a
`proof-search index prune --select NAME --format json --output PREVIEW.json`
preview. Apply only that saved selection with `prune --apply --preview-file
PREVIEW.json`. The default index, retained evidence, active publishers and
uncertain sidecars are protected. Persistent `.lock` files are coordination
state, not evidence that an active writer is present. The commands and limits
are documented in [CLI contracts](../../docs/CLI.md).

Use `proof-search explain --candidate <qualified-name> --goal <goal>` for
structural comparison of one uniquely attributable, nonempty, untruncated
Lean-rendered indexed type. Its `--module` selects the candidate's owner.
Retain candidate type, owner, location and generation evidence. Ambiguous,
missing, lexical-only, truncated or stale evidence is unavailable; do not
substitute the declaration name for its type. Even an available explanation
does not establish Lean applicability.

After a check, explain its stored rendered type with `explain --check-artifact
<artifactRef> --check-local-id <localId>` in the same evidence store. Keep
stored freshness and omit the owner-module filter on this path. A normal
lexical index cannot supply an available rendered-type explanation. The
comparison does not transfer applicability to a new goal.

For the primary discovery workflow or an explicit candidate check, use `proof-search check` or `discover` only
within the user's authorized trusted-repository workflow. These commands can
execute repository code. Read their help for supported proposition profiles,
ordered local declarations, resource bounds and execution posture. Repeat
`--local NAME:TYPE` in dependency order, for example `--local P:Prop --local
h:P --goal P`. The supported goals are propositions. The module
used by discovery is the goal context; candidate population comes from scope
and roots. Keep rejected and unassessed candidates visible. An accepted
application with residual goals is partial; it does not prove those goals.

Read `request.maxCandidates` beside the population counts. `closedAccepted`
counts closed applications; `applicableWithResiduals` counts applications that
still leave obligations. The historical accepted aggregate includes both.
Substitution keys include binder positions, so repeated displayed names refer
to distinct binders. Keep candidate-specific evidence failures visible alongside
valid siblings; do not describe a partial batch as entirely checked.

Use `index build --progress` for long rebuilds; stage and module-count events
go to stderr. A publication event is not a successful terminal result. Updating
an evidence-bearing index preserves its old database in adjacent history and
publishes current lexical rows; it does not refresh compiled evidence. Use
`index history --format json` and `theorem lineage NAME --history SHA256
--refresh never` to inspect an exact original observation offline. Keep the
index and its `.history` directory together. Historical availability is not
current applicability; already-stale closures remain stale. Reacquire current
lineage separately after the intended owners compile. Optional
`index update --max-history-mib N` bounds history without evicting evidence.
Rebuild/prune protect history owners; unsupported bases need a new index path.

Source-goal completion supports earlier declarations in the same ordinary
file through a private selected-environment snapshot and separate compiler
replay. After upgrading, recapture source goals because captures bind helper
bytes. Structural expression graphs retain local proof values without recursive
tree expansion. Keep measured memory and output sizes in field reports.

Report exact checked inputs and execution receipts separately from stored
index evidence and structural explanations. Preserve unknown or stale states
and the installed version's limitations; a source digest, route card, or
successful index query supplies no theorem-verification authority.

Architecture review is secondary; evidence and lineage are the audit layer.

## Discover correspondence problems in an exposition

When investigating an exposition without a supplied diagnosis, start from its
source claims before selecting formal endpoints. Read the selected source range
broadly, inventory intermediate assertions and uses, and retain unexamined spans.
Give the inventory's attribution and completeness limits. Mapping every supplied
component does not establish complete source coverage.

For a concrete correspondence discrepancy, use the [local derivation challenge workflow](../../docs/DERIVATION_CHALLENGES.md): `init --derivations`, exact source-bound steps, `challenge` export for a fresh reviewer, and `witness` for rational scalar counterexamples. Prioritize unresolved local inferences over expanding the inventory. A sampled success does not prove the step, and a rational refutation applies only to its faithfully interpreted assumptions.

Follow the [source-first audit procedure](../../docs/CORRESPONDENCE_DISCOVERY.md) and [investigation loop](../../docs/INVESTIGATION_LOOP.md). Initialize the source-bound plan at the actual start with an explicit budget. After every batch save a plan snapshot and use `ladon investigation next`. Before reporting, use `finish`: if it returns `continue` (exit 2), continue useful work within the budget. A budget or blocker exit remains incomplete. The commands validate source bindings and authored workflow records; they do not compare mathematical meanings or certify inventory completeness.
Compare exact local hypotheses, domains, quantifiers, conclusions and quantitative
dependencies. State the implication required by the consumer, check it in that
direction, and inspect the concrete producers of premise-bearing structures.
Keep statement correspondence and proof-method correspondence separate.

For actual Lean counterparts, follow [scoped correspondence and v3 review](../../docs/NL_LEAN_CORRESPONDENCE.md).
Use the current Ladon checkout explicitly (`PYTHONPATH="$PWD/src" uv run --project "$PWD" python -m ladon.entrypoint`),
not an independently installed pip copy. Author the source-bound interpretation
once, extract the actual application (`proof-search proof slice --scoped` for
nested local providers), then `interpret`, `align`, `check`, and `inspect`.
Slice traversal defaults to 131,072 nodes; `--max-nodes N` accepts 1–1,048,576
without changing time, memory, depth or output limits. Replay retains the
recorded allowance. Node exhaustion is incomplete extraction, not evidence of
a mathematical error; keep later extraction failures distinct from that limit.
Conditional replay, provider closures, original prose premise supply, parent
support, interpretation fidelity and described method are separate outcomes.
`init --correspondence` opts into investigation v3. Attach the native bundle,
export a sanitized challenge, and ingest an independently obtained response.
Preserve first responses; use a separate `reconcile` record for corrections.
Neither attributed reviews nor stored native labels are fresh mathematical
checks. Retain absent counterparts and unexamined spans in the review queue.

For opt-in mathematical contract analysis, use the ordinary
`investigation contract` commands and read [mathematical contracts](../../docs/PROOF_CONTRACTS.md).
`produce` snapshots attributed inputs; `propagate` and `obligations` generate
conditional results that still need checked support. `audit` preserves bounded
stage evidence and its original deadline. The [refinement workflow](../../docs/CONTRACT_REFINEMENT.md)
checks one supplied rational witness and a selected Nat/rational lift, retaining
separate source-cited and proposed-repair branches. Saved refinement `inspect`
and `report --refinement` evidence is historical and unverified, with no Lean
replay or automatic review closure. A citation does not certify formula fidelity,
and excluding one witness does not establish a universal claim.

For typed Real-bound estimates, read [typed bound adapters](../../docs/REAL_BOUND_CONTRACTS.md).
Use observe-bound on the full formal snapshot; its exit 2 and unresolved admission
are expected. Use plan-bound-prefix/check-bound-prefix for a supplied measure,
or plan-derivative-prefix/check-derivative-prefix for the fixed full joint real
Frechet derivative measure. A checked-binding establishes the selected predicate
laws. Use plan-real-bound/admit-real-bound on that plan for fresh predicate and
canonical Real scalar checks. inspect-real-bound/report-real-bound always show
historical evidence; replay-real-bound executes both checks again with current
identities. The source theorem proof and prose norm bridge remain separate.
For attributed Real prose estimates, read [authored Real readings](../../docs/REAL_PROSE_NATIVE.md)
and its observation/recognition guides. `produce-real-prose-bound` creates an
authored reading with unresolved admission, preserving alternatives, all guards,
full typed scope and exact source ownership. `connect-real-prose-bound` accepts
that reading, an admitted formal input, both source roots and an explicit proof
request; its implication retains the formal theorem and ordered local premises
as assumptions. New v2 connections require independent owner-target commitment,
kernel checking and replay; v1 history lacks target-owner binding. Reporting is
historical and authority-free. Fresh replay requires both original input records;
do not replace them with newer equivalent records or grant NL fidelity, source
theorem proof, mathematical falsity or discovery credit from a conditional check.
Connection transport preserves canonical v1 bytes when they fit and uses a
separately versioned bounded ASCII/zlib envelope only when needed. Keep the
existing 8 MiB wire, 32 MiB expanded, graph/string and native artifact limits;
decompression is bounded before DAG validation. An unavailable aggregate result
is an operational stop; retain inputs and the failed cap, report it, and stop
dependent checks without truncation or raised limits. Saved compressed-output
digest reproduction is currently tied to the local zlib implementation, so
cross-version history validation is not established.
When reporting evaluation results, count shape observations, adapter bindings
and native admissions separately. Reuse the qualification linked in the typed
bound guide only with matching runtime/input identities; informed-source success
does not establish unfamiliar-source detection, and resource stops are incomplete.
Use compare-real-bounds for same-source definitional predicate equivalence, or
compare-real-bounds-proofir to persist its exact native evidence.
inspect-real-comparison (also ordinary inspect) stays historical-only;
replay-real-comparison reruns both admissions and the relation.
propagate-real-bound-identity checks each adjacent edge but has no native
propagation artifact. Use check-real-bound-prefix --stronger/--weaker for an
individually checked higher-to-lower input-prefix implication in otherwise exact
contexts. This rechecks the admission proof and order inequality; it establishes
only the input-predicate implication. Add `-proofir` to that command to persist
its native evidence. `inspect-real-prefix` (or ordinary inspect) stays historical;
`replay-real-prefix --input ... --root ...` freshly rechecks both admissions and
the directional proof under one shared deadline. Saved success cannot replace
a failed fresh check. Use `propagate-real-bounds-proofir` with ordered
`--production` paths and one `--rule identity-v1|order-prefix-v1` per adjacent pair
to persist individually checked edges. `inspect-real-chain` stays historical;
`replay-real-chain` rechecks each position and edge under one shared deadline.
An unresolved edge cannot become a complete chain. This is not a separately
checked endpoint theorem or transfer composition. Use
`check-real-bound-coefficient --input admitted.json --root ...` for a pointwise
output-bound implication under `K ≤ L` and `0 ≤ C`. It retains original `K` in
predicate/object parameters; it neither infers coefficient uniformity nor
proves the source estimate. Use `check-real-bound-coefficient-proofir` for native
storage, `inspect-real-coefficient` for history and `replay-real-coefficient`
for fresh checking. `compose-real-bounds[-proofir] --left ... --right ...`
checks conditional composition from compatible source applications. Both
transfer steps remain assumed; report `transferPremises:assumed` explicitly.
Use `inspect-real-transfer`/`replay-real-transfer` for saved evidence. These
conditional goals are not identity/prefix chain edges or new admitted estimates.
Old Nat consumers remain unsupported. Preserve the complete telescope,
instances, quantified domains, scalar guards and actual numerical loss.

Process-tree RSS defaults to 12 GiB. On `Stop progress and report back to user:`,
preserve the failure and report the configured cap, available measured peak and
command. Stop dependent work; do not automatically increase memory or reset the
original deadline.

Freeze an interpreted local goal before checking it. A changed premise or goal
is a separately reviewed repair. An accepted endpoint cannot clear an unexamined
intermediate step; a failed application does not refute it. Retain unresolved
questions and coverage gaps when the work budget ends. Save initial findings
before a reference answer is supplied. Built-in command help remains sufficient
for invocation details; development examples are not required investigation inputs.

For lineage routes, `--max-nodes` also limits traversal rows. Repeated paths can
visit the same declaration, so `acquisition.rowsObserved` differs from returned
distinct nodes. One extra row detects truncation. A closure's distinct-node
count cannot establish a sufficient route budget; retain truncation and omissions.

## Integration evidence boundary

Establish contract support from a named installed, network-disabled discovery
exit and a matching evidence registry. External outcomes remain separately
required for external evaluation. A pair of child receipts is insufficient
for complete integration qualification. Follow
[the integration contract](../../docs/AUTHORITY_SAFE_INTEGRATION.md) and retain
exact candidate and receipt identities when citing qualification. Maintainers
must include `skills/**` in the tracked candidate; `.codex/**` is host-owned.

Consult the [measured alpha profile](../../docs/MEASURED_ALPHA_PROFILE.md) before
claiming current support. Portable contract support, external observations,
independent maintainer labels, and release approval are separate evidence.
Current external-outcome and owner-decision admission fails closed. Retain
unavailable imports, stale populations, and evidence caps as operational
limitations; they do not establish an incorrect mathematical suggestion.

When applying current field-hardening behavior, run the checkout from its own
Ladon directory with `uv run --locked python -m ladon.entrypoint`; an installed
pip executable can have older semantics. Use immutable `investigation checkpoint`
receipts for progress and `investigation finalize` for termination. If finalization
returns `continue`/exit 2, consume the queue with real work under the original
clock. Never reset the deadline or wait idly to manufacture budget exhaustion.
An actual cancellation can be attributed with `--stop-record`; it is not
identity-authenticated and must not be invented. Explicit per-work blockers must
cover every remaining queue item to permit early blocked termination; retain
policy-limited references as unverified. Terminal permission does not certify
mathematical completion, and plain prose is not mechanically controlled by these
commands. See [the investigation guide](../../docs/INVESTIGATION_LOOP.md).
