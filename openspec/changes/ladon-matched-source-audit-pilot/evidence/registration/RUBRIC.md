# Blind adjudication rubric

Adjudicators receive anonymized first reports and their cited source/Lean
evidence, with arm labels, Ladon-specific prompt text, and run-directory names
removed where practical. They do not receive the other adjudicator's ratings
before submitting their own. The registered unit manifest may be consulted for
mapping a reported claim to the preregistered score population, but contains no
correctness labels.

For each alleged finding or other scored claim, record:

- **Identity:** exact source span, interpreted assertion, and corresponding
  declaration or an explicit unresolved mapping.
- **Judgment:** upheld discrepancy, supported/faithful correspondence,
  ambiguous/underspecified (abstention warranted), unsupported allegation,
  unresolved, or outside the registered six-unit population.
- **Evidence:** source, Lean type/definition/proof, assumptions, domains and
  quantifiers considered; reproduce only bounded local checks needed for the
  judgment and record their exact commands/results.
- **Usefulness:** whether the result changes what a reader may conclude about
  the mathematical assertion or the described argument, and why. A name or
  representation difference alone is not useful.
- **False-accusation severity:** none, minor, material, or serious. Serious
  means the allegation incorrectly says a central claim or a necessary proof
  step is false/unsupported in a way likely to mislead the reader about the
  mathematical result. State the reason; do not infer severity from tone.
- **Confidence and unresolved questions.**

An upheld useful finding requires both a source/formal discrepancy and a
specific reader consequence. A failed tactic, missing search hit, or source
name mismatch does not qualify. A method mismatch is separate from a statement
error. A proposal that changes assumptions or weakens a conclusion is not
evidence for the original claim.

For each of the six preregistered source claims, adjudicators also record
whether an arm's treatment is a correct correspondence/control, warranted
abstention, unsupported accusation, or no treatment. Claims outside the six
are retained as exploratory outcomes and cannot satisfy the primary gate.

Two independent ratings are required. Any disagreement on judgment, usefulness,
or severity remains unresolved in the primary analysis; report both rationales
without resolving by arm identity. Unresolved items earn neither finding nor
false-accusation credit. Unblind arm labels only after both signed rating files
and their hashes are frozen.
