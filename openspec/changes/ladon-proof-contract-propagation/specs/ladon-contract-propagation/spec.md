## Purpose

Bounded route-preserving mathematical contract propagation over derivation hypergraphs. This capability supports bounded prose–formal auditing with explicit evidence and limitations.

## ADDED Requirements

### Requirement: Conjunctive application semantics
A propagated application contract SHALL include a compatible contract for every ordered premise occurrence and all rule side conditions. Alternative derivations SHALL remain separate complete routes.

#### Scenario: One conjunct is unavailable
- **WHEN** an application needs both A and B but only A has an available contract
- **THEN** the application does not yield supported output and B remains a residual

### Requirement: Correlated route frontiers
The evaluator SHALL retain incomparable complete contracts and route witnesses. It SHALL NOT create an output by taking independently preferable components from different alternatives.

#### Scenario: Fictitious optimum
- **WHEN** one route loses three derivatives and permits M dependence while another loses five without M dependence
- **THEN** the frontier retains both routes and contains no invented three-derivative M-free route

### Requirement: Evidence-backed pruning
Pruning SHALL require dominance for the same endpoint/context and admitted monotone transfer behavior. Pruned routes SHALL retain attributable dominance evidence; equivalent-route compression SHALL disclose any omitted method provenance.

#### Scenario: Heuristic ranking prefers a route
- **WHEN** a cheaper route is ranked first but neither contract dominates the other
- **THEN** ranking does not remove the other contract

### Requirement: Context-safe route composition
Route witnesses SHALL preserve branch scopes, substitutions and premise occurrences. Results from incompatible branches or local witness scopes SHALL NOT be combined or reused through a context-free cache.

#### Scenario: Facts come from different cases
- **WHEN** two premises are individually available only in mutually exclusive local contexts
- **THEN** the evaluator does not combine them into an unconditional application

### Requirement: Honest finite coverage
A result SHALL distinguish explored support from completeness over the supplied graph and admitted profile. Frontier, combination, time or graph limits SHALL retain named residuals and SHALL NOT establish absence of a mathematical proof.

#### Scenario: Combination budget exhausted
- **WHEN** the evaluator reaches its combination cap before visiting another alternative
- **THEN** it reports partial coverage and the unvisited alternative rather than no supporting route

### Requirement: Acyclic first profile
The initial propagation profile SHALL reject cyclic mathematical propagation with explicit cycle or SCC evidence and SHALL preserve existing structural-query semantics.

#### Scenario: Self-supporting route
- **WHEN** a contract depends on itself through a cycle
- **THEN** it is not accepted by fixed-point iteration or memoized as a proved contract
