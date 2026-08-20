## 1. Ownership And Executable Contract Tests

- [x] 1.1 Verify reconciliation archived its prerequisite source additions and then itself, and require `canonicalized-legacy-cli-deltas` before integrating flag removal; legacy-spec mutation remains owned by `ladon-openspec-state-reconciliation`.
- [x] 1.2 Record `ladon-proofir-bridge` as a supported general auxiliary entrypoint under the shared applicable process rules.
- [x] 1.3 Add installed-console subprocess tests for help, valid analysis, invalid invocation/configuration, operational failure, signal termination, and policy rejection.
- [x] 1.4 Add stdout/stderr tests for default text, JSON stdout, file output, legacy dual files, conflicts, diagnostics, and unwritable destinations.
- [x] 1.5 Add fake Lake/Lean preflight and build fixtures for success, text-backend build check, missing toolchain/state, failure, timeout, interruption, and descendant cleanup.
- [x] 1.6 Add exact `--fail-on` grammar tests for repetition/OR, severity ordering, case sensitivity, invalid selectors, phase requiredness, deterministic matches, and exit precedence.
- [x] 1.7 Add partial-report assertions for failures after completed discovery.

## 2. Output And Invocation

- [x] 2.1 Add canonical `--format text|json` and `--output PATH|-` selection with text stdout as the default.
- [x] 2.2 Support legacy `--json PATH`/`--text PATH` for one alpha release with exact dual-file/conflict rules, deprecation diagnostics, and later exit-2 removal tests.
- [x] 2.3 Remove `--skip-build` and update root-matrix construction, tests, docs, and maintained examples to omit it.
- [x] 2.4 Ensure at most one representation reaches stdout and all progress/deprecation/error messages reach stderr.
- [x] 2.5 Make packaged entrypoints and maintained wrappers propagate the canonical return code unchanged.
- [x] 2.6 Add `--report-version v2|v1`, default v2, route v1 only for a sole JSON representation, and reject v1 with text or legacy dual output without changing analysis.

## 3. Build, Preflight, And Failure Policy

- [x] 3.1 Add build intent and preflight state to `RunContext` without coupling it to caller identity.
- [x] 3.2 Implement a shared target-process supervisor with finite build deadlines, process groups, output draining, cancellation, escalation, and reaping.
- [x] 3.3 Implement explicit `--build` orchestration for text and Lean backends and capture command/toolchain/diagnostics as a report phase.
- [x] 3.4 Validate repository, root, Lake/toolchain, compiled-state, and output prerequisites with the documented error classification.
- [x] 3.5 Implement the documented normal 0/1/2/3 exit mapping, required-phase precedence, and conventional signal propagation.
- [x] 3.6 Implement exact `--fail-on` selector parsing/matching and record ordered selectors/matches in report metadata.
- [x] 3.7 Serialize trustworthy completed phases and failed-phase diagnostics before returning operational failure.

## 4. Documentation And Gates

- [x] 4.1 Publish the command, output-channel, security, partial-report, migration, and exit-code matrices.
- [x] 4.2 Include `ladon` and `ladon-proofir-bridge` in the installed process-contract audit without changing behavior based on caller type.
- [x] 4.3 Assert public help has no model-only, agent-only, prompt-only, or hidden alternate-analysis option.
- [x] 4.4 Add `tests/test_installed_cli_contract.py` and run it against a built wheel outside the checkout.
- [x] 4.5 Expose the installed process-contract assertions for reuse by `ladon-clean-checkout-and-ci`; clean-checkout owns the integrated distribution-smoke execution and is not a CLI-child completion dependency.
- [x] 4.6 Update `automation.json` with the installed contract test and locked-environment focused/quality gates.
- [x] 4.7 Run `uv run --locked pytest -q tests/test_clean_cli.py tests/test_root_matrix.py tests/test_pipeline.py tests/test_render.py tests/test_proofir_bridge_cli.py tests/test_installed_cli_contract.py`.
- [x] 4.8 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 4.9 Run `openspec validate ladon-cli-execution-contract --strict`.
