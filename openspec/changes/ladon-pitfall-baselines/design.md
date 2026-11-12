# Design

## Context

The seven focused correspondence tests rerun during the initial inspection passed (397.00 seconds); they exercise existing safeguards, not a complete pitfall benchmark. src/ladon/_contract_evaluation_registration.py fixes legacy registration at 24 A and 12 B cases with C blocked. Reusing that registration for this new 24-case population would change its contract.

## Goals / Non-Goals

**Goals:** establish each child’s family baseline before its runtime changes, preserve one original runtime and common policy, and deliver reusable red tests and fair full-corpus comparisons.
**Non-goals:** claim blindness for article-derived examples, replace the legacy evaluation population, count agent output labels as checked evidence, or require an expensive paper run.

## Decisions

### Fixed 24-case corpus

Create six families, each with two faults and two faithful controls:
1. Domains and quantifier order, including a checked representation bridge.
2. Joint assumption feasibility: contradictory equalities and an impossible domain; inhabited and legitimate contradiction-branch controls.
3. Premise provenance: direct and class-wrapped supplied conclusions absent from the claimed source assumptions; explicit conditional and independently proved provider controls.
4. Existence/defaults: empty-set minimum/infimum and an unsatisfied selector property; nonempty selection and intentional default controls.
5. Operation semantics: truncated subtraction transported to integers without its guard and a second algebraic identity falsely asserted without its required guard; correctly guarded and correctly typed controls.
6. Claim/trust integrity: silent hypothesis strengthening and an admitted/custom-axiom dependency; unchanged-goal and standard-axiom controls.

Every case has original prose, explicit interpretation, actual pinned Lean source, exact intended judgment dimensions and independent evidence. Additional resource/schema mutations belong to engineering tests, outside these 24 case denominators. The second selector case may use a simple total fallback definition; adapter support remains constrained to an explicit typed selection property, not arbitrary function analysis.

### Case construction and review boundary

Construct each case as a prose/formal pair before assigning its expected role. The case record binds the original quote and source span/digest, a typed interpretation with quantifiers and assumptions, the actual formal declaration/application and context, and the exact comparison obligation. Record the expected judgment dimension, evidence needed to justify it, and its limitations. Repeating the quote in an `interpretation` string or saying “compile and inspect axioms” does not supply this information.

A formal counterpart and a certificate refuting the prose are different subjects. For example, a pointwise formal theorem can be the proposed support for a uniform reading; a separate theorem proving the uniform reading false is an oracle. Do not substitute that oracle for the formalization under audit. Faults may be statement mismatches, unjustified premises, violated selected-value properties or trust-policy failures; the record must say which. A valid conditional is a control when the original prose states its premise, even if the conclusion is supplied by that premise.

Use distinct mathematical/source comparisons, not new names for the same proof, to fill the six families. The required operation cases must use the actual operation: proving that a false predicate has no witness does not test natural-set infimum behavior. Pin the Mathlib environment needed for `sInf`, including imports and compiled dependencies, alongside the Lean version; the current Lean-only prototype is insufficient for that case. A default selector takes a predicate on its selected values, and the obligation mentions the returned value and that predicate explicitly.

Keep oracle certificates and expected labels outside modules and inputs accessible to unsupplied proof search. Trusted counterpart code may be supplied; correctness certificates for the generated comparison goals must not become available by importing a combined fixture. Preserve prototype revisions before repairing them. Obtain review of the final prose, typed meanings, formal counterparts, oracle evidence and role counts at exact digests. Renaming or correcting an already-reviewed input invalidates that input's prior review binding.

### Lessons from corpus review

The current implementation findings and completion status live in [tasks.md](tasks.md). The earlier independent acceptance verified several pairings and hashes but missed requirement coverage. A revised review must map each promised behavior to the actual selected declaration: a bound on `Fin.val` does not establish construction/value preservation, and subtraction by zero does not exercise an explicit order guard.

Record the source interpretation, formal subject, comparison goal and validation certificate as separate identities. Identify declaration kind explicitly. A `def X : Prop := ...` can encode a well-typed claim without proving it; neither compilation nor an empty axiom inventory of that definition establishes `X`. A theorem computing a counterexample is evidence about the claim and must not silently replace it as the subject. Evidence expectations must specify the judgment dimension (fidelity, feasibility, premise provenance, operation property or trust), its supporting goal and its limits.

