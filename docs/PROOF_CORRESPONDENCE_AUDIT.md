# Audit a proof passage, not just its conclusion

A Lean proof of the final theorem can coexist with a false intermediate argument, a missing informal existence assumption, or a valid alternative proof. Ladon's correspondence workflow keeps those questions separate. Ordinary Markdown/TeX, named Lean obligations, and compiler/axiom output are sufficient; a Ladon command or model account is not required.

Start from an unchanged source passage and its proposed formal counterpart. State the exact local assertion in its original context, inspect or check that assertion, and propose a small revision. Keep a failed attempt separate from a checked counterexample. Label added assumptions as narrowing, and read proof source before claiming that a particular argument was translated.

For an investigation without a supplied fault location, use the
[source-first discovery procedure](CORRESPONDENCE_DISCOVERY.md). It adds a
breadth pass, source-span inventory, explicit unexamined population and
consumer-directed comparison before concentrating on a proof slice. Its
[development evidence](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/README.md)
records known-case exercises and controls separately from withheld evaluation.
The [frozen two-arm pilot](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md) exercised 28 fresh attempts on fourteen elementary authored inputs. Both arms found the same discrepancies with no false alarms; assistance used more observed time and tokens. No detection advantage or research-paper effectiveness was demonstrated. The supplied formal counterparts were summaries, and no scored run performed Lean checking.

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

## Inspect the stored source and application together

For a native correspondence alignment or check bundle, use the existing command:

```sh
ladon investigation inspect --plan alignment.json --context-max-bytes 65536
```

The outer response retains `ladon-correspondence-inspection-v1`; its `native`
section uses `ladon-native-correspondence-inspection-v2`. Alongside object maps,
obligations, residuals and result dimensions, `native.context.interpretation`
contains the exact stored record (source quote/digest, formula and symbols),
lowered formula, fidelity and source reference. `native.context.formalSlice`
contains the stored formal selection, local context and application observation.
Resolve the two together before using a reported support label.

Each component has its own UTF-8 stored-text allowance, default 65536 bytes;
`--context-max-bytes` accepts 1 through 8388608. Oversized components are omitted
whole with `reason: context-byte-limit` and `storedBytes`; raise the allowance to
retrieve them. Missing referenced interpretations are explicitly unavailable.
Either condition makes native inspection coverage incomplete. The allowance
bounds these context components, not the whole report or plan loading. It applies
to the native projection of alignment/check bundles; version-three investigation
plans retain their separate assessment workflow.

`native.checkEvidence` now resolves each exact check reference to its retained
`ladon.correspondence-receipt/v1` extension. Each row shows the original goal
digest, the actual `checkedGoal` (including negation for refutation), mode,
obligation ID and stored completion metadata. Its `binding.status` is
`matched-stored-records`, `mismatched` or `unavailable`. The comparison covers the
plan identity, planned obligation/goal/status, polarity and check operation.
`unboundObligations` lists displayed non-open obligations lacking a matching
receipt. Mismatches and unavailable evidence make `checkEvidenceComplete` and
overall native coverage false; original result dimensions remain visible.

The check rows share the existing row limit, and receipt payloads share one
`--context-max-bytes` allowance for the whole `checkEvidence` section. This is
separate from the per-component interpretation/slice allowances. Oversized
receipts are omitted whole. A `receipt-digest-only` result means the projection
retained only a digest; raising the inspection allowance cannot recover that
payload. Use the retained canonical bundle when available.

A matched binding describes consistency between stored records. It does not
rerun completion, authenticate a producer's claims, or establish that prose
assumptions supplied a premise. The plan identity carries the object map and
source/slice identity; inspection does not invent a per-obligation dependency
graph from Lean text. Review the actual mapping and conclusion transfer along
with these targets.

This is stored-evidence inspection. Complete coverage means the selected stored
context and child rows were delivered; it does not certify source fidelity,
current filesystem freshness, or mathematical support. Canonical artifacts and
stored result dimensions retain their authority. No Lean check runs on inspect.

## Distinguish a refuted route from a false claim

