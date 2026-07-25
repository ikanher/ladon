## ADDED Requirements

### Requirement: Batched inventory extraction
Lean inventory extraction SHALL amortize environment startup through a
versioned batch protocol, SHALL require a configured inventory batch size of at
least two, and for multi-module inventory MUST NOT use a one-process-per-source
strategy. A single uncached module may require one helper invocation.

#### Scenario: Multi-module inventory
- **WHEN** inventory scope contains `n` uncached modules and configured batch size `b`
- **THEN** Ladon uses at most `ceil(n / b)` ordered helper invocations, with `b >= 2`

#### Scenario: Invalid batch size
- **WHEN** configuration requests inventory batch size below two
- **THEN** Ladon rejects the configuration instead of reverting to one helper per module

#### Scenario: Per-module records
- **WHEN** a batch completes
- **THEN** the helper emits one framed result or diagnostic per requested module plus a terminal summary

### Requirement: Bounded helper lifetime
Every Lean helper invocation MUST have a configured deadline and cancellable
process-group lifecycle.

#### Scenario: Extraction timeout
- **WHEN** a helper exceeds its deadline
- **THEN** Ladon terminates the helper process group, records timeout diagnostics, and leaves no running descendant from that batch

#### Scenario: Caller interruption
- **WHEN** analysis is cancelled while a helper is active
- **THEN** Ladon cleans up the helper group and preserves already validated records

### Requirement: Deterministic partial results
A module-level failure SHALL NOT erase successful records from the same
inventory, and partial rows MUST be deterministic.

#### Scenario: One malformed module
- **WHEN** one module fails or emits malformed payload data while other modules succeed
- **THEN** successful module rows remain in stable order and the failed module has a structured diagnostic

### Requirement: Versioned cache validity
A Lean extraction cache key SHALL include protocol/helper identity, extraction
options, Lean/toolchain identity, Lake configuration, target source, transitive
local import state, and identifiable compiled or external environment state.

#### Scenario: Toolchain change
- **WHEN** `lean-toolchain` or the resolved Lean version changes
- **THEN** an earlier cache entry is not reported as a valid hit

#### Scenario: Imported source change
- **WHEN** a source in the target's resolved local import closure changes
- **THEN** dependent extraction entries are invalidated

#### Scenario: Unfingerprintable environment
- **WHEN** relevant imported environment state cannot be fingerprinted
- **THEN** Ladon bypasses the cache or marks its weaker status explicitly rather than claiming a sound hit

### Requirement: Lake-aware source discovery
Lean discovery SHALL prefer declared Lake library roots and support multiple
libraries, `srcDir`, and declared generated source roots.

#### Scenario: Library with srcDir
- **WHEN** Lake declares module `Pkg.Core` under a non-root `srcDir`
- **THEN** Ladon maps it to `Pkg.Core` rather than inventing a module name from the repository-relative path

#### Scenario: Conventional fallback
- **WHEN** a simple repository has no usable declared library layout
- **THEN** Ladon uses the documented conventional scan and records fallback discovery status

### Requirement: Extraction provenance
Every Lean extraction phase SHALL report helper/protocol version, Lean version,
cache outcome, elapsed time, requested/completed/failed counts, and timeout or
cancellation state.

#### Scenario: Warm cache
- **WHEN** a valid cached result is used
- **THEN** the phase reports a cache hit and the fingerprint version that justified it

### Requirement: Target-code execution warning
Lean-backed extraction MUST document and report that loading target modules may
execute imported initializers and is not safe analysis of an untrusted
repository.

#### Scenario: Lean backend selected
- **WHEN** a caller selects the Lean backend
- **THEN** CLI help and phase provenance expose the target-code execution boundary

### Requirement: No implicit build
Extraction SHALL consume existing build state and MUST NOT invoke `lake build`
unless the shared CLI build phase was explicitly requested.

#### Scenario: Missing build state
- **WHEN** required compiled state is absent and no build was requested
- **THEN** extraction records an actionable failure without starting a build

### Requirement: Non-skippable real-Lean acceptance
The runtime child MUST provide a required real-Lean gate whose missing
toolchain status is a failure rather than a test skip.

#### Scenario: Runtime child closeout
- **WHEN** runtime completion is evaluated
- **THEN** the required gate provisions the fixture's pinned reference toolchain, runs root and multi-module batch extraction on the tracked Lake fixture, and fails if Lean is unavailable
