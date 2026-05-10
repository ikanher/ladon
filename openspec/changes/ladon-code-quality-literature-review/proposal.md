# Proposal

Build a local literature-review corpus for Ladon under `paper/`, prioritizing
arXiv source tarballs where possible.

# Scope

- Create `paper/ladon-code-quality/`.
- Download relevant paper artifacts, preferring arXiv e-print tarballs.
- Add a local index with bibliographic metadata, source URLs, artifact paths, and
  Ladon relevance notes.
- Keep the corpus focused on code quality, static analysis, software
  architecture, dependency graphs, clone/similarity detection, and theorem/proof
  engineering signals.

# Non-Goals

- No implementation changes to Ladon analyzers in this packet.
- No exhaustive survey claim.
- No copyrighted full-text redistribution beyond locally downloaded research
  artifacts for review.
