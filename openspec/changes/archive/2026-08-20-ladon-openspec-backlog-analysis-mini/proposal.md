# Proposal

Add a small OpenSpec backlog/self-audit analysis surface.

# Why

The status-hygiene check caught a real process defect. Ladon should continue
auditing its own packet artifacts for operational issues that affect review:
missing automation, missing validation evidence, stale child references, and
status/task drift.

# Scope

- Summarize OpenSpec change directories.
- Reuse status-hygiene inference.
- Flag missing automation files.
- Flag automation without an `openspec validate` command.
- Flag child packet references without a corresponding change directory.
- Add a JSON-producing script.

# Non-Goals

- No semantic packet acceptance judgment.
- No execution of automation commands.
- No archive/delete workflow.
- No deep markdown natural-language analysis.
