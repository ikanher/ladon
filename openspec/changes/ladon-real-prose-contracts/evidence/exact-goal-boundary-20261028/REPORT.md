# Exact source-goal boundary repair

The new additive constructor resolves the tested source-goal interoperability
blocker. Task 2.2 remains open: this is a checked component and an informed
boundary regression, not the public native connection pipeline.

## Behavior and ownership

`src/ladon/lean/LadonProseExactGoal.lean` constructs one target directly from the
live formal theorem type, ordered local premise Prop definitions and authored
Prop definition value. It checks the copied module, declaration kind, complete
source/selection range, full typed expression and expression closure. Formal
observation uses zeta normalization; the comparison projection erases binder
names, while the actual target retains original Exprs and binder names.

The target is `formalType -> premise1 -> ... -> premiseN -> authoredValue`.
Every supplied premise remains explicit. The constructor grants no proof or
admission authority. Original-to-copy association remains the orchestrator's
obligation. Existing source-goal capture/completion supplies source/import/
toolchain custody and independent kernel replay; neither the older
`correspondence_check._check_goal` nor the Real admission `_accepted` predicate
was changed or weakened.

Requests use a closed canonical JSON schema (including duplicate-key rejection),
with at most 16 distinct ordered premise owners, 100,000 rendered nodes,
depth 128 and separate 8 MiB request/rendered-expression limits. The final target
also counts toward these limits. Process-tree RSS stays capped at 12 GiB.

## Root-observed checks

- The initial compiled scaffold rejected exact-owner construction. Root retained
  that semantic red failure and froze the acceptance tests before implementation.
- Independent review found a missing rendered-byte limit. A separate regression
  reproduced the failure before the limit was added. The reviewer subsequently
  checked the final production helper and confirmed the repair.
- Four component test files cover exact target construction, ordered premises,
  original binder names, source-goal capture/completion/replay, module/range/kind/
  expression/import substitutions, duplicate JSON keys and owners, malformed
  schemas, over-limit request/output/nodes/premises, exact total depth 128 and
  rejection at depth 129. They do not claim acceptance at the exact request-byte
  or node-count ceiling.
- `FINAL-CANONICAL-TESTS.txt` records 32 passing final component tests (50.80 seconds). `COMPATIBILITY.txt`
  records 35 passing existing native-authoring and dependent-instance source-goal
  checks (150.79 seconds). Together these are 67 passing scoped checks, not a whole-repository pass.
  Generic constructor tests use pinned Lean 4.32.1 standard-library propositions;
  the informed regression uses the actual Lean 4.34.0-rc2/Mathlib context.
- Ruff, scoped strict quality and compileall results are in `QUALITY.txt`.

## Informed boundary regression

A single new constructor regression used a separately declared 600-second
engineering budget, 12 GiB process-tree RSS and 8 MiB process output. The old
feasibility probe and its closed clock were untouched. This is a test of the
new mechanism, not a reset or rerun of that old probe.

The five-order conditional witness completed kernel checking and independent
replay in 110.70 seconds at 5.78 GiB peak process-tree RSS, with no resource stop.
Trust coverage is complete, using only `Classical.choice`, `Quot.sound` and
`propext`. The original formal source is an exact prefix of the copied context;
one new helper import accounts for the verified one-line declaration-range
shift. The authored control was freshly observed in that same copied context.
The exact final source, request, capture, completion and supervised process
receipts are preserved.

The proof takes the formal theorem as the explicit `original` premise; it does
not use the theorem body as proof. The scope remains one informed conditional
boundary regression. There is no fresh formal semantic admission, native
connection, fidelity certification, mathematical falsity or discovery credit.
The earlier four-order route result remains historical and was not rerun here.

## Frozen-test refactor and review

The user explicitly approved the reviewed helper-only refactor. Root compared
all 13 mutation outputs and all 11 assertion ASTs before application; the copied
28-case suite and quality checks passed. The original source, exact patch,
proposal, equivalence receipt and approval/application record are retained under
`quality-proposal/`; the board preserves the superseded frozen revision and
new freeze. No case or assertion was weakened. Final tests run on the canonical
approved file, not just the proposal copy.

Luna-medium sidecars provided a contract/test review and an independent final
code/evidence review on the canonical board (posts 1966 onward). Workers ran no
builds or tests; execution evidence above is root-observed. The final helper
matches the revision reviewed after the byte-limit fix.

## Remaining work

Integrate this component with complete original/copy/import owner validation,
fresh formal semantic admission and authored recognition under one outer
resource/deadline lease. Implement safe bounded lossless transport for the full
formal/authored histories. Then qualify the public native connection with
unrelated positive cases, wrong direction/carrier/set/constant/scope negatives,
stale/history/resource controls and informed route outcomes. Task 3.1 and the
parent's propagation/discovery gates remain open.

All 2,670 protected primary inputs, the 24 previously integrated runtime files
and all seven earlier sealed evidence packets were verified unchanged. The
additive Lean helper changes the conservative implementation identity: old
root-aware prose histories require fresh replay; historical inspection retains
its existing meaning. No original paper/formalization was edited. Nothing was
committed or pushed.
