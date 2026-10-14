# Common local tool setup

Lean executable: /home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean
Your input directory contains Main.lean, Main.olean, source.txt and lean-toolchain.
Work only in your assigned output directory; do not edit input bytes. For a check,
write output/Check.lean and invoke Lean from the input directory with LEAN_PATH
set to that input directory. Import Main to use the actual supplied declarations.
Record argv, cwd, environment, exit, elapsed time, stdout and stderr for each command.
No Lake/cache/package/installation commands. Existing stdlib only. Read only your
assigned files and permitted tool documentation. No online or target-paper searches.
The task is to inspect the entire prose passage, select relevant steps yourself,
and compare meaning, dependencies and claimed method against the actual proof.
A valid endpoint can coexist with a faulty intermediate inference. Distinguish
an unsupported link, ambiguity, alternate method, and mathematical refutation.

Assisted arm only: current Ladon executable is
PYTHONPATH=/home/codex/projects/ladon/src /home/codex/projects/ladon/.venv/bin/python -m ladon.entrypoint
Use --help and correspondence --help for the ordinary public interface. You may
read tool implementation under src/ladon solely to understand command/schema
usage; never development fixtures, example reports, other pilot cases or keys.
The relevant subcommands are correspondence slice, interpret, align, check.
Use --root pointing at your own input directory and outputs in your own output
directory. Select the declaration/application from your actual supplied proof;
no application or tested inference has been chosen for you. A scoped slice is
opt-in. Elaborated local replay checks the interpreted obligations, not source
fidelity; preserve residuals. The ordinary arm uses local Lean and source tools
without importing or invoking Ladon. Both arms may provide directly checked
original-goal terms or clearly attributed mathematical evidence.
