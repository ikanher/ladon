# Handoff: harder local-derivation test

## Objective and current state

Run a fresh evaluation on substantially harder, independently chosen proof
fragments with correct controls. Use the results to decide whether to restart
the full Navier–Stokes exposition audit or improve Ladon again.

The Navier–Stokes exposition reportedly contains an error. Its location and
nature are unknown to the next auditor. Previous independent audits did not
confirm it. This handoff provides no reference answer or clues to that error.
Do not search online for it or consult published fault explanations.

The completed development packet is
`openspec/changes/ladon-local-derivation-challenges/`. It adds opt-in version-two
investigation plans, source-bound derivation steps, priority for disputed steps,
sanitized independent challenge exports, and exact rational witness checking.
The final consumer suite passed 174 tests, and independent integration review
found no actionable defects. All six packet tasks are complete.

The previous elementary exercise had three valid controls and three invalid
implications. The challenger classified them correctly, and the public command
replayed three counterexamples. This establishes a working checking path; it
does not establish detection of a difficult exposition error. Its cases and
answers are development material, not fresh evaluation inputs.

## Run Ladon from the current checkout

**Use `/home/codex/projects/ladon`, including its current uncommitted changes.
Do not use the pip-installed Ladon or a bare `ladon` command from PATH.**

Start with:

```sh
cd /home/codex/projects/ladon
export PYTHONPATH=/home/codex/projects/ladon/src
uv run python -c 'from pathlib import Path; import ladon; import ladon.investigation_derivation as d; import ladon.rational_witness as w; expected = Path("/home/codex/projects/ladon/src/ladon").resolve(); modules = (ladon, d, w); assert all(Path(m.__file__).resolve().is_relative_to(expected) for m in modules); print("\n".join(m.__file__ for m in modules))'
uv run python -m ladon.entrypoint investigation --help
```

The import check must resolve all three modules under the checkout's
`src/ladon/`. Record those paths and source identities in the new run. The help
command must list `init`, `challenge`, `witness`, `status`, `next`, and `finish`.
These commands were verified when this handoff was written.

Use `uv run python -m ladon.entrypoint ...` for every Ladon invocation, retaining
the explicit `PYTHONPATH`. If working from an evaluation directory instead, add
`--project /home/codex/projects/ladon` to `uv run` and keep the same source path.
Pass `--root` for the actual evaluation source directory; this is distinct from
the directory containing the Ladon implementation. Inherit the source path in
subprocesses and auditor tools too. A version number alone cannot establish
that these uncommitted upgrades are loaded.

## Prepare a fresh, bounded evaluation

Create a new OpenSpec evaluation packet before nontrivial setup or implementation.
Leave the completed development packet and previous runs intact. Preserve the
existing dirty worktree, especially unrelated `FIRST-HAND-REPORT.md` changes.
Do not change Quux's active packet or reset either repository.

Have an independent case author choose several harder proof fragments unrelated
to the target paper's known answer. Mix faulty arguments with correct controls;
use opaque case IDs and keep their ordering and classifications undisclosed.
Require enough surrounding definitions and assumptions to judge each fragment.
Freeze the source inputs and a separately justified answer key before evaluation.
Do not give the auditor preselected suspect steps or prewritten scalar
interpretations: identifying and translating the inference is part of this test.

Separate the case author from a fresh auditor. The auditor receives only the
generic procedure, public case sources, relevant formal sources when available,
and the current local Ladon commands. It receives no reference answers, earlier
case assessments, developer conversation, or historical target findings. Save
its first responses before revealing any key or giving feedback. If workers
share a filesystem, explicitly record that isolation is procedural rather than
access-enforced; preferably give the auditor a workspace containing only allowed
inputs. User authorization for sub-agents already exists; follow the applicable
swarm skills if using them.

Record a time budget and evaluation criteria before dispatch. Require the auditor
to identify the exact inference, preserve the original obligation, and provide
either a justification, a counterexample meeting every premise, or an explicit
unresolved obligation. Incorrect controls must count as false accusations.
Report all cases, including unresolved cases, rather than only successes.

## Use the new workflow

Read `docs/DERIVATION_CHALLENGES.md` for the schema and supported arithmetic.
Initialize with `investigation init --derivations`, then save source-bound
contracts and individual steps. Expand named rules into their actual premises,
substitutions, domains, and conclusions. Resolve disputed steps before extending
broad inventories. Use `challenge` for sanitized review inputs and `witness` to
replay proposed assignments against the stored goal. Save `next` and `finish`
outputs with the plan.

Check separately that the encoded implication faithfully represents the prose.
The rational checker only evaluates its authored scalar interpretation. A
`counterexample` must satisfy every encoded premise and falsify the conclusion;
`outside-assumptions` cannot refute it. `not-counterexample` is not universal
support. Use mathematical reasoning or appropriate Lean evidence for claims
outside the supported fragment. A successful Lean build alone does not check
the exposition's individual inferences. Keep repairs separate from the original
claim, and retain uncertainty when the translation or realization is incomplete.

## Preserve results and make the next decision

Save input identities, tool import paths, exact invocations, plans, source
quotes, exported challenges, first responses, witness receipts, elapsed time,
and unresolved work in a new run directory. Keep the key separate until the
first report is frozen. After reveal, compare each claimed fault and supporting
argument with the key; inspect controls through actual reasoning, not passing
samples. Record both classification and whether the reasoning established it.

If the auditor resolves the harder faulty fragments with valid evidence and
avoids falsely accusing the controls, use that evidence to decide whether a new
full-paper audit is justified. If it struggles, identify the exact failed stage
and propose a focused upgrade. Do not count implementation tests, agreement
between workers, or extra captured records as successful mathematical detection.

Operator evidence for the completed upgrade is in
`openspec/changes/ladon-local-derivation-challenges/evidence/INTEGRATION-REPORT.md`.
Its exercise answer files belong to the operator, not the fresh auditor's inputs.
No new evaluation or full-paper audit has been run as part of writing this handoff.
