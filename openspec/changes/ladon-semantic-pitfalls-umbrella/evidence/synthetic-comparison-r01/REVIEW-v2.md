# Registration review v2 — synthetic comparison r01

**Scope:** Re-reviewed the updated `REGISTRATION.md` and `ARM-PROMPT.md`, with `HANDOFF.md` and umbrella task N.2c as context. No case prose, answers, or custody material was read. The initial review is preserved in `REVIEW.md`.

**Disposition: registration design accepted; execution remains gated on prelaunch artifacts.** The added operational definitions resolve the prior findings:

- The registration now names the packet checksum and input identity artifacts, the per-unit allowlist source, and the exact tool/runtime read boundary; the prompt restricts access to the delivered workspace and resolved roots in its launch manifest.
- A useful finding and the claim-level score categories are operationalized. Independent ratings are preserved, a third fresh reviewer resolves remaining disagreements, and unresolved adjudication cannot support the gate.
- Invocation accounting is defined per started Lean executable process, including spawned processes and failed starts; it requires launch-side instrumentation and prevents a twenty-first process. A launcher unable to enforce/account for the boundary must fail readiness before launch.

The paired inputs, shared complete recipe and preparation, treatment distinction, comparable model and resource budgets, runtime and no-live-sibling controls, exposure policy, first-report preservation, and descriptive endpoint/cost reporting remain coherent with N.2c.

**Prelaunch artifact outstanding:** The target directory currently has no `SHA256SUMS`, although the handoff requires verifying it and the registration defines its coverage. Create and verify it after the registration/prompt are frozen, bind it with the input identities and resolved delivered-file lists in the run manifest, and only then apply the stated launch gate. This is a missing readiness artifact, not a remaining design defect. No execution is authorized by this review.
