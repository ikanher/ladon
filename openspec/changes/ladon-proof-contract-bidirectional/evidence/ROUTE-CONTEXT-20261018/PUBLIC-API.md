# Mathematical contracts

The opt-in mathematical contract domain records a small, explicitly interpreted
estimate profile. Native `proofir.contract` artifacts bind the source proposition,
assumptions, conclusion, source maps and environment. A contract is an authored,
extracted or derived summary; validating its JSON does not check its mathematical
truth or establish fidelity to prose.

The first profile is `norm-scale-v1`. Its formal calibration uses natural-valued
indexed scales and estimates of the form

```text
forall s x, M s (f x) <= c * N (s + loss) x
```

The scale functions and operator are explicit. Composition requires exact
intermediate scale compatibility; its constant is the product and its loss the
sum. Weakening from a lower loss to a higher loss requires monotonicity of the
input scale. Combining requirements at their maximum requires both explicit
embedding implications. These are conditional rules over the declared profile,
not an extraction theorem for arbitrary analytic norms.

Dependency permission means that valuations agreeing on the allowed binders
produce the same witness. The empty allowed set means independence; `unknown`
with null permissions is different. A parameter used in one proof need not be
necessary for every proof. Existential witnesses may refer only to preceding
universal binders. Every existential binder has a permission record.

An explicitly quantified estimate constant uses `constantDependencies.binderId`
to identify its existential choice point. It cannot depend on a later parameter.
Without this optional anchor, the profile describes a separate implicit estimate
constant chosen after the telescope; it does not identify that constant with a
named existential witness. Source producers must preserve an explicit source
constant's anchor. Different implicit and explicit anchors compare as unknown.
When the constant and its anchored witness both have known permissions, their
sets must agree; incomplete summaries remain incomplete.

`ladon.proof_contracts.validate_contract` validates the closed bounded record and
returns a detached copy. `compare_contracts` compares complete correlated tuples,
returning `dominates`, `dominated`, `equivalent`, `incomparable` or `unknown`.
Comparison requires the same endpoint, object, domain, scale, representation,
assumptions, conclusion and compatible ordered telescope. Binder identities are
normalized by position for comparison; original native artifact identities are
preserved. Unsupported features and absent representation bridges stay unknown.
The scalar ordering assumes the scale nesting in the declared profile. It does
not infer that an arbitrary source scale satisfies that assumption.

A lower-loss route with parameter dependence and a higher-loss independent route
can be incomparable. Taking the preferred coordinate from each would invent a
proof. Comparisons therefore operate on whole contracts, and result authority is
`profile-structural` with mathematical falsity `not-established`.

`ladon.proof_contract_artifacts.comparison_artifact` creates a native comparison
with exact external references to its two input contracts. Batch validation
checks reference closure and recomputes the result from those inputs. Individual
envelope validation checks shape and identity only; it cannot resolve an external
source or replay Lean. Check-run references are retained without promoting a
producer's label to checker acceptance. Different source statements can share an
authored abstract endpoint, but this does not establish that their summaries
faithfully interpret either statement. Every comparison must retain the stable
`source-contract-binding-unchecked` limitation; it cannot discharge a formal
bridge or certify source-proposition equivalence.

Existing public artifact commands accept the new kinds:

```sh
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint proofir validate CONTRACT.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint proofir inspect CONTRACT.json
```

The analysis payload admits `comparison` and `propagation`. Obligation,
probe and refinement stages require their child implementations; an unknown
stage rejects. Each record caps collections at 4096 entries, identifiers/reasons
at 512 UTF-8 bytes and offsets at the native safe integer limit. Native 8 MiB
artifact and 32 MiB batch caps still apply.

Python validation, ordinary inspection and SQLite projection support both new
kinds. The disposable SQLite schema is version 11; older projections require a
rebuild and are not migrated in place. Contract statement/source and comparison
input lookups have named indexes and exact subject foreign keys. Rust currently
rejects both kinds explicitly; no new cross-language payload parity is claimed.
The frozen nine-kind parity corpus is unchanged.

