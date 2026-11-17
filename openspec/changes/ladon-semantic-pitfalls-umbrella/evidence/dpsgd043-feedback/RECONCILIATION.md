# DP-SGD internal 0.4.3 feedback reconciliation

Reviewed 2026-11-17 against Ladon `94cfb203f304f9a7cbe98e0e98507b69c8177f9b`.
The consumer used MF `4dfd3d8d46943ac92d9d122130f00894c3124b30`, dirty, with
Lean 4.33.0. This is assisted, non-blind field use with previous findings
available, not a new discovery comparison or release gate.

## Evidence checked

The supplied `dpsgd-exposition-ladon043-feedback.zip` has SHA-256
`8250543933237ceb7439ca5dc3b3a701c519cc9907cd9d373cd38d4a198c1495`.
All 54 entries in its SHA256SUMS verify; README.txt and SHA256SUMS itself are
outside that manifest. All 22 JSON files parse. All 15 recorded source/toolchain
hashes still match the read-only MF donor, including the two included sources.
The saved slice identity recomputes, its selected summary fields match the raw
slice, and the native inspection summary agrees with the raw stored view.

[VALIDATION.json](VALIDATION.json) records these checks, timings and identities.
[FEEDBACK.txt](FEEDBACK.txt) and [review.json](review.json) retain the consumer's
claims. The local `temp/dpsgd-exposition-ladon043-feedback.zip` and extracted
directory retain the full input; this evidence directory retains selected small
records only. Its [RETAINED-FILES.json](RETAINED-FILES.json) binds those copies.
The copied original SHA256SUMS describes the full ZIP, not this subset.

No supplied script was executed. No new Lean replay, candidate retry, MF edit,
dependency update or performance profiling was performed. Current CLI help and
source inspection checked the interface findings. A fresh temporary lexical
fixture independently reproduces the name/type-text provenance difference:
[LOCAL-PROVENANCE-PROBE.json](LOCAL-PROVENANCE-PROBE.json). This fixture is not a
Lean theorem check; its initial wrong `--query` invocation was corrected to
the documented `--text` and is disclosed in the record.

## Finding dispositions

| Feedback | Disposition | Evidence and implication |
| --- | --- | --- |
| Useful exact search and scoped application | Supported by retained records. | Searches take 0.164–0.215 s whole-command time. The selected application uses `stationarityUpper_mono` with the produced `stepRateD_optimal` premise. Provider-boundary and provider-unreplayed frontiers remain. This does not validate the prose's differentiation method. |
| Candidate exceeded 4 GiB | Confirmed operational failure, not mathematical rejection. | Explicit `--max-rss-mib 4096`; sampled peak 4,419,682,304 bytes; 10.029 s. The memory diagnostic correctly stops progress. No candidate was assessed and no higher-cap retry is authorized by this feedback intake. |
| Slice lacks time/RSS overrides | Confirmed interface gap. | `correspondence_cli.proof_slice_main` exposes nodes/depth only. Both `extract_proof_slice` and `SliceRunner.run` fix 60 s per process and 12 GiB RSS. The separate slice succeeded in 34.717 s with peak 7,337,013,248 bytes (6.833 GiB). This is not a retry or evidence that the production 12 GiB default is insufficient. |
| Comprehensive status is expensive | Timing confirmed; cause unresolved. | 59.483 s internal, 59.616 s whole command; 267,753 declarations, 10,208 modules, 993,472,512-byte database and 48,910,589,952 history bytes. Code includes counts/schema/history/storage diagnostics plus two source snapshots. These are candidate costs, not measured attribution. History deletion or caching is not justified by this record alone. |
| Name/type-text provenance differs | Confirmed in records, source and fresh lexical fixture. | Name has stored generation/index identity and `unchecked` freshness; stored type-text lacks these identities and reports `stored`. That policy label must not be mistaken for a source freshness check. |
| Slice output needs a compact view | Reader need accepted; size claim refined. | The saved public JSON is 2,011,398 bytes (1.918 MiB); 2,588,268 bytes is each successful Lean helper stdout, not the saved file size. The reader's authored summary is useful evidence of delivery friction. Preserve full evidence and explicit omissions in any compact view. |
| Exposition recipe is scattered | Accepted documentation feedback. | Existing guidance contains the distinctions but leads into interpretation/alignment/checking rather than a short path for TeX plus a named theorem without a native bundle. A reader should be able to stop after a bounded source/application review with its actual authority. |

