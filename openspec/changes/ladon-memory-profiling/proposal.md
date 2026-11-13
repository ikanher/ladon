## Why

Internal users need to distinguish Python allocation growth from Lean/Lake subprocess
memory. Existing watchdog receipts provide sampled RSS limits and bounded summaries.
Before adding product machinery, establish what the installed external profilers provide.

## What Changes

Qualify Memray and psutil against a representative read-only Ladon query and document
repeatable profiling recipes. No new Ladon command, Python module, or runtime dependency.
An initial CLI proposal was superseded after the owner questioned its necessity.

## Capabilities

### New Capabilities
- `memory-profiling`: documented external profiling workflow and measured limitations.

### Modified Capabilities
None.

## Impact

Documentation and local measurement evidence only. Core packaging, CLI, Lean helpers,
watchdog policy and result schemas remain unchanged.
