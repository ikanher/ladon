## Context

Matrix-Factorization contains command-only audit facades and hundreds of
resource directives that are invisible to declaration-only review. This child
models those constructs as bounded source facts without turning queries into
proof claims.

## Decisions

### Lexical audit extraction is always available

The comment/string-safe scanner records `#check`, `#print axioms`,
`maxHeartbeats`, and `maxRecDepth` rows with source ranges and bounded subject
text. Command-only modules remain valid roots with zero owned declarations.

### Lean enrichment is optional and separate

When the Lean backend is selected, the existing bounded helper may attach
resolved subjects or axiom-query output. Lexical intent and Lean result retain
separate authority, status, provenance, and nonclaims. No new helper or
supervisor is introduced.

### Resource settings are navigation evidence

Numeric values and lexical scope are preserved; zero heartbeat is normalized
to Lean's unlimited meaning. Presence or magnitude never establishes measured
runtime, proof failure, theorem truth, or a defect.

## Existing Owners And Exclusions

Declaration identities, source evidence, Lean runtime, scope, and population
classification remain externally owned. This child does not infer audit intent
from filenames, transitive axiom closure from text, or mathematical readiness.

## Risks

Lean command syntax is richer than the bounded scanner. Unsupported expressions
remain explicit unparsed rows; fixtures protect comments, strings, nesting, and
ordinary declaration-only modules from false promotion.
