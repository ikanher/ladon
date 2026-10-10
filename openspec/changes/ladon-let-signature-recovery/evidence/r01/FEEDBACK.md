# Ladon 0.2.2 navigation and freshness feedback

The new skill gives a useful workflow for source edits: verify freshness, inspect changed modules, incrementally update lexical rows, retain old evidence separately, and reacquire current compiled lineage. This directly addresses the earlier stale-index friction.

## Observations

- The installed version/content identities before and after the upgrade are preserved separately in version.json and version-0.2.2.json. The private build was launched before the upgrade; its timing is not attributed to 0.2.2. No clean-install release qualification is claimed.
- The original default index reported incompatible-schema. It was preserved, including its earlier compiled lineage. The private index built successfully within the default 1024 MiB cap. Version 0.2.2 then reported that private generation fresh.
- On 0.2.2, the exact query found Mf.Optimization.FiniteMemoryAdam.streamRun_joint_centered_carried_remainder at InitializedMaskCarriedMemory.lean:20. The scoped carried-memory search returned relevant declarations. These remain lexical navigation observations.
- A no-change index update returned unchanged, reused 8168 modules, extracted 0 modules, and took approximately 2.29 seconds. Actual changed-module extraction, history preservation across a source change, semantic candidate checking and refreshed lineage were not tested in this pass.

## Reproducible type-signature issue

exact.json records the current-law endpoint with typeText ending in `: let state`, typeTextBytes 263 and typeTextTruncated false. The source statement continues with multiple let-bindings and its actual inequality, including defaultCarriedMemoryCoefficient. Likewise the initialized scalar-response signatures end at `: let p`.

The module-scoped type-text query for defaultCarriedMemoryCoefficient returned only defaultCarriedMemoryCoefficient_nonneg; it missed the response theorems whose conclusions contain that symbol after the let-bindings. Commands and full outputs are retained in navigation-commands.json, exact.json, conceptual.json and type.json.

Recommendation: distinguish let-binding assignments inside theorem types from the declaration's proof assignment. Until complete lexical extraction is supported, report a partial-signature limitation rather than a complete-looking typeTextTruncated false. Add a regression covering consecutive let-bindings and a symbol appearing only in the final inequality.

## Documentation consistency

The skill describes index update after source edits, but docs/LADON.md still recommends rebuilding a missing or stale index. Align that short runbook with status --changed / update, retaining explicit rebuild for incompatible schema or stale configuration and keeping retained compiled lineage separate.

## Scope

This is a bounded navigation/freshness field observation, not a full Ladon validation run. No Lean/Lake checking, production theorem edits or review-packet changes were performed. The disposable private index is pruned through Ladon's reviewed lifecycle operation; the original default index remains intact. JSON commands and stderr captures remain available here.
