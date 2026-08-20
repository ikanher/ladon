# Proposal

Add a deterministic SQLite export and canned query layer for Ladon report
atlases.

# Why

The current atlas JSON is useful as a machine artifact, but reviewers still
need to inspect raw graph rows to answer operational questions. SQLite gives us
a system-level, dependency-free query surface that can answer hotspot,
recurrence, review-region, and proof-pressure questions directly.

# Scope

- Convert existing atlas JSON nodes/edges into normalized SQLite tables.
- Add canned query functions for common reviewer questions.
- Extend the atlas export script with optional SQLite output.
- Add a small query script for humans and automation.

# Non-Goals

- No replacement of atlas JSON.
- No UI.
- No arbitrary query language wrapper beyond SQLite itself.
- No schema migration system.
