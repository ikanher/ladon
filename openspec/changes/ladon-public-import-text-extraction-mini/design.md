# Design

Keep this as a text-extraction fix, not a new analysis layer.

## Import Syntax

Replace the current bare-import recognizer with a small line-based parser that
accepts the import forms Ladon can honestly support:

```text
import Foo.Bar
import all Foo.Bar
public import Foo.Bar
public meta import Foo.Bar
public meta import Foo.Bar -- trailing comments allowed
```

The parser should extract only the module name. It should not treat `public`,
`meta`, or `all` as module components.

## Comment And Docstring Filtering

Before import extraction, remove or mask Lean block comments:

```text
/- ... -/
```

This intentionally covers module docstrings because mathlib examples often
contain import snippets inside documentation. Those snippets are useful for
humans but are not file dependencies.

Line comments can be handled conservatively by ignoring trailing text after
`--` once the import module name has been parsed.

## Regression Evidence

The packet should add small synthetic fixtures rather than checking in a mathlib
snapshot. The closeout smoke can use the local vendored mathlib checkout under:

```text
/home/codex/projects/quux/.lake/packages/mathlib
```

The expected direction is not a pinned exact mathlib edge count, because the
vendored checkout may move. The expected direction is:

- edge count increases by orders of magnitude compared with the `270`-edge
  failed smoke;
- false one-node cycles from docstring self-import examples disappear;
- `Mathlib.lean` public imports contribute to root import closure instead of
  leaving nearly all source modules unreachable.
