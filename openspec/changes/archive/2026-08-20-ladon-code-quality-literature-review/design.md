# Design

The corpus layout:

```text
paper/ladon-code-quality/
  INDEX.md
  manifest.json
  arxiv/
  pdf/
```

For arXiv papers, store source tarballs from `https://arxiv.org/e-print/...`
when source is available; otherwise store the PDF and mark why.

The index should group papers by how they inform Ladon:

- static analysis and program graphs;
- software metrics and maintainability;
- clone/similarity and repeated proof-shape detection;
- architecture recovery and dependency analysis;
- proof engineering / theorem-prover tooling.