The checked mathematical fixture is
`tests/fixtures/proof_contracts/ContractMath.lean`, pinned to Lean 4.32.1. It
proves the conditional composition, maximum, dominance and permission rules and
one incomparable pair. Its axiom judgments use at most standard `propext`.
Portable record/native tests need no Quux checkout or model service; mathematical
qualification additionally runs the actual pinned Lean fixture.

Contract production, propagation and the integrated audit workflow are developed
in separate child packets. Successful domain checks alone do not establish
source interpretation accuracy or unfamiliar-paper discovery benefit.

Propagation evaluates a native acyclic AND/OR derivation. Every ordered premise
occurrence needs a compatible scoped contract. Composition adds losses;
`combine-estimates` takes their maximum and unions dependency permissions under
explicit side conditions. The generic `combine-requirements` rule remains
unsupported by the numerical estimate evaluator. The frontier retains complete
incomparable contracts; selecting one preferred coordinate from each route is
not a supported route. Shared witness references preserve repeated occurrences,
substitutions, local contexts, source owners and declared interfaces.

The ordinary commands accept native inputs and a closed request object with
`goalRef`, `ruleBindings`, `endpointInterfaces`, `scopeBindings` and `bounds`.
This runnable example uses authored demonstration artifacts; it does not encode
a checked source theorem or manuscript interpretation:

```sh
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract propagate \
  --derivation tests/fixtures/proof_contract_propagation/graph.json \
  --contract tests/fixtures/proof_contract_propagation/contract.json \
  --request tests/fixtures/proof_contract_propagation/request.json \
  --analysis-id analysis:example --output /tmp/contract-propagation-example.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract inspect \
  --input /tmp/contract-propagation-example.json \
  --context tests/fixtures/proof_contract_propagation/context.json
```

Output paths must be new. The native analysis names the exact external graph
goal owner and input contract owners. Batch inspection replays the request
against those inputs and rejects an altered result even if its content ID was
recomputed. SQLite retains the exact derivation goal through a typed foreign key
and named lookup index. Validation or replay does not promote the profile's
conditional authority to proof acceptance or source fidelity.

Fixed maximum bounds are depth 64, 128 contracts per frontier, 4096 combinations
per application, 16384 total combinations, 8192 evaluated steps, 4096 graph
references, 256 witness candidates, 8 MiB aggregate encoded input and 8 MiB
result output. Request bounds may lower the operational caps. `deadlineUtc`
is one absolute timezone-aware deadline. Cycles remain unsupported; caps and
missing evidence produce partial coverage with named residual/pending work.
Known fitted routes survive truncation, and incomplete visits are not cached
as mathematical negatives. A bounded partial result exits successfully; invalid
inputs or failed publication return exit 2.

The propagation CLI additionally caps the total raw input files at 8 MiB before
decoding any JSON; native inspection shares a 32 MiB raw cap across the analysis
and its context file. Reads use the remaining budget, so a file growing during
loading cannot bypass the aggregate bound. Whitespace counts toward these raw
file caps. Duplicate keys and nonfinite JSON values are rejected.

The result records a bounded count of deadline decisions and the first exceeded
check, if any. Native replay consumes exactly those historical decisions without
consulting the current clock. This reproduces a saved computation; the trace
does not authenticate its original timing or authorize fresh work after expiry.

Produce each prose reading before selecting formal counterparts. Author a source
interpretation JSON using the existing typed interpretation schema, a contract
record, and feature origins such as
`{"regularity":["/formula"],"constantDependencies":["/formula/body/binder"],"witnessDependencies":["/formula/body/binder"]}`.
Each pointer must resolve in the original formula. Unsupported claims remain
`unknown` or `unsupported`, with a reason; a positive-constant passage alone
cannot justify an indexed estimate. The executable authoring example is
`tests/test_proof_contract_source.py::prose_inputs`.

```sh
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract produce \
  --channel prose --root SOURCE_ROOT --interpretation reading.json \
  --record contract.json --origins origins.json --alternative-id reading:a \
  --environment-ref sha256:ENVIRONMENT_DIGEST --author source-reader --output reading-a.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract fidelity-record \
  --root SOURCE_ROOT --input reading-a.json --output fidelity-record.json
```

