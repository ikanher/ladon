# Ladon 0.4.2 internal development snapshot

This internal snapshot collects bounded proof-extraction controls, a closed-proof
printer repair, and source-to-formal audit guidance. Ladon remains alpha. Lean
checks supplied terms; it does not certify that a natural-language passage was
interpreted correctly.

## Changes

- Proof slicing and contract expansion default to depth 128 and accept an
  explicit `--max-depth` bound. The selected bound is recorded across consumers,
  and bounded extraction failures are reported clearly.
- Closed proof serialization uses a finite 200,000-step printer budget and
  rejects omission syntax before replay. This prevents truncated pretty-printed
  expressions from being mistaken for complete proofs. Larger expressions may
  still be rejected at the explicit limit.
- The correspondence guide and Ladon skills explain definition substitution,
  premise attribution, and checking a complete theorem application under the
  source assumptions, including conclusion transfer and unresolved outcomes.
- The semantic-pitfalls work records a real PLD reconstruction-formula error,
  several source audits, and a negative comparative pilot. Incremental detection
  benefit from Ladon's native tools remains unestablished.

## Verification

The inherited printer qualification passed its focused regression and affected
completion suite (14 tests), with native replay/trust checks for the completed
claim. In this release-preparation pass, 22 focused completion, depth, guidance,
and release-contract tests passed; `uv lock --check` passed; and strict
validation accepted all 91 OpenSpec items. The versioned lockfile was refreshed
for 0.4.2.

The full strict quality command currently fails on ten complexity findings in
pre-existing real-bound modules and tests, outside this release's code diff.
A clean checkout of commit `c0d3cfa` subsequently built and installed the package,
passed all 41 installed CLI contracts, and passed the pinned real-Lean
integration gate. Temporary files were placed on the main disk after `/tmp`
user-quota failures during the initial archive extraction attempts.
The optional full candidate suite was intentionally stopped after 561 passing
tests in 263.41 seconds; this is a partial result, not a full-suite pass.
[Verification receipt and logs](releases/0.4.2/verification.json) identify the
candidate. Follow-up edits correct the handoff path and record these results;
the tested production code is unchanged. Both supported Python-version CI jobs
and a complete strict release gate remain unverified.

## Distribution and limits

This is for local internal use. It has not been pushed or published. The
repository's publication gate remains blocked pending an owner-granted license.
The prior 0.4.1 notes retain their own candidate-specific evidence and limits.