Each manifest row carries a versioned `comparisonGoal` identity with explicit source and formal claims plus an obligation description. The goal must be checked against the actual declaration type and context; prose similarity or a row ID alone is not a generated-goal binding.

Operational isolation is a module and dependency property. Removing `oracleSource` from JSON or renaming a theorem is insufficient while its proof or equivalent helper remains importable. Build per-case operational inputs containing the permitted counterpart code and its reviewed dependencies; put answer certificates and labels in validation-only inputs. Prevent one case's validation/control certificates from supplying another case's search answer. Verify both the positive validation path and the absence of answer declarations and files from the operational environment before freeze.

Fixture qualification must exercise the actual documented entry point and imports. Direct compilation of an external source file from a donor project proves only that execution in that environment. Record the Lean binary, package revisions/dirty bytes and imported artifacts actually used; reconstruct them in the preserved fixture, and capture command exit status along with stdout/stderr and per-declaration axiom observations. Do not infer success from the presence of axiom output after an earlier compiler error.

### Semantic review and isolation diagnostics

A content hash authenticates which bytes were reviewed; it does not prove that a formula expresses its quoted prose. Review the quantifiers, domains and assumptions along the complete quote → selected interpretation → formal subject → comparison obligation → evidence chain. Include a deliberate quantifier-order mutation with unchanged quote/span identifiers and require review/scoring to reject it. After declaration moves, resolve named expected-evidence helpers and certificates in their current namespaces; source/goal locators alone do not validate evidence descriptions.

Negative import checks require a diagnostic establishing that the requested forbidden module cannot be resolved. Memory stops, killed processes, unrelated compiler errors and failed dependencies provide no such evidence. Retain the diagnostic and return code; qualification includes both an unrelated-failure injection that must not pass and a deliberately exposed forbidden module that must fail isolation. The positive control must execute in the same environment.

The current isolation helper copies existing `.olean` files into temporary directories and imports them. It does not rebuild or authenticate them against source bytes, and it returns after deleting its temporary directory. Source-to-artifact custody belongs to 1.1; the actual operational invocation must be qualified under 1.3 while its restricted paths remain alive. Persist the complete source/artifact/dependency inventory and immutable completed receipts; only publish their hashes for review after the producing command is terminal. Make the corpus acceptance index authoritative rather than inferring acceptance from inconsistent mutable status fields and old review prose.

### Staged family baseline before implementation

Freeze the common 24-case population, judgment dimensions, family command/tactic repertoire, preparation rules, ordering, scoring rubric and budgets before the first family run or production semantic edit. The first accepted batch is the four feasibility cases. Provenance uses its four cases; operation-definedness uses both existence/defaults and operation-semantics families (eight cases). The remaining domains/quantifiers and claim/trust cases remain required in the full baseline and final comparison.

Task 1.4 owns per-child acceptance. Each batch must satisfy runtime reconstruction, source/artifact freshness, exact goal/evidence binding, live operational isolation and independent review for its own cases. Record every case, including unsupported and resource-stop outcomes. A versioned per-case record plus independently reviewed application of the frozen scoring rubric suffices for this unlock; implementing the full automated scorer is not a prerequisite. The validated scorer later consumes these same immutable records and must agree with the reviewed judgments or retain an explicit adjudication discrepancy. It must never rewrite first reports.

Every batch executes the same preserved pre-change runtime, including batches measured after sibling implementation begins. Never substitute the developing checkout or alter tactics, expectations or budgets in response to results. A policy change creates a separately identified comparison and cannot be mixed into the registered one. The full scorer, all 24 baseline cases and matched enhanced evaluation remain mandatory before final acceptance. This changes execution order, not population, evidence standards or improvement thresholds.

### Registration and later runner qualification

Task 1.3d freezes the six-family evaluation configuration: exact input mappings, judgment dimensions, baseline command repertoire or bounded capability probes, preparation policy, ordering, budgets and scoring rubrics. Later batch harness implementation and environment qualification belong to Tasks 1.4/2.2. They must implement the registered protocol and bind their runner bytes before execution; they cannot introduce new tactics or reinterpret results under the original comparison identity. Completing every later runner is not a prerequisite for feasibility implementation once its own baseline, common registration, shared contract and child controls are accepted.