Capture that record with ordinary `investigation observe`, then use
`investigation challenge` and `investigation ingest` for independent review.
Each alternative has a separate immutable snapshot. Challenges expose the
original quote and structured reading and withhold the author's comparison and
evidence. Review attribution requires distinct reviewer labels; labels do not
authenticate independence. Reviewed fidelity does not establish formal support
or mathematical falsity and never changes the frozen snapshot's attribution.

Formal production observes a selected elaborated declaration type independently
of its proof body. It preserves the raw and normalized expression, scoped binder
positions, source range, source digest, exact environment, helper digest and
bounded process receipts. The command accepts no authored feature override.

```sh
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract produce \
  --channel formal --root LEAN_ROOT --file Module.lean --module Module \
  --declaration Namespace.estimate --output estimate.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract inspect \
  --root LEAN_ROOT --input estimate.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract expand \
  --root LEAN_ROOT --input estimate.json --application Namespace.provider \
  --obligation-id premise:1 --output selected-provider.json
```

Inspection checks freshness and deterministic native attachments without proof
body extraction. Expansion requires an explicit application and obligation and
retains the original statement snapshot even if the selected body slice is
unavailable. Selected slices leave overall provider/body coverage incomplete.
Statement completeness describes the admitted feature fragment only. A snapshot
hash binds recorded bytes; it is not an authenticated Lean certificate.

| Formal expression | Treatment |
| --- | --- |
| Nat-indexed `M s (f x) <= c * N (s+k) x` | Recognize builtin order, arithmetic and literal identities |
| Alpha-renaming; implicit binders; local let aliases | Preserve scoped positions; safely reduce lets |
| Constant before/after a parameter | Record its exact existential anchor and permitted dependencies |
| Dependent `Fin` domain or restricted subtype | Preserve original expression and named unsupported residual |
| Custom arithmetic, order or numeral instances | Unsupported; surface syntax does not identify semantics |
| Imported declaration selected from another file | Unavailable; module and namespace names need not coincide |
| Full proof body or all premise providers | Not extracted by statement production |

The default formal worker bound is 60 seconds, 12 GiB process-tree RSS and 8 MiB
output. Memory exhaustion reports the configured limit and measured peak and
instructs the agent to stop and report to the user before a higher-cap retry.
Unsupported expressions remain inspectable observations with residuals and no
complete contract; they never mean a requirement is absent.

`RestrictedTransport.lean` in the production fixtures checks a subtype/guarded
representation equivalence and a concrete non-equivalence after membership
is erased. This control certifies those exact propositions. It does not create
a generic representation bridge or certify a manuscript interpretation.

## Conditional backward templates

The Python statement producers `produce_formal_contract` and
`produce_formal_snapshot` accept an optional `runner` and `max_output_bytes`.
An orchestrator can supply the same deadline-clamping supervisor used by
source-goal capture and completion. The output cap also bounds the helper result
file; defaults remain 8 MiB output and 12 GiB RSS. These parameters do not change
statement or proof authority.

`instantiate_source_bound_premise` in `proof_contract_source_obligations.py`
constructs one source-bound atomic requirement from an exact backward
request/result and selected occurrence. It freshly observes the original
statements, checks a completed generated prefix through the strict frontend,
and captures a closed goal from the prefix before the parent declaration.
Its initial fragment is two explicit Nat binders with a global named
coefficient; unsupported transport remains incomplete. Construction returns a
candidate, with `goalOrigin` identifying a generated requirement. A supplied
term must pass the existing `SourceGoalCompletionRequest` /
`complete_source_goal` checks. Callers must retain the same deadline-clamping
supervisor through completion. The source adapter clamps its work to any earlier
backward-request deadline and preserves memory-stop instructions.

The separate `instantiate_planned_source_leaf_requirement` operation accepts a
complete `ContractObligationPlanRequest`, its exact result and a selected source
leaf's full occurrence identity. It recomputes the plan, binds the exact native
provider artifact/source map and fresh observations, then captures the local
requirement even when its operator differs from the original endpoint. The
original plan desired record must still equal the observed formal parent.
Partial plans retain their pending coverage and alternatives. Both operations
return conditional local candidates; a checked atom does not complete the plan.
Version-two planner replay runs in a supervised Python worker under the shared
deadline, output and memory limits. The legacy version-one API retains its
cooperative replanning behavior. Source stages enforce that shared deadline and
roll back newly staged files on failure. See the
[three-step source control](../openspec/changes/ladon-proof-contract-bidirectional/evidence/PLANNED-SOURCE.md).

