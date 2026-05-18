# Proposal

Turn stabilized Ladon report directories into a portable review atlas. The first
target is the root-matrix evidence directory because it already has calibrated
Quux/MF reports and regression predicates.

# Scope

- Add a deterministic report-atlas exporter.
- Include JSON and Markdown outputs.
- Run the exporter on `temp/root-matrix-evidence-pass/reports`.
- Keep the atlas focused on reviewer-facing signals rather than full duplicated
  module DAGs.

# Non-Goals

- No visualization framework dependency.
- No database in the first packet.
- No LLM-generated classifications.
