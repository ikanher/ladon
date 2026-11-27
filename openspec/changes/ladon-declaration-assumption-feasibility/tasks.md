# Tasks

## 1. Replay an automatic refutation of the exact premise closure

- [x] 1.1 Copy the two acceptance declarations from [design.md](design.md#acceptance-fixtures-lean-4321) into the pinned Lean fixtures. Add an inhabited arithmetic case, a proposition parameter with a dependent hypothesis `h : P`, an inhabited structure used in a legitimate proof by contradiction, and an unsupported proof-dependent binder. Verify ordinary compilation and compare the generated closures with independently elaborated expected types. Include the case where the same impossible premises lead to a trivially true conclusion. Check the distinct expected closures of the negation and explicit-arrow fixtures against the compiled binder shapes. Exercise a truncated binder prefix and verify the check abstains.
- [x] 1.2 Qualify the automatic arithmetic route on the generated `silly_theorem` premise goal using native auxiliary transfer, independent replay, and the standard axiom audit. Require an accepted closed refutation without a supplied term. If auxiliary replay still fails, fix the scoped replay issue or qualify a fixed general alternative before wiring the public verdict.
- [x] 1.3 Qualify bounded projection to `False` on the generated `prove_anything` premise goal and on the renamed-field and different-proof controls. Require independent replay and axiom acceptance with no supplied term. Verify the inhabited structure and `h : P` controls receive no inconsistency verdict, and exercise the inhabited field named `contradiction : False → True`.

- [x] 1.4 Verify replay checks the exact subject and independence for both routes. Inject a valid certificate paired with its own matching but wrong target, and a certificate that uses an axiom-free forwarding helper calling the reviewed theorem. Both must fail evidence acceptance. Exercise forbidden axioms, incomplete dependency traversal, and changed compiled inputs. Require both original certificates to pass with their own exact subjects.

## 2. Expose the theorem-level advisory

- [x] 2.1 Wire `ladon theorem feasibility` to exact compiled declaration selection and both checked routes. Verify the two root-namespace user theorems report `inconsistent`, imported owners fail exact selection, and the inhabited controls report `unresolved`. Check unsupported hypotheses, stale or mismatched inputs, resource exhaustion, and an untrusted proof through the relevant seams. Assert text and JSON communicate the same assessment and exercise the documented exit classes for completed checks, invalid selections and operational stops.
- [x] 2.2 Document the command, pinned environment, supported telescope and advisory result in the CLI reference. Run the documented command against both built user fixtures and run the affected theorem CLI and completion/replay regression tests. Confirm ordinary Lean builds still accept both examples.

## 3. Generalize refutation and replay after review

- [x] 3.1 Add bounded propositional reasoning. Exercise complementary hypotheses and an implication chain in different binder orders, plus a satisfiable near miss and an exhausted search. Require independently replayed findings through the public CLI.
- [x] 3.2 Generalize existential closure over data domains and pass integer constraints to the arithmetic route. Check the exact closures of the Boolean and dependent-type fixtures, retain the unsupported proof-dependency control, and exercise contradictory and satisfiable integer bounds. Keep the natural-number cycle, parity contradiction and inhabited control as regressions.
- [x] 3.3 Derive and reuse facts through bounded structure projection from both proof hypotheses and data witnesses. Verify the nested wrapper, the structure in `Type`, and incompatible bounds on one witness. Check inhabited analogues, renamed fields, and a traversal stopped by its bound. Update CLI coverage and limit documentation for the expanded search.
- [x] 3.4 Make the certificate name fresh and use it throughout replay and trust inspection. Exercise a pre-existing `LadonFeasibility.certificate`, generated auxiliaries, and an indirect dependency on the reviewed theorem in the colliding environment. Run the new cases, both original examples and the existing replay rejection tests through their respective entry points.

## 4. Combine the refutation techniques

- [x] 4.1 Feed implication results into bounded projection and return projected facts to implication search. Provide conditional field proofs to the fallback for implications whose antecedents can be established during arithmetic or case analysis. Exercise nested fields, derived conjunctions, and an exhausted projection budget.
- [x] 4.2 Exercise bounded Lean proof search with direct and projected arithmetic antecedents, `True → False`, `Empty`, disjunctions, and equality. Verify satisfiable controls, original routes, and replay and trust regressions. Document the fallback and its bounds.

## 5. Cover the vacuity challenge

- [x] 5.1 Extract premises through bounded transparent aliases and quantify proof-dependent witnesses. Check the exact closures and replay the missed cases. Use an aliased negation and a satisfiable dependent premise as controls.
- [x] 5.2 Refute the empty recursive witness, impossible natural-number descent, and negative integer self-product through the public CLI. Run each against its satisfiable counterpart and require independent replay and trust for each finding.
- [x] 5.3 Add and document the fail-on-unresolved exit policy. Run the existing bounded search, replay, CLI, and trust regressions alongside the new cases.

## Verification of the initial implementation (tasks 1–2)

- [Feasibility integration tests](../../../tests/test_theorem_feasibility.py) and [pinned Lean checks](../../../tests/fixtures/theorem_feasibility/FeasibilityChecks.lean) passed. The full feasibility run passed 24 tests, and a subsequent targeted run passed the native closure and additional auxiliary transfer tests.
- The installed theorem CLI, lineage CLI, and source-goal completion workflow, CLI contract, and generated-auxiliary regression tests passed all 31 cases.
- Both documented CLI checks reported `inconsistent` with accepted replay on Lean 4.32.1. The same two checks passed with explicit executables pinned to Lean 4.36.0.
- Strict OpenSpec validation, Ruff, and the static quality checks passed. The full repository pytest run was stopped after 568 passes.

## Verification of the follow-up (task 3)

- The two initial regression tests reproduced the missed propositional contradiction and the certificate name collision. The expanded [feasibility suite](../../../tests/test_theorem_feasibility.py) passed all 45 cases. A targeted rerun passed the final inhabited wrapper control and the additional occupied-name certificate rejection test.
- The installed theorem CLI, lineage CLI, and source-goal completion workflow, CLI contract, and generated-auxiliary regression tests passed all 31 cases.
- The public CLI independently replayed implication, integer, projected arithmetic, and universe-polymorphic witness cases with explicit pinned Lean 4.36.0 executables. The fixture suite uses Lean 4.32.1.
- Repository-wide static quality checks, Ruff, Python compilation, and strict OpenSpec validation passed.

## Verification of the combined search (task 4)

- The original missed composition cases and the follow-up arithmetic and disjunction wrapper cases reproduced as `unresolved` before their changes. All seven contradictory review cases now receive accepted replay and trust. The new cases also cover arithmetic from projected facts, structure results enabled by arithmetic or case splitting, satisfiable controls, and projection exhaustion.
- All 60 cases in the [feasibility integration suite](../../../tests/test_theorem_feasibility.py) and all 31 adjacent theorem CLI, lineage, and source-goal completion regressions passed. The 91 cases ran across five isolated pytest groups on the final worker.
- Lean 4.36.0 independently replayed the derived-structure projection, arithmetic-to-wrapper, disjunction-to-wrapper, and equality-transport cases through the installed CLI. The full fixture suite uses Lean 4.32.1.
- Repository-wide static quality checks, Ruff, Python compilation, and strict OpenSpec validation passed.

## Verification of the vacuity challenge (task 5)

- The five challenge regressions reproduced as `unresolved` before the changes. All five original scratch declarations now report `inconsistent` with accepted replay and trust on Lean 4.32.1. The five corresponding fixture patterns also passed through the installed CLI on Lean 4.36.0.
- The checker accepted replay after 64 transparent head reductions. An otherwise equivalent statement at 65 reductions returned exit 1 with `premise-unfold-limit`.
- The [feasibility suite](../../../tests/test_theorem_feasibility.py) passed all 71 cases, including the satisfiable controls and `--fail-on-unresolved`. All 31 adjacent CLI, lineage, and source-goal completion regressions passed. The 102 cases ran across five isolated pytest groups on the final implementation.
- Repository-wide static quality checks, Ruff, Python compilation, and strict OpenSpec validation passed.
