# proofir-v3-lean-worker-framed-protocol

Replace target-initializer/source-probe/first-brace behavior with a request-bound NDJSON protocol and direct Lean MetaM elaboration.

Start after typed schema and identity hardening. r03 verified direct MetaM elaboration and request framing, but found discarded local context, non-Lean name parsing, implicit universe closure, and enabled target initializers. Exit only when those semantics plus all transport mutations, bounds, environment mismatch, and deterministic check-run tests pass.
