# Planner requirement to actual Lean goal

The public `instantiate_planned_source_leaf_requirement` operation now binds an
exposed source-leaf requirement from a freshly recomputed plan to an actual Lean
goal. The constructed three-step control completed in **80.70 seconds** within
its declared 1,800-second execution budget. Preparation included five fresh Lean
statement observations and planning; implementation and earlier debugging were
outside this execution measurement. This establishes the narrow localization
control in task 1.3, with independent evidence review and the final regressions below.

The described graph has two composition applications over three source estimates,
followed by an identity finish (three application step references). Its middle source theorem
`ThreeSteps.secondBound` supplies loss two, while the selected backward
requirement needs loss zero. That requirement uses `N2`, `N1` and `F2`; the
original endpoint uses `N3`, `N0` and `H`. The constructor captured the local
requirement using the source prefix before the endpoint declaration. Supplying
`ThreeSteps.secondBound` as its proof term was rejected by Lean. Rejection of
this term does not establish mathematical falsity or failed exhaustive search.

The planner retained a separate alternative route. Its exact source goal was
captured and `ThreeSteps.alternateBound` passed ordinary source-goal completion
and kernel replay. The original endpoint is supported by this alternative;
the result makes no whole-method certification. Repeating the identical middle
request preserved its request, prefix, generated-source and capture identities.
The original source remained unchanged.

The request owns the complete `ContractObligationPlanRequest` and result,
selected route/requirement indices and complete occurrence identity. The
operation recomputes the entire plan, validates the occurrence against its
route, derivation premise, interface and scope, and binds the exact native
contract artifact and source-map declaration range to fresh provider
observations. Matching a coarse profile alone is insufficient. The original
formal parent must still equal the original desired contract; only a verified
plan trace can supply the distinct intermediate record. The direct atomic API
retains its original parent-equality check.

The supported source fragment remains two explicit Nat binders, a named global
coefficient, and an earlier provider in the same exact source module. A selected
record must equal its provider's record apart from regularity offset. Prefix
frontend checking, exclusion of the original parent/module, exact goal DAG and
compiled-import checks remain mandatory. Partial plans can supply a retained
local candidate while preserving all route comparisons and pending coverage.
`planVerified` describes recomputation; `sourceBindingVerified` additionally
requires fresh source observations and symbol-role checks. Neither authenticates
the attributed prose reading or method graph.

Source stages share the earlier outer/planner deadline and supervised resource
limits. Staging checks expiry before mutations and rolls back only files
exclusively created by the failing attempt. Memory-stop instructions are retained.
**Python replanning is cooperative:** the outer deadline is checked before and
after the call; it does not forcibly interrupt that call. This limitation remains
open for a stricter orchestration contract.

Full raw records, original source, generated source and hashes are in
[planned-source/MANIFEST.json](planned-source/MANIFEST.json). The machine-readable
[acceptance record](PLANNED-SOURCE.json) retains limits, runtime source hashes,
resource receipts, prior failed attempts and coordination incidents. The timed
run was serial and began after those exploratory test incidents ended. Its 27
receipts show a maximum of 3,748,958,208 bytes (3.49 GiB), with no resource stops.
Independent review corrected the initial aggregate, which had omitted completion
receipts using camelCase field names.

The complete outer source request was held in driver memory, rather than
serialized. In particular, its original monotonic deadline cannot be
reconstructed from the raw report. Repeated `requestDigest` equality is empirical
evidence from the retained driver, not an independently recomputed digest from
a retained complete input wrapper.

Reproduce from this checkout with a fresh output directory:

```bash
PYTHONPATH=src:tests .venv/bin/python \
  openspec/changes/ladon-proof-contract-bidirectional/evidence/run_planned_source_fixture.py \
  --output /tmp/ladon-three-step-control-new
```

This is a constructed development fixture. It does not estimate unseen-paper
detection benefit or exercise beam search. Domain/representation and conclusion
transfer, ordered obligation bundles, provider-slice dispatch and the native/CLI
workflow remain unfinished; tasks 1.2 and 2.2 remain open. The earlier matched
matrix/portable no-beam baseline remains immutable and predates this adapter.

Validation: **797 checks passed in 252.39 seconds** (763 prior compatibility
checks and 34 additional checks). Whole-repository no-cache Ruff and strict
quality checks pass, as does frozen-test verification. The exact command and
JUnit report are retained as [command](PLANNED-SOURCE-INTEGRATION-COMMAND.json)
and [results](PLANNED-SOURCE-INTEGRATION.xml). Independent review checked the
canonical code, reproduced two defects before their fixes, reviewed the fixes,
and verified all raw manifest and production-source hashes. The corrected
resource maximum and outer-request serialization limit are recorded above.
