## Why

The CLI currently accepts a no-op build flag, does not clearly separate report
data from diagnostics, and has no stable finding-policy exit contract. The
ordinary Ladon command must be predictable enough for interactive and
automated use without creating a separate interface for either.

## What Changes

- **BREAKING**: Remove the no-op `--skip-build` option and document that analysis
  never builds the target unless the caller explicitly requests `--build`.
- **BREAKING**: Replace mixed JSON-plus-text stdout with one selected
  `--format`/`--output`; retain the old file-output flags for one documented
  compatibility release only.
- Add an opt-in build phase using the target repository's ordinary Lake
  command, with a finite deadline, cancellation/process-group cleanup, and
  preflight diagnostics for missing toolchains, manifests, and build artifacts.
- Define stable exit classes for success, invocation/configuration errors,
  operational failures, and explicitly configured finding-policy failures.
- Add a general `--fail-on` policy for CI and shell use while keeping successful
  analysis advisory by default.
- Guarantee that report bytes go to the selected stdout/file destination and
  progress or diagnostics go to stderr.
- Add a general JSON report-version selector for the bounded report-v1
  compatibility period; text always renders the canonical v2 model.
- Make phase completion, skipping, partial failure, and failure visible to the
  caller with human-readable reasons.
- Keep `ladon` and existing general-purpose CLI entrypoints under one execution
  contract; text and JSON remain renderings of the same result, not
  caller-specific products.

## Capabilities

### New Capabilities

- `ladon-cli-execution`: Shared command semantics, build opt-in, output-channel
  discipline, phase visibility, and exit-status behavior.

### Modified Capabilities

None.

## Impact

- Affected code: CLI parsing, run context, preflight/build orchestration,
  report writing, failure policy, and root-matrix command construction.
- Affected documentation and tests: command examples, exit-code matrix,
  stdout/stderr assertions, build fixtures, and unsupported-option behavior.
- Existing callers that pass `--skip-build` must remove it; the default remains
  no-build analysis.
- Before `--skip-build` is removed, reconciliation must archive its explicit
  modifications to the historical `ladon-python-quality` and
  `ladon-root-matrix` requirements, and the resulting
  `canonicalized-legacy-cli-deltas` milestone must pass.
