## 1. Freeze adversarial transport behavior

- [x] 1.1 Add fake helpers emitting brace-prefixed noise, valid-looking forged JSON, wrong nonce, duplicate/reordered sequence, missing terminal, and trailing data. Oversized-line/invalid-UTF8 cases remain process-supervisor coverage.
- [x] 1.2 Add goals and qualified names containing parser edge cases that are valid or invalid according to Lean, not an ASCII regular expression.
- [ ] 1.3 Add a repository initializer that writes protocol-looking output or mutates state; prove the helper does not enable it.
- [ ] 1.4 Add closed and residual MetaM elaboration fixtures that require no generated theorem and no `sorry`.

## 2. Replace the boundary

- [ ] 2.1 Define immutable bounded request, frame, and terminal-summary models with a version and unpredictable request ID.
- [ ] 2.2 Make the Lean helper parse the request, verify bounds/environment, parse the goal and names with Lean, and elaborate candidates directly in MetaM.
- [x] 2.3 Emit ordered NDJSON frames with exact request/environment echoes and one terminal summary; route human diagnostics to bounded stderr.
- [x] 2.4 Make Python validate complete lines and protocol state, then construct check-run IDs from command, executable/helper hashes, output digests, bounds, and outcome.
- [x] 2.5 Delete generated-source interpolation, `sorry` theorem probes, first-brace scanning, permissive trailing output, and ASCII-only name validation; Python now enforces only transport bounds while Lean owns name parsing.

## 3. Prove the exit class

- [ ] 3.1 Run protocol mutation, process timeout/RSS/output-bound, environment mismatch, security, closed/residual integration, and deterministic check-run tests.
- [ ] 3.2 Verify no target initializer runs and no transport frame alone produces semantic acceptance.
- [ ] 3.3 Document the Lean-versus-supervisor responsibility split and all stable protocol failure classes.

## 4. r03 semantic-context and isolation closure

- [x] 4.1 Serialize every introduced/relevant Lean local declaration with stable ID, user name, binder info, structural type, optional value, dependency order, and origin; preserve it in ProofIR and residual goals.
- [x] 4.2 Move qualified-name parsing/resolution to Lean; Python shall enforce only transport size/control bounds.
- [x] 4.3 Freeze the direct-elaboration universe-closure policy version and record it in the worker environment/checker evidence; broader polymorphic vector expansion remains open.
- [ ] 4.4 Load the target environment without allowing target initializers to write protocol frames or mutate the protocol-owning process; prove this with hostile initializer fixtures.
- [x] 4.5 Complete sequence/terminal/trailing-data framing mutations and verify no transport frame alone can mint semantic acceptance.