Domain and conclusion transfer remain open. The earlier atomic fixture, limits and
receipts are in
[the source-atom evidence](../openspec/changes/ladon-proof-contract-bidirectional/evidence/SOURCE-ATOMS.md).

The Python API `BackwardTransformRequest` and `transform_backward_sufficient`
in `ladon.proof_contract_obligations` generates sufficient premise requirements
for a requested profile contract. It currently supports identity, estimate
composition, estimate combination and loss weakening. Composition requires
explicit nonnegative loss partitions with the exact requested sum and matching
intermediate types, scales and norms. Weakening requires a selected premise loss
at most the requested loss and attributed nesting evidence. Combination retains
both ordered premise occurrences, including repeated premises.

The request contains `desired_contract`, `rule_evidence`, ordered
`premise_interfaces`, `output_interface`, `parameters`, `choices` and `bounds`.
`rule_evidence` names the exact `PROFILE` declaration and digest, an attributed
application reference/status and opaque evidence references. The executable
request examples are in `tests/test_proof_contract_backward.py`. Generated
requirements preserve the desired telescope, assumptions and dependency
permissions, using each exact premise interface. The API never reverses an
arbitrary implication. Its preconditions are sufficient; it makes no necessity
or weakest-precondition claim.

Returned `branches` contain ordered `requirements`; residuals retain unsupported
rules, incompatible interfaces, unknown features that need interpretation,
anchored choices that cannot be transported, and invalid or empty selected
partitions. An unchanged feature may be carried without interpreting it, such
as through identity or loss weakening. Every result binds its exact request and
profile with a digest. Attributed references remain unchecked: authority is
`conditional-template`, checker authority is `none`, and mathematical falsity is
`not-established`. This low-level transformer alone does not bind native
application ownership or construct source-goal contexts. The planner and public
workflow below add those checks for a restricted source fragment.

Fixed caps are 8 MiB encoded input/output, 128 generated branches, 256 premise
occurrences and aggregate opaque references, 4096 explicit choices and 512-byte
identifiers. Supported rules additionally enforce arity one or two. Caller bounds
may lower branches, occurrences and output (minimum 1024 bytes). An optional
`deadlineUtc` is shared across choices. Deadline, branch and output stops retain
completed branches and exact pending counts; they do not refute the goal. A
result whose indispensable metadata cannot fit the requested output cap is
rejected with a bounded input error.

The actual Lean fixture `proof_contract_obligations/BackwardMath.lean` checks a
one-way implication whose converse fails and a monotone scale where a loss-four
estimate holds while a selected loss-two precondition fails. These controls
explain why a proposed stronger premise is not necessary. They certify the
specific fixture statements, independently of any manuscript correspondence.

## Route-local obligation planning

`ladon.proof_contract_obligation_planner` provides
`ContractObligationPlanRequest` and `plan_contract_obligations`. The request
supplies the native derivation, source contract artifacts, goal, rule/interface
and scope bindings, original desired contract and reading identity, ordered
described method, explicit backward choices, priority metadata and bounds.
Executable examples are in `tests/test_proof_contract_obligation_planner.py`.

Each goal witness defines a shared proof DAG. Planning retains ordered premise
occurrences, follows each distinct witness once per route, and compares each
generated sufficient requirement with its exact provider. The method's actual
final contract determines conditional endpoint support. Support from another
method preserves the described method's findings. If intermediate pruning leaves
the described method without a complete native witness, its review stays pending.

Route IDs bind the witness alternatives and remain stable when priority metadata
changes. Routes sort by declared source location, route identity and heuristic
priority. `earliestUnresolved` indexes a retained comparison in that route's
dependency order; its scope and ordering are explicit. This identifies a first
unresolved comparison among retained work, without a global minimality claim.
Unknown comparisons remain unresolved bridges. Mismatch dimensions distinguish
regularity, constant permissions and witness permissions.

