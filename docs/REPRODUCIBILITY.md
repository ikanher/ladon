# Reproducibility and release support

Ladon's maintained product gates use tracked source as their only repository
input. The authoritative inventory is:

- `pyproject.toml`, `uv.lock`, and `build-constraints.txt` for bootstrap and
  builds;
- `src/**`, including the packaged Lean helper, for installed behavior;
- `scripts/**` for maintained quality, candidate, package, Lean, and OpenSpec
  gates;
- top-level `tests/test_*.py` as maintained tests;
- `tests/fixtures/**` as inert data, including test-shaped files that pytest
  must not collect;
- `README.md`, `docs/**`, `.github/**`, and OpenSpec artifacts as maintained
  documentation, workflow, and change metadata;
- `skills/**` for maintained Ladon skill instructions. Host-owned `.codex/**`
  is excluded.

The clean-candidate gate compares `git ls-files` with required input roots,
rejects an untracked required input, materializes an explicit candidate outside
the checkout, and compares nonempty live/candidate pytest collection. It then
runs locked bootstrap, strict quality, constrained package build, and the
requested installed checks without using the original virtual environment,
`PYTHONPATH`, or home directory.

When Lake is available, the gate explicitly builds its tracked pinned Lean test
fixture before running tests. The isolated HOME retains configured or inferred
Elan and Rust compiler/cache locations. Required documentation checks read only
Ladon's maintained files, without a sibling skill repository.

The following paths are deliberately outside Ladon's maintained product input:

- `.codex/**` is host/plugin-owned. The former Ladon test that imported the
  ignored pro-review skill helper has been handed back to that skill's owning
  test surface rather than vendoring it into Ladon.
- `temp/**`, local virtual environments, caches, build products, and editor
  state are local artifacts.
- Quux is outside Ladon's maintained inputs and is never inspected, executed,
  or used for calibration. Matrix-factorization, mathlib, and other approved
  targets are optional calibration or drift smokes. Required CI uses only
  tracked portable fixtures.

## Supported runtimes

The supported Python set is exactly CPython 3.11 and 3.12. `requires-python`,
package classifiers, the lockfile, and the required GitHub Actions matrix use
that same finite set. A newer Python minor is unsupported until all four are
updated and its required matrix job passes.

The mandatory Lean integration fixture pins
`leanprover/lean4:v4.32.1`. This is a CI reference toolchain, not a requirement
for analyzed projects: the Lean backend runs through each target repository's
resolved Lake/Lean environment. Loading a target module can execute imported
initializers, so Lean-backed analysis is not safe for an untrusted repository.

## Required gates

From a tracked candidate, the technical release gate requires:

```bash
uv lock --check
uv run --locked python scripts/clean_checkout_gate.py --candidate worktree
uv run --locked python scripts/installed_distribution_smoke.py --candidate worktree
uv run --locked python scripts/lean_integration_gate.py --candidate worktree --required
uv run --locked python scripts/ladon_benchmarks.py --candidate worktree --required
uv run --locked python scripts/python_quality.py --strict
openspec validate --all --strict --no-interactive
uv run --locked python scripts/ladon_openspec_backlog.py --openspec-root openspec --check
uv run --locked python scripts/ladon_openspec_hygiene.py --openspec-root openspec --check
uv run --locked python scripts/alpha_readiness.py \
  --candidate worktree \
  --ledger openspec/changes/ladon-alpha-hardening-umbrella/children/dependency-ledger.json \
  --require-all-children
```

The candidate scripts also accept an explicit treeish or materialized directory.
They never silently choose `HEAD`. Large external repositories remain optional
manual smokes and cannot turn the required gate green or red. Alpha readiness
resolves each child from active or uniquely archived state, validates the
phase-qualified dependency graph, substitutes isolated validation for an
archived change's stale active-ID command, and runs preserved automation from
the same materialized candidate.

The portable signal benchmark builds and installs that explicit candidate,
runs ordinary `ladon` commands over tracked fixtures, and keeps correctness,
coverage, runtime, memory, cache, process, and stability results separate. Its
synthetic budgets and interpretation boundary are documented in
[Portable signal benchmarks](BENCHMARKS.md). The deterministic helper stand-in
does not replace the pinned real-Lean integration and declaration gates.

## Distribution status

**publication blocked—no license granted**

No owner-granted license text is present, so workflows build and install local
sdist/wheel artifacts for technical verification but do not publish them. A
future distribution authorization must add the granted license text and
matching package metadata before any publication step is enabled. Technical
alpha readiness does not imply permission to distribute.

The [measured alpha profile](MEASURED_ALPHA_PROFILE.md) records the exact
qualified candidate and the remaining external-evaluation gaps. A successful
technical gate does not complete the prerequisite umbrella or qualify a newer
working tree. Candidate-specific receipts retain their original scope.

Candidate-specific integration qualification is described in
[Authority-safe integration](AUTHORITY_SAFE_INTEGRATION.md). Passing the two child receipts alone
does not close integration or the experimental verified-discovery exit.
