# Tasks

## 1. Discover canonical source ownership

- [x] 1.1 Detect one resolved source path appearing under multiple candidate names. Extend `tests/test_lean_layout.py` to exercise the supplied fixture and retain coverage for two paths claiming the same module name.
- [x] 1.2 Resolve supported ownership declarations and provide a declarative selection for unresolved static layouts. Document the resolution contract with a fixture where the nested owner and the unrelated module both remain visible.

## 2. Publish a queryable index or report an actionable conflict

- [x] 2.1 Use the resolved source mapping for build, update, and freshness. Build the fixture under confirmed ownership and verify exact lookups of both declarations, canonical module scope, and a fresh status.
- [x] 2.2 Report unresolved collisions before publication. Exercise a build and an update and check the path, competing names, exit result, and preservation of any prior generation. Verify ordinary nonoverlapping roots still behave as before.
- [x] 2.3 Compare the normalized mapping for the OAI example with the `HodgeConjecture` ownership indicated by its Lakefile. Use a bounded source inventory or a small subset before any full corpus build.

## Verification

- The installed 0.5.1 reproducer fails on `modules.path`. Running the same script with `--ladon "$PWD/bin/ladon"` reports `ambiguous-source` before publication and lists both names.
- The [layout tests](../../../tests/test_lean_layout.py) replay publication, scoped search, update, freshness, and preservation of the prior generation using the ownership rules in the [CLI guide](../../../docs/CLI.md#overlapping-lake-source-roots).
- The index, search, layout, and extraction suite passed all 281 tests. Strict Radon, Vulture, Ruff, and byte-compilation checks also passed.
- A temporary copy of the OAI Lakefile and three real source files produced a fresh lexical index with `HodgeConjecture.Variants`, `ComparatorChallenges.AbhyankarSathaye`, and `OAI.Probability.Ballisticity.Coupling.CellSeedParameters` under their respective libraries. The rule below selects the Hodge helper name. Verification used this three-file inventory.
- A read-only source discovery pass on the OAI checkout found 257 ambiguous paths. All 257 match the rule below and include its selected module among their candidates. This check did not build a full index.

```toml
[module_owners]
"ComparatorChallenges/HodgeConjectureCMAbelianVarieties/HodgeConjecture/" = "HodgeConjecture"
```