Forward evaluation, backward generation and pruned-witness replay share step,
combination and deadline limits. Output admission precedes retention and keeps
completed requirement records when later work cannot fit. Pending work retains
references or a compact count and digest. Replay has an additional 8 MiB cache
budget. Conservative admission can stop before a maximally packed result would.
Route reconstruction also limits distinct witnesses to `maxDepth`, so a wide
shallow route can remain pending even when its graph depth fits.

Results have `conditional-profile` authority, checker authority `none`, and
mathematical falsity `not-established`. Attributed source readings and rule
evidence are not authenticated by planning.

## Ordered obligation bundles and native plans

`plan_contract_obligation_bundles` is a separate version-two API. It preserves
the version-one planner output contract and adds a demand DAG to every retained
route. A demand can have alternative branches; each branch retains its ordered
required premises. A shared child records every incoming occurrence, including
repeated premises. A truncated branch names both expected and pending premise
ordinals and cannot count as complete. Source leaves require separate checking.

The native `proofir.contract-analysis` stage `obligations` retains the complete
planner request, exact derivation and contract owners, original reading identity,
result and deadline observations. Native batch validation replays the whole plan
against those exact owners. Historical replay uses recorded deadline observations;
it does not replace them with the current clock. Changed contexts or rehashed
forged bundles fail validation. Disposable SQLite projections now use schema
version 12; rebuild older projections explicitly.

Use the checkout's Python entry point for the public workflow:

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract obligations \
  --derivation graph.json --contract provider-contract.json --request request.json \
  --analysis-id analysis:example --output obligations.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract inspect \
  --input obligations.json --context context.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-obligations \
  --input obligations.json --context context.json --sources sources.json \
  --root /absolute/path/to/lean-project --output-dir /absolute/path/to/fresh-run
```

Repeat `--contract` for every provider. `request.json` uses the camelCase fields
of `request_payload` in `proof_contract_obligation_artifacts.py`, including the
desired contract/reading, application choices and bounds. `context.json` is
`{"artifacts": [...]}` containing the exact derivation, provider contracts and
their source-map owners. `sources.json` contains `parentSnapshot`,
`parentReadingId` and `providers`; each provider contains `contractRef`,
`providerSnapshot`, `providerReadingId` and a list of candidate proof `terms`.
Snapshots come from `produce_formal_snapshot`, not authored summaries.

Checking uses one absolute deadline and a shared attempt budget. Defaults are
180 seconds for the source run, 16 proof attempts, 12 GiB RSS per supervised
process and 8 MiB aggregate evidence. Output directories must be fresh. Complete
source request wrappers are saved before construction; constructions and proof
attempts retain separate evidence. Only accepted replay with accepted trust
counts as `checked-support`. A rejected term remains `unresolved`; missing
providers produce bounded slice requests with `status: not-dispatched`.
Resource stops halt later work and preserve the memory report-back instruction.

These checks cover the restricted Nat estimate source fragment above. Route
source-check status is distinct from a certificate for the method:
`wholeMethodAuthority` remains `none`, and domain/representation and conclusion
transfer remain unfinished. This workflow does not authenticate a prose reading
or establish mathematical falsity. The source summary covers retained source
demands; inspect the native plan for global planner omissions and pending work.

The complete constructed fixture prepares fresh snapshots and executes all three
public commands serially, under a 180-second total budget:

```bash
PYTHONPATH=src:tests .venv/bin/python \
  openspec/changes/ladon-proof-contract-bidirectional/evidence/run_public_obligation_fixture.py \
  --output /tmp/ladon-public-obligations-new
