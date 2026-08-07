## 1. Goal And Context Capture

- [ ] 1.1 Add supervised Lean source-position capture for the current goal, local declarations, imports, namespace, options, and source fingerprint.
- [ ] 1.2 Normalize local binder identity and map captured locals back to source spans without treating pretty-printed names as stable identity.
- [ ] 1.3 Reject stale or ambiguous locations with explicit diagnostics and no silent fallback to a different goal.

## 2. Scratch Application Probes

- [ ] 2.1 Normalize relevant Lean compiler diagnostics into structured unsolved-goal, type-mismatch, unknown-name, timeout, and infrastructure classes.
- [ ] 2.2 Generate isolated temporary examples from captured context and a candidate route without modifying the target repository.
- [ ] 2.3 Compile probes through the existing process supervisor and return reproducible inputs, bounded output, and cleanup status.

## 3. Verification

- [ ] 3.1 Expose goal capture and probe execution through the shared CLI contract.
- [ ] 3.2 Add fixtures for nested namespaces, local notation, sections, stale locations, multiple goals, successful probes, rejected probes, and timeouts.
- [ ] 3.3 Strictly validate this change and run focused context-fidelity, isolation, and process-tree gates.
