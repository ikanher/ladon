## Context

An expert could inspect the architecture but could not reproduce the cited packet-local tests because essential files were omitted. The packet also cited a 1,352-test checkout observation without content-addressing the exact checkout, command, or logs.

## Goals / Non-Goals

**Goals:** packet-local review reproducibility, exact content inventory, explicit source/toolchain state, machine-validated evidence, honest limitations, and a deterministic Rust gate.

**Non-Goals:** a signed supply-chain release, Lean theorem replay when no theorem is claimed, or bundling unrelated repository content.

## Decisions

1. `proof-state.md` is mandatory and records current completed/open tasks, commands, blockers, limitations, and next gate.
2. Every packet file has a relative path, role, byte size, SHA-256, and source classification.
3. Source provenance records commit, dirty-tree status/diff digest, relevant lock/toolchain hashes, packet builder version, and build time.
4. Every claimed command has argv, working directory, bounded environment description, start/end time, exit code, stdout/stderr log paths, sizes, and hashes.
5. JSON Schema evidence is validated with a schema validator, not merely parsed.
6. The packet includes all fixtures, support modules, CLI sources, child OpenSpec artifacts, and schemas needed by its advertised packet-local commands.
7. Rust remains held until the reviewer marks each original blocker closed or explicitly nonblocking with evidence.

## Risks / Trade-offs

- [Complete packet becomes broad] → include the transitive source/test closure for advertised commands, not the whole repository.
- [Dirty-tree identity is awkward] → record both HEAD and a canonical diff/untracked-file manifest digest.

## Migration Plan

Create the proof state and packet manifest schema, make packet-local commands fail on omissions, build after all hardening children pass, independently replay it, then request expert review.

## Open Questions

- None.