```

Its retained inputs, request wrappers, source checks and receipts are in
[the public-workflow control](../openspec/changes/ladon-proof-contract-bidirectional/evidence/public-obligations-20261018/MANIFEST.json).
The output directory must not already exist. Fresh observation receipts produce
new identities; saved requests retain the exact original paths and deadlines.

## Checking a generated source-leaf bridge

The Python API `check_planned_source_bridge(source_request, terms)` in
`ladon.proof_contract_bridge` connects one verified version-two source demand to
actual provider-application extraction and the existing correspondence checker.
It currently supports universal estimates with exactly two explicit `Nat`
binders, a named global coefficient, no proposition assumptions, and identical
domain/representation records. Other transports remain unsupported.

Use a live, exact planned-source request, as accepted by
`instantiate_planned_source_leaf_requirement`: `repoRoot`, `parentSnapshot`,
`providerSnapshot`, `parentReadingId`, `providerReadingId`, `planRequest`,
`planResult`, `routeIndex`, `requirementIndex`, `selectedIdentity`,
`deadlineMonotonic` and `limits`. `planRequest` is a
`ContractObligationPlanRequest`. The operation replays the complete plan, checks
fresh source observations, and derives its own formulas and identity object map.
Additional assumptions, caller-written formulas and prepared plans are rejected.
It retains the original reading and desired contract, selected occurrence, exact
demand and all its incoming occurrences.

The four independent term keys are `source-requirement`, `domain`, `object-map`
and `conclusion`. For the constructed fixture's first source leaf:

```python
from ladon.proof_contract_bridge import check_planned_source_bridge

result = check_planned_source_bridge(source_request, {
    "source-requirement": "by intro s x; exact ThreeSteps.firstBound s x",
    "domain": "by intro s x; exact ⟨rfl, rfl⟩",
    "object-map": "by intro s x; trivial",
    "conclusion": "by intro s x; dsimp only; intro h hformal; exact hformal",
})
```

The source requirement is closed and has no assumed provider proof. The domain
goal checks the generated identity maps on `Nat`; this profile does not claim
semantic transport between different domains. The correspondence object-map
goal checks representation typing. Conclusion transfer retains only the actual
provider statement as its formal antecedent. Generated `let` bindings are
visible in these goals; the example reduces them before naming hypotheses.

A complete provider adapter uses the checked source prefix ending before the
parent declaration. Compiler guards exclude the parent declaration and its
original module. The adapter is extracted as an actual scoped application;
its generated positions are not observations of the original proof body.
Every supplied term goes through source-goal completion, independent replay and
trust checking. All four must pass for local `checked-support`. Missing terms
and rejected terms remain `unresolved-bridge`, with separate per-goal evidence.
No proof terms are supplied automatically.

The operation shares the original absolute and inherited deadlines. Each Lean
stage is supervised with ceilings of 30 seconds, 12 GiB process-tree RSS and
8 MiB output; stricter requested limits are preserved. A nested resource stop
halts later obligations, and memory stops retain the instruction to stop and
report back to the user. Input admission precedes copying; the complete compact
JSON result is bounded to 8 MiB. Oversized evidence yields an incomplete result.

This API returns its complete source request, construction, extraction,
correspondence plan and attempts. It leaves `wholeMethodAuthority: none`,
`mathematicalFalsity: not-established` and
`sourceFidelity: attributed-unreviewed`. General premise contexts and transports
and public CLI dispatch of this bridge API remain open. The separate original
provider observation operation is described below.

## Expanding a missing provider

`check-obligations` now emits `ladon-provider-slice-request-v1` records for
missing providers. Each retains the exact native analysis, original reading,
desired contract digest, route, source demand and all incoming occurrences.
A unique referenced declaration anchor supplies its source path, module,
declaration, content hash and byte range. Missing or ambiguous anchors remain
explicitly unavailable. Creating a request does not observe a proof or discharge
the source demand.

Select a request from `summary.json`'s `providerSliceRequests` and save that exact
JSON object as `provider-request.json`. A caller chooses the application name
and occurrence to inspect inside its provider's original proof:

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract expand-provider \
  --input obligations.json --context context.json --request provider-request.json \
  --root /absolute/path/to/lean-project --application Eq.trans --occurrence 0 \
  --output provider-observation.json
```

The corresponding Python API is `expand_obligation_provider(request)` in
`ladon.proof_contract_provider_expansion`. Its closed input fields are
`repoRoot`, `analysisArtifact`, `context`, `providerSliceRequest`, `application`,
`occurrence`, `deadlineMonotonic` and `limits`. All clocks tighten the work budget:
outer invocation, saved request and original planner deadline. CLI total timeout
defaults to 60 seconds; each worker stage has a 30-second / 12-GiB process-tree
ceiling, preserving stricter limits. Input and compact output are each capped at
8 MiB. A resource stop ends the operation, preserving memory report-back guidance.

