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
After upgrading to 0.2.3, run explicit update to recover signatures from the
previous lexical extractor, including theorem-type `let` expressions. This
one-time recovery re-extracts unchanged sources and preserves retained evidence.
Unknown extractor identities require a new index path. Unsupported signatures
are unavailable with an omission; type text is still lexical, not elaborated.

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
