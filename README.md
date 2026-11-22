# Ladon

Ladon helps mathematicians and coding agents find Lean theorems they can reuse
and trace the dependencies of a compiled proof. **Version 0.5.0 · alpha.**

- **Find a theorem when you don't know its name.** Search an indexed library
  for a fragment of the type you need. A source match gives you a declaration
  and a file location. Inspect its hypotheses, then ask Lean to check the
  application against your goal. [Find and check Lean results](#find-and-check-lean-results)
- **See what a proof actually uses.** Trace a compiled dependency to the
  statement or proof that uses it. Ladon reports when the stored evidence is
  stale or the displayed graph is incomplete. [Inspect compiled theorem lineage](#inspect-compiled-theorem-lineage)

## Finding a Gaussian integral in a number theory archive

While working on differentially private Adam, we needed the exponential moment
of a Gaussian quadratic form with off-diagonal terms. We suspected a Fourier
transform theorem could supply the integral, but didn't know its name.
We searched Levent Alpöge’s Riemann Hypothesis archive for the square root of
a matrix determinant. Given the local index from the walkthrough, the query is:

```bash
uv run --locked ladon proof-search search type-text \
  --repo-root . --index "$RH_INDEX" --freshness stored \
  --pattern 'Real.sqrt |S.det|' --limit 10
```

Three declarations matched. One was `fourier_gaussian_real_place`. Setting its
frequency to zero gave the integral for a positive-definite matrix. A second
search found the identity for completing the square, and we checked the
resulting expectation formula in Lean on our project's toolchain.

The walkthrough downloads the author’s archive and builds a local index. On our
machine, indexing **1,057,634 declarations in 175,187 files** took 10 min 34 s
and produced a 3.83 GiB SQLite file. Both example searches read that snapshot
without building the RH project. [Build the index and reproduce both searches](docs/RH_INDEX_EXAMPLE.md)

## Setup

From the Ladon checkout, use Python 3.11 or 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run --locked ladon --version
```

Source search works without running Lean. Application checks and compiled
dependency inspection need the project's pinned toolchain and compiled
dependencies. Use Lean-backed operations with trusted projects because they can
execute project code. [Instructions for coding agents](skills/ladon/SKILL.md)

## Find and check Lean results

Set `PROJECT` to your Lean project's root. Build its index once, then search by
name or type. To search another library, point the same commands at its root.

```bash
uv run --locked ladon proof-search index build --repo-root "$PROJECT"
uv run --locked ladon proof-search search name --repo-root "$PROJECT" --text integrable --limit 10
uv run --locked ladon proof-search search type-text --repo-root "$PROJECT" --pattern 'Nat → Nat' --limit 10
```

Check the reported search scope and freshness before reusing a match. For
example, the RH search above explicitly asks for the stored snapshot. After
source edits, `proof-search index status --changed` identifies stale files and
`proof-search index update` refreshes the index. [Index and search options](docs/CLI.md#proof-search-index)

To try a candidate, replace `Project.Basic` below with a compiled module in
your project. Lean checks the application in that module's environment.

```bash
uv run --locked ladon proof-search check candidate \
  --repo-root "$PROJECT" --module Project.Basic \
  --goal '∀ a b : Nat, a + b = b + a' --candidate Nat.add_comm
```

If a candidate leaves premises open, Ladon shows the remaining goals. Use
`proof-search discover` to try a shortlist against a goal with local hypotheses,
or capture a goal directly at a position in your Lean file.
[Application checks](docs/APPLICATION_OBSERVATIONS.md) · [Source goals](docs/SOURCE_GOAL_CAPTURE.md)

## Inspect compiled theorem lineage

When reviewing a proof, it helps to distinguish declarations mentioned in the
theorem's type from lemmas used in its proof. The `closure` view reports both
kinds of dependency. For example, in a spectral-coordinate proof it let us
trace the polynomial spectral mapping step back to the Lean result supplying it.

```bash
uv run --locked ladon theorem lineage Fully.Qualified.theorem \
  --repo-root "$PROJECT" --view closure --refresh missing
```

Replace the theorem name with one from your compiled project. Use
`--refresh never` to inspect an existing record. Check the reported coverage
before treating the graph as complete. In one audit, a 100-node cap displayed
100 of 2,242 declarations and reported the 2,142 omitted.
[Lineage, graph limits, and historical snapshots](docs/CLI.md#theorem-lineage)

## More workflows

- **Review an exposition.** Map written claims to Lean statements and compare
  their hypotheses and conclusions. [Proof correspondence walkthrough](docs/PROOF_CORRESPONDENCE_AUDIT.md)
- **Review a project’s structure.** Inspect module imports, duplicate imports,
  and dependency boundaries. [Architecture analysis](docs/CLI.md#analyzer-command)
- **Explore a declaration.** Use `proof-search explain`, `consumers`, and
  `constructor` to inspect available type and usage evidence. [CLI reference](docs/CLI.md)

## Development and license

Run `uv run --locked python scripts/python_quality.py --strict` for the Python
quality and test checks. [Reproducibility](docs/REPRODUCIBILITY.md) ·
[Measured alpha capabilities and limits](docs/MEASURED_ALPHA_PROFILE.md)

Ladon's own code and documentation are licensed under Apache-2.0. External
Lean projects and their declaration text retain their own terms. [License](LICENSE)

## A personal note

Ladon is **fully VIBE CODED**. I build it in my spare time alongside my day job
and my main research. It grew out of needing these tools in my own Lean work.
