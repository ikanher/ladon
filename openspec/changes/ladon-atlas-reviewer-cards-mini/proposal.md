# Proposal

Add compact reviewer cards to the Ladon atlas Markdown surface.

# Why

Counts and graph rows are not enough for review routing. Reviewers need a
short, repeated shape per root/report: what it is, what is hot, what evidence
exists, what is not claimed, and where to inspect the raw report.

# Scope

- Derive one reviewer card per report node.
- Include root, backend, top findings, review regions, strongest evidence,
  known non-claims, and source report links.
- Extend atlas export with optional card Markdown output.

# Non-Goals

- No UI.
- No LLM summarization.
- No claim that cards replace raw JSON/text reports.
