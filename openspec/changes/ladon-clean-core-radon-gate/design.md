## Design

### Goal

Make Ladon's active package code clean enough that `radon` and `vulture` are
actionable gates. The first clean core should be intentionally smaller than the
legacy analyzer, but it must be honest, tested, and extensible.

### TDD Sequence

1. Add tests for the behavior we keep:
   - package entrypoint imports without importing `ladon.ladon`;
   - CLI can analyze a tiny synthetic Lean tree without invoking Lake;
   - JSON output includes metadata and module-DAG summary;
   - text output includes actionable sections;
   - unsupported advanced legacy flags fail or warn explicitly.
2. Add tests for the quality gate:
   - strict mode rejects a synthetic C-or-worse function;
   - strict mode accepts the project source after refactor;
   - vulture high-confidence findings fail strict mode.
3. Implement or refactor only enough code to satisfy those tests.
4. Delete or quarantine the old monolith after the new entrypoint passes.

### Quality Gate Policy

The strict gate should enforce:

- `radon cc` has no C, D, E, or F blocks in active targets;
- `radon mi` has no C-grade active source files;
- `vulture --min-confidence 80` reports no findings;
- `compileall` succeeds for `src`, `tests`, and `scripts`;
- tests pass.

If legacy code must be kept temporarily, it must live outside active targets
and include a README explaining why it exists, how to compare against it, and
what packet will remove it. The preferred outcome is deletion, not quarantine.

### Clean Core Shape

The package entrypoint should call a small CLI module, for example:

- `ladon.cli`: argument parsing and orchestration only;
- `ladon.extract.lean_text`: cheap text-based Lean module discovery for smoke
  runs;
- `ladon.analysis.module_dag`: pure module-DAG analysis;
- `ladon.render`: JSON/text rendering;
- `ladon.quality`: reusable quality-gate helpers if needed by tests.

This packet should not reintroduce a broad all-in-one file.

### Compatibility Boundary

Supported in the clean core:

- `--repo-root` and old `--root` spelling for target repository root;
- analysis root by file path or module name;
- `--skip-build`;
- JSON/text output through old and new flag names where practical;
- module-DAG summary over the root namespace.

Explicitly unsupported until clean modules are rebuilt:

- packet-review internals;
- export-surface freshness checks;
- witness audits;
- certificate-artifact routes;
- declaration-level proof graph heuristics beyond what has clean tests.

Unsupported features must not silently pretend to run.

### Risks

- Removing legacy code may temporarily reduce feature coverage. That is
  acceptable if the CLI is honest and the removed features are tracked as
  clean-core follow-up packets.
- Radon thresholds can encourage pointless decomposition. Keep functions small,
  but prefer meaningful modules and tests over mechanical fragmentation.
- Downstream skills may reference old flags. Update the Ladon skill after the
  new CLI behavior is known.

### Validation

Expected validation after apply:

```bash
uv run pytest -q
uv run python scripts/python_quality.py --strict
uv run python -m compileall -q src tests scripts
uv build
bin/ladon --repo-root /home/codex/projects/quux --root Quux/Semantics/Propagation.lean --skip-build --output-json /tmp/ladon-clean-core-quux.json --output-text /tmp/ladon-clean-core-quux.txt
```
