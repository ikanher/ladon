# Proposal

## Why

Typed lowering prevents several encoding mistakes, but a correctly typed total operation can still fail the property presumed by the exposition. Existing missing-existence examples are known audit evidence rather than reusable operation obligations.

## What Changes

- Observe exact instantiated operation, type, instance and coercion identities, using existing typed interpretation machinery.
- Introduce a small versioned adapter registry for domain-sensitive subtraction and a total-selector/default family, beginning with natural-set infimum.
- Connect source-attributed expectations to explicit operation-preservation or existence/membership obligations; do not invent prerequisites from an operation name alone.
- Distinguish checked failure, checked property, and unresolved source expectations, with valid total-operation controls.

Detailed acceptance is in [the capability specification](specs/ladon-operation-definedness/spec.md). Success is evidence for the declared bounded behavior, with limitations visible to the caller.

## Capabilities

### New Capabilities

- `ladon-operation-definedness`: Typed operation observations and checked source-attributed existence/property obligations.

### Modified Capabilities

None. Existing probe, identity, authority and coverage requirements remain in force; these additions do not reinterpret historical results.

## Impact

Typed lowering and observation consumers, bounded adapter planning, existing Lean completion/replay, and investigation reports. Requires acceptance of the eight existence/defaults and operation-semantics baseline cases under the [staged baseline policy](../ladon-pitfall-baselines/specs/ladon-pitfall-regression-evaluation/spec.md) before semantic runtime implementation. No universal definition analysis, automatic source repair, or mathematical-library semantics implemented in Python.

