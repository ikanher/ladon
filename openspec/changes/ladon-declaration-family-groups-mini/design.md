# Design

For a declaration basename such as:

```text
bifrHalfSlicePackedSqrtProfileSum_ge_one_add_firstLag
```

the family suffix is:

```text
ge_one_add_firstLag
```

Declarations with the same suffix are grouped. This is deliberately simple, but
it catches many Lean theorem families where the prefix names an object and the
suffix names the lemma shape.

Rows include:

- `suffix`
- `count`
- `sample_declarations`

Groups with count at least three are promoted into findings.