Expansion revalidates the whole native plan, rebuilds the source request exactly,
and checks a fresh declaration observation and source-map attachments before
extracting the selected actual application. The anchor identifies a declaration;
it does not assert that an application occurs there. An absent application stays
incomplete. Stale source, forged bindings and malformed selections are rejected.
An expired request remains incomplete; it does not receive a new deadline.

A complete selected slice yields `status: observed` with
`goalOrigin: original-provider-source`, separately from generated contract goals.
It retains `unresolvedDemand`, `demandDischarged: false`,
`wholeMethodAuthority: none` and incomplete provider/proof-body coverage.
It is input for further auditing, not a proof of the missing premise.
`check-obligations` leaves expansion to the orchestrator and reserves aggregate
evidence capacity before retaining each pending request.

## Checking an original source context

`plan_context_bridge(request)` and `check_context_bridge(request, plan_id, terms)`
in `ladon.proof_contract_context_bridge` handle ordered premise contexts and
explicit object maps over an existing native `proofir.correspondence` owner.
This is a separate operation from the norm-specific route bridge above.
The native owner freezes the original interpretation/source map, selected scoped
application and object map. The operation accepts no additional assumptions,
replacement interpretation, caller-written goal or caller-selected source prefix.

The closed request has `repoRoot`, `correspondenceRef`, `context`,
`deadlineMonotonic` and `limits`. `context` contains the native `artifacts` batch;
`correspondenceRef` is the exact external reference with `artifactRef`,
`kind: correspondence` and its native `localId`. Produce that owner with the
ordinary `prepare_correspondence`, `interpretation_artifacts`,
`bind_native_interpretation` and `correspondence_artifacts` APIs. It must retain
open original obligations rather than checked-status claims.

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract context-obligations \
  --input context-request.json --output context-plan.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-context-bridge \
  --input context-request.json --plan-id sha256:THE_SAVED_PLAN_DIGEST \
  --terms context-terms.json --output context-result.json
