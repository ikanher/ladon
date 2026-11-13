# Source-audit workflow v1

This is a generic workflow for an auditor given one source passage and a local
Lean capsule. Case diagnoses, supplied development witnesses and evaluation
answers are not part of this recipe. It applies to a bounded source claim;
coverage of the rest of a paper must remain explicit.

1. Verify the capsule/source identities and read necessary definitions and
   surrounding assumptions. Record whether formal crosswalks were supplied.
   Use the local project and pinned toolchain; disclose dependency/cache reuse.
2. List the passage's mathematical claims. Preserve first interpretations,
   quantifiers, parameter domains, normalization, probability laws and objects.
   Record multiple defensible interpretations before checking rather than
   silently selecting the interpretation easiest to prove.
3. Find plausible formal owners using scoped Ladon name/type-text navigation
   and source inspection. Read the actual statement. A lexical hit or a module
   name is navigation evidence. Retain the selected source span and exact
   formal judgment with its context; a valid conditional theorem may expose a
   source obligation without being a false theorem.
4. Choose the smallest relevant question: can the actual context hold, where
   is a premise supplied, or does a source-attributed operation/property follow?
   Preserve lets and fixed assignments. Substitute a claimed formula into its
   defining identity when applicable. A total Lean operation alone does not
   supply the property attributed to it by the source.
5. Inspect retained native dependency evidence for the selected declaration.
   Follow actual proof/source uses when premise supply matters; use scoped
   observations if available and necessary. Keep declaration dependencies,
   source-inspected binder use, native local-term observations and independently
   checked provider terms distinct. Missing routes retain unresolved frontiers.
6. Construct the complete judgment before checking. For a universal refutation,
   either negate the fully closed claim or give an assignment satisfying every
   original premise and violating its conclusion. Check the assignment's domain
   first. Preserve a repair or extra hypothesis as a separate proposed claim.
   A scalar abstraction needs a separately justified realization in the source's
   mathematical setting. Failed search or replay is unresolved evidence.
7. Use ordinary Lean and the existing local Ladon checking interface as needed.
   Inspect current help and record exact effective settings. For a supplied
   candidate, `proof-search check candidate` checks that candidate against its
   stated closed goal in the selected compiled module; it does not discover the
   source interpretation. Retain residuals, axiom/trust reports, tool failures
   and finite resource stops. Do not import answer/helper modules from outside
   the registered auditor input closure.
8. Explain what each result changes for the reader. Distinguish a refuted source
   claim, an unmet source justification, a faithful correspondence, warranted
   abstention and unresolved checking. Record unexamined claims. Freeze the first
   report before seeing reference answers; independent review adjudicates each
   alleged discrepancy and control. Account for preparation, tool use, ordinary
   Lean attempts and review effort, including failures and unavailable telemetry.

This recipe promises bounded evidence with explicit authority limits. It cannot
certify a natural-language interpretation or guarantee error discovery. Its
evaluation must measure useful findings and costs against the same LLM using
ordinary Lean and the same mathematical recipe.
