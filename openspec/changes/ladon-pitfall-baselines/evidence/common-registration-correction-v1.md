# Common registration v1 correction record

**Date:** 2026-11-12  
**Disposition:** v1 review invalidated for future use; the original registration and review remain unchanged as historical evidence.

The prior independent review in `common-registration-review-v1.md` accepted
claims that do not match the current source or implementation:

1. **Wrapped command argv is malformed.** `runtime_custody.py run --profile
   python --` already dispatches the preserved interpreter through
   `runpy.run_module("ladon.entrypoint", ...)` and forwards the remaining
   argv. The registered `-m ladon.entrypoint` therefore became extra arguments
   to Ladon's CLI. This affects the wrapped profiles that used that prefix.
2. **Proof-slice selectors were source expressions, not selector names.** The
   command accepts `--application` as an ordinary Lean constant name. Its
   helper resolves that name in the environment and searches for an application
   whose head is exactly that constant. The registered values `h.proof`, `h`,
   and `provider.proof` are not valid selector contracts. The projection
   constant `PitfallCorpus.HasConclusion.proof` is the likely selector for
   cases 01, 02 and 04 and still requires qualification under the preserved
   runtime.
3. **The case 03 prose rubric contradicts the accepted corpus role.** Case 03
   is a fault: the source says “P follows without an additional assumption,”
   while the formal theorem has an explicit `h : P` binder. Calling it a
   control would reverse its judgment. The proof body is the local variable
   `h`, so the current constant-headed proof-slice extractor has no supported
   selector for this subject. A valid negative capability probe may establish
   that limitation, but it cannot be scored as route-absent.

The parser and helper contracts were checked directly in
`src/ladon/correspondence_cli.py`, `src/ladon/proof_slice.py`,
`src/ladon/lean/ladon_proof_slice_helper.lean`, and the frozen launcher
`scripts/runtime_custody.py`. Independent read-only audits confirmed the case
03 role/rubric mismatch and the command/selector mismatch.

`common-registration-v1.json` remains byte-preserved (SHA-256
`17ef0d68644cdb4c253c938641501b7d7d9a583ffaaa6218607c341e08bb4fe4`). Its
acceptance claim must not be used to authorize a baseline run. The proposed
successor `common-registration-v2.json` corrects the duplicate launcher args,
the available projection selector, and the case 03 rubric, while registering
a negative case 03 capability probe. It is a draft, not an accepted freeze;
the exact diagnostic still needs execution qualification in the preserved
runtime before it can support an unsupported classification.

The v2 review also found and corrected four execution-contract details before
acceptance: proof-slice needs the preserved Lean toolchain exposed through its
`Path.home()` resolver, the unqualified case 03 selector is namespace-prefixed
before Lean reports it, source-goal captures must be written to the file later
consumed by completion, and the digest argument must use the parser's
`sha256:<64-lowercase-hex>` syntax. The exact failed-helper receipt is recorded
in the case 03 probe contract. These corrections are in the current v2 draft;
they do not qualify the commands or replace per-batch execution evidence.

A subsequent review also required the claim-trust axiom probe to derive
`LEAN_PATH` from the exact isolated case repository, run under the preserved
process-tree supervisor, and retain a raw resource receipt. The draft now uses
a hash-bound bootstrap for that purpose. All registered outputs are required
to live under a new external run directory outside both the case repository
and reconstructed runtime root. These command adaptations remain pending
independent review and per-batch qualification.

The same review found that the source-interpreter command needs a closed,
reproducible input record. The v2 draft now registers its exact schema,
source-span/full-file-hash mapping, typed formula records for cases 01, 03 and
04, and an opaque source record for the non-propositional trust sentence in
case 02. It binds canonical record digests and keeps case-slot mappings on the
host side. The review boundary now accepts either a positively qualified case
03 route or an independently accepted unsupported capability result; the
unsupported result remains in the denominator without detection/control credit.

The domain/quantifier command initially accepted an unspecified staged audit
plan, which left its executed operations open to later variation. The v2 draft
replaces that plan with two fixed source/formal snapshot commands and four
closed source-interpretation records. Their formula trees, source spans, file
hashes, module derivation and canonical record digests are registered. The
formal snapshot uses the preserved runtime bootstrap to expose the pinned
Lean toolchain through its temporary home. These inputs remain unqualified
until per-batch execution and independent review.

**Task state:** Task 1.3d is reopened. Before it can close, the successor must
receive independent review and every profile it authorizes must have a
qualified command/input contract. The registered negative probe for case 03
must not be interpreted until its expected selector-name diagnostic is
confirmed under the preserved runtime. No premise-provenance baseline run is
authorized by this correction record.
