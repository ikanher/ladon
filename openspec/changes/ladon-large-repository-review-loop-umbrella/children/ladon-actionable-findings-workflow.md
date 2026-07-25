# `ladon-actionable-findings-workflow`

Owns stable evidence references, finalized counts, scope-aware ranking,
deterministic filtering, and public CLI lookup for existing promoted findings.

- Dependencies: explicit scope populations, calibrated ownership populations,
  and the bounded report projection contract.
- Existing owners reused: finding kinds, severities, stable IDs, refactoring
  prescriptions, authority labels, and source evidence.
- Excludes: new smell families, automatic repairs, fabricated source ranges,
  confidence/authority promotion, and unbounded default text output.
- Exit: every promoted finding resolves to raw or aggregate evidence or carries
  an explicit unavailable reason; text/JSON/phase/atlas counts agree; ID,
  severity, confidence, scope, and priority filters work from an installed CLI.
