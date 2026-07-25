## ADDED Requirements

### Requirement: Versioned labeled manifests
Every required benchmark case SHALL declare its fixture, ordinary CLI command,
report version, expected labels, and applicable metrics in a versioned manifest.

#### Scenario: Reviewed expectation
- **WHEN** a benchmark case is added or changed
- **THEN** its positive, intentional-negative, or boundary expectation is explicit source data rather than copied from current Ladon output

### Requirement: Signal correctness metrics
The harness SHALL report per-kind true positives, false positives, false
negatives, precision, and known-case recall where labels support them.

#### Scenario: Seeded missing imports
- **WHEN** a fixture contains labeled internal missing imports and labeled external absent imports
- **THEN** the harness reports internal recall and external false-positive counts separately

#### Scenario: Intentional negative
- **WHEN** a facade, namespace, generated, similarity, architecture, source-pattern, or claim-authority fixture is labeled intentional
- **THEN** promotion of the corresponding unwanted finding is counted as a false positive

#### Scenario: Source and claim boundary
- **WHEN** portable fixtures label both positive and negative source-pattern or claim-authority cases
- **THEN** the harness preserves their authority labels and reports misses or overflags separately

### Requirement: Extraction coverage metrics
Lean fixtures SHALL measure declaration-surface coverage and direct elaborated
dependency coverage against labeled expected rows.

#### Scenario: Known declaration inventory
- **WHEN** a fixture declares a labeled set of theorem, definition, axiom, opaque, and unsafe forms
- **THEN** the harness reports extracted versus expected declarations and required fields

#### Scenario: Known direct constants
- **WHEN** a fixture labels direct type and value dependencies
- **THEN** the harness reports coverage separately from parser-candidate matches

### Requirement: Runtime and resource metrics
The harness SHALL measure cold and warm wall time, cache outcomes, helper
process count, timeout cleanup, report size, and peak RSS where the platform
supports it.

#### Scenario: Inventory process bound
- **WHEN** a multi-module synthetic inventory is benchmarked
- **THEN** helper process count satisfies the batch bound and no descendant remains after completion

#### Scenario: Timeout cleanup
- **WHEN** a controlled helper exceeds its deadline
- **THEN** the benchmark records bounded termination and no orphaned helper process

### Requirement: Cache invalidation oracles
The harness SHALL verify hits and invalidations for source, helper, toolchain,
Lake manifest, and imported-state changes.

#### Scenario: Warm unchanged run
- **WHEN** an identical extraction repeats with a valid cache
- **THEN** it records a hit and completes within the committed synthetic warm-run budget

#### Scenario: Fingerprint input changes
- **WHEN** any labeled fingerprint input changes
- **THEN** the affected cache case records an invalidation rather than a hit

### Requirement: Report stability metrics
The harness SHALL validate schema conformance, normalized byte determinism,
text/JSON semantic parity, and size budgets.

#### Scenario: Equivalent repeated run
- **WHEN** a portable fixture is analyzed twice with equal explicit metadata
- **THEN** normalized JSON bytes match and both documents validate

### Requirement: Ordinary CLI execution
End-to-end benchmark cases MUST invoke the installed `ladon` CLI and MUST NOT
use caller-specific analysis flags or an alternate benchmark analyzer.

#### Scenario: CLI parity audit
- **WHEN** benchmark command manifests are inspected
- **THEN** every product case uses documented general-purpose CLI options available to all callers

### Requirement: Portable required gates
Required CI benchmarks SHALL use tracked portable fixtures and SHALL NOT depend
on sibling repositories or maintainer-local absolute paths.

#### Scenario: Clean exported tree
- **WHEN** required benchmark gates run from a tracked-only export
- **THEN** they complete without Quux, matrix-factorization, mathlib, or another sibling checkout

#### Scenario: Missing explicit candidate
- **WHEN** the required benchmark command is invoked without a treeish, materialized directory, or explicit tracked-worktree candidate
- **THEN** it fails before measurement rather than benchmarking an implicit live checkout

### Requirement: Optional live drift evidence
Optional live smokes SHALL remain observational: Quux, matrix-factorization,
and mathlib results may be recorded, but their moving cardinalities MUST NOT
define portable pass/fail correctness.

#### Scenario: Live topology changes
- **WHEN** an optional live repository's module count or top fan-in node changes
- **THEN** the harness records drift without failing an otherwise green portable gate

### Requirement: No composite quality score
The harness MUST preserve metric families separately and MUST NOT publish a
single proof-quality, repository-quality, or model-quality score.

#### Scenario: Summary rendering
- **WHEN** benchmark results are summarized
- **THEN** correctness, coverage, runtime, memory, cache, and stability are reported as separate measures

### Requirement: Evidence before promotion
A changed default finding or declaration surface SHALL NOT be marked benchmark
ready until its required positive, negative, and boundary cases pass.

#### Scenario: Missing negative fixture
- **WHEN** a promoted behavior has positive evidence but no applicable intentional-negative boundary
- **THEN** the promotion gate remains incomplete
