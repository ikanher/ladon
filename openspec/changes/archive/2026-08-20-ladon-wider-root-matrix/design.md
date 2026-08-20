# Design

The root matrix is static and explicit for the first slice.

Entries include:

- Quux project root.
- Quux `ProofIR`, `Bridge.Example.Core`, `Semantics.Propagation`, and selected
  problem owners.
- Matrix-factorization project root.
- Matrix-factorization `GaussianCore`, `BSRFactorCore`, `Optimization` owner,
  and BIFR packed-profile owner.

The script supports:

- dry-run command rendering;
- selected entry names;
- optional execution with JSON/text output paths.
