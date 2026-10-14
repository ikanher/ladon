# Design

## Context

See [proposal.md](proposal.md) for motivation and [sources.md](sources.md) for
planning evidence. This is a Ladon implementation umbrella, with executable
work packages rather than a requirement to create another layer of planning.

The existing native derivation model already has ordered premise occurrences,
rule/substitution/context references, AND premises, and OR alternatives.
`proofir_derivation.py` explicitly performs structural analysis without checking
mathematical truth. `source_goal_capture.py` and the Lean source-goal helper
observe exact goals and local contexts through InfoTree; `ladon_expr_graph.lean`
serializes shared structural expressions. `source_goal_completion.py` checks a
term in the captured context and independently compiles the closed application
under an axiom policy. These are implementation foundations, not operations to
rebuild under new names.

In contrast, `investigation.py` stores seven prose contract fields as strings,
and `investigation_derivation.py` validates authored steps and challenges. It
checks rational witnesses but neither discovers a prose interpretation nor
extracts the informal/formal correspondence. The latest paper finding was
independently reviewed outside this bound workflow. The same run reported a v3
declaration-compaction rejection and an advertised option rejected by entrypoint
routing. Those observations require reproduction before root-cause claims.

Existing main specs for native v3, evidence identity, observation authority, and
derivation semantics remain authoritative. Earlier binder-difference and
premise-routing changes concern lexical comparison or candidate applications;
they do not establish source-faithful prose correspondence. Reuse their shipped
code where suitable without marking their unrelated unfinished tasks complete.

## Goals / Non-Goals

**Goals:** make a small original prose obligation an executable checked subject;
preserve its interpretation independently of the selected Lean proof; expose
exact missing implications and premise providers; keep corrections and review
evidence usable from one public workflow; measure capability and cost on a fixed
evaluation.

**Non-Goals:** a bijection between proofs and prose, a unique canonical proof
strategy, unrestricted automatic natural-language semantics, a second Lean
kernel in Python, extracting every tactic in a research repository, or proving
that every undiscovered paper assertion was inventoried. No mandatory model
API, automatic manuscript repair, legacy ProofIR conversion, or Quux dependency.

## Decisions

### 1. Two arguments with checked links

Maintain a source interpretation graph and an observed formal proof slice.
Each alignment selects explicit nodes from both graphs, an object map, and the
mathematical relationship claimed. One prose step can cover several formal
steps, and a formal lemma can cover several prose steps. A shared endpoint does
not establish that the arguments use the same method.

The authoritative material is the original passage, the attributed interpreted
proposition, the observed Lean expressions/contexts, and actual check results.
Graph reachability, reviewer agreement, and fingerprints do not replace checks.
Round-tripping generated prose from Lean can be a display feature, but cannot
test an independently written original argument.

### 2. Structured interpretations with an explicit translation boundary

Add an opt-in investigation version 3 referencing immutable native evidence.
Versions 1 and 2 retain their semantics. A new interpretation records source
span and digest, attribution, alternative ID, scoped binders, domains,
hypotheses, conclusion, and permitted dependencies for witnesses/constants.

The initial structured fragment supports typed binders, logical connectives,
quantifiers, equality/order predicates, and applications of declared symbols.
Binders have scoped identities rather than names as identity. Terms outside the
fragment stay opaque with a limitation; they are never reparsed heuristically
into a supposedly complete proposition. Scope checking can reject forward or
captured references, but cannot infer mathematical equivalence.

The structured prose form is an authored interpretation. Lower its admitted
fragment deterministically through a binder-preserving Lean presentation; a
Lean worker elaborates that presentation and the object map in a frozen declared
environment. Bind the generated goal to that exact lowering. If a caller also
supplies a Lean expression, compare its elaboration with the lowered subject
through the Lean worker rather than assuming both representations agree. Core
readers only validate structure; Lean expressions remain opaque for semantic
comparison. A checked elaboration establishes the encoded interpretation, not
fidelity to the quoted sentence. Independent review must assess fidelity.

For ambiguity, retain multiple interpretations before matching formal support.
Evidence for one interpretation must not silently select it as the intended
meaning. A refutation of one reading remains conditional on that reading.

### 3. Bounded Lean application extraction

Extend the existing helper boundary to observe selected successful theorem
applications and local `have` proofs with their fully elaborated terms. Use
InfoTree ranges where available, and proof-term inspection for instantiated
arguments, implicit/typeclass arguments, local definitions, and premise-provider
references. Unsupported syntax-to-term attribution remains an explicit residual.
Do not synthesize applications from declaration dependency names or goal diffs.

