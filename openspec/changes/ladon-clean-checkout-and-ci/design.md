## Context

The live workspace passes the scoped quality command, but an exported tracked
tree fails because a maintained test imports ignored `.codex` code. Broad
pytest discovery can also execute inert `tests/fixtures/**` test files. The
catch-all `.*` rule hides standard project metadata, and `uv.lock` is valid but
untracked. No checked-in CI proves installation or real Lean extraction.

## Goals / Non-Goals

**Goals:**

- Make tracked source the complete authority for bootstrap, tests, build, and
  release smoke.
- Align declared Python/Lean support with an enforced CI matrix.
- Prevent fixture, temp, sibling-repository, and host-plugin content from
  becoming hidden required inputs.
- Test the installed distribution outside the repository.

**Non-Goals:**

- Publish or sign a release.
- Require large external Lean repositories in CI.
- Add unrelated formatters, linters, or services.
- Choose a software license on behalf of the project owner.

## Decisions

1. **Test both live and explicit candidate trees.** CI exports the commit under
   test. Every candidate-aware script requires `--candidate`: a treeish or
   materialized directory selects that exact input, while the explicit sentinel
   `worktree` copies the current contents of `git ls-files` into a fresh
   directory and rejects any untracked required input. No argument is an error;
   a dirty checkout paired with an implicit or explicit stale `HEAD` is refused.
   Gates run outside the checkout with sanitized `HOME`, `PYTHONPATH`, and
   virtual-environment state, plus an absolute-path audit. Testing only the live
   directory or an implicit stale `HEAD` was rejected because ignored and
   host-local dependencies caused the current false green.

2. **Define maintained pytest discovery explicitly.** `pyproject.toml` names the
   maintained test roots/patterns and excludes `tests/fixtures/**`, `.codex/**`,
   and `temp/**`. Live and export `--collect-only` node IDs must match and be
   nonempty. Inert fixture tests remain data.

3. **Resolve `.codex` ownership deliberately.** Required Ladon tests stop
   importing ignored host state. Code is moved or vendored only if Ladon is its
   declared owner; otherwise the test is removed from Ladon's maintained suite
   and handed off to the separately owned skill/plugin. The broad `.*` ignore
   is replaced with explicit cache/environment rules; project-owned dotfiles
   can be tracked.

4. **Separate locked environments from constrained builds.** Commit `uv.lock`;
   run `uv lock --check`, `uv sync --locked`, and test/quality commands through
   the locked environment. Pin or constrain isolated build requirements through
   package metadata and record their resolved versions. Tests and builds must
   not rewrite the application lock. Requiring a nonexistent locked mode from
   `uv build` was rejected.

   The baseline gate also accepts repeatable
   `--package-resource <package>:<relative-path>` checks. It verifies the
   resource in both the constrained sdist/wheel build and an isolated installed
   wheel, so feature children can prove packaged assets without introducing
   their own unconstrained build path.

5. **Match CI to a finite support set.** Documentation/classifiers list the
   currently released supported CPython minors, and `requires-python` excludes
   future untested minors through an upper bound or an equivalent explicit
   policy. Tests and installed-wheel smoke run across that finite matrix; the
   expensive strict quality analysis may run once.

6. **Make one pinned Lean reference job mandatory.** It provisions a tracked CI
   reference toolchain and tiny Lake project, installs the wheel, runs
   `ladon --extraction-backend lean`, prints the resolved target Lean version,
   and treats a skip as failure. This is a baseline compatibility job, not a
   claim that target repositories must use that Lean version.

7. **Run release smoke from outside the checkout.** Build sdist and wheel from
   the candidate, validate metadata, install in a fresh environment, run
   dependency checks and every declared supported console-script help path,
   verify the packaged Lean helper, analyze a portable fixture, and confirm
   imports resolve from site-packages.

8. **Enable repository-wide OpenSpec gates only after reconciliation.** Strict
   validation, backlog, and status hygiene currently expose known historical
   failures; the reconciliation child fixes those before CI makes them
   blocking.

9. **Keep licensing separate from technical readiness.** In the absence of an
   owner-granted license, documentation and metadata state that publication is
   blocked and the workflow omits publication. Local tracked-source build,
   install, and smoke remain mandatory and can close this packet. If the owner
   later authorizes distribution, license text and metadata become publication
   prerequisites. Choosing a license on the owner's behalf was rejected.

## Risks / Trade-offs

- **Full supported-version matrix is costly** → Publish a finite support set and
  narrow truthful metadata rather than advertise future untested versions.
- **Tracking project skills grows the distribution scope** → Move product code
  out of skills or test skills in their owning package; classify every `.codex`
  artifact explicitly.
- **Lean setup makes CI flaky** → Pin the toolchain and use a tiny local fixture
  with no sibling dependency.
- **No license has been granted** → Mark publication blocked by default; require
  license text/metadata only if the owner later authorizes distribution, while
  local package smoke remains mandatory.

## Migration Plan

Fix ignore/discovery and hidden test inputs first, commit the lock, add
clean-export gates, then add Python/package and Lean CI. Enable all-change
OpenSpec checks after reconciliation. Each gate can be introduced separately,
but no alpha release is ready until the full exported-tree smoke passes.

## Open Questions

None. The supported Python minor set is selected from the first required matrix
run and committed before this packet closes; publication remains blocked unless
the owner separately grants a license.