The reported historical f-DP inspection took 1.115 s and retains four matched
bindings, refuted-correspondence parent support and attributed-unreviewed prose
fidelity. It supplies no evidence against the current DP-SGD note. Manifest
validity with unmapped components and unavailable/not-ingested lineage were
reported honestly. There is no demonstrated false-support defect in this bundle.

The installed and checkout package-content identities differ even though both
report 0.4.3 and the same observed source revision. The consumer explicitly used
the checkout for substantive field operations. Keep that invocation guidance;
the installed identity does not establish byte equality with the checkout.

## Mathematical scope

The included Lean endpoint visibly applies monotonicity to its algebraic
optimizer result. A matching endpoint does not certify the separate derivative
argument in prose. The centered-coordinate criticism is also supported by the
included passage: at q=1/2, u=1, its displayed r(z) is
exp(-1/8) cosh(z/2). Its expectation under N(0,1) is 1, while under N(1/2,1)
it is cosh(1/4), greater than 1. The reference measure must be explicit. This is
an analytic/source check here, not new Lean evidence or automatic Ladon discovery.

The missing table parameters and proposed scientific extensions remain
attributed MF editorial work. This intake does not replay their numerical or
asymptotic claims, amend the manuscript, or certify the whole DP-SGD proof.

## Recommended next work

First make a bounded interface/documentation follow-up:

1. Expose slice `--timeout-seconds` and `--max-rss-mib`, display existing defaults,
   and preserve the chosen bounds in execution, diagnostics and slice identity.
   State that the timeout is per process, not whole-command wall time. Inspect
   both correspondence re-extractions and proof-contract consumers: nondefault
   bounds must not create spurious identity mismatch or silently raise a caller's
   authorized replay budget. Test defaults, invalid values, propagation, failures
   and compatibility before any large live run.
2. Bind stored type-text results to generation and index identity from the same
   read snapshot as their rows. Distinguish retrieval policy from verified
   freshness, preserving documented compatibility. Test both search paths and
   generation changes; verify mode must not attach another generation's evidence.
3. Put a short TeX-plus-named-theorem recipe in the shared and bundled skill:
   freeze the source reading, inspect theorem definitions/assumptions, capture
   the selected application, separate statement/method support, retain frontiers,
   and create correspondence only when needed. Extraction does not populate an
   unmapped manifest or certify unexamined spans.

Then assess a compact projection using the saved slice, without rerunning Lean:
show selection, source/environment identity, application, premises, frontiers,
limits and receipts first, with a reference to the unchanged full evidence.
Reuse existing projection conventions; do not introduce another ProofIR schema
merely to reorder delivery. The consumer's summary supplies the initial use case.

For freshness, ordinary name search with `--freshness verify` already avoids the
full status diagnostics while returning generation and scoped coverage. It still
hashes supported inputs twice and is not a cheap batch token. Stored queries
remain unchecked. Measure the verified-query path against comprehensive status
before choosing another command, shared validation or caching. Type-text verify
currently still calls full status. `status --no-verify-sources` avoids hashing,
but keeps diagnostics and makes no live-freshness claim; it is not a replacement.

No source-memory cause is identified. Profile before optimizing or raising
defaults. No broad diagnostic integration, new comparative campaign, 0.4.3
acceptance rewrite or automatic implementation follows from this intake.
