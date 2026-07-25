## ADDED Requirements

### Requirement: Tracked-source authority
An explicit commit/treeish or materialized tracked candidate SHALL contain every
input required to bootstrap, test, validate, build, and smoke Ladon.

#### Scenario: Exported-tree gate
- **WHEN** CI exports the commit under test into a fresh sanitized environment outside the original checkout
- **THEN** locked bootstrap, maintained tests, strict quality, package build, and installed smoke complete without reading the original working tree, host home, or host virtual environment

#### Scenario: Ambiguous local candidate
- **WHEN** a local release gate is invoked with tracked dirty state and no explicit materialized candidate
- **THEN** the gate refuses to test an implicit stale `HEAD` and requests an explicit candidate

#### Scenario: Tracked-source baseline milestone
- **WHEN** tracked-input/discovery tasks are complete and the baseline-only gate materializes the explicit candidate outside the checkout
- **THEN** `tracked-source-baseline` is attained only if locked bootstrap, collection parity, strict quality, constrained build, lock immutability, and required-input audits pass

#### Scenario: Hidden maintained-test input
- **WHEN** a maintained test attempts to read repository content absent from tracked files
- **THEN** the reproducibility gate fails and names the hidden path

### Requirement: Explicit test discovery
Maintained pytest discovery SHALL be configured explicitly and MUST exclude
inert test-shaped files under `tests/fixtures/**`, `.codex/**`, and `temp/**`.

#### Scenario: Collection parity
- **WHEN** live-tree and exported-tree maintained tests are collected
- **THEN** their nonempty node-id sets are identical

#### Scenario: Fixture test file
- **WHEN** a benchmark packet fixture contains `tests/test_review.py`
- **THEN** it remains inert fixture evidence and is not executed as a Ladon product test

### Requirement: No host-plugin dependency
Required product tests MUST NOT import ignored host-owned `.codex` code.

#### Scenario: Pro-review helper ownership
- **WHEN** a test exercises the pro-review helper
- **THEN** the helper is tracked Ladon-owned code or the dependency is removed from Ladon's suite and handed off to the separately owned skill/plugin

### Requirement: Explicit ignore policy
The repository MUST replace the catch-all `.*` ignore rule with explicit rules
that distinguish trackable project metadata from local environments, caches,
build products, and temporary output.

#### Scenario: Trackable project files
- **WHEN** ignore behavior is tested for `.github/**`, `uv.lock`, and selected project-version metadata
- **THEN** those required files are trackable

#### Scenario: Local artifacts
- **WHEN** ignore behavior is tested for `.venv/`, Python caches, build/dist output, and local temp output
- **THEN** those artifacts remain ignored

### Requirement: Locked bootstrap
The dependency lockfile SHALL be committed; environment resolution and
test/quality commands MUST use the locked environment without rewriting it.

#### Scenario: Lock consistency
- **WHEN** CI runs lock check, locked sync, locked-environment tests/quality, and package build
- **THEN** every command succeeds, isolated build requirements are constrained and recorded, and the application lockfile remains byte-unchanged

#### Scenario: Required package resource
- **WHEN** a child requests a package resource through the clean candidate gate
- **THEN** the gate verifies the resource in the constrained sdist and wheel and through the isolated installed package

### Requirement: Truthful Python support
Package metadata and documentation SHALL declare a finite set of currently
released supported CPython minors covered by the required CI matrix.

#### Scenario: Supported Python minor
- **WHEN** a Python minor is listed in the published support set and classifiers
- **THEN** CI installs the wheel and runs the required test/smoke contract on that minor

#### Scenario: Future untested Python minor
- **WHEN** a newer CPython minor is not yet in the tested support set
- **THEN** package metadata does not imply support until the matrix and documentation are updated

### Requirement: Mandatory pinned-Lean integration
CI SHALL provision a pinned reference Lean toolchain and tracked tiny Lake
project, then run the installed wheel's Lean backend without allowing a skip.

#### Scenario: Lean integration skip
- **WHEN** the mandatory Lean test is skipped because the toolchain or fixture is unavailable
- **THEN** the Lean CI job fails

#### Scenario: Lean helper package
- **WHEN** the installed wheel runs `ladon --extraction-backend lean` on the tracked Lake fixture
- **THEN** it uses the packaged helper, prints the target toolchain version, and produces the expected declaration evidence

#### Scenario: Target repository toolchain
- **WHEN** Ladon analyzes another repository outside the reference CI fixture
- **THEN** it uses that repository's resolved Lake/Lean environment rather than forcing the CI reference version

### Requirement: Isolated distribution smoke
Release smoke SHALL build sdist and wheel from tracked-only source, install the
wheel outside the repository, and verify metadata, dependencies, entrypoints,
packaged Lean assets, and portable analysis.

#### Scenario: Installed CLI smoke
- **WHEN** the wheel is installed into a fresh environment with no editable or `PYTHONPATH` leakage
- **THEN** dependency checks, every declared supported console-script help command, and analysis of a portable fixture succeed from site-packages

#### Scenario: Maintainer-local path
- **WHEN** packaged metadata or documentation contains a required absolute maintainer path
- **THEN** release smoke fails

### Requirement: Reconciled OpenSpec gate
After the state-reconciliation child completes, CI SHALL require strict
validation of all changes plus clean backlog and status-hygiene results.

#### Scenario: Invalid completed change
- **WHEN** any completed or active change fails strict validation, backlog analysis reports a finding, or status hygiene reports drift
- **THEN** the OpenSpec CI gate fails

### Requirement: Explicit distribution and support documentation
Repository documentation SHALL state supported Python/Lean versions, locked
bootstrap, execution safety, required versus optional smokes, and whether
publication is authorized or blocked.

#### Scenario: Missing licensing decision
- **WHEN** no license or explicit non-distribution posture has been recorded
- **THEN** documentation records that no license has been granted, publication stays blocked, and local tracked-source build/install smoke remains eligible to close the alpha technical gate

#### Scenario: Distributable release
- **WHEN** the owner authorizes distribution
- **THEN** license text and package license metadata are present before publication

#### Scenario: Non-distribution posture
- **WHEN** the owner records that the project is not distributable
- **THEN** publication remains blocked while local sdist/wheel smoke may still run

### Requirement: Gate failure propagation
The workflow MUST propagate failure from every required lock, collection, test,
quality, OpenSpec, build, install, or Lean subcheck.

#### Scenario: Empty maintained collection
- **WHEN** pytest returns its empty-collection status or a required test fails
- **THEN** the workflow fails instead of treating the command as successful
