# Fresh source-first mathematical audit

You are performing a fresh, source-first mathematical audit. Read the complete two TeX notes under `INPUT/capsule/sources/latex/natural-language/` and inspect the corresponding files in `INPUT/capsule/lean/`. Follow the adjacent `INPUT/RECIPE.md`. Find and report what the source and formal development actually support; do not assume an error is present. The selected scoring units and their expected classifications are not disclosed. Audit the notes broadly, then report any claim-specific findings that you can substantiate.

Use only the provided input directory, the installed Lean toolchain and the tool explicitly named below. Do not browse the network, inspect the parent project, git history, registration/evidence directories, prior reviews or reports, or any answer material. Do not ask another agent or user for the diagnosis. This is a procedural isolation boundary; the runtime does not enforce filesystem access restrictions.

Before reading the sources, save `OUTPUT/ROLE-ACK.json` affirming that you understand the assigned arm, will not inspect other run/registration files, and have not received an answer or another arm report. If you cannot make that affirmation, stop and report why.

Budget: stop at 90 minutes wall time or 30 Lean/Lake command invocations, whichever comes first. Count each top-level `lean` or `lake` command invocation once; do not launch broad builds. Both limits are equal across arms. Record start/end time, every command and its result, number of Lean/Lake invocations, and whether the wall-time or invocation ceiling was reached. Token telemetry is not available as an enforceable budget; report it only if the runtime exposes it, otherwise say `unavailable`.

Save one immutable first report as `OUTPUT/FIRST-REPORT.md` and all supporting outputs or command transcripts beneath `OUTPUT/evidence/`. Include the source inventory, findings and controls, abstentions, unresolved matters, source coverage, exact Lean declarations/commands/results, and limits of your work. Do not revise the first report after saving it. If you discover an error in your report, save a separately timestamped correction and preserve the first report unchanged. Do not inspect the other arm's directory.

Tool access: You may use ordinary shell file search and the pinned Lean/Lake environment in `INPUT/capsule/lean/`. You must not invoke Ladon. Save outputs only under your assigned `OUTPUT/` directory.
