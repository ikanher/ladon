## ADDED Requirements

### Requirement: Local Code Quality Literature Corpus

Ladon SHALL keep a local literature-review corpus for code quality and analysis
under `paper/`.

#### Scenario: corpus index exists

- GIVEN the literature review has been prepared
- WHEN a contributor opens `paper/ladon-code-quality/INDEX.md`
- THEN it SHALL list downloaded artifacts, URLs, and Ladon relevance notes.

#### Scenario: arXiv tarballs preferred

- GIVEN a selected paper is available on arXiv with source
- WHEN the artifact is downloaded
- THEN the corpus SHALL store the arXiv e-print tarball rather than only a PDF.

#### Scenario: manifest is machine-readable

- GIVEN the literature review has been prepared
- WHEN tooling reads `manifest.json`
- THEN it SHALL find title, authors, year, topic tags, URL, artifact path, and
  artifact type for every entry.
