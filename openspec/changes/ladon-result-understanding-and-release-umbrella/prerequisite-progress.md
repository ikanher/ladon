# Prerequisite progress — 2026-10-02

## Discovery scope repair

The implementing LLM reproduced an omission while using discovery: `--module Main`
was passed to the type-text shortlist as a declaration-module filter, even when
the requested scope was repository-wide or explicitly selected another module.
For a project where `Main` imports `Helpers`, this hid `Helpers.useful : True`.

Discovery now uses `--module` only for the Lean checking environment. Candidate
selection uses the existing `--scope`/`--root` owner, retaining its freshness,
field-contribution, cap, coverage, and omission evidence. CLI help and the CLI
guide explain the distinction. Ordinary `search-type` module filters are unchanged.

Nine regression cases exercise repository, project, module, namespace, file,
imports, closure, neighborhood, and external scopes. Eight failed before the
fix. The imports scope includes its roots as well as direct imports; the test
expectation was corrected to match the existing scope contract.

Two ordinary-console Lean regressions create a pinned, dependency-free local
project and check `Helpers.useful` inside `Main`. Repository/stored and
module/verify requests both find the lemma, receive an accepted application,
and compile an advisory scratch replay. The fixture's initial Lake configuration
omitted the Helpers library, and its first assertion used the shortlist's
`candidateName` key instead of the discovery row's `name`; both test-harness
errors were corrected before recording passing evidence.

## Verification boundary

- Full strict quality gate: 1,767 tests passed on Python 3.11. The two new Lean
  tests were added after collection and passed separately.
- Installed wheel outside the checkout: 109 focused tests passed on each of
  Python 3.11.15 and 3.12.12, including both new Lean regressions and the existing
  offline manifest tests. The environments use locked development dependencies,
  isolated Python mode, no `PYTHONPATH`/`PYTHONHOME`, and the installed console.
- The wheel was built from an explicit copied candidate including the new
  files. This is development evidence, not a tracked-candidate release exit.
- These Lean runs use the ambient toolchain selection mode with repository pin
  verification. Network isolation was not enforced. They do not satisfy the
  explicit-pinned, network-disabled full discovery exit.

The run-state file records exact commands, source hashes, log hashes, outcomes,
and limitations. Temporary logs and installations are local replay aids, not
portable release artifacts.

## Remaining prerequisites

Canonical result-target resolution still requires the existing compatible
authority-safe and verified-discovery exits. The audit identified concrete
unfinished contracts, not only missing receipt files:

1. Upstream task 3.13 requires authority-sensitive commands to fail closed when
   configured isolation requirements cannot be met. Doctor currently reports
   `initializerIsolation: absent` and `trusted-repository-only`; the discovery
   parser has no required-isolation policy option or enforcement path.
2. Upstream tasks 3.7/3.11 require complete transition coverage across projection
   boundaries. The shared dimension owner exists, but the inspected tests sample
   transitions and do not establish the required total parent/projection/child
   corpus. Shared-owner use alone is insufficient evidence for completion.
3. The tracked-candidate integration, installed adversarial suites, explicit-pinned
   network-disabled discovery run, and compatible exit receipts remain pending.

The subsequent authority slice addresses required isolation, adds the projection
table/corpus, and attributes stored reads; see [authority progress](authority-progress.md).
Full propagation and child exit obligations remain open. Subsequent iterations should address these contracts in the upstream owner,
then issue receipts only after its declared gates pass. No authority-safe or
full discovery exit is asserted by this repair.

## Qualitative usage feedback

This feedback comes from the implementing LLM, not an independent user. The
failure was a silent missing candidate, so an empty or apparently complete
shortlist did not itself expose the unintended module filter. Comparing the
same declarations through the standalone type-text owner made the discrepancy
visible. The revised help explains how to search one module while checking in
another; the regression commands preserve a reproducible example. No search
quality or human-understanding improvement rate is claimed. Quantitative
metrics remain deferred by the user.