The first slice is deliberately small: one selected application and its local
providers, with exact earlier-scope availability. Later expansion follows
requested premise branches. Each branch is external support, observed provider,
or unresolved; a convenient single dependency path cannot close an AND step.
Case branches and witness scope remain distinct. Initial support is ordinary
non-modular source under the existing frontend profile.

Freeze finite selection, node, expression, depth, output, process-time, and RSS
bounds before integration tests. Reuse existing worker supervision and native
artifact ceilings. Exceeding a bound yields partial evidence and a named frontier,
never a false absence or a complete slice. Do not serialize the entire kernel
proof and then truncate until validation passes.

### 4. Generate exact correspondence obligations

After an explicit object translation, let the original interpreted step be
`H_N -> C_N` and selected formal support be `H_F -> C_F`. Generate separately:

1. Well-typedness and any required representation/transport obligations.
2. Premise supply: `H_N -> H_F`, preserving each premise occurrence.
3. Conclusion transfer: `H_N ∧ C_F -> C_N`.
4. Provider checks: whether the original predecessors establish every assumed
   local premise in the original argument.

Represent contexts as ordered dependent telescopes, not flattened conjunctions
when later types depend on earlier terms. Preserve existential witness scope and
its allowed dependencies. Never introduce `C_N`, a disputed premise, or an
unfinished theorem as an extra assumption just to close the generated goal.

Generated obligations live in immutable scratch Lean modules with explicit
imports and locals. Capture their goals through the existing source-goal path;
complete proposed terms through original-context checking and independent replay.
Mark these as generated correspondence goals, not positions observed in the
original manuscript or original formal proof. Existing candidate discovery is
optional navigation, not the checker. No universal automated solver is assumed.

A missing or rejected proof attempt leaves an obligation unresolved. A checked
counterexample must address the exact quantified implication and satisfy its
premises. The rational checker remains an optional existing checker; an analytic
argument can be retained as attributed evidence without masquerading as scalar
replay or Lean acceptance.

### 5. Preserve separate result dimensions

Report interpretation fidelity, local conditional validity, premise establishment,
parent support, method correspondence, extraction completeness, and checker
authority independently. Parent support requires all load-bearing providers and
the actual links, not merely matching local reviewer labels. A valid alternative
proof can establish the interpreted conclusion while leaving the described route
unsupported. A checked structural mismatch or unchecked proof gap is distinct
from a semantic counterexample.

Dependence on constants and witnesses is tested using exact obligations. Merely
finding a variable in a proof term is not a proof that dependence is necessary;
failing to find it in a displayed type is not evidence of uniformity. Different
definitions or representations need an explicit justified translation, not a
string-normalization whitelist.

### 6. Native evidence, one authoring workflow

Use existing native environment, claim, source-map, plan, derivation, attempt-log,
check-run, and attachment artifacts for the subjects they already represent.
Add two explicitly closed native payload kinds: `proofir.interpretation` for
source meanings and `proofir.correspondence` for selected graph relations and
their obligation references. Keep validators in dedicated owners and register
their payload/reference schemas, inspection, and projection routes explicitly.
Do not hide semantic records in unchecked extension dictionaries. Older consumers
must reject unsupported kinds; existing artifacts retain their canonical IDs.

Interpretations and alignment proposals are authored, not accepted derivations.
Only actual check evidence can support a checked obligation. Both new kinds
remain under the existing native v3 envelope, authority, identity, and size rules.
Python implements the consuming route. Update shared conformance declarations
and give held Rust consumers explicit unsupported-kind behavior unless parity is
actually implemented and exercised; do not claim a broader parity release.

Proposed public command family under `investigation`: `interpret` records a
source-bound interpretation, `align` selects formal slices and generates
obligations, `check` executes bounded supplied proof/witness attempts, and
`inspect` renders the exact remaining work. Add a bounded `proof-search proof
slice` operation for the Lean producer. These are planned interfaces, not
currently available commands; freeze precise arguments during the red-contract
task. Reuse `challenge`, `next`, and `finish` for v3 rather than making a parallel
review application. A record is authored once and referenced thereafter.

First responses are immutable. Sanitized review packets exclude earlier labels,
repairs, and answer metadata while carrying necessary original context. Reviewers
can return assignments for coordinator replay without opening a hidden author
plan. Context changes invalidate affected links; unaffected independent results
remain reusable only when their complete input identities match.

### 7. First working vertical, then expansion

