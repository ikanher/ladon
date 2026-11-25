# Resolve source ownership before index insertion

## Context

`lean_layout.modules_from_roots` identifies conflicts where one module name has multiple files. The OAI case has the inverse shape. Two names survive discovery with the same file. `proof_search_index._indexed_source` records resolved source paths, and the `modules.path` uniqueness constraint rejects the second row. OAI's Lakefile uses a library facet to remove the broader challenge aliases and retain the helpers under their original names. Ladon reads a conservative subset of the Lake declarations and does not evaluate the facet. See [bug-report.md](bug-report.md) for the specific path and fixture.

## Goals / Non-Goals

- Resolve source ownership before extracting or publishing index rows. Give the same result to every path that observes the source generation.
- Keep the existing source path identity and SQLite uniqueness constraint. Arbitrary Lake code execution and support for indexing two genuine module identities from one source file are outside this change.

## Decisions

1. Detect aliases at the source inventory boundary using the same path identity that is stored in the index. Group all candidate names for a path before choosing an owner. Insertion-time deduplication would leave the chosen name dependent on iteration order and would hide the conflict from freshness and scope queries.
2. Use canonical ownership from supported static configuration when available. Provide a declarative selection for a layout whose custom Lake logic cannot be resolved statically. For the OAI case, the intended owner is `HodgeConjecture.*` as shown by the facet. Root depth by itself does not establish what a custom facet does.
3. Include the ownership resolution and any unused candidates in the observed layout. Feed the selected mapping into source fingerprinting and preserve the existing atomic publication behavior. An invalid selection or a remaining ambiguity yields a layout diagnostic before any replacement is published.

## Risks / Trade-offs

- A wrong owner can silently misroute import, scope, or compiled evidence lookup. Check the canonical module and source path in the fixture and preserve the separate diagnostic for two files claiming one module name.
- A change in ownership can alter a source generation even when file bytes are identical. Check build, update, and freshness together. Preserve existing evidence under its original generation when compatibility rules require a new build.
