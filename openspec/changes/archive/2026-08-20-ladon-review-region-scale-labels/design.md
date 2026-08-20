# Design

Use the existing root-import-closure hotspot threshold (`5`) as the line
between context and pressure:

- if an import region contains a pressure finding or a direct closure whose
  reachable module count is at least `5`, keep `import_pressure_region`;
- otherwise emit `import_context_region`.

This keeps reports honest: small direct imports can still help reviewers orient
the owner, but the label no longer overstates them as architecture pressure.
