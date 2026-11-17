# Ladon 0.4.4 internal release

This internal alpha release addresses DP-SGD/MF field feedback on freshness,
history growth, query provenance and resource controls.

## Changes since 0.4.3

- Focused `proof-search index freshness` checks current supported inputs without
  historical integrity or storage scans, with generation comparison and timings.
- `proof-search search batch` shares one read transaction and two source captures
  across 1–32 bounded name/type-text queries. Edits or generation replacement
  withhold results. Saved results describe their observation window; persistent
  cross-process freshness tokens remain unimplemented.
- Ordinary `index update` invalidates derived cache observations and creates no
  historical snapshot. No-op updates keep current observations. Explicit
  `--archive-history` preserves the former opt-in behavior. Separately saved
  audit outputs and authored idea metadata are retained.
- `index history-cleanup` previews selected old snapshots/catalog entries and
  applies a saved preview with file checks and interruption recovery. At the
  owner's request MF's 50 already-missing snapshot entries were removed; that
  operation deleted zero file bytes and retained the active generation.
- Update `phaseSeconds` separates enumeration, hashing, extraction and database
  work using exclusive wall-time accounting. Total elapsed time also includes
  uninstrumented orchestration/publication overhead.
- Stored type-text results carry generation/index identity from the rows' read
  transaction, with explicit freshness status and generation-race rejection.
- Proof slicing exposes timeout/RSS controls with defaults of 60 seconds per
  process and 12 GiB. Chosen limits bind execution and identity; elevated saved
  slice limits require explicit correspondence replay allowances.
- Docs and bundled/shared skills include the short TeX-plus-named-theorem recipe.

No runtime dependencies or SQLite schema migration are added. Consumers of the
old default automatic archival must explicitly choose `--archive-history`.
Historical artifacts and evaluation conclusions retain their original scope.

## Verification

Candidate `78b2fc8` built and installed successfully, passed all **41 installed
CLI contracts**, and passed the pinned **Lean 4.32.1** integration gate outside
the checkout. All **171 selected integration tests** pass in 189.97 seconds,
covering batch/freshness, default/explicit history, cleanup, public CLI contracts,
real Lean slice extraction/replay, and memory controls. Repository Ruff and
strict static quality are clean. All 94 OpenSpec validations, both skills and
the offline lock check pass.

[The verification receipt](releases/0.4.4/verification.json) binds the candidate,
production/test/lock identities, shared skill commit and exact logs. Later
release-record commits change documentation only. No full-repository pytest run,
Python 3.12 qualification, or old large-capsule memory rerun was performed for
this release. These limits do not inherit a green result from prior versions.

A single sequential MF exercise took 5.658/5.749 seconds for two standalone
verified queries and 5.834 seconds for the equivalent batch, with identical rows
and generation. A prior profiled status spent 54.631 of 72.778 seconds hashing
legacy history. These are bounded field observations with uncontrolled
cache/order and profiler effects, not general speedup guarantees.

## Use and remaining scope

Follow [the internal handoff](INTERNAL_HANDOFF_0_4_4.md). Persistent tokens across
later live queries, compact slice inspection and the old large-capsule memory
rerun remain outside qualification. Interpretation fidelity and comparative
mathematical discovery benefit are not established by this release. The older
superseded pitfalls gates remain unmet historical requirements.

Internal use only. Nothing is pushed or published.
