# Focused paragraph projection — second r61 gate

Parent task9.1 stays open. Add `exposition` to GUIDE_SECTIONS and optional
`component_id` to guide API / `--component` to CLI. Exposition requires an exact
claim and known component; component selection on other guide sections rejects.
Guide now accepts the existing assessments companion, standalone and bundled;
complete guide, assessment, canonical and stored-check validation is preserved.
No new schema, dependency, implicit Lean/model/network call or receipt importer.

Each selected authored step becomes one lazy row:
- `paragraph`: existing step card (stepId, revision, explanation, author,
  sources, prerequisites, currency, targetBindings, existing exact references).
- `selectedComponent`: existing component card, with
  `associationBasis='caller-selected-component-not-correspondence-review'`.
- `supportingStatements`: exact statement rows for the paragraph's bound
  targets, ONLY when the whole step and individual target bindings are current.
  A supporting target need not be a component mapping; add
  `relationship='guide-support-not-component-correspondence'`.
- `reviews`: all existing explanation-scope reviews for this exact step,
  current and historical, with original reviewer/rationale/status and currency.
- `reviewStatus`: `current-attributed-reviews` only with at least one current
  explanation review, otherwise `not-reviewed`. This never means proof success.
- `recheckNotices`: rows `{reason, stepId, reviewId?}` for historical paragraph
  (`historical-paragraph-binding`) and historical explanation review
  (`historical-explanation-review`); notices request reassessment, not falsehood.
- `checkingScope='explicit-application-operation-required'`,
  `reuseApplicability='not-checked'`,
  `mathematicalVerdict='not-inferred'`.

Historical paragraphs retain their old prose and review records. Their
supportingStatements are empty, their paragraph targetBindings have no typeText
and statementAvailability unavailable, and their selectedComponent has no
formalStatements: no current statement is lent to a historical explanation.
Current selected component context remains labelled as caller-selected, never
an approval of the prose or proof strategy. Historical paragraph status alone
does not invalidate the current manifest target or assert that any claim is false.
Authored source citations, including digested application outputs, remain
citations; no fresh checking authority is imported from their presence.

No guide yields one unavailable row with reason no-guide-inputs-supplied;
valid guide with no selected paragraph yields zero rows. Optional target selector
conjoins paragraph selection by its own guide target bindings, not claim-wide
targets. All new nested fields have exact original input references, avoiding
fabricated projection paths. Input binding includes projectionVersion=2,
component and assessments, alongside all existing query and input identities.
JSON/text parity, 32KiB/page, <=100 rows, authored order, lazy page construction,
whole-input validation and strict guide-v1 schemas remain intact.

Independent red controls: current correct text + attributed review; altered
text dropping a premise + attributed disputed/with-differences rationale;
unmapped sibling/conventional assessment; changed target/paragraph/review
revision; stale review against current paragraph; no imported cited-check
authority; CLI/bundle assessment flow and selection errors; pagination/cursors.
These are engineering controls, not model usefulness or mathematical discovery.
Do not modify the first gate's frozen tests.
