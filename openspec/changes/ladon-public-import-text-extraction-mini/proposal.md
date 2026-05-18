# Proposal

The mathlib smoke run exposed a text-extraction defect, not a mathlib defect.

Current evidence from `temp/mathlib-ladon-smoke/`:

- mathlib inventory: `7649` modules;
- Ladon reported only `270` module edges;
- raw text count found roughly `286` bare `import` lines but more than `31k`
  `public import` lines;
- reported cycles came from `import ...` snippets inside docstring code
  examples, including self-import examples such as `Mathlib.Tactic.Rify`.

The text extractor is still using a narrow regex for bare import lines. That was
good enough for small local repos, but it is not good enough for current mathlib.

# Scope

- Extend text import parsing to recognize Lean import modifiers used by mathlib:
  - `public import`
  - `public meta import`
  - `import all`
  - plain `import`
- Ignore imports that occur inside block comments and module docstrings before
  extracting module edges.
- Add regression tests that reproduce the mathlib failure mode:
  - public imports are counted as edges;
  - imports inside fenced docstring examples do not become graph edges;
  - self-import examples do not create false cyclic components.
- Re-run the mathlib text-backed smoke report and record the new edge count and
  cycle status.

# Non-Goals

- No Lean elaboration or proof-dependency extraction.
- No attempt to fully parse Lean syntax.
- No broad mathlib architecture claim from this packet alone.
- No changes to target repositories.
