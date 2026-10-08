# Audit a proof passage, not just its conclusion

A Lean proof of the final theorem can coexist with a false intermediate argument, a missing informal existence assumption, or a valid alternative proof. Ladon's correspondence workflow keeps those questions separate. Ordinary Markdown/TeX, named Lean obligations, and compiler/axiom output are sufficient; a Ladon command or model account is not required.

Start from an unchanged source passage and its proposed formal counterpart. State the exact local assertion in its original context, inspect or check that assertion, and propose a small revision. Keep a failed attempt separate from a checked counterexample. Label added assumptions as narrowing, and read proof source before claiming that a particular argument was translated.

The [r70 exercised recipe](../openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/AUDIT_RECIPE.md) provides concrete commands and evidence:

| Boundary | Development case |
|---|---|
| Wrong step, true final theorem | A polynomial's false factorization is refuted at zero; a different correct factorization proves the original inequality. |
| Total default, missing existence | An empty natural-number set has a formal `sInf` default; later algebra does not establish membership or existence. |
| Valid proof, different method | Direct symmetry and spectral diagonalization both prove nonnegative trace, but their proof strategies differ. |
| Changed estimate, open implication | A pinned inverse-estimate declaration requests five additional derivatives while the cited paper asserts four. The stronger guarantee remains an unresolved formal connection, not a refuted theorem. |

The [findings and proposed corrections](../openspec/changes/ladon-proof-correspondence-audit-umbrella/evidence/r70/README.md) retain original sources, new checks, failed attempts, authorship and adoption status. These are known published examples with authored controls, not a blind fidelity-detection benchmark. No general reader-benefit claim follows.

Use existing [assessment and exposition mechanisms](RESULT_EXPOSITION.md) when a revision-bound companion helps a real reader. They display attributed reviews; they do not automatically discover semantic discrepancies. [Source-goal completion](SOURCE_GOAL_COMPLETION.md) remains optional when an application must be tied to its captured original goal. It does not by itself verify the meaning or strategy of an informal argument.

The governing motivation remains [precise exposition and honest informal/formal correlation](../openspec/changes/ladon-result-understanding-and-release-umbrella/sources.md), supporting mathematics that readers can understand, question and reuse. The r70 investigation closes with the existing tools and its explicit unresolved scope. Further interface expansion needs an actual missing operation or failure; another known example is not automatically the next milestone.
