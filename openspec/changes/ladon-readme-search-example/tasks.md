# Tasks

## 1. Replace the headline example

- [x] 1.1 Verify the three Mathlib type searches from the [design](design.md), with a literal and a formatting-aware source baseline on the same checkout. Verify an accepted direct application of `MeasureTheory.integral_prod` with no residual goals and a rejected direct application of `MeasureTheory.integral_integral`. Mathlib `db584cd6` returned 1, 1, and 8 signature matches. Fixed-string searches found none of the exact compact strings. Spacing-aware searches located the intended declarations, including a multiline match for Fubini. The application check returned the expected outcomes.
- [x] 1.2 Publish the progressive examples and the pinned setup. Replay the exact README and Mathlib walkthrough commands from a clean scratch directory. Confirm the README scopes its type-search findings and attributes application checking to Lean. A fresh v4.33.0 checkout reproduced all three README searches and both Fubini application outcomes. The 19 focused proof-search and RH lookup tests passed.

## 2. Keep the archive walkthrough runnable

- [x] 2.1 Give the RH walkthrough a standalone setup for the three verified files. Replay the two documented searches and check the Fourier and completing-the-square hits. Keep the fixed-string baseline in the implementation record. The documented commands returned `fourier_gaussian_real_place` at line 122 and `qf_add` at line 24. The literal source baseline had five matching lines.