Start from `native.context.interpretation.value.loweredFormula`, then follow the
object map into the exact premise-supply and conclusion-transfer goals. Resolve
their receipt targets and polarity through `native.checkEvidence`. The
welltypedness obligation `P → P` does not prove `P`; the map's
`representation-transport` goal ending in `True` checks its declared type, not
its intended meaning. Review the mapped mathematical obligations themselves.

A proof of the negation of a correspondence link rejects that route. An alternative
map or proof may still establish the source. Source falsity requires a separately
justified refutation of the original source proposition under its assumptions.

The [three exposed mathematical controls](../openspec/changes/ladon-proofir-correspondence-context/evidence/mathematical-controls-r01/REPORT.md)
exercise this distinction with real Lean receipts: `Fin.val` supplies a valid
bound, shifting the map by five refutes premise supply while the identical source
claim stays true, and a pointwise upper-bound theorem fails to establish one
uniform bound. The last source proposition is separately refuted. All nine native
checks replayed, with the distinctions visible in the current inspection output.
This is root qualification of the reading procedure; no reader-benefit or fresh
detection score follows.

## Read the native MF examples

The [native MF qualification report](../openspec/changes/ladon-proofir-correspondence-context/evidence/mf-native-r01/REPORT.md)
provides one supported common-law claim and one refuted conclusion transfer.
Use these exposed examples to learn the evidence path. The supplied
interpretations and proofs were already known during qualification.

From this checkout, inspect both retained bundles with the local Ladon executable.
These commands create new scratch outputs and perform no Lean replay:

```bash
mf_evidence=openspec/changes/ladon-proofir-correspondence-context/evidence/mf-native-r01
mf_inspection=$(mktemp -d /tmp/ladon-mf-inspection.XXXXXX)
.venv/bin/ladon investigation inspect \
  --plan "$mf_evidence/fdp/checked-1800-r02.json" \
  --context-max-bytes 8388608 --output "$mf_inspection/fdp.json"
.venv/bin/ladon investigation inspect \
  --plan "$mf_evidence/adam/checked-1800-r02.json" \
  --context-max-bytes 8388608 --output "$mf_inspection/adam.json"
```

1. Read the exact quoted passage and attributed formula under
   `native.context.interpretation.value`. List uncertain readings before using
   the support label. A typed symbol can name a large predicate whose definition
   still needs review.
2. Follow `native.objectMap` and the selected application in
   `native.context.formalSlice.value`. Review the wrapper's preserved source and
   its argument producers. In the DP-Adam case, `AdamNative.Inputs` packages
   primitive data and hypotheses; `commonLaw` has **one** existential law outside
   the conjunction of both limits. Its `bridge` applies the existing paired
   convergence theorem. In the fDP case, the Nat argument is a dummy wrapper
   index and `neighbor` aliases the original neighboring dataset.
   Read `native.premiseScope`: zero direct premise obligations is compatible
   with hypotheses packaged in `Inputs` and its nested `Primitives`. It does not
   establish that the prose supplies those hypotheses. The common law may
   depend on the input; it is not one uniform law for every input.
3. Read each generated obligation and its `checkEvidence` target, mode and status.
   `interpretation` proves `P → P`; `object-map` checks typing with a goal ending
   in `True`. Neither establishes source fidelity. `conditional` checks the
   selected formal result. `conclusion` checks its transfer to the attributed
   source claim.
4. Require matching stored bindings and complete inspection coverage before
   saying all requested evidence was delivered. Then inspect the original
   checked bundle's `completion.replay` and `completion.trust` receipts. A
   matching inspection record is a consistency result; it does not rerun Lean.
5. State the reader consequence. DP-Adam supports the selected common-law
   interpretation under its packaged hypotheses. For fDP the reverse strict
   inequality refutes the conclusion transfer; the original finite countermodel
   separately establishes the failed event bound under inherited ordering.
   Review its normalization, adjacency, base privacy and sampled law before
   calling it a source counterexample. The manuscript's intended ordering
   remains unresolved. Neither selected result completes a whole-paper audit.
6. Record unexamined claims and costs. The successful checks took about 8.3 and
   7.5 minutes at 8.99 and 9.46 GiB peak process-tree RSS. The 1800-second timeout
   belonged to the qualification supervisor; it is not an `investigation check`
   CLI option or a changed production default. Preserve earlier timeouts and
   failed attempts when accounting for work.

