# r68 — accepted request-scoped canonical preparation reuse

The bounded r07 maintenance passes its preselected cost and unchanged-behavior
gates. Ordinary Lean remains the proving route; mathematical adoption and reader
benefit are not prerequisites or outcomes of this work.

## Result

The canonical owner now retains immutable artifacts and encoded occurrence sizes
for one request. Private dossier/receipt routes consume exact member handles.
Subset validation still closes exactly `[environment, check]`, with occurrence
bounds; it does not borrow missing dependencies from the full catalog. Raw APIs
continue independently validating. Every receipt and execution-context decision
still runs per check, before target/page selection.

Seven runtime files changed, including the private population helper. No public
signature, command, schema, dependency, database, session or persistent cache was
added. See [exact patch](runtime-diff.patch), [identities](runtime-identities.json)
and [acceptance](acceptance.json).

## Ordinary installed cost

Five alternating before/after pairs per workload; all forty outputs byte-identical.
Both real after operations were faster in all five pairs.

| Workload | Before median (range) | After median (range) | Reduction |
| --- | --- | --- | --- |
| Component inspection | 4.92s (4.85–5.03) | 2.67s (2.65–2.78) | 45.7% |
| Checking guide | 4.86s (4.81–5.19) | 2.70s (2.65–2.75) | 44.4% |
| Small inspection | 0.12s (0.12–0.13) | 0.12s (0.12–0.13) | none at timer precision |
| Small guide | 0.12s (0.12–0.13) | 0.12s (0.11–0.12) | none at timer precision |

Real median peak RSS decreased from 228,256 to 224,976 KiB (inspection) and
226,064 to 224,944 KiB (guide). No material small-input or memory regression.
The fixed gate required ≥20% median wall reduction and ≥4/5 faster pairs, with
material small regression above both 20% and 50ms and memory above both 10% and
32MiB. It was frozen before implementation and was not lowered.

[All samples](measurement/results.json) retain argv, output hashes/bytes, wall,
user/system CPU, peak RSS and raw timing records. These are shared-host results,
not general performance estimates. Profiling is separate: preparations fall
164→89, one population preparation and 25 exact subset validations remain;
inclusive times overlap and are not added or used to predict savings.

## Validation and limits

- Before implementation: three characterization controls pass and preparation
  reuse fails (six preparations for three occurrences). Four new owner-boundary
  tests fail because the private owner does not yet exist.
- Integrated focused run: 109 pass. Full maintained strict gate: 3,181 pass.
  Seventeen later receipt-parity cases pass separately, with focused strict
  quality, Ruff and compile checks. Do not call this a single 3,198-test run.
- Installed canonical, stored/live receipt, SQLite, compact, historical and
  result contracts: 995 pass on each Python 3.11 and 3.12. Installed origins and
  changed source hashes match the final wheel candidate. Distribution smoke passes.
- Fifty additional commands preserve bytes/exit/stderr across full/selected
  views, next pages, text/JSON, invalid selectors, relocation and raw explicit
  file entrypoints. Relocated small views also equal original views.
- Independent source audit (board968) finds no remaining issue; it did not rerun
  tests or timings. Its two initial findings compared inherited git changes;
  both were withdrawn against the actual saved r65 baseline.

Retained failures: initial strict quality found import/test hygiene issues;
exception guards were narrowed and original assertions retained. Installed
harness first lacked jsonschema, then nine relative-file tests failed from `/tmp`;
corrected development dependency/cwd runs passed. Extra receipt test preparation
initially changed environment options without resealing their environment digest;
its valid checker-identity variant passed. These are preparation/test failures,
not evidence of renewed worker qualification or runtime defects.

The first timing smoke used an earlier small fixture/preformat candidate; its
results remain local historical state and do not satisfy the final gate. The
accepted samples use the complete receipt-bearing small fixture and final wheel.
The 32GiB measured-process cap is RLIMIT_AS, not process-tree RSS supervision;
these CLI requests launch no Lean worker. Actual peak RSS is retained.

## Stopping point

Accept this maintenance and close the package. Interface expansion, another
uptake challenge and automatic optimization of the next hot function remain
frozen. The umbrella remains 33/50 with mathematical handoff proposed and
comparative benefit unmet/deferred. The next review should assess this candidate,
owner tests and measured cost, then recommend concrete user-driven work or
consolidation without treating maintenance as demonstrated mathematical benefit.
