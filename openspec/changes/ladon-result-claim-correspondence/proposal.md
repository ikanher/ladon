## Why

The result-understanding umbrella needs an exact, bounded claim manifest before it can join theorem evidence. Implement the independent artifact-only layer now so an LLM can exercise real inputs without waiting for or claiming authority-safe Lean integration.

## What Changes

- Add a packaged v1 JSON schema and bounded strict JSON reader with semantic identity/reference validation.
- Preserve revision-bound correspondence reviews and their historical applicability, independently of unresolved canonical targets.
- Expose experimental `ladon result validate MANIFEST --format json|text` and a portable example.
- Add explicit local canonical target resolution after the compatible integration/discovery prerequisite check, keeping the offline validator unchanged.
- Keep the full child exit gated by fresh compatible-candidate qualification; upstream umbrella acceptance remains separate.

## Capabilities

### New Capabilities

- `ladon-result-claim-correspondence`: Implements the umbrella-owned claim manifest contract, starting with artifact-only validation.

### Modified Capabilities

None.

## Impact

Additive CLI dispatch, packaged schema, small manifest validation modules, portable fixtures, and focused installed tests. No runtime dependency, Lean invocation, network operation, index mutation, or external-benefit promotion.
