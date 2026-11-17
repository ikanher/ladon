# Ladon 0.4.3 internal consolidation

This internal alpha snapshot consolidates source-to-formal correspondence
inspection and the completed MF qualification. Lean checks the supplied formal
judgments; their interpretation of prose remains separately reviewable.

## Changes since 0.4.2

- Native correspondence inspection delivers exact owner-qualified source and
  formal context plus stored goal/polarity/receipt bindings. The configurable
  `--context-max-bytes` allowance defaults to 65536 and accepts up to 8388608
  bytes per context component, with explicit omissions. It starts no Lean run.
- Recognized correspondence slice and capture inventories admit up to 32768
  modules. Generated-goal diagnostics preserve their origin and unresolved
  outcome across those sizes. Unrelated lists, bytes and trust checks retain
  their existing bounds.
- Check-role accounting distinguishes interpretation and object-map typing
  from conditional replay, premise supply and conclusion transfer. Counts mean
  attempted checks. Zero direct premise obligations explicitly leave hypotheses
  packaged in argument types and source-assumption correspondence unassessed.
- The source-goal completion heartbeat default and generated-auxiliary replay
  repair committed after the earlier snapshot are included. Existing authority
  and forbidden-axiom checks remain required.
- Reader guidance covers structured inputs, source context, object maps and
  conclusion transfer. A delegated internal reader correctly withheld an older
  common-law certificate from a newer finite-batch claim. This is one useful
  handoff, without a measured detection or total-effort advantage.
- The external Navier–Stokes test requiring a private sibling checkout is
  removed at the owner's request. Its historical failed run remains recorded.
- Helper extraction addresses ten pre-existing complexity findings in Real-bound
  orchestration and its tests, preserving all 136 assertions and all test cases
  in the five affected test files.

No runtime dependency or canonical artifact/SQLite schema migration is added.
The native inspection response uses its documented v2 context shape; new role
reporting identifies `correspondence-check-roles-v2`. Frozen records are unchanged.

## Verification

Release qualification is in progress; the final candidate and results will be
recorded in `releases/0.4.3/verification.json` before handoff. The earlier native
MF qualification retained eight checks with accepted replay/trust across f-DP
and DP-Adam, taking about 8.3/7.5 minutes and 8.99/9.46 GiB peak process-tree RSS.
These are retained measurements, not new release benchmarks or product speedups.
The f-DP result remains conditional on inherited ordering; the manuscript's
ordering is unresolved. DP-Adam common-law support is per admitted input and
does not establish a finite-run rate or a complete source-method audit.

## OpenSpec disposition and use

The native correspondence-context child is complete (12/12) and its specification
is synchronized. The parent r04 package is complete (R.1–R.5). The old broad
three-diagnostic/full-scorer roadmap is superseded as an investment plan; its
11 unmet tasks and original evaluation gates remain historical acceptance
boundaries. They are not claimed as completed or required for this internal
snapshot. Frozen evidence stays at its original paths.

Follow [the internal handoff](INTERNAL_HANDOFF_0_4_3.md). Collect concrete task,
query, evidence, interpretation and effort feedback before expanding ProofIR.
This release is local internal use only; nothing is pushed or published.