The [common-registration audit](evidence/COMMON-REGISTRATION-AUDIT.md) correctly observes that the current host accepts only feasibility cases and the worker accepts only module/proposition inputs. Its instruction to implement all remaining profiles before closing Task 1.3d is superseded by this clarification. Additional baseline harnesses may transport and record existing runtime capabilities; new context closure, provenance reasoning and operation adapters belong to the enhanced children. A registered, qualified capability probe can establish that the original runtime lacks a requested diagnostic. Such a result remains unsupported/unresolved with no detection or justified-control credit; a nonexistent command, malformed input, missing dependency or unqualified harness cannot stand in for that probe. Capability absence must be independently supported for the exact subject and runtime, not inferred merely from the feasibility runner's narrow interface.

The accepted common registration was written after r18/r19. It binds those historical reports and records compatibility without claiming that the missing common configuration was preregistered. Changed inputs, tactics, rubrics or budgets require a separate comparison identity. Registration does not confer acceptance on an unrun family.

#### Post-acceptance correction for proposition-valued definitions

The independent [v3 profile audit](evidence/common-registration-profile-audit-v3.md) found that the pending existence/default and operation-semantics templates retain unbound source positions, and that `source-goal-probe-v1` observes tactic goals rather than declaration types. Several selected subjects are `def subject : Prop := ...`; a source-goal capture at those declarations does not observe a proof goal for `subject`. The other pending theorem cases also lack registered positions and goal/context bindings. Therefore neither family may run or receive scores under v3. Keep v3 and the already accepted feasibility and provenance records immutable.

Before Task 1.4 proceeds, a separately versioned correction must bind the exact proposition queried for each case, generated query source bytes/digest and position, polarity, imported case artifact, preserved runtime/toolchain, fixed tactic, and terminal interpretation. Generated wrapper theorems may be used only if an unscored feasibility probe confirms that capture returns the selected proposition under the preserved runtime and operational isolation excludes validation evidence. A failed positive or negative proof attempt is unresolved; fault credit requires a checked proof of the negation or another registered counterexample check. The adapter probe is harness qualification, not a scored baseline result.

The adapter must distinguish declaration kinds. For `def subject : Prop := P`, the proposition is the definition's value, which may be referenced as `subject`. For a theorem `subject (a b : Nat) (h : b ≤ a) : a - b + b = a`, the proposition is its fully quantified type, `∀ a b : Nat, b ≤ a → a - b + b = a`; the theorem constant is a proof and cannot itself be used as a proposition. Preserve binder order, dependent types, instances, quantifiers and original premises. Bind elaborated goal/context evidence to the selected subject; a matching query-file digest alone cannot establish this semantic relation. Generated sources must not introduce a repair premise or make a query's own admitted proof available to completion. Query construction transports supplied interpretations; operation reasoning and new semantic detectors remain enhanced-arm work.

The v3 existence profile also incorrectly names `lean-core` executables. The frozen core fixture pins Lean 4.32.1; the existence fixture pins Lean 4.33.0 with Mathlib. The successor must select `lean-core` for operation-semantics and `lean-mathlib` for existence-defaults, with the matching preserved library/artifact closure, Lean and Lake executables. Qualify at least one known-goal control in each environment before implementing the full batch harness. Toolchain mismatch or unavailable imports are qualification failures, not mathematical unknowns.

Freeze polarity ordering and exact fixed candidate policy before any scored attempt. Preparation, capture, both polarity attempts and replay share the existing 600-second/12-GiB case budget. Record the unscored qualification observations and their chronology; a successor registration is not retroactive preregistration. Because query/polarity bindings change, retain a distinct comparison identity and explicit per-family policy references. Reuse accepted feasibility/provenance evidence only through reviewed unchanged-profile compatibility; do not relabel those runs as executions of the successor. The matched enhanced arm must use the same corrected family query protocol. The pending correction does not block the umbrella shared-contract task or erase already satisfied family baseline prerequisites.

### Qualification before scoring

