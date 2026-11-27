# Ladon

Ladon helps mathematicians and coding agents find Lean theorems they can reuse
and trace the dependencies of a compiled proof. **Version 0.5.2 · alpha.**

- **Find a theorem when you don't know its name.** Search an indexed library
  for fragments of the type you need. A source match gives you a declaration
  and a file location. Inspect its hypotheses, then ask Lean to check the
  application against your goal. [Find and check Lean results](#find-and-check-lean-results)
- **See what a proof actually uses.** Trace a compiled dependency to the
  statement or proof that uses it. Ladon reports when the stored evidence is
  stale or the displayed graph is incomplete. [Inspect compiled theorem lineage](#inspect-compiled-theorem-lineage)

## Search Mathlib by theorem type

Start with the pieces of the statement you expect. Each `--fragment` matches
a sequence of Lean tokens, regardless of spacing between those tokens.
Multiple fragments must occur in the same declaration signature.
All three searches use the same source-only index.
[Build the Mathlib index](docs/MATHLIB_TYPE_SEARCH_EXAMPLE.md#build-the-mathlib-index)

### When does distance zero imply equality?

```bash
uv run --locked ladon proof-search search type-text \
  --repo-root "$MATHLIB" --index "$MATHLIB_INDEX" \
  --fragment 'dist x y=0 ↔ x=y'
```

The search returns `dist_eq_zero` in `Mathlib/Topology/MetricSpace/Defs.lean`.

### Does an injective map preserve intersections?

Look for injectivity and the image of an intersection in the same signature.

```bash
uv run --locked ladon proof-search search type-text \
  --repo-root "$MATHLIB" --index "$MATHLIB_INDEX" \
  --fragment 'Injective f' --fragment "f '' (s∩t)"
```

The search returns `Set.image_inter` in `Mathlib/Data/Set/Image.lean`. Its
conclusion identifies the image of the intersection with the intersection
of the images.

### Which version of Fubini fits the goal?

To turn an integral over a product measure into an iterated integral, look
for integrability, the product measure, and the two nested integrals.

```bash
uv run --locked ladon proof-search search type-text \
  --repo-root "$MATHLIB" --index "$MATHLIB_INDEX" \
  --fragment 'Integrable' --fragment 'μ.prod ν' --fragment '∫ x,∫ y'
```

The shortlist includes both `MeasureTheory.integral_prod` and
`MeasureTheory.integral_integral`. For the goal with the product integral on
the left and the integral in `x` outermost on the right, Lean accepts
`integral_prod` with no remaining goals. Direct application of
`integral_integral` is rejected because its equality goes the other way.
[Run the Lean check](docs/MATHLIB_TYPE_SEARCH_EXAMPLE.md#check-the-fubini-candidates)

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

Check the reported search scope and freshness before reusing a match. After
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
