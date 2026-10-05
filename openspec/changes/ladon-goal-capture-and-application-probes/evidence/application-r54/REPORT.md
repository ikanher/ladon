# First application slice (r54)

Task 1.1 is qualified against candidate `40f91d77f97f5d8b7ab4fd0dda0a7b22394dc175`. Compact candidate and discovery text now prints projected residual propositions before their own receipt, with exact expansion references and disclosed projection omissions. JSON and existing checker authority are unchanged. Missing or malformed projected detail is unavailable, never inferred to be an empty obligation list.

The fresh installed fixed-epoch checks report `applicable-with-residuals` and `0 ≤ Mf.DP.fixedEpochCenterGap point h boundary` in both JSON and text. The two commands took 12.05 and 11.75 seconds and peaked at 8.31 and 8.35 GiB process-tree RSS under the accepted 32 GiB limit. They are separate fresh checks of a known named candidate, not an automatic discovery test, independent compiler replay, or evidence of reader benefit. Exact argv, outputs and process classifications are in `field/`.

Strict clean-checkout qualification passed 2,979 maintained tests and 29 installed CLI contracts. Isolated wheel installs on Python 3.11 and 3.12 each passed 1,061 relevant contracts. Both changed renderer modules were imported with `-I` outside the checkout and matched the recorded candidate/source hashes. `acceptance.json` records identities, wheel hash and origin checks.

Red tests failed before implementation, green changes passed, and a distinct auditor found no actionable renderer defect. The root retained the auditor report in `audit/` and subsequently satisfied its remaining installed-field gate. A quality-only test refactor was re-run against the original renderer (the same six red failures), explicitly superseded and re-frozen; all 64 frozen tests matched. Root HEAD and index were not staged or changed.

Source-position capture, per-residual contexts, declaration binder extraction and explicit completion remain separate open tasks. A scratch-only source probe can observe dependent locals, let values and multiple goals even in an unfinished file; it is not yet a product capture or identity-qualified completion input. Historical r52/r03 qualifications and reader outcomes are not renewed by this slice.