Work packages and gates are in [work-packages.md](work-packages.md). M1 must
exercise the public command path, actual Lean extraction, generated obligations,
and replay before generalized search, large indexing, or broad AST expansion.

The real-source development target is the reported page-3 pressure-direction
passage and selected applications in
`NavierStokes.PressureDatum.deriv_pressure_pos` and
`NavierStokes.PressureDatum.deriv_pressure_pos_of_active`.
It is already exposed and cannot count as blind detection. Separate the one-axis
datum from the physical off-axis object through explicit maps; the datum lemma
alone proves neither the physical coordinate chain rule nor uniform near-axis
direction. Retain the interpretation-sensitive outcome if those links remain
open. Do not turn the previously reported conventional countercalculation into
a Lean-checked finding without actually formalizing and replaying its obligation.

Portable actual-Lean controls accompany this passage: preserved alpha-renaming,
valid representation transport, an invalid witness-dependency/quantifier swap,
a true endpoint reached by a different proof, and a valid downstream conditional
with an unestablished predecessor. These establish the checker path even if the
natural passage remains partially analyzed. Optional further checker families
need a concrete unsupported obligation and a portable consumer before admission.

### 8. Evaluation and overlap policy

Use the latest run only as development evidence. Freeze a new bounded population
of passages with actual Lean source, independent source selection/key preparation,
faults and faithful controls, including method differences and ambiguity. No
public outcome identifies a passage as faulty in the auditor input. Include a
small selection task with surrounding text so the fault is not prelocalized.

Compare fresh assisted and ordinary-tool contexts with identical primary inputs,
budgets, reviewer access, model configuration, and cache/preparation policy.
Record actual source use, independent mathematical reasoning, unsupported
interpretations, false positives, abstentions, costs, and the first-response
corrections. A false reference claim needs justified refutation; disagreements
with the key remain adjudication work. Separate capability success from an
incremental benefit claim. Stop after one predeclared evaluation; a negative
result completes evaluation reporting but not the objective of improved detection.

The assembly rendering and option-routing observations get focused reproductions
and consumer tests. Fix only demonstrated defects affecting the path; preserve
reserved-key rejection for malformed/untrusted payloads. The new slice operation
need not depend on a repository-wide architecture report. No automatic fallback
to a legacy report can count as native-v3 success.

## Risks / Trade-offs

- **Proof applications cannot be mapped reliably from available InfoTree data**
  → perform an initial feasibility check on two portable proofs (tactic and term)
  and one selected real application, within four hours of engineering time and
  existing per-process caps. Success requires exact instantiated premises and a
  replayed local application. If unavailable, save concrete residuals, stop broad
  extraction work, and revise the packet around a narrower supported producer;
  dependency names or handwritten replacements cannot satisfy extraction.
- **Structured prose is systematically mistranslated** → preserve alternatives,
  independently review source fidelity, and score translation failures separately
  from solver failures. Compilation cannot certify prose meaning.
- **A proposed implication route is incomplete for the claim** → report its
  residuals as route-specific; try a bounded alternative without declaring the
  original claim false merely because the first route failed.
- **Infrastructure absorbs the work without detection gains** → require M1
  before generalization and a fixed evaluation; do not add a model service,
  database redesign, or solver suite speculatively.
- **Large contexts defeat resource bounds** → retain exact omitted frontier and
  measured costs; explicit unsupported results are preferable to lossy acceptance.
- **Known examples contaminate evaluation** → separate development sources,
  curator key, and fresh auditor inputs; report procedural versus enforced
  isolation, and never count repeated target discovery as an unseen-case result.
- **Current dirty changes or unfinished packets conflict** → baseline relevant
  bytes, preserve unrelated changes, and reconcile only overlapping implementation
  contracts. Do not retroactively complete another packet or historical result.

## Migration Plan

Add opt-in v3 authoring and native producers with existing v1/v2 readers intact.
An old plan can be copied into a new run, but free-text contracts do not acquire
structured interpretations or checked authority automatically. Existing readers
reject unknown new artifact kinds explicitly. Register native projection support
before advertising semantic query coverage. Use the current source checkout for
all qualification commands and preserve actual import and toolchain identities.

Rollback is to disable new opt-in entrypoints and retain immutable artifacts and
failed attempts for inspection; no production input or historic plan is rewritten.
The first real-source run stays external and pinned; portable tests and ordinary
Ladon use must work without Quux or the Navier–Stokes checkout. No package release,
archive, or manuscript modification is implied by implementation completion.
