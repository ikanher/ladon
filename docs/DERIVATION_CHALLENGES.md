# Challenge a local derivation

When a prose argument and its proposed formal support diverge, work on the exact implication at that point. Preserve the original statement. Expand each named rule into its actual premises, substitutions and conclusion, including parameter domains and permitted dependencies. A complete theorem build does not discharge this local work.

Initialize the opt-in step workflow:

```sh
ladon investigation init --text exposition.txt --root . --output plan.json --derivations
ladon investigation next --plan plan.json --root .
```

Existing version-one plans remain supported. For an existing investigation, save a separate snapshot before changing its `version` to `2`; never rewrite a completed first report. Version two puts claims with an explicit nonempty `concern`, differing/unresolved judgments, or an existing `derivation` ahead of unrelated inventory. It retains unexamined material and the budget gate.

For a suspect claim, author its seven-field local contract, then a `derivation` with `author` and `steps`. Each step has:

- A unique `id`, inclusive `startLine`/`endLine`, and exact `quote` inside the parent claim.
- A `contract` with `objects`, `assumptions`, `domains`, `quantifiers`, `conclusion`, `dependencies` and `neededImplication`.
- The exact `rule` and `substitution`, and `dependsOn` listing earlier step IDs (or an empty list).
- An optional `assessment` with `outcome` (`supported`, `refuted`, or `unresolved`) and a substantive `evidence` explanation.
- An optional `arithmetic` interpretation for the small rational fragment described below.

Use separate steps for separate inferences. An assertion such as “the standard inequality applies” must be expanded enough to inspect its side conditions. An unsupported original step remains open even if a repaired statement can be proved. Put repairs in a separate record.

Export the challenge after recording the author's assessment:

```sh
ladon investigation challenge --plan plan.json --root . --claim claim-id --output challenge.json
```

The new file contains the original claim, candidate formal counterpart and step obligations. It omits previous assessments, judgments, challenges and repair metadata. Give it and the referenced primary sources to a fresh reviewer. Save the reviewer's first response separately. Ask for a derivation supporting the step, a counterexample satisfying its premises, or an explicit unresolved obligation. A successful example is not a proof.

Copy a response into the step's `challenge` as `reviewer`, `subjectSha256`, `outcome` and `evidence`. The packet supplies the subject digest. A distinct reviewer label is required; this is attribution, not identity verification or enforced context isolation. Changed contracts, arithmetic, source bindings, predecessor steps or author assessments invalidate the challenge. Workflow-only changes to the parent judgment do not. Missing challenges and disagreements remain queued. Matching assessments complete only review bookkeeping.

## Check a rational counterexample

For scalar implications, the checker can independently replay exact arithmetic. The stored `arithmetic` object has exactly `variables`, `premises` and `conclusion`. Each variable ranges over rational values satisfying every supplied premise. A predicate has `op` (`le`, `lt`, `eq`, `ne`, `ge`, `gt`), `left` and `right`. Expressions are:

```json
{"var": "x"}
{"rat": "2/3"}
{"op": "mul", "args": [{"var": "x"}, {"rat": 2}]}
{"op": "pow", "args": [{"var": "x"}], "exponent": 2}
```

Binary operations are `add`, `sub`, `mul`, `div`; unary operations are `neg`, `abs`; powers have integer exponent 0–8. Rationals are integer JSON values or integer/fraction strings. Decimals, booleans and zero denominators reject. Expressions have at most 32 levels, 4096 total nodes, 32 variables, 64 premises, 128-character literals and 4096-bit intermediate numerators/denominators. Unsupported or undefined arithmetic rejects even after an earlier false premise. Exponent zero evaluates to one.

An assignment file contains only the declared names and rational values, for example `{"x":"1/2"}`:

```sh
ladon investigation witness --plan plan.json --root . --claim claim-id \
  --step step-id --assignment assignment.json
```

The command checks the stored goal. It cannot substitute a goal from the assignment. Exact premise and conclusion values accompany one of three outcomes:

- `counterexample`: every premise holds and the conclusion fails.
- `outside-assumptions`: the assignment violates a premise.
- `not-counterexample`: this assignment does not refute the implication.

All three are valid computations (exit 0); malformed input exits 2. To attach a counterexample, copy the assignment into `challenge.witness`. It is recomputed during plan validation. A non-refuting witness cannot justify a `refuted` outcome, and a real counterexample cannot be hidden by `supported` labels.

This arithmetic disproves only the authored scalar implication. A separate mathematical review must establish that it faithfully represents the source, including all assumptions and quantifiers. It does not prove universal support, eliminate existential constants, realize abstract quantities as functions, or validate an analytic estimate automatically. Use ordinary Lean checks or a conventional proof for obligations outside this fragment and preserve any remaining gap.

## Runnable small-case exercise

From the Ladon development checkout:

```sh
python scripts/demo_derivation_challenges.py --output /tmp/ladon-step-cases
```

Use a new output directory. The script creates six source-bound plans and sanitized packets from independently authored public fixtures. It supplies no classifications. The accompanying development evaluation retains first challenger responses and replay outcomes separately; these elementary cases do not measure research-paper detection accuracy.

After each actual review batch, save the plan and use `next`. Use `finish` before reporting. An unresolved step remains work, and budget/blocker exits remain incomplete. Neither extra record count nor a successful build is evidence that the disputed implication was checked.