The current qualification status and review findings are authoritative in [tasks.md](tasks.md#tasks). A draft policy file and successful negative imports alone do not qualify the operational command. Freeze the exact runner and policy bytes, validate their agreement on tactics, preparation and bounds, and retain the source bytes and argv of each attempt. Preserve each polarity's source independently even if execution uses one temporary path. Save partial receipts before an operation can fail, including deliberate unavailable/available-module controls and launcher timeouts.

First qualify the public invocation against an independent known-goal control and exact source-position observation. Any explanation of differing captures must be supported by a controlled comparison; speculative syntax, tracking or scheduling workarounds are not accepted contracts. Compare effective resource settings as part of that diagnosis. RSS limits do not imply an equivalent virtual-address-space limit. The r14/r15 comparison found successful capture after removing the runner’s undeclared 12-GiB address-space cap; r5 also captured a goal with the cap present. The historical r18 batch used its then-locked runner and completed with a shared preparation-inclusive 600-second deadline, retained timeout/process-tree checks, and independent protocol review. Preserve this result without claiming a complete causal diagnosis of all earlier failures. Invocation qualification and diagnosis are separate conclusions.

Distinguish invalid qualification (wrong invocation, broken harness, stale inputs or failed isolation) from a correctly invoked original-runtime limitation (unsupported capture, failed tactic or replay, resource stop). The former blocks scoring. A report claiming successful capture with a missing or mismatched required source binding belongs to invalid qualification even when the CLI exits successfully. A valid unavailable report need not carry a successful capture object. The latter runtime-limitation category yields a retained unresolved case and allows the remaining registered cases to run; baseline acceptance does not require every original-runtime capture or proof to succeed. Do not repair the frozen runtime to improve the baseline. Semantic and checker improvements remain in the enhanced arm after independent family acceptance.

The exposed-module control must successfully import the injected artifact and cause the exclusion predicate to reject it. An unrelated error merely shows that the module was not proven unavailable; it does not establish deliberate availability. Resource flags invalidate diagnostic-only isolation evidence even when output happens to resemble a missing-module message.

### Two measurement layers

Validation layer receives selected interpretations and separately labeled proof terms. Operational layer runs deterministic bounded probes without oracle terms, selected by family rather than case ID. Record exactly which inputs each arm receives. Source-reading trials, if conducted, use separate reports, model/configuration and reviewed fidelity; they do not silently contribute to operational checker metrics.

The initial operational tactic budget uses a fixed ordered repertoire of existing proof-search capabilities; no per-case theorem names or embedded answer proofs. Cases outside that repertoire abstain. Before baseline execution freeze the concrete commands, tactic list and preparation policy. Equal per-case total deadline is 600 seconds and RSS 12 GiB; sequential execution avoids confounding process-tree measurements. Preparation time is included unless an identical prebuilt fixture policy is explicitly frozen for both arms. No full benchmark is run during planning.

### Custody, scoring and gates

Create a separately versioned pitfall registration/scorer; reuse canonical hashing and bounded I/O only where contracts match. Freeze runtime file manifests including dirty bytes, source/toolchain/import identities, ordering and invocation JSON. Local-checkout launchers must not resolve the pip-installed package. First reports are immutable; adjudication corrections are append-only.

A runtime freeze must preserve recoverable bytes (a verified snapshot/archive, or an exact reconstructable commit plus retained changes) and a launcher that checks those identities before execution. Include relevant untracked runtime files, deletions and launcher bytes. Record the interpreter and actual dependency/toolchain/import environment used to run cases. A list of hashes cannot restore overwritten files; pointing `PYTHONPATH` at a changing working directory does not freeze the runtime. Keep preliminary inventories as history and publish the accepted freeze separately.

Use exact counts and denominators for established faults, false accusations, justified controls, unknowns, checker failures, attempts and resource use. Per-family validation accepts both faults and both controls for the three new semantic families. The integrated operational improvement gate requires zero false accusations, no lost baseline detections, and at least one newly established fault in each of feasibility, provenance and existence. If baseline already finds all faults in one family, report no room for this predeclared improvement gate; do not revise the corpus post hoc.

Correct local evidence is not an automatic accusation: explicit conditional controls may have a conclusion-bearing premise. Interpretation fidelity must be reviewed separately for every claim of source mismatch. Report runtime/memory distributions and totals without claiming a speedup from a single run or optimizing ahead of a measured problem.

## Risks / Trade-offs

- [Corpus becomes answer-specific] → vary names/representations, forbid case-ID dispatch, independently review fault/control pairs.
- [Baseline adapter missing] → record unsupported at the same boundary; do not backport new semantic detection into baseline.
- [No improvement] → retain the negative result and stop at bounded development evidence.
- [Slow pinned Lean fixtures] → share prebuilt fixture preparation only under the same frozen policy for both arms.

## Migration Plan

Keep legacy evaluator schemas and reports byte-compatible. New evaluation records live in their own namespace/profile. Freeze the common policy before semantic edits and accept each child’s family baseline before its implementation; retain the original runtime for later baseline batches. Execute the full enhanced arm only after integrated source identities stabilize.

