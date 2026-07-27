## Why

Ladon already retains a rich lexical source index, but ordinary reports discard
most large-repository declaration evidence and the installed CLI cannot inspect
arbitrary modules, declarations, imports, audits, options, resources, or proof
mechanisms. Reviewers need bounded, deterministic access to canonical evidence
without requesting an unbounded report or a caller-specific interface.

## What Changes

- Add one caller-neutral installed inspection surface for modules, declarations,
  imports, audits, options, resources, and lexical proof mechanisms.
- Read canonical report/source-index evidence without implicitly rerunning
  analysis, Lake, Lean, or version-control commands.
- Provide stable filters, exact lookup, deterministic pagination, source anchors,
  authority, population, fingerprints, and visible/total/omitted coverage.
- Reject stale indexes and pagination cursors explicitly rather than returning
  misleading empty or mixed-snapshot results.
- Index comment/string-safe lexical tactic tokens, scope context, generic
  `set_option` rows, and supported normalized resource settings as navigation
  evidence.
- Register resource review input only for normalized unlimited settings or
  explicit fingerprinted policy matches; finite values have no implicit
  magnitude threshold, and final region synthesis remains report-owned.
- Keep lexical evidence separate from optional Lean resolution and the retained
  proof-xray roadmap.
- Gate the installed text/JSON operations with portable positive and negative
  fixtures; keep Matrix-Factorization as optional read-only observational evidence.

## Capabilities

### New Capabilities

- `ladon-analysis-inspection-surface`: Defines ordinary installed navigation over
  canonical modules, declarations, imports, audits, options, resources, lexical
  mechanisms, and related evidence.

### Modified Capabilities

None. This capability consumes the existing source-index, CLI, finding, audit,
atlas, report, and proof-authority contracts rather than redefining them.

## Impact

- Affected code includes source-index models and cache fingerprints, lexical
  evidence extraction, CLI dispatch and rendering, canonical-row lookup, filter
  and pagination models, and installed-distribution tests.
- The public CLI gains general-purpose inspection used identically by people,
  scripts, editors, and models. No LLM-specific command, threshold, output, or
  default is introduced.
- Text-only inspection does not establish tactic execution, theorem dependencies,
  binding resolution, instance selection, proof success, or theorem quality.
- Required tests remain target-neutral and non-executing by default.
