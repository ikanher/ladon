# Proposal

Ladon now exposes useful declaration graph metrics, but users still need to
manually interpret raw fan-in, fan-out, and unresolved-reference rows.

Add a small pure findings layer that converts obvious root-local graph signals
into concise triage findings.

# Scope

- Add `analysis.findings` as a pure module.
- Emit findings for declaration fan-in hotspots, declaration fan-out hotspots,
  unresolved reference hotspots, and unreachable declaration counts.
- Render findings in text reports.
- Preserve the raw graph tables for detailed inspection.

# Non-Goals

- No proof correctness claims.
- No elaborated dependency analysis.
- No severity taxonomy beyond simple informational/warning levels.
