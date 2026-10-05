# Discovery correctness acceptance

The correctness child exits at isolated tracked candidate `a11edfba61f5f4c852bc67839e515f8aea72910f`. The authority child is requalified from the same candidate, and both installed validators accept their content-addressed receipts and conjunction. This is the two-child receipt check; the remaining integration freeze/documentation tasks and vertical-slice exit are still open.

## Changes

- Exact explanation filters the candidate's owning module, rejects missing/blank, lexical-only, truncated, ambiguous or stale type evidence, and retains type bytes/truncation, authority, owner, path/line and stored/verified generation identities. Available explanations remain structural and route callers to explicit checking.
- `search type-text` emits `ladon-proof-search-type-text-result-v2`, with a packaged schema, literal SQLite ASCII case rules, field contributions, population/row completeness, omissions, lower bounds and caps. API diagnostics and explicit CLI zero caps are bounded. Freshness callbacks cannot overwrite lexical authority.
- Namespace filtering uses literal prefixes; type-text namespace scopes include every selected root. Name search retains namespace descendants containing underscores.
- CLI help, README, scope/CLI docs, generated feature matrix and repository-owned `skills/ladon/SKILL.md` describe the breaking rename and evidence boundary.

## Qualification

- Correctness: 20 frozen targets, **142 passed per runtime**, no skips, failures, deselection or collection errors.
- Authority: 62 frozen targets, **1,058 passed per runtime**, no skips or failures.
- Installed child/gate adversarial contracts: **86 passed per runtime**. Exact final runner: **13 orchestration cases** with expected outcomes.
- Clean tracked candidate: **2,542 maintained + 29 installed CLI tests**, strict Ruff/radon/vulture, compile, lock/dependency, sdist/wheel/resource and required pinned Lean fixture checks pass.
- Required portable benchmark: **17/17**, zero correctness or stability failures.
- Original five repaired behaviors are rechecked through the installed console/API probes on both runtimes. The frozen exposition retains **nine unchanged offline scenarios per runtime and all 127 files**; no Lean replay or benefit improvement is inferred.

The exact scope is `/tmp/ladon-correctness-qualification-ntctf4j4/context-r28.json`; the source manifest owns 2,318 tracked files. Wheel digest: `sha256:db58daddaa839ae6400e4926c434584d7f9b6b0945b1552440956ed3939ec360`. Bundle: `/tmp/ladon-correctness-qualification-ntctf4j4/child-bundles-r28-qualified`. Test commands, Python/import identities, selected environment, Lean pin/executables, expanded node IDs, logs and content hashes are bound by the receipts. The final commands use absolute runner/inventory paths; earlier passing suites with relative inventory arguments were rejected by the independent receipt validator and are not used for acceptance.

## Chronology and limits

The five original review defects remain retrospective old-version reproductions. Initial new missing-type, owner, generation, cap, schema, case-contribution, callback and multiple-root failures have pre-edit captures. Namespace descendant fixtures were strengthened after the initial repair; their prior-installed-wheel reproductions are explicitly retrospective. The first name fixture had an incorrect display-name assertion, which is excluded as defect evidence. The regression comparison and ledger record these limits; no reconstruction establishes earlier TDD chronology.

Integrity and finite test coverage do not authenticate the producer, establish OS isolation, verify arbitrary target-code secrecy, establish held-out mathematical benefit, or grant public release authority. Exposition baseline files and historical authority reports are preserved. The workspace Git index is left untouched; the candidate commit exists only in the isolated qualification repository.

## Remaining work

Prerequisite tasks **48/76**; result-understanding umbrella **9/50**; claim correspondence **5/8**. Close integration materialization/documentation/freeze and final go/no-go tasks, then qualify the ordinary verified-discovery vertical slice before resuming canonical result integration. No daemon, new ProofIR family, Rust expansion or optional-layer prerequisite is introduced.
