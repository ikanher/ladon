## Why

Ladon's live workspace passes its strict gate, but a clean archive fails tests
because a tracked test imports an ignored machine-local helper, and the valid
lockfile is untracked. Alpha releases must be reproducible from committed
source rather than the maintainer's workspace.

## What Changes

- Narrow the broad `.*` ignore rule so required dotfiles, CI configuration, and
  project metadata can be tracked intentionally.
- Commit and verify the dependency lockfile.
- Remove test dependence on ignored `.codex` content and constrain pytest
  discovery so inert tests under `tests/fixtures/**`, `.codex/**`, or local
  `temp/**` artifacts are not collected as maintained product tests.
- Add CI for supported Python versions, lock consistency, scoped tests, the
  strict quality gate, strict OpenSpec validation, package build, isolated wheel
  install, and console-script smoke tests.
- Add a provisioned Lean integration job pinned to a CI reference toolchain
  while production analysis continues to use the target repository's
  toolchain; keep external Quux/mathlib-style smokes optional.
- Document supported Python/Lean versions, package/release checks, and project
  licensing.
- Require the same gates against an explicit candidate snapshot in an isolated,
  sanitized environment to catch ignored, untracked, and host-local
  dependencies.

## Capabilities

### New Capabilities

- `ladon-project-reproducibility`: Clean-checkout dependency, test, CI,
  packaging, Lean-integration, and release-smoke requirements.

### Modified Capabilities

None.

## Impact

- Affected files: `.gitignore`, `uv.lock`, `pyproject.toml`, tests, CI
  workflows, package metadata, license/support documentation, and quality
  scripts.
- Affected workflow: pull requests and release candidates must pass from
  committed files only.
- Runtime dependencies remain minimal; this packet does not add a service or
  deployment surface.
