## Context

Type fingerprints are excellent search keys but do not identify declarations. A successful elaboration of `candidate ?premise` is evidence about that application shape, not acceptance of the residual goal.

## Goals / Non-Goals

**Goals:** nonconflated typed identities, sound strongest-tier attachment, and check results whose subject communicates their exact guarantee without prose interpretation.

**Non-Goals:** proof-term equivalence, global identities outside an environment, or promoting a closed elaboration to more than the named checker observation.

## Decisions

1. Declaration identity binds environment, fully qualified name, identity scheme, and digest.
2. Statement/type identity binds environment, expression-fingerprint scheme, and digest; it remains a search and semantic-comparison key.
3. Value/proof identity is optional and binds the declaration name as well as its value fingerprint.
4. Residual checks target a `candidate-application` or derivation-step subject; the requested goal has result `unchecked` unless a closed derivation establishes it.
5. Exact attachment requires an emitted declaration reference or environment plus exact qualified name plus declaration identity.

## Risks / Trade-offs

- [More subject types complicate queries] → provide explicit relations rather than implicit string equality.
- [Existing fingerprints change] → regenerate alpha artifacts and rebuild disposable SQLite databases.

## Migration Plan

Add collision and residual red tests, introduce new typed subjects, update the worker and resolver, regenerate fixtures, and remove the conflated identifier route.

## Open Questions

- None.
