# Comparison launcher

You are the launch custodian. Do not perform a mathematical audit yourself.
Preparation stops before any audit source inspection. The canonical readiness
record will be `openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/synthetic-launch-r01/READINESS.json`
in `/home/codex/projects/ladon`; require status `ready-to-launch` before proceeding.
Read the registration and HANDOFF.md in sibling `synthetic-comparison-r01`.
Do not give those records or this file to mathematical auditors.

Use the exact workspace order in READINESS.json. For each workspace:

1. Check its LAUNCH.json hash against READINESS.json; verify its inputFiles
   digests and that outputs/ is empty. Reverify the registered runtime source
   snapshot before the first audit. A mismatch is an incident, not permission
   to substitute inputs or silently change the registration.
2. Spawn one fresh context with `fork_turns=none`, model `gpt-6-luna`, reasoning
   `medium`. Give only the absolute path to its PROMPT.md and tell it to read
   LAUNCH.json and activate CHECK.py before inspecting mathematical sources.
   Do not add mathematical advice, roles or prior results. No worker reuse.
3. The registered invocation is:
   `/home/codex/projects/ladon/.venv/bin/python WORKSPACE/CHECK.py --activate`
   and each checking command uses that same Python with
   `WORKSPACE/CHECK.py -- COMMAND ARG...`. The runner binds local Ladon src;
   control can use its shared supervisor but cannot use native Ladon tools.
4. Monitor actual SESSION.json deadline. Preserve first reports and all command
   receipts. Interrupt an auditor that exceeds its wall deadline. Freeze its
   output hashes before moving to the next fresh context. Missing reports,
   command overruns, incomplete receipts or exposure incidents remain reported.
   Do not retry a scored unit after seeing its result.

Run sequentially. Keep inputs private to the assigned context. Filesystem and
network separation are procedural instructions, not an OS security claim.
Underlying Lean process telemetry is descriptive; missing counts are null.

After all ten first reports are frozen, follow the registration's two-reviewer
blind adjudication and tie-breaking procedure. Preserve first independent ratings
before reference consultation. Custodian reference material remains in the Ladon
repository and must never reach auditors. Apply the frozen primary gate only
when required pairs and adjudications are valid. Report incomplete outcomes.

The preparation receipt is not authorization to change cases or tune the recipe.
No audits were started during preparation.
