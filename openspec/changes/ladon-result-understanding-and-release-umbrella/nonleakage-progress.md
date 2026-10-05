# Maintained execution nonleakage gate — 2026-10-02

Candidate `8ef4da28a87b2435beea87e9e7b4491cd8156816` adds a maintained gate
for discarded caller environment inputs. It injects seven synthetic values and
checks their absence, together with six disallowed key names, across launch,
evidence and presentation paths. Ladon's derived `LEAN_PATH` key remains valid
metadata; its injected caller value must be absent.

This is verification coverage for existing behavior. All 297 package members and
the complete r20/r21 wheel archives are byte-identical. The added files are tests,
test support, documentation and OpenSpec evidence; no runtime repair was needed.

## Covered paths

| Maintained suite | Cases | Exercised boundary |
| --- | ---: | --- |
| `test_execution_nonleakage_scanner.py` | 4 | Positive contamination controls for every marker in diagnostic, metadata-key and binary carriers, plus SQLite sidecar scanning |
| `test_execution_nonleakage_failures.py` | 20 | Actual child environment observation; version/pin failures, missing compiled module, nonzero/invalid frames, timeout/output/RSS limits, single/batch/scratch failures, ambient preparation, and RSS platform policy |
| `test_execution_nonleakage_discovery.py` | 5 | Framed accepted/rejected/residual batch observations with compiled or failed scratch; production evidence construction, persistence, all projections/renderers and stored expansion |
| `test_execution_nonleakage_lean_integration.py` | 6 | Ordinary installed commands against pinned Lean 4.32.1: three direct outcomes, explicit/ambient discovery plus advisory scratch, and preflight rejection without publication |

Failure subprocesses independently write their actual environment under an ignored
build directory. The test scans that observation even if the shared output cap
omits stderr. Direct failure results, diagnostics and progress are scanned along
with artifact/receipt output. Discovery fixtures exercise all audit/LLM/review JSON
and text views, preserving failed scratch's weaker evidence. Real-Lean runs scan
attempt logs for residuals and reload both candidate and scratch checks through
the ordinary stored-evidence command. A live reader retains a nonempty SQLite
write-ahead log while production delivery registers evidence, so both database
and sidecar bytes are inspected.

The six real-Lean cases run Lean only for the initial observation and reuse its
captured artifacts across renderers. Required mode fails when the pinned fixture
toolchain or Linux `/proc` RSS measurement is unavailable. Ordinary test runs can
skip those unavailable capabilities. See the exact gate command and installation
procedure in [execution policy](../../../docs/EXECUTION_ENVIRONMENT.md).

## Qualification

- All **35 new cases** pass as part of **302 relevant installed tests on each of
  Python 3.11 and 3.12**, with `LADON_REQUIRE_EXECUTION_NONLEAKAGE=1`, isolated
  interpreter mode, the selected installed console and no `PYTHONPATH`/`PYTHONHOME`.
- The required benchmark passes **17/17** cases with zero correctness or stability
  failures. Scoped strict quality, Ruff and compilation pass.
- The clean-candidate gate passes **2,441 maintained tests** and **29 installed
  CLI contracts**, strict quality, compilation, distribution/resource and
  collection checks.
- Source-first review found one test portability issue: unguarded RSS assertions
  would time out on platforms without `/proc`. The correction adds ordinary-skip
  versus required-failure behavior and checks both branches. No runtime defect was
  found in this slice.

Initial test-harness corrections were needed for a nonexistent SQLite column,
a residual fixture's closed protocol shape and the assumption that stderr survives
an output cap. Final tests instead scan the registry's actual WAL, use the closed
residual schema and independently capture the child environment. These were
checker/fixture failures, not Lean theorem failures or detected secret leaks.

Raw commands and logs are under `/tmp/ladon-nonleakage-dg68rdqn`; current and
historical evidence hashes are retained in [apply-run-state.json](apply-run-state.json).
The wheel is `/tmp/ladon-isolation-authority-vetts2n2/dist-r21/ladon-0.2.0-py3-none-any.whl`.
The candidate commit belongs to the isolated local qualification repository; the
user's Git index was not changed.

## Exposition and scope

The [frozen fixed-epoch exposition baseline](baselines/fixed-epoch-v1/README.md)
retains all **127 file hashes** and all **nine expected outcomes on each runtime**.
Successful output bytes are unchanged; failing/unavailable cases retain their
exit codes and diagnostics. Exact comparison evidence is in
[baseline-nonleakage-comparison.json](baseline-nonleakage-comparison.json).

This gate covers selected synthetic environment inputs and exercised output
carriers. Framed discovery failure observations are explicitly mocked; real Lean
cases are separate. The gate does not detect arbitrary secrets, isolate target
code or protect secrets supplied through allowed values, files, sources or goals.
It does not hash every compiled library or complete any full authority/discovery
exit. The result umbrella's mathematical coverage and unavailable dossier/guide
commands retain their existing baseline status.

## Roadmap boundary and next action

Prerequisite task **3.5 is complete**, bringing its umbrella to **41/76**. The
result umbrella remains **9/50**, and the claim child remains **5/8**. No complete
authority, correctness, integration or discovery exit is emitted by this slice.

Next, complete task 1.3's historical installed defect reproductions with honest
retrospective provenance, then freeze task 3.16's complete authority-suite
inventory and its candidate-bound evidence bundle. Reconcile the ledger's full
exit-class name with the receipt gate's abbreviated name explicitly; verify suite
coverage and referenced artifact bytes in addition to receipt syntax. Authority
and correctness can finish independently in Wave 1. Their compatible complete
exits remain prerequisites for integration and downstream result evidence.
