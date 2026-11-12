# Design

## Context

src/ladon/correspondence_check.py generates implication obligations under interpreted assumptions. src/ladon/source_goal_completion.py checks exact goals and allows only Classical.choice, Quot.sound and propext. Neither establishes joint inhabitance of a selected hypothesis context.

## Goals / Non-Goals

**Goals:** construct correct independent context-feasibility goals and retain their evidence separately.
**Non-goals:** decide all consistency problems, reject every conditional statement, remove useful hypotheses, or infer feasibility from lack of a contradiction.

## Decisions

### Proof-position selection

Bind selection to source digest, file, syntax span/position, goal ordinal and owner-qualified local identities through existing native source-goal capture. The declaration name is a locator, not a substitute for the local context at that position. Preserve the complete selected data, hypotheses and let declarations with their transitive type/value dependencies. Unsupported proof-dependent data remain explicit rather than being silently dropped.

Acceptance must select two positions inside one proof where assumptions or derived aliases differ, and distinguish same-name locals in sibling branches. A fixed assignment is applied through the request to the same captured context; testing separate theorems containing different literals does not qualify assignment binding. The declaration-only prototype is supporting evidence for goal construction, not acceptance of proof-position coverage.

### Telescope closure and contamination prevention

The initial profile accepts a finite typed data telescope and Prop hypotheses whose dependencies can be closed safely in the existing Lean expression/context machinery. Start with Nat/Int/Rat examples; opaque or unsupported proof-dependent data remain residuals. Represent the complete selected context as an existential closure S = ∃ data, H1 ∧ ... ∧ Hn. A witness proves S; an inconsistency certificate proves ¬S. Preserve dependent data ordering where supported; never flatten proof-dependent types into unrelated independent variables.

All selected theorem parameters are existentially closed unless the caller explicitly selects fixed values. Fixed parameter assignments and their exact bindings are part of subject identity. Uniform feasibility over external parameters is outside the initial profile. Any retained ambient hypotheses make the finding conditional and must be shown as an outer context; the initial decisive profile requires that outer proof context to be empty.

Witness construction runs in a fresh goal without H or proof/local-value aliases derived from H. Definitions and imports are retained under the standard axiom check. The contradiction goal introduces H only inside its own negated existential proof. Use expression identities and dependency closure, not rendered-name filtering.

The invariant is inhabitance of the context with all admitted dependencies preserved. The conjunction presentation is valid only within the supported profile. A let-bound value must retain its defining relation or substitution: replacing `k := n + 1` with an independent existential k changes the question. Validate the actual replayed closed target so ordinary completion cannot turn an intended independent S or ¬S into H → S or H → ¬S. Report existential success as “some assignment satisfies these premises,” and show fixed assignments explicitly; do not imply uniform feasibility over external parameters.

### Evidence and automation

Expose plan/check operations consumable by the umbrella audit stage. Result dimensions include context subject, parameter policy, witness status, contradiction status, source role and coverage. Here `witnessed` and `inconsistent` concern the exact existential closure of the selected context. A checked implication such as `False → True` cannot witness its premise context, and a theorem `∀ n, ∃ k, k = n` does not test the fixed-assignment request API. Supported decisive statuses are witnessed and inconsistent; unsupported, not-run, unresolved and resource-stop are separate. Conflicting accepted receipts for the same context are evidence-integrity failures.

Use existing completion/replay for caller-supplied terms and the fixed bounded tactic repertoire from the baseline for optional automated attempts. Neither mode changes the source formula. A contradiction certificate reports an impossible context, while source review determines whether that context was intentionally hypothetical or improperly introduced.

### Reuse and bounds

Extend typed-context preparation and exact source-goal machinery rather than proving propositions in Python. Context planning is bounded to 64 binders, 128 selected hypotheses and existing expression byte/depth limits in the first profile. Allow lower caller limits. The parent deadline and 12 GiB default remain authoritative; no per-obligation deadline reset. Task 2.1a owns the known tactic-auxiliary replay regression. Resolve it through existing completion or qualify a general automatic alternative from the predeclared repertoire on the same generated goal. Supplied manual proof terms remain validation-only. A repertoire change after baseline freeze requires a separately identified matched comparison; it cannot silently improve only the enhanced arm.

## Risks / Trade-offs

- [Dependent telescope or alias contaminates the witness] → mandatory adversarial red tests for leaked hypotheses, derived let values, ambient sections and fixed parameters.
- [New goal cannot be reconstructed faithfully] → first run a bounded four-fixture Lean feasibility check (inhabited, contradictory, alias-contaminated, unsupported dependent), at most 600 seconds total and 12 GiB. Stop with retained residuals if exact closure fails; do not substitute displayed text.
- [Witness existence mistaken for universal feasibility] → report selected assignment and parameter policy prominently.
- [Tactic-generated proof depends on an auxiliary declaration absent from replay] → retain the failed candidate as unresolved; only independent successful replay can support a feasibility verdict. The [native experiment](evidence/native-probe/README.md) observed this with an `omega` refutation while a direct equality proof of the same goal passed.

## Migration Plan

Add a distinct versioned diagnostic receipt. Do not alter historical parentSupport or interpret old receipts as feasibility checks. Wire stage execution only after checker and mutation tests pass.

