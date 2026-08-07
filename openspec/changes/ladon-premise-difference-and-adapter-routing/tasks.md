## 1. Lean-Backed Premise Differences

- [ ] 1.1 Add a supervised Lean-helper protocol that attempts candidate application and returns substitutions, remaining premises, residual target differences, and structured failures.
- [ ] 1.2 Classify differences conservatively as missing premises, stronger or weaker conclusions, representation mismatches, parameter mismatches, or unknown.
- [ ] 1.3 Preserve local context and source evidence while keeping bounded report presentation separate from complete helper evidence.

## 2. Dischargers And Adapters

- [ ] 2.1 Search for candidate dischargers for each missing premise using type-directed search and normalized scope controls.
- [ ] 2.2 Implement a checked adapter registry for common symmetry, equality transport, coercion, subtype, order, and representation routes.
- [ ] 2.3 Emit stable route cards containing the candidate, substitutions, obligations, suggested adapters, rejected routes, and evidence identity.

## 3. Verification

- [ ] 3.1 Expose difference analysis and route cards through the shared CLI contract with deterministic text/JSON output.
- [ ] 3.2 Add portable positive and negative fixtures for direct application, one missing premise, incompatible conclusions, transports, ambiguity, and helper limits.
- [ ] 3.3 Strictly validate this change and run focused Lean-helper supervision and routing gates.
