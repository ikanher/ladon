## Context

Generated source should remain visible, but it should not hide handwritten
architecture pressure. Duplicate imports in generated files should point toward
generator-side cleanup.

## Goals / Non-Goals

**Goals:**

- Tag generated modules generically.
- Group duplicate import rows by likely generator family.
- Keep generated and handwritten fan tables separate.

**Non-Goals:**

- No generator-specific code paths.
- No source rewrites.

## Decisions

- Infer generator family from generic generated module/path segments.
- Keep attribution heuristic and evidence-backed.

## Risks / Trade-offs

- Family inference can be wrong -> Report samples and avoid hard failure based
  solely on attribution.