The Adam quote in the frozen interpretation is narrower than its attributed
common-law consequence. Read the [append-only context clarification](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/r04-consolidation/ADAM-CONTEXT.md)
for the surrounding clock, initialization, query and diffusion assumptions.
It does not amend the old interpretation or certify prose fidelity.
See [role accounting](NL_LEAN_CORRESPONDENCE.md#keep-the-outcomes-separate)
before comparing old and new counts: object-map typing is now separated from
substantive checking, and neither count measures reader benefit.

For custody verification, run the retained `read_results.py` in the evidence
root. It checks original-source prefixes, exact goals/polarities, accepted
replay/trust fields and source/compiled-import hashes against the retained
result. It requires the recorded local dependency paths to remain available;
this evidence directory is not a standalone dependency capsule. Inspection of
an existing bundle does not need those dependency paths. For a new claim, use
new output paths and the ordinary extract/interpret/align/check workflow; the
qualification's `run.py` has a historical fixed deadline and is not a reusable
launch script.

## Check a formula against its definitions

When a passage reconstructs an object, changes coordinates, or converts between
representations, compare the claimed formula with the defining identity before
searching for a theorem. This is a source-review recipe using existing tools;
Ladon does not automatically select or interpret the formulas.

1. Give each assertion a stable ID, source span, original domain and quantifiers.
   List nearby defining equalities, side conditions and conventions. Include
   intermediate assertions even when the final theorem compiles.
2. Substitute the claimed reconstruction back into its definition. Check inverse
   factors, signs, inequality direction, units and endpoint domains. A mismatch
   is a candidate obligation; it is not yet a premise-satisfying counterexample.
3. Freeze the original implication and a separate candidate repair. Find an
   assignment satisfying every original premise. If the quantities are laws,
   functions or integrals, justify that the assignment can actually arise in
   that source setting. An inconsistent ambient context cannot refute a claim.
4. Use the [local derivation workflow](DERIVATION_CHALLENGES.md) when the exact
   implication fits its rational fragment: `init --derivations`, author the
   contract/arithmetic, then `investigation witness`. Keep the plan, assignment,
   exact evaluated premises/conclusion and command output. Use ordinary Lean or
   reviewed mathematics for unsupported operations. Replacing exp(t) by a scalar
   parameter is an authored abstraction whose source correspondence needs proof.
5. Check a repaired formula and a degenerate/boundary control. `not-counterexample`
   describes one assignment; universal support needs its own argument.
   `outside-assumptions` rejects a witness, not the original implication.
6. Before treating a formal declaration as support, write the explicit object
   map in both directions: signs, pushforwards, laws, normalization and parameter
   domains. Similar names or a successful `#check` do not establish that map.
   A useful restricted theorem keeps its own support ID instead of replacing
   the original source claim or control.
7. Freeze the complete evidence before review. Reviewers must return the same
   IDs and source labels; reject omissions and ID mismatches before acceptance.
   Record whether reviewers received hints or known answers. Preserve first
   reports and put corrections and additional coverage in separate records.

The [PLD audit](../openspec/changes/ladon-pld-core-source-audit/evidence/pld-core-r03/REPORT-v2.md)
found a real inverse-factor error by this reasoning and identified a nontrivial
sign map between paper and formal loss laws. The
[exposed scalar qualification](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/source-consistency-r01/REGISTRATION.md)
checks the existing witness operation with a fault, repair, degenerate control
and invalid assignment. These are development evidence, not a discovery score.

## Follow a new discrepancy and a faithful control

Read [case e03](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e03/INPUT.md) and its retained [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e03-ladon-assisted/first-report.json). The exposition asks for one real y with x+y=0 for every real x; the supplied formal proposition chooses a y for each x. Preserve the original quantifier order. Taking x=0 forces the common y to be zero; taking x=1 then gives a contradiction. This is a conventional counterargument and a localized statement mismatch, not a report of a failed tactic.

Now read [case e09](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/cases/e09/INPUT.md) and its [assisted first report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/runs/e09-ladon-assisted/first-report.json). Both texts allow y to depend on x and choose y=-x. The assertion and witness agree. A comparison procedure must accept this control rather than flagging the presence of an existential quantifier alone.

These files and the displayed arguments are sufficient to follow the reviews without a model service or a Quux checkout. They are elementary synthetic examples; actual formal source, argument inspection and source coverage remain necessary for a research exposition. The [pilot report](../openspec/changes/ladon-correspondence-discovery-umbrella/evidence/implementation/evaluation/REPORT.md) preserves the underspecified control, additional omissions, incidental report errors, resource measurements and attribution limits.

## Trace a conclusion back to its premise

A selected application can show that a proof uses a conclusion-bearing local or instance. Follow the actual application arguments into the same scoped local context, then follow local `let` values to their providers. Match structural local IDs; display names only help navigation. A type-class projection can be a legitimate conditional interface, a hidden premise, or a field backed by an independently proved value. Inspect the provider's source before judging which one.

Keep three questions separate: what the original proof uses, whether Lean checks the selected projection/type, and whether the prose discloses or establishes that premise. A route alone proves neither necessity nor circularity. Compare the exact passage and declared scope with the complete formal telescope. Preserve unresolved providers and unexamined source spans. A successful selected slice does not certify the whole theorem.

The [premise comparison recipe](../openspec/changes/ladon-premise-provenance/evidence/premise-comparison-r01/RECIPE.md) gives a step-by-step procedure and the [reviewed result](../openspec/changes/ladon-premise-provenance/evidence/premise-comparison-m2-r01/ADJUDICATION.md) shows a conclusion-bearing assumption, a disclosed conditional, an independently derived provider, and a real Gaussian moment route. Those are exposed development examples. They do not show autonomous prose discovery or a detection advantage. Use this recipe to gather and explain scoped evidence; obtain source review before calling an omitted premise an exposition error.


## Check a complete application under the source assumptions

First record the passage's objects, assumptions, quantifiers, conclusion and ambiguous readings before looking at a proposed owner theorem. Keep later interpretation changes explicit. For known development examples disclose prior exposure; this first-pass procedure does not erase it.

Encode the attributed source context and conclusion in a local Lean goal. Apply the selected theorem at one consistent object/parameter assignment and include the conclusion transfer in the proposed full term. Account for theorem arguments with cited source assumptions, checked derivations or unresolved obligations. Equivalent wording and stronger assumptions can supply a premise; a complete table alone cannot establish support. Preserve dependent locals, lets and fixed assignments. Check the whole route with [source-goal capture](SOURCE_GOAL_CAPTURE.md) followed by [completion](SOURCE_GOAL_COMPLETION.md), using the actual context rather than checking the theorem against its own printed type.

Inspect the structured outcome, replay and trust. An unresolved premise or conclusion transfer blocks completed support for that route; it does not establish necessity or source falsity. A transformed object or another proof may support the original claim. Preserve repairs as separate claims. To refute the source, independently check a counterexample satisfying every original premise in the original mathematical setting.

For diagnosis, an expression-form partial application can retain a missing argument as an explicit residual. A tactic `?_` can instead be admitted as `sorryAx`: the final trust rejection blocks completion even when its residual list is empty. An empty residual list or exit zero alone is never acceptance. If valid ordinary Lean code fails the completion helper's closure/round-trip step, retain the exact failure and the separate ordinary compiler/axiom evidence; do not label that a native completion success or infer that the source claim is false.

Keep pristine capsule payloads separate from working projects with packages/build outputs. Source capture/completion does not require capsule replay when the necessary compiled imports are already available; record cache provenance and actual toolchain bindings. Keep measurable-limit claims separate from samplewise existence, and check library definitions such as real `Summable` instead of importing the familiar meaning of ordered conditional convergence.

The [C05 printer repair](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/c05-printer-fix-r01/REPORT.md) now lets the previously rejected shifted-state proof complete through the native capture, replay and trust path. Proof printing uses a finite step budget and reports omitted terms directly. A longer future proof can still exceed the bound; preserve that rejection and use the separate ordinary Lean route when necessary. The original N.3c report remains the pre-fix result.

The [exposed seven-case qualification](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/checked-application-n3c-r01/REPORT.md) retains faithful, omitted/derived/conditional, shifted-object, shared-parameter and quantifier cases. It exercises existing checks and ordinary Lean with supplied interpretations and proofs. It is not a fresh discovery comparison or evidence of incremental detection benefit.

## Construct the objects behind a theorem application

When the candidate theorem takes a structured family, law or mechanism, inspect
the producers of that record. Assuming the record exists can hide the very
connection the source asks the reader to believe.

1. Map source objects to formal objects with their units and indexing intact.
   Check normalization, reference population, public versus input-dependent
   parameters, initialization, and which quantities vary along a limit.
2. Construct the needed record from source assumptions or locate its existing
   producer. Classify each field as primitive data, a checked consequence, or an
   unresolved obligation. Do not store the desired conclusion as a premise.
3. Derive properties for the transformed object actually used by the consumer.
   Measurability or regularity at one parameter need not transfer automatically
   to another. Changing a reference Finset to a finite type also needs a map.
4. Before treating an auxiliary record field as a new mathematical assumption,
   inspect whether the relevant observation depends on it. A checked
   irrelevance equality can remove a packaging obligation. It does not permit
   replacing the source objective in a utility theorem.
5. Complete each claimed conclusion with the same objects and parameters.
   Common limiting laws, eventual privacy, and finite-iterate utility are
   different obligations. A bound holding eventually for every positive
   tolerance supplies neither a computable threshold nor a finite-run rate.

Unperformed review remains unfinished work. Calling it blocked requires a
specific evidenced obstruction; a controller accepting authored blocker labels
does not verify them. A selected application can be complete while the source's
intermediate arguments remain unreviewed.

### Worked example: DP-Adam batch-pair support

Start with the retained [reader question](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-batch-pair-r01/HANDOFF.md),
then the [general construction report](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-source-constructor-r01/REPORT.md)
and [Full.lean](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-source-constructor-r01/Full.lean).
The report maps source requirements to the constructor, resampling/common-law,
privacy and empirical-objective consumers. Its final receipt is
`full-attempt-12.json`. The preliminary handoff's reproduction commands are
historical; use fresh output paths when repeating any check.

The pair has sampling rates `q` and `k*q`, counts `k*(j+1)` and `j+1`, fixed
beta, and matching expected epochs at each `j`. Epoch budgets grow with `j`.
The general proof constructs the families and derives the empirical gradient
identity rather than assuming the desired family or objective connection.
Its `objective_field_irrelevant` result concerns a stored path-law field only;
the utility proof still uses the actual empirical objective.

From this Ladon checkout, the following read-only check verifies the retained
example's bytes and displays its historical compiler outcome:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path("openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-source-constructor-r01")
entries = json.loads((root / "MANIFEST.json").read_text())
for entry in entries:
    assert hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() == entry["sha256"], entry["path"]
receipt = json.loads((root / "full-attempt-12.json").read_text())
assert hashlib.sha256((root / "Full.lean").read_bytes()).hexdigest() == receipt["sourceSha256"]
print("Verified manifest entries:", len(entries))
print({key: receipt[key] for key in ("returncode", "timed_out", "memory_limited", "peak_rss_bytes")})
print(receipt["stdout"])
PY
```

This is integrity inspection, not a fresh proof replay. A fresh ordinary Lean
check is optional when needed: copy `Full.lean` and `check.py` from that directory
into a new scratch directory and invoke the copied runner with arguments
`fresh-check Full.lean`, using `PYTHONPATH` set to this checkout's absolute `src`
path and its `.venv/bin/python`. Inspect the runner first: it binds the original
local donor path and Lean 4.33.0, uses existing compiled imports, and caps execution
at 60 seconds, 12 GiB RSS and 8 MiB output. Verify the recorded source/import
identities before treating a repeat as reproduction. Missing or changed inputs
require an explicitly new environment assessment. Never write a new receipt
into the frozen evidence directory.

The general composition has ordinary Lean compiler/axiom evidence, not native
completion of the whole proof or a portable dependency closure. The earlier
[native privacy-cancellation result](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-batch-pair-r01/NATIVE-SUMMARY.json)
checks a smaller subordinate goal. Neither result certifies the broader source
method, transfers simultaneous beta changes, or demonstrates a detection gain.

### Worked example: hidden fixed-size f-DP subsampling

This exposed case shows why the source-to-formal object map must include the
sampler's ordering and released law. In the read-only matrix-factorization source,
`subsample.tex:37` chooses a uniform subset and passes its records to a mechanism
on `X^m`; it does not say how that subset becomes an ordered tuple. The dataset
is formally an ordered tuple with coordinate replace-one adjacency
(`fDP/fDP.tex:32`). The appendix replaces one selected index and says the resulting
mechanism inputs are neighbors (`appendices/property.tex:286-299`), which relies
on a tuple representation. The source does not explicitly connect these steps.
See the [source interpretation record](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/fdp-source-interpretation-r01/INTERPRETATION.md)
for exact file hashes and scope.

Under one explicit interpretation, order selected records by their original
indices. A finite mechanism on `X={0,1,2,3}` releases a Bernoulli result and
satisfies the original coordinate replace-one privacy bound with factor 2 for
every input pair. For neighboring datasets `(0,1,2)` and `(3,1,2)`, uniform
selection of two indices gives true-output probabilities `7/18` and `2/9`.
The claimed classical amplification factor is `5/3`, but
`7/18 - (5/3)(2/9) = 1/54 > 0`. Thus this interpreted hidden mechanism violates
the claimed event bound. The [checked report](../openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/fdp-ordering-privacy-20261115T072023Z/REPORT.md)
records all finite base-mechanism premises, the sampled law, randomized-test
checks, exact proof receipt and a shuffled-order control for this pair.

The verdict is conditional: the inherited-order claim is refuted, while the
source's intended subset-to-tuple map remains unresolved. The shuffled control
covers only this pair and is not a general repair. To audit another sampled
mechanism, state its input representation, adjacency, sampling law, tuple order
and observable before transferring a privacy bound. Prove a counterexample in
the original premise domain; an LP or finite search can find a candidate, but the
exact law and inequality still need checked justification. This example came
from informed development work and is not a held-out Ladon discovery or evidence
of detection advantage.

## Quick review: TeX and a named Lean theorem

Use the selected checkout's CLI. Preserve the passage and first interpretation:
objects, assumptions, quantifiers, conclusion and ambiguous readings. Read the
named theorem and the definitions behind its argument types before comparing it
with the passage.

1. For indexed navigation, use `proof-search index freshness --repo-root REPO
   --format json`. This checks the current supported source/configuration inputs
   and reports phase timings. Add `--expected-generation ID` to compare with an
   earlier generation. It does not inspect historical database integrity, and
   its result does not remain fresh after later edits. Stored searches should
   retain their generation identity; they do not independently check freshness.
2. Select an application in the actual proof and capture it:

   ```bash
   ladon proof-search proof slice --repo REPO --source FILE.lean \
     --module MODULE --declaration THEOREM --application PROVIDER \
     --scoped --timeout-seconds 60 --max-rss-mib 12288 --output slice.json
   ```

   The timeout is per Lean process; extraction can run several processes.
   Inspect `selection`, `source`, `limits`, `nodes`, `localContext`, `frontiers`
   and `processReceipts`. Preserve the full JSON including compiled inventory.
   A memory-limit result requires reporting back before a higher-cap retry.
3. Explain which source assumptions supply the application's premises and
   whether its conclusion is the source conclusion. Distinguish a matching
   theorem statement from a matching proof method. Record unresolved providers
   and unexamined passages. A selected slice does not fill unmapped manifest
   components or establish a whole-paper audit.
4. If a particular missing implication needs formal checking, prepare an
   interpretation/object map and use correspondence checking. For a saved slice
   above the normal replay allowances, explicitly supply
   `investigation check --slice-timeout-seconds N --slice-max-rss-mib M`.
   These options authorize slice re-extraction only; they do not raise other
   checking-stage limits. Context-bridge consumers retain their normal replay
   allowances and reject saved slices exceeding them.

A short source/application report is a useful endpoint when it resolves the
reader's question. Native correspondence is optional when no such formal
obligation is needed.
