# Spec Delta

## Purpose

Expose checked contradictions among the declared hypotheses of a selected compiled Lean theorem so readers can identify vacuous implications.

## ADDED Requirements

### Requirement: Exact declaration selection

The feasibility command SHALL check one explicitly named compiled theorem in a selected module under a pinned Lean toolchain. It SHALL resolve the exact declaration name and verify module ownership. Results SHALL identify the declaration, module, and compiled inputs used for the check.

#### Scenario: Root namespace theorem

- **WHEN** the user selects `silly_theorem` in its owning module
- **THEN** the command accepts the root-namespace name and checks that exact theorem

#### Scenario: Visible declaration from another module

- **WHEN** the selected module imports the named declaration but does not own it
- **THEN** the command reports an invalid selection and issues no feasibility verdict

### Requirement: Joint premise closure

The command SHALL form a closed proposition from the outer binders of the compiled type. It SHALL existentially quantify non-proof parameters over their Lean domains, quantify proofs used by later binder types, and conjoin the remaining proof hypotheses. Replay SHALL have no ambient assumption of the tested premises. The conclusion and proof-local hypotheses are outside the check. A telescope that cannot be closed faithfully SHALL yield `unresolved`.

#### Scenario: Contradictory equality premises

- **WHEN** the declaration's telescope consists of `n : Nat`, `n = 0`, and `n = 1`
- **THEN** its feasibility proposition is definitionally equal to `∃ n : Nat, n = 0 ∧ n = 1` regardless of the original conclusion or proof

#### Scenario: Negation as a conclusion

- **WHEN** the compiled declaration is `theorem negFalse : ¬ False := fun h => h` and its type has no outer function binder before unfolding `Not`
- **THEN** its premise proposition is `True` and the declaration receives no inconsistency finding
- **AND** the separately compiled declaration `theorem explicitArrow : False → False := fun h => h` has one outer proof binder and the premise proposition `False`

#### Scenario: Proposition parameter independent of the hypothesis

- **WHEN** the declaration has a parameter `P : Prop`, a proof hypothesis `h : BadStructure` with `BadStructure : Prop`, and conclusion `P`
- **THEN** the feasibility proposition is definitionally equal to `∃ _ : Prop, BadStructure`

#### Scenario: Hypothesis depends on the proposition parameter

- **WHEN** the declaration has a parameter `P : Prop` followed by a proof hypothesis `h : P`
- **THEN** the feasibility proposition retains that dependency as `∃ P : Prop, P`

#### Scenario: Ordinary data parameters in the joint premise

- **WHEN** a theorem has `b : Bool` and `h : False`, even if the theorem never uses `b`
- **THEN** its premise is definitionally equal to `∃ _ : Bool, False` and the command reports `inconsistent` after replay
- **AND** for `(α : Type) (x : α) (h : False)` the premise retains the dependent domain as `∃ α : Type, ∃ _ : α, False`

#### Scenario: Premises behind a transparent alias

- **WHEN** there is a transparent chain of aliases for an implication with premise `False`
- **THEN** the command extracts the premise and reports `inconsistent` after replay
- **AND** an alias for `¬ False` retains premise `True`

#### Scenario: Dependent assumption

- **WHEN** a theorem has `h : False` and a witness of a type `Receipt h`
- **THEN** its joint premise is definitionally equal to `∃ h : False, ∃ _ : Receipt h, True` and replay accepts its refutation
- **AND** a satisfiable theorem with a proof-dependent witness receives `unresolved`

### Requirement: Automatically checked refutation

The command SHALL attempt refutation using elementary propositional implications, linear natural-number and integer constraints, and facts reachable by bounded structure projection from proof hypotheses or data witnesses, without a caller-supplied proof. It SHALL report `inconsistent` only after independent Lean replay verifies a closed proof of the exact negated feasibility proposition under the declared transitive axiom policy, with no dependency on the theorem under review.

#### Scenario: Contradictory natural-number assumptions

- **WHEN** the command checks the compiled `silly_theorem` with `n = 0` and `n = 1` and conclusion `2 + 2 = 5`
- **THEN** it reports `inconsistent` automatically, identifies the premise proposition, and provides a successful replay and trust receipt

#### Scenario: Contradiction exposed by a structure field

- **WHEN** the command checks the compiled `prove_anything` with `P : Prop` and `h : BadStructure`, where `BadStructure` has a direct projection of type `BadStructure → False`
- **THEN** it discovers the projection without a supplied proof or field name and reports `inconsistent` with a successful replay and trust receipt for the exact closure
- **AND** renaming the field or replacing the original conclusion and proof while retaining the same premises preserves the verdict

#### Scenario: Elementary propositional contradictions

- **WHEN** the assumptions include proofs of `P` and `¬ P`, or proofs of `P`, `P → Q` and `¬ Q`, for proposition parameters `P` and `Q` as applicable
- **THEN** each declaration receives `inconsistent` with accepted replay and trust, regardless of hypothesis order
- **AND** the satisfiable context `P → Q`, `¬ Q` receives `unresolved`

#### Scenario: Linear arithmetic over more than one premise

- **WHEN** the premises require `z < 0` and `0 ≤ z` for an integer `z`, or require `a < b`, `b ≤ c` and `c ≤ a` for natural numbers
- **THEN** each declaration receives `inconsistent` with accepted replay and trust
- **AND** a satisfiable integer interval receives `unresolved`

