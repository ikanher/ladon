## ADDED Requirements

### Requirement: Separate root and population selection
Ladon SHALL represent requested analysis roots separately from the module
population selected for analysis. Every report and preview MUST record the
requested roots, resolved roots, requested scope, effective scope, primary
population, contextual population, and inventory discovery boundary.

#### Scenario: Owner inside a broad library
- **WHEN** a caller selects one owner module in a library containing many unrelated modules
- **THEN** the owner remains the primary root and the report does not silently redefine the whole top-level namespace as the primary analysis population

#### Scenario: Scope metadata
- **WHEN** any supported scope completes or becomes partial
- **THEN** its root-resolution and population metadata remain available through the existing typed report envelope

### Requirement: Owner scope
Owner scope SHALL analyze the explicitly resolved owner modules as the primary
population. Imports selected by a documented owner-context rule SHALL be
retained only as authority-labeled context and MUST NOT promote unrelated
inventory-wide findings as owner findings.

#### Scenario: Single owner review
- **WHEN** a caller requests owner scope for one source file or module
- **THEN** owner declarations, direct imports, source evidence, and owner-local findings are primary while unrelated modules are absent or explicitly contextual

#### Scenario: Owner has no declarations
- **WHEN** an owner resolves to a command-only or facade module with no declarations
- **THEN** Ladon records that empty owner surface explicitly and does not replace it with an inferred mathematically meaningful root

### Requirement: Import-closure scope
Import-closure scope SHALL select the deterministic transitive local import
closure of every requested root, including the roots themselves, and SHALL
record direct-root attribution for each selected module.

#### Scenario: One closure
- **WHEN** a root imports local modules through multiple paths
- **THEN** the effective population contains each reachable local module once and retains a deterministic witness path or root attribution

#### Scenario: External import boundary
- **WHEN** the closure reaches an external library module outside the target's declared source roots
- **THEN** Ladon records the external boundary as context without adding that external library's full inventory to the primary population

### Requirement: Namespace scope
Namespace scope SHALL select modules owned by one or more explicitly requested
module namespace prefixes within declared source roots. Prefix matching MUST
respect module-segment boundaries rather than raw string prefixes.

#### Scenario: Namespace prefix
- **WHEN** namespace scope is requested for `Pkg.Surface`
- **THEN** `Pkg.Surface` and `Pkg.Surface.*` modules are selected while `Pkg.SurfaceExtra` is not

#### Scenario: Namespace directory
- **WHEN** a caller supplies a directory that maps unambiguously through the declared Lake layout
- **THEN** preview and analysis resolve it to the same namespace population and record the path-to-module mapping authority

### Requirement: Named multi-root scope
Named multi-root scope SHALL accept two or more explicit roots, deduplicate
their effective populations, and retain per-root attribution and overlap
counts. Root order MUST NOT change normalized analysis results.

#### Scenario: Overlapping roots
- **WHEN** two named roots share local dependencies
- **THEN** shared modules occur once in the effective population and are attributed to both roots

#### Scenario: Reordered roots
- **WHEN** equivalent multi-root requests differ only in argument order
- **THEN** their resolved root set, effective population, and normalized report bytes are identical

### Requirement: Changed-set scope
Changed-set scope SHALL derive primary modules only from an explicit changed
file list or versioned changed-file manifest supplied by the caller. Ladon MUST
record the change-source authority and caller-supplied identities when present,
unmapped paths, and the deterministic expansion rule used around changed
modules. This capability MUST NOT invoke version-control commands or mutate a
checkout.

#### Scenario: Explicit changed-file manifest
- **WHEN** a caller requests changed-set scope with a versioned manifest containing repository-relative changed Lean paths and optional before/after identities
- **THEN** Ladon maps those paths to modules, records the supplied identities as caller-provided context, and does not inspect or include unrelated working-tree files

#### Scenario: Version-control reference without a manifest
- **WHEN** a caller supplies only a version-control reference where an explicit changed-file list or manifest is required
- **THEN** Ladon returns an actionable invocation diagnostic and executes no version-control command

#### Scenario: Unmapped changed Lean file
- **WHEN** a changed Lean path is outside every declared source root or has ambiguous module ownership
- **THEN** preview reports the path as unresolved and analysis does not guess a module name

### Requirement: Full-inventory scope
Full-inventory scope SHALL select every unambiguous module under the target's
declared source roots and SHALL identify it explicitly as the broadest and
potentially most expensive scope.

#### Scenario: Inventory request
- **WHEN** a caller explicitly selects inventory scope
- **THEN** preview reports the full module and source-line estimates before analysis and the resulting report labels inventory-wide findings as such

#### Scenario: Ambiguous module ownership
- **WHEN** two declared roots map different files to the same module name
- **THEN** the ambiguity is a structured scope diagnostic and the conflicting files are not silently merged

### Requirement: Side-effect-free analysis preview
The ordinary installed CLI SHALL provide text and machine-readable preview for
every supported scope. Preview MUST resolve layouts, roots, policies,
populations, cache expectations, and estimated Lean helper batches without
running Lake builds, Lean helpers, target initializers, or analysis passes.

#### Scenario: Lean-backed preview
- **WHEN** a caller previews a Lean-backed inventory request
- **THEN** preview reports the selected module count, batch-size estimate, execution warning, compiled-state expectation, and cache directory without starting Lean

#### Scenario: JSON preview channel
- **WHEN** machine-readable preview is selected
- **THEN** stdout contains one schema-versioned preview document and diagnostics or progress remain confined to stderr

#### Scenario: Missing root
- **WHEN** preview cannot resolve a requested root through the existing target-input contract
- **THEN** it returns the established input-error class with candidate source roots and no target-controlled process is started

### Requirement: Deterministic scope fingerprints
Every effective scope SHALL have a stable fingerprint over root identities,
scope kind, population, layout identity, changed-set authority when present,
and scope-affecting options. Scope fingerprints SHALL participate in cache
validity and report provenance.

#### Scenario: Equal scope
- **WHEN** equivalent root and scope requests resolve against unchanged source and layout state
- **THEN** they produce the same scope fingerprint

#### Scenario: Scope expansion
- **WHEN** a namespace gains a new owned module or a closure gains a new local import
- **THEN** the scope fingerprint changes and a cache entry for the earlier population is not reported as a complete hit

### Requirement: Explicit root nonclaims
Ladon MUST NOT claim that a selected, previewed, inferred facade, changed set,
or high-pressure module is the mathematically correct proof root. Any suggested
root SHALL carry heuristic authority and the evidence used to suggest it.

#### Scenario: Suggested follow-up root
- **WHEN** analysis suggests another owner or facade for follow-up
- **THEN** the suggestion is labeled review routing and remains separate from the caller's requested and resolved roots
