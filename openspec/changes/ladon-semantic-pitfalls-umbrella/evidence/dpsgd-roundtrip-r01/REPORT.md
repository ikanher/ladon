# DP-SGD descent-premise provenance: development result

The isolated extractor successfully observed the original application of `expected_aligned_step_bound` inside `gaussian_actual_one_step`. The observation links its mean premise to the local value supplied by `gaussian_direction_mean`, and its energy premise through an actual argument referencing the local value supplied by `gaussian_direction_energy`. This is evidence of legitimate premise discharge in this selected application. No hidden-descent or circularity fault was established.

## Original question and faithful control

The [frozen question](../dpsgd-provenance-r01/QUESTION.json) asks whether the actual update derives descent or simply assumes it. The reusable `expected_aligned_step_bound` explicitly assumes its mean and energy identities; that is a legitimate conditional interface. The concrete Gaussian adapter must supply them. Source inspection had identified this route, but initial Ladon attempts had not exported it. These runs are informed development work, not a blind discovery evaluation.

The [compact route](ROUTE.json) binds exact original application, occurrence, scope path, source digest, local IDs and actual argument indices 35 and 36. Both argument structural graphs contain the recorded original local fvar IDs; the reported provider values are copied from that observation's local context. Name matching selects presentation rows but does not supply the binding evidence. The energy argument includes a typed identity wrapper; it must not be reported as a direct bare local argument. The observer checks and round-trips the closed application and provider terms during extraction.

The final [slice](slice-attempt-05.json) is `extracted`/`complete` for the selected application. This does not mean complete proof or provider coverage: the slice retains provider-boundary and provider-unreplayed frontiers. No independent exported provider replay, necessity proof, scientific assumption-feasibility check, full-paper certification or automatic fault discovery is claimed.

## Measured sequence

1. Existing production depth 128 reached term reconstruction, where default pretty-printing omitted terms and elaboration failed. The earlier depth1024 experiment measured actual traversal depth 70.
2. Attempt01 is a harness failure: this Lean version lacks Options.setNat. It contributes no semantic evidence.
3. Attempt02 used explicit proof/deep-term printing and a 1,000,000-step printer budget in an isolated helper. It hit Lean's 200,000-heartbeat computation allowance.
4. Attempt03 raised only the isolated heartbeat allowance to 1,000,000, retaining 60 seconds per process and 12 GiB process-tree memory. It passed the earlier reconstruction point and rejected a serialized result above 8 MiB.
5. Attempt04 measured frame 8,959,167 bytes, including 4,539,222 bytes of provider observations. This justified a modest 16 MiB export experiment before proposing a new observation API.
6. Attempt05 retained the higher printer/heartbeat allowances, depth 128 and original per-expression 1 MiB ceiling, with a 16 MiB frame/process-output allowance. Both private compilation/observation passes succeeded and agreed on the complete selected observation/compiled inventory. `validate_slice_shape` then passed.

Final elapsed time: 104.57 seconds across four bounded processes and inventory verification. Peak sampled process-tree RSS: 9,008,246,784 bytes, approximately 8.39 GiB. No process exceeded 60 seconds or 12 GiB. `ATTEMPT-05.json` binds the isolated settings and changed runtime-file digests. All attempt receipts, including failures, are preserved. Production printer/heartbeat/output settings were not changed by these experiments.

## Meaning for Ladon and the pitfalls work

The existing scoped extraction mechanism can expose this selected real premise route with larger printing/computation/output allowances. The 8-binder Nat summary profile was never a prerequisite for this observation. The experiment does not justify building a separate provenance API before qualifying the existing path's resource configuration. It identifies useful production work: explicit configurable roundtrip/serialization budgets, diagnostics distinguishing their exhaustion, and regression/compatibility qualification before promoting the successful experimental configuration.

The generic conditional estimate is a faithful control rather than a suspected bug. The concrete route supplies its selected moment premises, consistent with the source. This supports one bounded provenance question; the other pitfall families remain open. Resource/preparation/review costs and independent provider replay prevent claiming comparative benefit over ordinary source reading and Lean. A new mathematical diagnostic has not been validated by this support case alone.

## Independent review

[Independent review](REVIEW.md) validated slice shape and structural local-identity links for both selected arguments, upheld the faithful-control conclusion and confirmed the remaining coverage limits. Root reverified the selected original source digest. The bounded development probe is delivered; it does not close the diagnostic child’s acceptance gates.