#### Scenario: Nested structures and data witnesses

- **WHEN** a proof hypothesis contains a structure field whose own field supplies `False`, or a data witness belongs to a structure declared in `Type` with a proof field of type `False`
- **THEN** the command reports `inconsistent` with accepted replay and trust for each declaration
- **AND** an inhabited wrapper whose inner proof field supplies `True` receives `unresolved`

#### Scenario: Arithmetic from fields of one witness

- **WHEN** the premises are `n : Nat` and `h : Bounds n`, whose fields prove `n < 2` and `n > 5`
- **THEN** the command reports `inconsistent` with an accepted refutation of `∃ n : Nat, Bounds n`
- **AND** compatible bounds from a single witness receive `unresolved`

#### Scenario: Implication results supply new fields

- **WHEN** a proof of `P` and a proof of `P → Wrap` are premises, and a nested field of `Wrap` proves `False`
- **THEN** the command reports `inconsistent` with accepted replay and trust
- **AND** a result of type `Q ∧ ¬ Q` can also supply both facts to the search

#### Scenario: Arithmetic proves an implication antecedent

- **WHEN** the premises include `n : Nat`, `n = 0`, and `n < 1 → False`
- **THEN** the command reports `inconsistent` with accepted replay and trust
- **AND** compatible bounds from structure fields can together establish an antecedent needed to derive `False`
- **AND** when the implication yields a structure whose nested field proves `False`, an antecedent established by arithmetic or in a disjunction branch can enable that projection
- **AND** an uninhabitable structure behind an antecedent that can be false does not by itself establish a contradiction

#### Scenario: Elementary splitting and equality

- **WHEN** the premises include `P ∨ Q`, `¬ P`, and `¬ Q`, a proof of `True → False`, an `Empty` witness, or an equality that transports a positive fact to contradict a negative one
- **THEN** the command reports `inconsistent` with accepted replay and trust for each case
- **AND** a satisfiable disjunction control retains `unresolved`

#### Scenario: Empty recursive inductive witness

- **WHEN** a theorem requires a witness of a recursive type whose only constructor takes a previous witness of the same type
- **THEN** the command constructs an induction refutation and reports `inconsistent` with accepted replay and trust
- **AND** an inhabited recursive type with a base constructor receives `unresolved`

#### Scenario: Infinite descent and negative squares

- **WHEN** the premises require a natural-number sequence to strictly decrease at every step, or an integer self-product to equal a negative integer
- **THEN** the command reports `inconsistent` with accepted replay and trust for each declaration
- **AND** an increasing sequence and a satisfiable self-product equation receive `unresolved`

#### Scenario: Certificate name already exists

- **WHEN** a selected module declares or imports an unrelated theorem named `LadonFeasibility.certificate` and the selected theorem has independently refutable premises
- **THEN** the check succeeds with a fresh certificate name, and replay and trust inspection verify that exact new declaration
- **AND** dependency on the reviewed theorem through a helper still invalidates a certificate in this environment

#### Scenario: A refutation uses the theorem under review indirectly

- **WHEN** a refutation of `∃ _ : Prop, BadStructure` derives `False` through a helper whose proof uses `prove_anything False h`
- **THEN** the checker rejects that evidence even if Lean replays it successfully and reports an empty axiom set

#### Scenario: A refutation has the wrong subject

- **WHEN** a well-typed closed refutation for a different premise proposition is presented for the selected declaration
- **THEN** replay rejects the subject mismatch even if the proof and its reported target agree with each other

#### Scenario: A tactic result cannot be independently verified

- **WHEN** the attempt yields a term with a forbidden axiom, a replay failure, or a mismatched goal or environment
- **THEN** the command reports the reason and withholds an inconsistency finding

### Requirement: Advisory verdict and explicit limits

The command SHALL report `unresolved` with a reason when it establishes no refutation. It SHALL distinguish unsupported inputs, exhausted checks, and operational errors from a checked contradiction. A finding SHALL describe the declared premise context as uninhabitable and preserve the original declaration's validity and ordinary Lean build behavior.

#### Scenario: Legitimate proof by contradiction

- **WHEN** a theorem with a satisfiable declared telescope introduces a temporary contradictory assumption inside its proof, including a theorem with an inhabited structure hypothesis
- **THEN** the command issues no inconsistency finding for the declaration

#### Scenario: Inhabited field mentions False

- **WHEN** a structure hypothesis has a field named `contradiction` of type `False → True` and the other declared premises can hold
- **THEN** the command issues no inconsistency finding

#### Scenario: Resource bound exhausted

- **WHEN** the configured check stops at a resource bound
- **THEN** the result identifies the bound and carries no feasibility verdict beyond `unresolved`

#### Scenario: Bounded projection and implication search

- **WHEN** a projection or propositional search budget interrupts the check before it establishes a refutation
- **THEN** the command returns exit 1 with `unresolved` and identifies the exhausted bound

#### Scenario: An automation caller requires a conclusive result

- **WHEN** the caller passes `--fail-on-unresolved` and the search finishes without a checked contradiction
- **THEN** the command retains the `unresolved` status and reason and exits with code 1
