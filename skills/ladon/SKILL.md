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
