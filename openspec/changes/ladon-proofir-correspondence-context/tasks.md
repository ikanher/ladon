# Tasks

## 1. Inspect exact source and formal context

- [x] 1.1 Add regression tests and implement exact-owner context joins with byte-bounded whole-component omission; verify identities, missing rows/tables, multibyte boundaries, unchanged dimensions and historical coverage.
- [x] 1.2 Expose the allowance through the existing public inspect command and document v2 authority/coverage; verify the actual CLI against a valid native bundle and invalid options.

## 2. Qualify integration

- [x] 2.1 Run relevant query/CLI tests, strict quality and OpenSpec checks; inspect the final diff, record limitations, and link the result from the pitfalls umbrella without crediting detection gain.

## Result and verification — 2026-11-15

Implemented in existing `proofir_v3_queries.py` and `correspondence_cli.py`.
The [audit guide](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#inspect-the-stored-source-and-application-together)
documents the public command, response version, per-component allowance and
coverage/authority interpretation. No canonical or SQLite schema changed.

Verification:

- Initial 11 query tests failed on v1 output, missing context and absent allowance;
  implementation then passed. Added a multibyte test and public CLI tests.
- `.venv/bin/python -m pytest -q tests/test_correspondence_context*.py tests/test_correspondence_projection.py tests/test_correspondence_query_coverage.py tests/test_correspondence_author_cli.py tests/test_correspondence_schema*.py tests/test_proofir_query_contracts.py`: **43 passed**.
- `.venv/bin/python -m pytest -q tests/test_correspondence_investigation_v3.py tests/test_correspondence_investigation_init.py tests/test_correspondence_quantifier_author_cli.py tests/test_correspondence_historical_profiles.py tests/test_correspondence_projection.py tests/test_correspondence_query_coverage.py`: **11 passed**; four overlap the prior suite.
- Ruff and `ladon.quality.strict_quality_issues` pass on all four changed Python files.
- Strict OpenSpec validation passes for this packet and its parent; `git diff --check` passes.
- Root reviewed exact-owner predicates, whole-value omission, SQL-side UTF-8 sizing,
  unchanged result dimensions and public versioning. No independent review claimed.

The public-path test extracts a real small Lean application, authors/aligns its
interpretation through the entrypoint, then inspects its valid native artifacts.
The test was corrected to use the actual fixture declaration names and compare
against the canonical stored slice (which normalizes process receipt floats),
rather than its precanonical Python extraction. A helper split resolved test
complexity without changing expectations.

Limitations: this improves stored evidence delivery. It does not certify source
interpretation, reconstruct an absent object map, verify a corrupt projection,
rerun Lean on inspect, or measure detection/reader benefit. The CLI still loads
its input bundle under the existing 32 MiB cap; the context allowance controls
native response components. Broader semantic stages remain deferred. The next
ProofIR question at that checkpoint was whether checked targets and mapping
dependencies survive inspection; the follow-up below records the diagnosis.

## 3. Inspect each obligation's stored checking target

- [x] 3.1 Expose bounded receipt evidence for each exact check reference and compare its plan, obligation, goal digest, polarity, status and check operation to the stored correspondence. Verify mismatches, missing/digest-only/oversized receipts, exact owners and limited rows without promoting stored labels.
- [x] 3.2 Qualify the public inspect path with an actual checked bundle, document the consistency-only boundary, run affected tests and strict quality/OpenSpec checks, and record the remaining dependency-map limitation.

## Follow-up result — 2026-11-16

The trace found no lost target inside the checker: it rebuilds the source/slice/map
plan, checks fully closed generated goals (or their negations), and retains exact
target/polarity metadata in the existing correspondence receipt extension. The
inspection projection previously omitted that metadata.

Native inspection now exposes `checkEvidence`, exact check references, bounded
stored receipts and explicit binding comparisons. It compares plan/obligation,
canonical goal digest, checkedGoal, mode, operation, status and outcome polarity.
Non-open displayed obligations without matching evidence are listed separately.
Missing tables/owners/check-local IDs, digest-only or oversized payloads and row
omissions keep coverage incomplete. One shared receipt allowance prevents output
from multiplying by the per-component byte cap. Original result dimensions and
stored authority remain intact; no canonical schema or dependency changed.

Verification:

- All 15 initial regression cases failed because checkEvidence was absent. The
  implemented missing-obligation case was corrected to report a mismatch; all
  initial cases then passed. Two more controls cover absent checks and invalid
  refutation/status polarity.
- New query tests and CLI tests: **22 passed**, including a real native checked
  bundle, in 149.67 seconds. Root verified the final inspection code again against
  that retained bundle: all five checks had accepted replay, completed parent
  support, matched stored bindings and no unbound obligations.
- Final affected query/binding/schema and CLI suite: **62 passed, 1 deselected**
  in 7.04 seconds. The deselected test is the already completed real five-check
  run above; its retained bundle was used for final CLI verification.
- Ruff and strict Ladon quality pass on all three changed Python files. A helper
  extraction reduced query complexity without changing behavior. Strict packet
  and parent OpenSpec validation and whitespace checks pass.
- The small real bundle exceeds the default formal-slice allowance: default
  inspection correctly reports complete check bindings but incomplete formal
  context. Reinspection with `--context-max-bytes 8388608` delivers all context
  with complete coverage. A root assertion expecting complete default context
  was corrected to respect this explicit bound; no production failure was hidden.

This is root-reviewed local/CLI qualification, without independent review or a
new detection score. The tests use disposable corrupt projections for adversarial
cases; their authored labels do not claim mathematical acceptance.

Remaining boundary: the plan identity carries the complete source, slice and
object map, but there is no newly inferred per-obligation dependency graph or
certified prose translation. Fully coordinated fabricated evidence is outside
this stored-consistency check's authority. The next useful question is whether a
reader can resolve a mapping/conclusion issue using the now-visible targets;
add a representation only if a concrete relationship is lost. Broad diagnostic
integration and historical acceptance gates stay deferred.

## 4. Qualify mathematical meaning through inspection

- [x] 4.1 Use three exposed source/formal controls: faithful representation, failed mapping of the same true source claim, and pointwise-versus-uniform quantifiers. Preserve first attributed interpretations, actual Lean checks and native inspections; verify a refuted route is not reported as source falsity. Record whether the existing representation loses a necessary relationship before proposing a schema extension.
- [x] 4.2 Document the supported reading procedure and disposition, retain exact evidence/limits, and validate packet/parent coherence. This is exposed root qualification, not a fresh reader comparison or new detection score.

## Mathematical qualification result — 2026-11-16

[The three-control report](evidence/mathematical-controls-r01/REPORT.md) records
faithful support, a refuted map for the identical true source, and a refuted
quantifier transfer with a separately checked source refutation. Nine native
checks completed with replay/trust acceptance; all three native inspections had
complete coverage and matching receipt bindings. Main bounded execution took
272.81 seconds. Relevant source propositions compiled separately without axioms.

The current representation preserved the decisive distinctions on these exposed
controls; no new runtime/schema change was warranted. The audit guide now gives
an explicit reading procedure, including typing-only interpretation/map checks
and the different authority of link refutation versus original-source refutation.
No fresh reader, independent review, comparative benefit or stochastic-context
coverage is claimed. Broader diagnostic integration remains deferred.

Final qualification checks: read_results.py passes; all 51 retained evidence
manifest entries verify; local report/guide/task links resolve; Ruff passes on
both evidence scripts; strict packet and umbrella validation and whitespace
checks pass. No production code changed in this mathematical qualification.

## 5. Trace existing MF cases through the evidence boundary

- [x] 5.1 Trace the retained fDP conditional countermodel and DP-Adam supported construction from source interpretation through original assumptions, object definitions, checked results and qualified reader verdict. Bind selected evidence and verify retained manifests/source receipts; disclose prior exposure and historical checking authority.
- [x] 5.2 Exercise existing receipt admission on the actual ordinary and native records; distinguish missing production from missing representation or inspection. Deliver a reproducible trace, a focused gap assessment and the next bounded action without inventing native authority or rerunning the mathematics unnecessarily.

## MF trace result — 2026-11-16

[The exposed two-case trace](evidence/mf-trace-r01/REPORT.md) binds the conditional
fDP refutation and supported DP-Adam construction to retained source and receipts.
All 69 entries in their two retained manifests verify; both source files match
successful ordinary Lean receipts. The smaller native DP-Adam scalar completion
is checked against its raw retained output. Existing admission correctly rejects
promotion of ordinary compilation into native correspondence acceptance.

The larger results were never produced as native correspondence bundles; this
exercise therefore found a production boundary, not a reproduced lost relationship
in native inspection. No runtime/schema change or new Lean run occurred. Native
authoring of the richer cases remains unqualified. Next qualify one supplied-proof
fDP application through the existing path, with the source-order ambiguity explicit,
then the DP-Adam common-law positive path. The report owns exact acceptance and
authority limits. This is exposed development, not a fresh detection result.

## 6. Produce native evidence for the existing MF cases

- [x] 6.1 Produce an actual inherited-order fDP application slice and native correspondence checks through the public CLI, preserving the original finite countermodel and source-order ambiguity. Inspect exact targets/receipts and distinguish link refutation from the separately established source counterexample.
- [x] 6.2 Qualify DP-Adam's existing common-law application as the positive path, or retain an exact unsupported input/diagnostic. Keep common-law quantifiers, source assumptions and ordinary/native authority explicit. Record outcomes and any demonstrated capability gap.

Execution scope: exposed supplied-proof qualification, local project, read-only
existing compiled dependency roots, 30-minute aggregate execution allowance,
initially 300-second outer commands, unchanged helper bounds, 12-GiB process-tree RSS cap
and 8-MiB captured command output. No downloads or full donor rebuild. Stop a
resource-limited route and report it; do not silently increase limits.

- [x] 6.3 Repair the reproduced correspondence module-inventory limit mismatch with exact-path 32768-entry bounds, unchanged generic limits and byte identities. Qualify boundary/escape tests and rerun the retained real public alignment and inspection before accepting the fix.

User authorized an 1800-second outer timeout after the ordinary and request-mode
fDP checks each exhausted 300 seconds. The [timeout revision](evidence/mf-native-r01/TIMEOUT-REVISION.json)
records the extension and new deadline; all prior attempts and costs remain part
of this exercise. Memory and individual helper limits are unchanged.

Inventory repair verification: public fDP align and inspect initially rejected
the actual 11034-module slice. Both now succeed without dropping modules. A
10-case initial regression run had four expected failures; a later standalone
projection case also failed before its fix. The final relevant suite passes
175 tests; Ruff and strict quality pass. Generic collections, nested rows,
wrong kinds/schemas, upper module bounds and artifact byte bounds remain tested.
A pre-existing unused private validator parameter was renamed `_env` to satisfy
the touched-file quality gate; positional callers and behavior are unchanged.
This closes the serialization repair only; native mathematical outcomes remain
owned by 6.1 and 6.2.

## Native MF qualification result — 2026-11-16

[Final report and reproducible verification](evidence/mf-native-r01/REPORT.md):
both richer cases now pass the public extract/interpret/align/check/inspect path.
All eight obligations have completed native replay/trust checks. The fDP
conclusion transfer is refuted; DP-Adam's attributed common-law interpretation
is supported. Both native inspections have complete coverage, matched stored
bindings and no unbound obligations. The original source-order ambiguity and
whole-exposition limitations remain explicit; no new discovery score is claimed.

The first 1800-second attempts exposed the same generic size limit inside receipt
hashing after 488.04/441.28 seconds. Exact-path captured-inventory support repaired
that third site; three new regression failures preceded the fix. The final suite
passes 184 tests, with Ruff and strict quality passing. Final checks completed in
498.73/447.57 seconds at 8.99/9.46 GiB peak RSS, below the unchanged 12-GiB cap.
Previous timeouts and failed attempts are retained and counted as development
costs. Separate project checks ran concurrently; no comparative speedup is claimed.

`read_results.py` verifies exact goals/polarities, accepted replay/trust, inspection
bindings, input and compiled-import custody, and original proof prefixes. The
report describes the named DP-Adam predicate and its source-visible definition;
inspection does not automatically unfold it. The real sources did reveal an
operational capacity bug, now fixed; they did not demonstrate a lost mathematical
relationship requiring a new ProofIR schema. Consolidate this exposed workflow
and retain the r03 review archive unchanged. Further discovery/value evaluation
requires a concrete prediction and separately declared fresh inputs.

## Workflow consolidation — 2026-11-16

The [native MF reading recipe](../../../docs/PROOF_CORRESPONDENCE_AUDIT.md#read-the-native-mf-examples)
now gives local-executable inspection commands and six steps covering attributed
source meaning, wrapper/predicate definitions, generated targets, receipt
bindings, qualified verdicts and costs. It distinguishes the historical supervisor
timeout from production CLI defaults and identifies the frozen launch script's
expired deadline. No new checker run or runtime change was needed.

Both documented public inspection commands were executed into disposable scratch
outputs and reproduced the retained inspections exactly. The custody script
passes again, all 70 manifest entries verify, and the frozen evidence is unchanged.
This completes consolidation of the existing 12/12 qualification tasks; it adds
no fresh reader or detection-benefit claim. Further investment remains a decision
for the pending r03 review or a concrete internal reader question.

## Internal 0.4.3 consolidation — 2026-11-17

All 12 tasks remain complete within their stated scope. The completed capability
is synchronized into the main `proofir-correspondence-context` specification.
The parent R package also completed the diagnostic/telemetry repairs and actual
reader handoff; ordinary navigation answered the question. Keep this completed
change and its immutable evidence at the current paths for receipt/link
stability. No new native run or broader diagnostic acceptance is implied.
Release qualification and known limits are in [the 0.4.3 notes](../../../docs/RELEASE_0_4_3.md).
