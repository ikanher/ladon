# Proposal

The installed Codex skill for Ladon still describes the earliest clean core: a
text-only module-DAG reporter with declaration analysis deferred. The project now
has a Lean-backed root declaration graph and an optional helper-payload cache.

Refresh the skill so other Codex instances call the shared tool correctly and do
not replicate old wrappers or underuse the declaration graph.

# Scope

- Update `/home/codex/.codex/skills/ladon/SKILL.md`.
- Mention `--extraction-backend lean`, root-scope declaration graph, and
  `--lean-cache-dir`.
- Keep limitations explicit: declaration references are conservative candidates,
  not elaborated proof dependencies.
