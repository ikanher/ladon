# Proposal

The Lean parser helper currently parses commands sequentially without carrying
parser context changes from earlier `open scoped` commands. This makes the Lean
backend fail on valid files that use scoped imported notation, such as
`𝓝[>]` after `open scoped Topology`.

Add a narrow parser-only context transition for `open` commands so imported
scoped syntax is activated for later commands without elaborating theorem
bodies.

# Scope

- Preserve parser-only extraction semantics.
- Carry parser context through `open scoped` and plain `open` commands.
- Add a regression test using an imported scoped syntax fixture.
- Reproduce the fix on the matrix-factorization `OptimalSubsamplingBISLR.lean`
  owner that originally triggered the failure.

# Non-Goals

- No full command elaboration of analyzed files.
- No theorem/proof dependency soundness claim.
- No support for syntax introduced later in the same file by unelaborated
  `syntax` or `macro` commands.
