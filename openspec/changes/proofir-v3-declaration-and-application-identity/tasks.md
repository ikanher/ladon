## 1. Pin the unsound cases

- [x] 1.1 Add two same-environment declarations with identical types and different qualified names; prove their declaration IDs differ while statement/type fingerprints may match.
- [x] 1.2 Add an attachment adversary whose requested name differs but environment and type fingerprint match; require rejection from every exact tier.
- [x] 1.3 Add residual and closed candidate cases; require residual acceptance to target an application/step subject and the goal statement to remain `unchecked`.

## 2. Split the identities

- [x] 2.1 Define typed declaration, statement/type, optional value/proof, and candidate-application subjects with environment-scoped schemes.
- [x] 2.2 Update the Lean/Python worker boundary to emit qualified declaration references separately from structural expression fingerprints.
- [x] 2.3 Update attachment policy ordering and retain all competitors plus the versioned decision method.
- [x] 2.4 Update check-run construction, SQLite projection, and query rendering so accepted results attach only to the checked subject.
- [x] 2.5 Delete fingerprint-as-declaration and result-by-guarantee-prose compatibility logic.

## 3. Prove the exit class

- [x] 3.1 Run identity collision, attachment adversary, worker residual/closed, SQLite foreign-key, and dossier rendering tests.
- [x] 3.2 Rebuild fixtures and verify explicit references replace all semantic joins based on local string equality.
- [x] 3.3 Document which identity is exact, searchable, optional, or checker-observed.

## 4. r03 reopening: context-complete application identity

- [x] 4.1 Add collision vectors with identical environment/rule/conclusion/residuals but different ordered substitutions or local contexts; require distinct application and step identities.
- [ ] 4.2 Define a typed local-context subject containing ordered local IDs, binder names/info, structural types, optional values, dependencies, and origin (`goal-introduced`, caller, synthesized, generated).
- [ ] 4.3 Make the Lean helper emit introduced binders and relevant local hypotheses; make Python validate and preserve non-empty contexts instead of rejecting them.
- [x] 4.4 Hash environment, exact declaration, conclusion, ordered substitutions, ordered residuals, and local-context reference under one versioned candidate-application scheme; include substitutions wherever step identity requires them.
- [x] 4.5 Add closed polymorphic and residual-context replay vectors; correct the closed-derivation limitation so it claims only that no residual premise remains.
