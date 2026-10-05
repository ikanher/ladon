# Selected components and paragraph review

This workflow supports precise exposition and explicit informal/formal coverage,
the selected contributions to [AGMAI's recommendations](../openspec/changes/ladon-result-understanding-and-release-umbrella/sources.md).
It reads supplied evidence offline. It does not generate a correspondence
verdict, prove prose false, or run a new Lean check.

Start with one claim component:

```bash
ladon result inspect result.json --assessments assessments.json \
  --claim claim-id --component component-id --artifact canonical.json
```

`statement` retains its existing whole-claim meaning. `wholeClaimStatement` and
`statementScope: whole-claim-context` make that scope explicit. `componentScope`
contains attributed assessment descriptions with authors and current/historical
currency; it is unavailable when no current description has been supplied.
These descriptions are not extracted component statements.

`claimComponentCoverage` counts all declared components and includes unmapped
siblings beside the selected mapping. For example, a transcript binding does
not certify an average-only conclusion elsewhere in the same claim. Unmapped
does not mean false or independently establish that no formal proof exists.

`formalStatements` retains exact target identity, revision, type text and
resolution. `stored-canonical-type-text` means the existing resolution owner
matched that rendered type to exact supplied canonical evidence; unresolved
targets retain `manifest-supplied` authority. Structured parameters remain
unavailable without a bound extraction owner. Read the exact type for its
premises; dependency frontiers and axioms are different evidence categories.

The component selector requires an exact claim and the `components` section.
An optional target selector combines conjunctively; an unmapped component
cannot borrow evidence from a mapped sibling. Ordinary component pages expose
the same scope fields. Whole input remains validated before selection.

## Review one paragraph

Use existing guide-v1 steps and explanation reviews; no new manifest fields
are required. Select a paragraph's claim and the component to compare:

```bash
ladon result guide result.json --guide-inputs guide.json \
  --assessments assessments.json --section exposition \
  --claim claim-id --component component-id --artifact canonical.json
```

An archive or extracted result bundle can replace `result.json`; its existing
guide and assessments roles supply the companions. Do not mix bundle input
with external evidence flags. The new component selector is available only
on the exposition section of `guide`, which requires both claim and component.

Each row retains the paragraph's prose, author, revision, sources and target
bindings, its explanation reviews, the selected component's coverage and
current supporting formal statements. `associationBasis` explicitly identifies
the component as caller-selected; that selection is not a correspondence
review. A supporting lemma need not itself be a component mapping.

Current and historical reviews retain their original statuses and rationales.
`current-attributed-reviews` says a current explanation judgment is present;
it is not a mathematical success badge. Historical paragraph bindings expose
no current supporting statement, even when a target is individually unchanged
but the claim, manifest or prerequisite changed. `recheckNotices` request
reassessment; they do not infer falsehood from changed content identities.

To review an application step, preserve the cited lemma's premises. If an
explicit application leaves a boundary-sign premise unresolved, a review can
identify that unsupported application and propose adding the premise. That
does not prove the conclusion false or the premise necessary for every proof.
Keep conventional arguments, unchecked translations, unresolved correspondence
and attributed mismatch judgments distinct. A successful alternative derivation
does not establish fidelity to the prose or the supplied proof's actual strategy.

Guide sources can cite a digested [source-goal completion](SOURCE_GOAL_COMPLETION.md)
output. The view preserves that source citation without loading it as a fresh
check receipt. Run completion explicitly against the captured original goal
when a fresh application check is required. Every offline exposition row reports
`reuseApplicability: not-checked` and `mathematicalVerdict: not-inferred`.

Both JSON and text fit 32KiB per page with bounded field omissions and exact
input references. Focused exposition pages prioritize short paragraphs, relevant
review rationales and named coverage over repeated formal context. Deduplicated
fields retain omission references; large sibling inventories use a bounded
preview with aggregate counts. Shortened formal types are labelled `EXCERPT`
at the point of use, with an input/target inspection template and the exact
input pointer for complete text. Target pages can also excerpt a very large
type, so the supplied original remains the complete-statement route. Read the supplied original input at those references for
unclipped prose/types. Cursors bind the projection, selectors and evidence
identities; changing a paragraph, assessment, review or target invalidates
continuation. No implicit model, Lean or network operation occurs.
