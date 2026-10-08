# Ladon

Ladon helps people and LLMs search Lean projects, check proposed theorem
applications, and examine the formal support behind mathematical explanations.
It works alongside Lean and ordinary proof-development tools.

The goal is to make AI-assisted mathematics easier to understand, check,
attribute, and reuse. Ladon is in **alpha**. Lean performs the proof checking;
a successful check does not certify the meaning or argument of nearby prose.

## Setup

Requires Python 3.11 or 3.12 and [uv](https://docs.astral.sh/uv/).
From this checkout:

```bash
uv sync --locked
uv run --locked ladon --version
```

The examples below run from the Ladon checkout. Replace `/path/to/project`
with your Lean project's root. Lean-backed operations need that project's
pinned Lean/Lake toolchain and compiled dependencies. They can execute project
code, so use them with trusted projects.

## Find and check Lean results

Build a local index, then search declaration names or type text:

```bash
uv run --locked ladon proof-search index build --repo-root /path/to/project
uv run --locked ladon proof-search search name \
  --repo-root /path/to/project --text integrable --limit 10
uv run --locked ladon proof-search search type-text \
  --repo-root /path/to/project --pattern 'Nat → Nat' --limit 10
```

Indexing and search read source text without running Lean. Results are
candidates to investigate, not proof that a theorem applies. The disposable
index lives in `.ladon/index/`; add that directory to your project's ignore
file, or choose another location with `--index`.

Check a candidate against a goal in a compiled module from your project:

```bash
uv run --locked ladon proof-search check candidate \
  --repo-root /path/to/project --module Project.Basic \
  --goal '∀ a b : Nat, a + b = b + a' --candidate Nat.add_comm
```

`proof-search discover` searches a bounded shortlist and checks candidates
against a goal. It accepts ordered local hypotheses with repeated
`--local NAME:TYPE` arguments. Results show the attempted application and any
remaining goals, including their local context. An application with remaining
goals is incomplete.

For an existing proof, `proof-search goal capture` reads the goal and context
at a source position. `proof-search goal complete` checks a proposed term
against that capture, replays it through the Lean compiler, and checks its
axiom dependencies. Completion concerns the selected goal; it does not edit
the file or complete the enclosing declaration.

See [search and checking](docs/CLI.md),
[application details](docs/APPLICATION_OBSERVATIONS.md),
[goal capture](docs/SOURCE_GOAL_CAPTURE.md), and
[goal completion](docs/SOURCE_GOAL_COMPLETION.md).

## Review proof explanations and formal coverage

A result manifest maps written claims and their components to formal results.
An optional guide adds explanations, citations, and attributed reviews.
Ladon shows which components have formal links, what the supplied evidence
supports, and which reviews need reassessment after a revision.

Read a supplied result bundle without its original project or cache:

```bash
uv run --locked ladon result inspect result.zip --section components
uv run --locked ladon result guide result.zip --section steps
```

These views read stored evidence; they do not run Lean or automatically judge
whether prose faithfully describes a proof. The [correspondence audit
recipe](docs/PROOF_CORRESPONDENCE_AUDIT.md) shows how to check a disputed step,
preserve its assumptions, and propose a correction using ordinary files and
Lean.

Use `result validate` for a manifest, `result export` to package explicitly
selected files, and `result verify` to check bundle integrity. Integrity,
proof checking, and human review remain separate.

See [manifests](docs/RESULT_MANIFEST.md), [reading guides](docs/RESULT_GUIDES.md),
[paragraph review](docs/RESULT_EXPOSITION.md), and
[portable bundles](docs/RESULT_BUNDLES.md).

## Review project structure

Inspect module imports, duplicate imports, large modules, and dependency
structure around a root file:

```bash
uv run --locked ladon --repo-root /path/to/project --root Project/Basic.lean
```

Default analysis reads source text without running Lean or building the project.
Add `--architecture-policy policy.json` to check your project's module-boundary
rules. Optional Lean extraction adds declaration evidence.

Use `--format json --output report.json` for a saved machine-readable report.
See the [CLI reference](docs/CLI.md) and
[example architecture policy](docs/policies/architecture-policy.example.json).

## Other tools

| Tool | Purpose |
| --- | --- |
| `proof-search explain`, `consumers`, `constructor` | Inspect available type, usage, and constructor evidence. [Reference](docs/CLI.md) |
| `proofir`, `proof-search evidence` | Validate proof-evidence files and inspect stored checks. [Reference](docs/CLI.md#stored-proofir-evidence) |
| `theorem lineage` | Explore dependencies of a compiled proof. [Reference](docs/CLI.md#theorem-lineage) |
| `theorem extract` | Package a theorem's source context and replay it in a fresh copy. [Theorem capsules](docs/THEOREM_CAPSULES.md) |
| `inspect` | Filter and page through an existing report. [Reference](docs/CLI.md) |
| Atlas, runsets, and reportsets | Compare reports and manage batches of analysis. [Reference](docs/CLI.md) |
| `doctor` | Inspect the installation and a project's execution prerequisites. [Reference](docs/CLI.md#build-and-execution-security) |

## Development and status

Run the maintained Python quality and test gate:

```bash
uv run --locked python scripts/python_quality.py --strict
```

See [reproducibility](docs/REPRODUCIBILITY.md) for the full verification workflow,
Python and Lean support, and distribution status. Ladon is developed primarily
with AI assistance.

For current support and known limits, see [product scope](docs/PRODUCT_SCOPE.md)
and the [measured alpha profile](docs/MEASURED_ALPHA_PROFILE.md). Agent
instructions are in the [Ladon skill](skills/ladon/SKILL.md).
