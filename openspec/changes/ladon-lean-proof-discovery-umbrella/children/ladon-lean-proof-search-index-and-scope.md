# `ladon-lean-proof-search-index-and-scope`

Adds a versioned persistent local navigation index with transactional updates, explicit freshness, and normalized proof-work scopes. The alpha SQLite backend defaults to the repository's disposable `.ladon/index/` subtree.

- Dependencies: module, declaration, elaboration, and snapshot authorities.
- Enables: fast bounded candidate discovery without weakening Lean authority.
- Excludes: storing raw toolchain-unstable expressions as portable truth.
- Exit: incremental, stale, partial, scoped, deterministic, and resource gates pass.
