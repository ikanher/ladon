## Why

The alpha worker enables target initializers, interpolates a goal into a generated theorem containing `sorry`, and parses stdout from the first brace. Target-controlled output can corrupt or impersonate this boundary.

## What Changes

- Define a nonce/request-bound NDJSON protocol with sequence numbers and a terminal summary.
- Parse and elaborate the requested goal directly in Lean MetaM.
- Disable target initializers and reject noise, duplicate, missing, reordered, mismatched, or trailing frames.

## Capabilities

### New Capabilities
- `proofir-v3-lean-worker-framed-protocol`

### Modified Capabilities

## Impact

Changes the Python supervisor, Lean helper, process invocation, protocol fixtures, security tests, environment observations, and worker documentation.
