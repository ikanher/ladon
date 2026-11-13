# Matched arm instructions

The two arm prompts share the same task text and recipe. The only permitted
difference is the final tool-access paragraph, whose SHA-256 values are recorded
in `RUN-REGISTRATION.json`.

## Shared task text

You are performing a fresh, source-first mathematical audit. Read the complete
two TeX notes under `INPUT/sources/latex/natural-language/` and inspect the
corresponding files in `INPUT/lean/`. Follow `RECIPE.md`. Find and report what
the source and formal development actually support; do not assume an error is
present. The selected scoring units and their expected classifications are
not disclosed. Audit the notes broadly, then report any claim-specific findings
that you can substantiate.

Use only the provided input directory, the installed Lean toolchain and the
tool explicitly named in your arm paragraph. Do not browse the network, inspect
the parent project, git history, registration/evidence directories, prior
reviews or reports, or any answer material. Do not ask another agent or user for
the diagnosis. This is a procedural isolation boundary; the runtime does not
enforce filesystem access restrictions.

Budget: stop at 90 minutes wall time or 30 Lean/Lake command invocations,
whichever comes first. Count each top-level `lean` or `lake` command invocation
once; do not launch broad builds. Both limits are equal across arms. Record
start/end time, every command and its result, number of Lean/Lake invocations,
and whether the wall-time or invocation ceiling was reached. Token telemetry is
not available as an enforceable budget; report it only if the runtime exposes
it, otherwise say `unavailable`.

Save one immutable first report as `OUTPUT/FIRST-REPORT.md` and all supporting
outputs or command transcripts beneath `OUTPUT/evidence/`. Include the source
inventory, findings and controls, abstentions, unresolved matters, source
coverage, exact Lean declarations/commands/results, and the limits of your
work. Do not revise the first report after saving it. If you discover an error
in your report, save a separately timestamped correction and preserve the first
report unchanged. Do not inspect the other arm's directory.

## Ordinary arm tool paragraph

You may use ordinary shell file search and the pinned Lean/Lake environment in
`INPUT/lean/`. You must not invoke Ladon. Save all outputs only under your
assigned `OUTPUT/` directory.

## Ladon arm tool paragraph

You may use ordinary shell file search, the pinned Lean/Lake environment in
`INPUT/lean/`, and the current Ladon working-tree executable at
`/home/codex/projects/ladon/.venv/bin/ladon`. If using Ladon, point it only at
`INPUT/lean/`, keep all generated outputs under your assigned `OUTPUT/`, and
record exact commands and results. Do not invoke any globally or pip-installed
Ladon executable.

## Prompt identity check

The canonical prompts are `ordinary/PROMPT.md` and `ladon/PROMPT.md` in the run
directory. Their shared task text must remain byte-identical; the only diff is
the ordinary-versus-Ladon tool paragraph.
