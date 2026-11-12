# Descent-premise provenance probe

Current correction: the Nat-profile rejection does **not** block proof expansion. A subsequent public `contract expand` call accepted the same unsupported observation and privately compiled GaussianStep successfully. Its scoped extractor then failed with `expression depth exceeds 64`. See [expanded.json](expanded.json). The original account below is retained as history; its inference that no expansion was available was incorrect.

## CLI usability follow-up

The CLI now explains retained observations and the specialized summary-profile restriction on stderr, including the eight-binder allowance for telescope-limit and a concrete expansion command. Unavailable expansion surfaces the first failed process output with bounded, escaped terminal controls. Canonical JSON and snapshot contents are unchanged. The change was reviewed independently by the Luna-medium reviewer; suggestions about first-failure ordering and partial-result wording were incorporated. Six new CLI regressions cover output-file and stdout evidence preservation, missing observations, bounded native diagnostics, multiple failed processes/control characters, and partial slices. Final verification: `PYTHONPATH=src pytest -q tests/test_contract_cli_guidance.py tests/test_proof_contract_formal_cli.py tests/test_proof_contract_formal_snapshot.py` passed 13/13 in 6.87 seconds; Ruff passed on all changed Python files, and strict umbrella validation passed. Scoped extraction at depth 64 remains open; no provenance-detection gain is claimed.

## Original probe report (superseded where noted above)

Question: does the concrete expected one-step descent estimate follow from the actual Gaussian/Poisson update, or is it imported as a premise?

## Source comparison

`expected_aligned_step_bound` in `Mf/Optimization/PoissonClippedSGD/OneStep.lean` explicitly assumes `hmean` and `henergy`. Those are legitimate inputs to this reusable analytic lemma. The caller `gaussian_actual_one_step` in `GaussianStep.lean` constructs `hmean` with `gaussian_direction_mean` and `henergy` with `gaussian_direction_energy`, then passes both to `expected_aligned_step_bound`. The latter develops integrability and applies expected smooth descent and clipping alignment. `gaussian_convergence` calls `gaussian_actual_one_step` to supply its per-state `hdes`, then telescopes it. Source inspection therefore supports the route: the public convergence theorem does not take expected descent as an assumption; the concrete update supplies the moments used by the generic estimate.

This is a local source-derived support result, not a claim that the moment premises are logically necessary, nor a circularity finding. The inspected route is inside Lean and mathematics already represented in the prior C1–C4 report. It is an informed development check, not blind discovery.

## What local Ladon exposed

The local `investigation contract produce` command observed the exact statement for `gaussian_actual_one_step` under Lean 4.33.0, but returned `status: unsupported`, `statementFeatures: unsupported`, `proofBody: not-extracted` and `providers: not-extracted`, with residual `telescope-limit`. It took 10.47 seconds and peaked at 8,740,999,168 bytes RSS under the 12 GiB cap. It did not extract an application route.

A stored `theorem lineage --refresh never --view closure` query on `gaussian_actual_one_step` was manually interrupted after about 40 seconds while validating a very large archived proof-search history; no result was produced. Its traceback records time in `inspect_proof_search_index` / `history_status` / `validate_history` hashing the history. No shared index, dependency or history file was modified by this read-only query. Do not count it as route evidence or as proof that no route exists.

The manuscript and theorem capsule still provide source and dependency context, and direct Lean checks establish the earlier C1–C4 correspondences. For this provenance question, however, Ladon did not expose which local proof applications supply `hmean` and `henergy`. The route above was established by manually reading the Lean proof. Therefore this probe has **not** demonstrated automatic premise-provenance detection. It has identified a concrete extraction boundary: a long telescope blocks the existing contract observer, while the current stored-lineage request did not return promptly because history validation was expensive.

## Disposition

No mathematical error was found. P.1's question and control are selected and frozen in [QUESTION.json](QUESTION.json); P.2 remains open because the tool did not supply the route and the manual source comparison is not credited as a Ladon detection. The existing proof-contract guide documents proof-body/provider coverage as unavailable from statement production and documents provider expansion, but this command returned no artifact to expand. Any improvement proposal should separately measure the index-history validation cost and qualify a route extraction on this declaration before claiming the capability works. This result does not justify raising the memory cap or changing generic algorithm limits: the 12 GiB cap was not reached, and the observed blocker was the supported telescope boundary / slow stored-history validation.