```

`context-terms.json` maps generated goal IDs to Lean terms. Missing terms remain
unresolved. The request contains one finite absolute monotonic deadline, created
by the orchestrator before planning; both commands retain it. A check regenerates
the entire plan before comparing the saved identity. Changing the reading,
assumptions, object map, source, selected application or any generated goal cannot
reuse that checkpoint. A separate reading needs its own native owner and plan.

The operation preserves every ordered premise occurrence, including repeated
propositions, and each provider obligation. It adds a separate `domain` goal
whose existential equality witnesses show that mapped values inhabit the
observed formal domains. The `object-map` goal checks representation typing;
the `conclusion` goal checks the required semantic direction. These checks do not
assert that a map is an equivalence or has an inverse. Existing lowering supports
scoped domains referring to earlier binders, such as `Fin n`; forward references,
escaped witnesses and unsupported proof-dependent mappings stay rejected or
residual. Residuals prevent `checked-support`.

Preparation freshly observes the original selected application and compiles the
source prefix ending before its parent declaration. Compiler guards exclude that
parent and its original module from every generated proof context. Each term stage
checks original Lean source, quoted prose, environment and prefix fingerprints
before and after capture/completion, independent replay and trust checks. Formal
conditional/provider goals may retain their observed formal hypotheses; separate
premise-supply goals must establish the needed propositions from the original
interpreted assumptions. The unfinished parent cannot supply any of them.

Preparation and each term stage use enclosing process-tree supervisors capped at
30 seconds, 12 GiB RSS and 8 MiB output, preserving stricter limits and the same
absolute deadline. Aggregate inputs and complete compact outputs are bounded to
8 MiB. Expanded binding costs are admitted before per-goal copies, and worker
output size is counted before JSON serialization. A resource stop prevents later
work; a memory stop retains the stop/report instruction and is never retried.

Only successful completion, independent replay and trust acceptance for every
required channel, with no residuals, yields local `checked-support`. The result
retains `wholeMethodAuthority: none`, `mathematicalFalsity: not-established` and
`sourceFidelity: attributed-unreviewed`. This does not establish prose fidelity,
whole-paper coverage or detection benefit. Connecting these richer contexts to
route-generated mathematical contracts remains open in bidirectional task 1.2.

## Connecting original contexts to a route requirement

`ladon.proof_contract_route_context` adds `plan_route_context_bridge(request)`
and `check_route_context_bridge(request, plan_id, terms)`. These operations bind
one original native correspondence to an exact source-leaf requirement in a
native v2 obligation analysis. They preserve the other routes and demands.

The closed request contains `repoRoot`, `analysisArtifact`, `context`,
`selectedIdentity`, `sourceBindings`, `deadlineMonotonic` and `limits`.
`sourceBindings` contains exactly `parentSnapshot`, `providerSnapshot`,
`parentInterpretationRef` and `correspondenceRef`. Both references identify
existing, source-bound native owners in `context.artifacts`. The analysis's
original `desiredReadingIdentity` must identify the parent interpretation by
its `readingId` and native artifact ID in `interpretationDigest`
(`nativeartifactId-v1`). Older APIs accepting attributed reading labels retain
their existing behavior.

The operation validates the complete native batch and replays the historical
planner result. It checks the exact selected occurrence, full demand with every
incoming dependency, admitted rule bindings, mathematical profile, source maps,
original desired contract and parent reading. Fresh formal observations bind
the selected provider to the original correspondence application. A compiled
source prefix ends before the provider; explicit compiler guards exclude both
that provider theorem and the original endpoint theorem and module.

After all original ordered context obligations, four additional goals appear:

| Goal ID | Required proposition |
|---|---|
| `source-reading` | The complete closed original provider reading, I |
| `contract-transfer` | I implies the exact closed selected requirement |
| `endpoint-transfer` | The observed formal endpoint statement implies its original prose reading |
| `source-requirement` | The exact closed selected requirement |

The current contract denotation supports the explicit two-Nat-binder,
global-coefficient norm-scale fragment. Rich prose domains and representations
remain in the original readings and context obligations; unsupported contract
denotations remain incomplete. An interpretation on `Fin 5`, for example,
requires an explicit checked transfer to a requirement on all `Nat` inputs.
Native identity alone supplies no such implication.

Callers supply terms for generated IDs except `source-requirement`. Once the
reading and its transfer both have accepted completion, independent replay and
trust checks, Ladon composes their exact terms and independently checks the
result against the closed requirement. Every original context goal, both
transfers, the reading and the composed requirement must pass, with no residuals,
for `demandDischarged: true`. Missing or rejected terms remain unresolved;
resource stops prevent later work. This supplies local support for one demand;
whole-method authority remains `none`, attribution remains unreviewed and
mathematical falsity remains `not-established`.

```bash
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract route-context-obligations \
  --input route-context-request.json --output route-context-plan.json
PYTHONPATH=src .venv/bin/python -m ladon.entrypoint investigation contract check-route-context-bridge \
  --input route-context-request.json --plan-id sha256:THE_SAVED_PLAN_DIGEST \
  --terms route-context-terms.json --output route-context-result.json
```

The orchestrator creates one absolute deadline before planning. The native UTC
planner deadline can only shorten it. The saved route identity also binds that
original deadline and effective resource limits, so refreshing a clock requires
a new plan. Preparation and each term stage retain the 30-second, 12-GiB,
8-MiB caps and stricter requested bounds. Aggregate inputs, expanded goals,
per-goal evidence admission and complete outputs are bounded before copies or
serialization; memory stops retain the stop/report instruction without retry.

Route responses retain compact goal results with the full completion/replay/trust
record and an `evidenceRef` (`path`, `sha256`, `bytes`). The reference identifies
immutable, complete raw capture/typecheck/completion evidence beneath the
request repository's `.ladon/contract-obligations/` directory. Preserve those
files when moving a result. `load_goal_evidence(root, compact)` in
`ladon._proof_contract_route_context_evidence` checks the content hash, byte
count, fixed location and exact projection before returning raw evidence. This
storage avoids duplicating large capture trees in the bounded response; each
raw evidence file remains limited to 8 MiB. Resource-stop codes survive the
projection, and an incomplete check never gains proof authority from storage.
