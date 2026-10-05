# Result understanding and release umbrella

Help people and LLMs determine what a mathematical result establishes, inspect its formalization and assumptions, and navigate evidence and explanations for reuse.

Source: [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (September 29, 2026). The [source map](sources.md) records relevant sections and the boundary between those recommendations and Ladon's design. Its [selected focus](sources.md#selected-focus-for-the-current-milestone) keeps clearer proof exposition and honest informal/formal coverage as the current goals; application checking is supporting work.

- [Proposal](proposal.md): scope and six new capabilities.
- [Design](design.md): identity, review, bounded CLI, export, and evaluation decisions.
- [Tasks](tasks.md): sequenced implementation work and current progress.
- [Dependency ledger](children/dependency-ledger.json): six child work packages, external gates, and core/full exits.
- [Capability specs](specs/): executable acceptance scenarios for each work package.

## First alpha milestone

One exact paper-claim/formalization pair produces a dossier, an annotated reading path, and a portable bundle. The acceptance corpus includes an extra assumption or incomplete mapping, a stale review, and a reusable lemma. Installed offline inspection and separately attributable real-Lean checks accompany qualitative LLM usage feedback.

The first core feedback pass precedes research-log and optional community-profile expansion. Those remain required for full umbrella completion. Core checks never imply human understanding, natural-language faithfulness, novelty, or institutional compliance.

## Planning and implementation status

The core correspondence, dossier, guide and portable bundle exits are recorded.
The umbrella has **33/50 tasks complete**. The qualitative alpha experiment,
bounded repairs and same-guide retests are complete as a work package; the
usefulness gate has not passed. See [current status](status.md), the
[external review](external-starter-review-r49.md), and the
[read/find/check outcome](baselines/read-find-check-r49/REPORT.md).

Both fresh readers completed explicit lemma reuse. The Ladon reader's scope
audit remained incomplete; added mathematical value over the same guide and
ordinary Lean is not established. Preserve all attempts and redirect the next
review toward core discovery/checking friction. Further result-layer expansion,
provenance/profiles and quantitative evaluation remain deferred. No archive or
public release is implied.
