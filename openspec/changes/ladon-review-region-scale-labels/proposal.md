# Proposal

The root-matrix evidence pass showed that review regions were more aggressive
than findings: any direct import closure created an `import_pressure_region`,
even when the closure was tiny and no pressure finding was emitted.

Add scale-aware labels so small root-local import neighborhoods remain visible
as context, while broad closures and correlated findings remain pressure.

# Scope

- Classify import review regions as either `import_context_region` or
  `import_pressure_region`.
- Preserve the existing signal list.
- Render the region kind/title in text as before.

# Non-Goals

- No change to module DAG extraction.
- No suppression of raw root-direct-import closures.
- No change to root-import-closure finding thresholds.
