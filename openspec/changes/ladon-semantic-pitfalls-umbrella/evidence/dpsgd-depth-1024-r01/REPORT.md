# DP-SGD selected application at depth 1024

The selected original proof traversal needs maximum depth **70**. With allowance 1024 it visited **61,122 nodes** and found **one** occurrence of `expected_aligned_step_bound` in `gaussian_actual_one_step`. The previous depth 64 ceiling was too low for this proof. The existing 131,072-node allowance sufficed.

## Experiment and outcome

An isolated copy of this checkout's extractor changed only the two helper depth defaults, recorded `limits.depth`, and scope-path validation from 64 to 1024. Production depth settings were not changed. [EXPERIMENT.json](EXPERIMENT.json) records the exact changes and initial hashes. [slice.json](slice.json) preserves the first attempt. The source-module compilation succeeded; generated slice compilation failed with `Function expected at hvariance`, with repeated warnings about `⋯` placeholders. No depth, node, memory, output or time limit was exhausted.

A second attempt instrumented the traversal to report maximum depth, node count and matching occurrences; [MEASUREMENT.json](MEASUREMENT.json) binds the instrumented helper. The saved [measured-slice.json](measured-slice.json) includes the diagnostic `LADON_DEPTH_MEASUREMENT maxDepth=70 nodes=61122 occurrences=1`. Traversal completes before later output reconstruction fails. Instrumented elapsed time was 17.21 seconds; maximum sampled process-tree RSS was 7,130,517,504 bytes, about 6.64 GiB. Private compilation and observation each remained within their 60-second, 12-GiB bounds. The selected application's full provider output was not obtained.

The two unavailable receipts are intentionally retained. Finding an occurrence during traversal is not an extracted/validated application or provider closure. The current evidence identifies the downstream roundtrip printing/elaboration boundary; the exact cause of the `hvariance` error is not yet established. Pretty-printer omissions are observed warnings, not a demonstrated complete causal diagnosis.

## Development consequence

A configurable CLI depth allowance is reasonable; this example requires at least 70 with the current traversal. Raising the allowance to 1024 gets past the depth check but does not yield a successful provenance extraction. Qualify the downstream term reconstruction before claiming that a higher default solves this example. No larger memory allowance is indicated by these measurements. This remains a development measurement, not a mathematical error finding or detection-benefit comparison.
