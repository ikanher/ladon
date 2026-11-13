# Frozen restricted initialized-Adam rate release

This release closes the presentation and reconstruction package for the R23
restricted theorem. It introduces no new positive utility result. The first
broader finite optimizer theorem was accepted in r12; its release verification,
privacy specialization, sharper successor and historical batch/privacy
explanation remain separate workstreams. See the [current queue](THEOREM-QUEUE.md).
The authoritative task ledger is
[finite-adam-restricted-rate-release](../../openspec/changes/finite-adam-restricted-rate-release/tasks.md).

The restricted-release r02 review accepts the mathematical presentation.
Its seven signature-metadata defects are corrected: all 19 complete raw source
spans match its independent excerpts. The theorem and TeX are unchanged.
The [corrected standalone release](../../temp/dpadam-restricted-rate-release-r06.zip)
and validation are bound by the
[review-closure receipt](../../witnesses/finite_memory_adam/artifacts/restricted-release-review-closure.json).
The earlier [r02 review packet](../../temp/dpadam-restricted-rate-review-data-r02.zip)
and [r04 handoff](../../witnesses/finite_memory_adam/artifacts/restricted-release-handoff.json)
remain historical immutable artifacts; their original metadata is not rewritten.

Current status: **restricted theorem frozen; conventional proof and source
correspondence reviewed; producer fresh replay passed; recipient source build
incomplete**. Task 5.1 owns separately operated recipient compilation and fresh
replay as one open release-verification task.

## Read the result

The [conventional mathematical proof](../../latex/natural-language/finite_initialized_clipped_adam_rate.tex)
contains the assumptions, full algorithm, common-step expression, horizon-selected
rate, same actively clipped nonconvex instance and limitations. The
[source audit](../../latex/lean/finite_initialized_clipped_adam_rate_audit.md)
separates exact declaration correspondence from proof-checking evidence and
Ladon's pending canonical associations. The
[primary-source comparison](RESTRICTED-RATE-RELATED-WORK.md) makes no novelty claim.

The theorem concerns independent uniform **pre-update expected squared true-gradient
norm**, with a positive-noise remainder. Full-batch zero-noise convergence is for
separate constant-step runs indexed by horizon, not a final iterate or a single
infinite run changing its rate. It is not a privacy certificate or a ranking of
actual batch performance.

## Reconstruct sources

The maintained builder accepts only the pinned R23 input archive and checks
source identity at the verified code and evidence revisions, current protected
owners, local import closure, unchanged Lean options and exact dependency pins.
It refuses to overwrite an existing release directory.

```bash
python local-scripts/build_dpadam_restricted_rate_release.py \
  --archive temp/dpadam-batch-size-review-data-r23.zip \
  --output temp/dpadam-restricted-rate-release-r06
python temp/dpadam-restricted-rate-release-r06/verify_release.py
```

Use a new output name if r06 already exists. The portable directory contains
all 332 local Lean sources, original and minimal Lake metadata, the protected
contract, exact lock, source manifest and reconstruction scripts. It excludes
external packages and compiled objects. Install the exact elan toolchain, then,
from the recipient project root:

```bash
python reconstruct_dependencies.py
python verify_release.py --require-dependencies
lake exe cache get
lake build Mf.Optimization.FiniteMemoryAdam.CumulativeSupportedBiasFinalAudit
lake env leanchecker --fresh Mf.Optimization.FiniteMemoryAdam.CumulativeSupportedBiasFinalAudit
```

The optional cache step obtains matching Mathlib objects; it is not an external
source build. The reconstruction helper can instead use local exact Git mirrors
with `--mirror-root /absolute/mirror/path`; Git object sharing must be disclosed.
No `lake update` or dependency repinning is used to repair a failed replay.
Check archive identity through a trusted digest before relying on its manifest.
Source/hash validation executes no Lean and makes no theorem claim.

The hardened verifier checks untracked and ignored files in dependency checkouts,
permitting only documented build/config caches, Lake's barrel trace and the
ProofWidgets cache markers. Extra Lean, TOML/YAML, toolchain and lock files and
cache symlinks fail. Cache names/sizes and the exceptional marker digest are
reported; this inventory does not authenticate compiled cache bytes. The r06
package changes reconstruction tooling, not the frozen Lean source snapshot.

To reproduce the signature correction and its regression checks:

```bash
python local-scripts/refresh_lean_source_signatures.py \
  latex/lean/finite_initialized_clipped_adam_rate.capture.json --check
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_lean_source_signatures.py tests/test_dpadam_restricted_rate_release.py -q
```

## Verification scopes

The [freeze receipt](../../witnesses/finite_memory_adam/artifacts/restricted-release-freeze.json)
reconciles code revision `c3cd1b611c9caec90cc8e615dd7777b1d8d5a984` and evidence
revision `767c864238b3d424f45a146b9070e5a747b7f92a`. All 332 protected Lean sources
are identical at both revisions and in the original archive. Unrelated worktree
changes are excluded.

The [fresh-kernel receipt](../../witnesses/finite_memory_adam/artifacts/restricted-rate-fresh-kernel.json)
records a successful root-operated fresh environment replay in 1735.76 seconds,
with sampled peak 13.46 GiB, after the earlier inconclusive timeouts. This is
Lean's own kernel, not an independent implementation or a separately operated
check. The release reconstruction receipt records the separate bounded source
build from zero project objects with copied matching external caches. Its outcome
must be read separately; it does not replace or invalidate the earlier success.

A clean recipient run operated separately remains an external verification
finish line. Source semantic review, compiled proof replay, canonical Ladon
association and arithmetic witness validation retain distinct scopes.
Give compilation and fresh replay separate resource budgets. Preserve stdout
and stderr continuously outside the release payload, including the interrupted
module, and record exact tool executables, cache origins and source/object
bindings. Checkpointed compilation is acceptable only within the same pinned
recipient environment, with every stage's starting state disclosed. Another
root operation cannot satisfy the separate-operator requirement.

## Bounded reconstruction outcome

The isolated source build finished with status **inconclusive** under the
1800-second / 48-GiB guard: 236 of 332 modules completed with exit zero,
in 1800.07 seconds, with sampled peak 9.64 GiB. Its
[receipt](../../witnesses/finite_memory_adam/artifacts/restricted-release-reconstruction.json)
preserves the exact commands, completed modules, compiled identities, source
snapshot, external-cache provenance and failed bytecode harness attempt.

The next uncompleted module is `Mf.Optimization.FiniteMemoryAdam.HeterogeneousSamplingCell09`. The
recipient final audit was not reached. This is an inconclusive bounded build,
not a false theorem or a completed recipient replay. The recipe remains
available; a longer or differently scheduled recipient build has not been
accepted as evidence. The earlier root fresh-kernel success is unchanged.

## Next research boundary

The [broader decision](BROADER-CLIPPED-ADAM-DECISION.md) is closed at valid
conditional components plus an actual-normalization obstruction. Its new review
prefix, tail and symmetric-query deductions remain paper results. The later
[r10 construction decision](../../openspec/changes/dpadam-batch-size-accounting-umbrella/cone-cell-repair-decision.md)
closes the bounded quadratic certificate attempt. The useful general
adaptive-regime theorem remains open; a new attempt needs a materially
different argument with a complete budget. Neither further theorem research
nor r10's external numerical replay discharges this release's separately
operated Lean compilation and fresh-replay obligation. No new training,
instrumentation, privacy calibration or synthetic objective is needed here.
