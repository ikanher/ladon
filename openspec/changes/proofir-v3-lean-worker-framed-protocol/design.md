## Context

Transport integrity is prerequisite to trustworthy checker observations. It is distinct from theorem truth and from the supervisor's construction of a check-run artifact.

## Goals / Non-Goals

**Goals:** unambiguous request/response framing, direct Lean parsing/elaboration, bounded output, exact environment echo, and fail-closed handling of target-controlled process behavior.

**Non-Goals:** having Lean mint the supervisor's check-run ID, accepting arbitrary target stdout, or treating a valid frame as proof acceptance.

## Decisions

1. Python sends a JSON request containing protocol version, unpredictable request ID/nonce, exact environment reference, operation, goal syntax, candidate reference, and bounds.
2. Lean emits one NDJSON frame per sequence number plus exactly one terminal frame; every frame repeats the request ID and protocol version.
3. The supervisor reads complete bounded lines, rejects any nonframe output on the protocol stream and any data after the terminal frame, then constructs the check run from process-level observations.
4. Lean parses names and terms with Lean's parser and elaborates the goal in MetaM; no generated declaration or `sorry` is used.
5. Target-repository initializers are disabled for this helper boundary.

## Risks / Trade-offs

- [Some repositories require initializers] → report an explicit unsupported worker environment rather than execute target-controlled initialization.
- [NDJSON diagnostics need human logs] → keep protocol stdout strict and capture ordinary diagnostics on bounded stderr with digests.

## Migration Plan

Land adversarial protocol tests, introduce a versioned request/frame model, update the Lean helper, switch the supervisor atomically, and delete first-brace/source-probe code.

## Open Questions

- None.
