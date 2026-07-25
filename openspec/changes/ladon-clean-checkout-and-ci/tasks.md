## 1. Tracked Inputs And Discovery

- [x] 1.1 Inventory every maintained test/runtime input against `git ls-files` and record hidden `.codex`, fixture, temp, or sibling dependencies.
- [x] 1.2 Replace the catch-all `.*` ignore rule with explicit trackable-dotfile and local-artifact rules plus `git check-ignore` tests.
- [x] 1.3 Configure maintained pytest discovery and exclude `tests/fixtures/**`, `.codex/**`, and `temp/**`.
- [x] 1.4 Assert live-tree and tracked-export `pytest --collect-only` node IDs are identical and nonempty.
- [x] 1.5 Remove the pro-review helper's ignored-host dependency from Ladon's maintained suite; vendor/move code only if Ladon is its declared owner, otherwise hand the test off to the skill/plugin owner.
- [x] 1.6 Add `uv.lock` to tracked source and document locked bootstrap.

## 2. Clean Export Gate

- [x] 2.1 Add `scripts/clean_checkout_gate.py --candidate <treeish|directory|worktree>` with no implicit candidate; `worktree` materializes current `git ls-files` content, and every mode uses a sanitized environment, outside-checkout execution, and absolute-path audit.
- [x] 2.2 Run `uv lock --check`, locked sync, locked-environment maintained tests/quality, and a constrained package build inside the candidate; support repeatable `--package-resource <package>:<relative-path>` assertions against both built artifacts and an isolated installed wheel.
- [x] 2.3 Assert the lockfile is byte-unchanged after bootstrap, tests, and build.
- [x] 2.4 Define `tracked-source-baseline` as tasks 1.1-1.6 and 2.1-2.3 complete plus `uv run --locked python scripts/clean_checkout_gate.py --candidate worktree --baseline-only` passing; that gate fails on empty collection, skipped mandatory checks, untracked required inputs, or any subcommand failure.

## 3. Python And Package CI

- [x] 3.1 Define a finite currently supported CPython-minor set and align `requires-python`, classifiers, and documentation with it.
- [x] 3.2 Add GitHub CI for maintained tests and installed-wheel smoke across every explicitly supported Python minor.
- [x] 3.3 Run strict Radon/Vulture/compile quality and clean-export gates in the required workflow.
- [x] 3.4 Build sdist and wheel from the export and validate package metadata.
- [x] 3.5 Install the wheel outside the repository with no editable/PYTHONPATH leakage and run dependency checks.
- [x] 3.6 Verify every declared supported console-script help path, site-packages import origin, packaged Lean helper, and portable fixture analysis.

## 4. Lean And OpenSpec CI

- [x] 4.1 Track a tiny Lake project and pin its CI reference Lean toolchain without constraining target-repository toolchains.
- [x] 4.2 Add `scripts/lean_integration_gate.py` and a mandatory job that installs the wheel, runs `ladon --extraction-backend lean` on the tracked project, prints the target version, and fails on skip.
- [x] 4.3 Keep Quux, matrix-factorization, mathlib, and sibling-repository smokes outside required CI.
- [x] 4.4 After state reconciliation, require all-change strict OpenSpec validation, backlog check, and status-hygiene check.

## 5. Documentation And Release Gate

- [x] 5.1 Gate README, package metadata, scripts, and installed defaults against required absolute maintainer paths; implementation owners remove each reported path.
- [x] 5.2 Document supported Python/Lean versions, locked setup, mandatory/optional gates, and Lean target-code execution risk.
- [x] 5.3 When no owner-granted license exists, document `publication blocked—no license granted` without choosing a license; if distribution is authorized, add the granted license text and artifact metadata.
- [x] 5.4 Add `scripts/installed_distribution_smoke.py --candidate <treeish|directory|worktree>` composing candidate export, constrained build, isolated install, declared entrypoints, helper, and fixture checks; reject a missing candidate.
- [x] 5.5 Run `uv run --locked python scripts/python_quality.py --strict` in both live and candidate trees.
- [x] 5.6 Update `automation.json` to invoke the clean-candidate, installed-distribution, mandatory-Lean, and reconciled OpenSpec gates.
- [x] 5.7 Run `openspec validate ladon-clean-checkout-and-ci --strict`.
