# Source-first planning baseline

This is planning evidence, not a reproduction or a passing test report.
`baseline.json` binds 62 implementation, test, guide, and historical inputs plus
the observed revision and dirty status. Reconcile drift before implementation.

## Observed field outcome

Primary report: `/home/codex/projects/navier-stokes-retest-5/runs/independent-01/FINDINGS.md`.
No paper error was established. Three distinct local claims were encoded; repeat
checks and typing goals are not extra mathematical claims. The formal endpoint
rebuild passed, while correspondence remained incomplete.

- The original cubic interpretation computed numeral-only `41/20` and
  `305719/1152000` at Nat before conversion to Real. The frozen original review
  missed it; a feedback-driven correction and a new typed record are preserved.
  The corrected record supplies an intended-semantic control, not retroactive
  validation of the first record.
- The adjacent derivative-letter application retained actual scoped A₀/A₁
  objects but left connecting goals unsupported due to their names. Its formal
  conditional/provider checks succeeded; this is not a false paper claim.
- `CORRESPONDENCE-TIMING.json` records public checks around 274–515 seconds,
  including repeated subjects and concurrent builds. These measurements do not
  isolate a bottleneck. Three checked bundles required compact serialization to
  fit the current 32-MiB input limit.
- The report froze at 3459.012 seconds, with 1940.988 seconds remaining. All
  final finish commands returned `continue`, exit 2, `mayFinalize=false`. The
  report disclosed this; the failure is continuation/termination discipline,
  not a gate that falsely returned complete.

## Inspected implementation and tests

| Owner | Observed behavior | Planned package |
|---|---|---|
| `correspondence_interpretation.py:lower_formula` | Numerals emit bare digits; applications emit symbol name/arguments without the declared use-site type | A |
| `correspondence_check.py:_check_goal` | Separately checks symbol types, then copies/elaborates source and captures/completes each generated goal | A, C |
| `correspondence_check.py:_LOCAL`, `_local_bindings` | Restricts local display spelling and constructs links from displayed types/expressions | B |
| `correspondence_maps.py`, scoped slice helper, expression DAG | Context identities exist, while public object maps use names | B |
| `correspondence_check.py:_verify_inputs_unchanged` | Fresh post-request extraction guards acceptance | C; preserve |
| `investigation_correspondence_inputs.py`, CLI loader | Bounded full native bundles; 32-MiB plan input | C |
| `investigation_correspondence_status.py:_final_status` | Returns `continue` for pending work before deadline; v3 `mayFinalize` currently reflects only completion | D |
| Existing correspondence representation, scope mutation, witness escape, ambient context, freshness, and v3 tests | Parent consuming contracts that must keep passing | All |

Evidence entry points within the run: `NATIVE-INDEX.json`, `PLAN-INDEX.json`,
`inner-corrected/record.json`, `axis-recursion/correspondence/record-02.json`,
and the original/corrected/fresh numeric reviews. Their hashes are bound; new
regression probes and results must be written elsewhere. The real passages are
known development inputs, not withheld tests.

Canonical spec inventory was checked with `openspec list --specs`. Native-v3
schema and observation authority requirements were read in full. The completed,
unarchived predecessor's interpretation/slice/check/review specs provide the
correspondence baseline; the new capability deltas add more specific guarantees.
No canonical spec, prior packet, historical run, or production source was edited
while preparing this umbrella. Quux's active marker remains unchanged.
