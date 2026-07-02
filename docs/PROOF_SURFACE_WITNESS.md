# Ladon Proof-Surface Witness

Proof-surface witness input is an optional bridge evidence layer. It lets a
project quote verifier-owned metadata about frozen spec stubs, proof endpoints,
no-drift gates, source pins, axiom audits, and proof-hole quarantine.

Ladon consumes that metadata to route review. Ladon does not run Lean, replay
proofs, validate theorem truth, certify witness adequacy, or decide
mathematical scope from this artifact.

## CLI Use

```bash
ladon-proofir-bridge \
  --ladon-report ladon-report.json \
  --proofir-index proofir-bridge-index.json \
  --proof-surface-witness proof-surface-witness.json \
  --out bridge-report.json
```

The witness can also be embedded in a compact `proofir_bridge_index` under
`proofSurfaceWitness`. Existing bridge reports are unchanged when no witness is
supplied.

## Contract

The compact artifact kind is `proof_surface_witness` with `schemaVersion: 1`.
The supported top-level fields are:

- `producer`: quoted producer/tool metadata.
- `specSurfaces`: frozen spec declaration rows.
- `proofEndpoints`: proof-backed endpoint declaration rows.
- `noDriftGates`: rows connecting a spec surface to an endpoint, such as an
  identity gate accepted by a project verifier.
- `axiomAudits`: quoted axiom footprints for endpoints or gates.
- `sourcePins`: source path, range, and content-hash pins.
- `proofHolePolicy`: quarantined proof-hole scopes and violations.
- `nonclaims`: statements about what this witness does not prove.

Example:

```json
{
  "artifactKind": "proof_surface_witness",
  "schemaVersion": 1,
  "producer": {"tool": "project-verifier", "version": "1.0"},
  "specSurfaces": [
    {
      "surfaceId": "spec.main",
      "declarationName": "Pkg.Spec.frozen_statement",
      "role": "lean_spec_stub",
      "sourcePath": "Pkg/Spec.lean",
      "contentHash": "sha256:spec"
    }
  ],
  "proofEndpoints": [
    {
      "surfaceId": "endpoint.main",
      "declarationName": "Pkg.Proof.proved_statement",
      "role": "lean_proof_endpoint",
      "requiresNoDriftGate": true,
      "requiresAxiomAudit": true,
      "sourcePath": "Pkg/Proof.lean",
      "contentHash": "sha256:endpoint"
    }
  ],
  "noDriftGates": [
    {
      "gateId": "gate.main",
      "surfaceId": "gate.main",
      "declarationName": "Pkg.Discharge.no_drift_main",
      "specSurfaceId": "spec.main",
      "proofEndpointSurfaceId": "endpoint.main",
      "status": "clean",
      "contentHash": "sha256:gate"
    }
  ],
  "axiomAudits": [
    {
      "auditId": "axiom.main",
      "proofEndpointSurfaceId": "endpoint.main",
      "status": "clean",
      "allowedAxioms": ["Classical.choice"],
      "command": "#print axioms Pkg.Proof.proved_statement"
    }
  ],
  "nonclaims": [
    "source pins establish attachment confidence only",
    "Ladon does not validate theorem truth"
  ]
}
```

Unknown fields are preserved under quoted metadata so producer drift remains
inspectable. Unsupported artifact kinds, unsupported schema versions, and
non-object JSON inputs produce `ladon.proof_surface.malformed_witness` and do
not fabricate proof authority.

## Route Audit

Claim rows can cite proof-surface evidence with a `proofSurface` object:

```json
{
  "claimId": "claim.main",
  "claimedStatus": "lean_closed",
  "claimedAuthority": "lean_proved",
  "primaryTheoremSurfaces": ["endpoint.main"],
  "proofSurface": {
    "specSurfaceId": "spec.main",
    "proofEndpointSurfaceId": "endpoint.main",
    "requiresNoDriftGate": true,
    "requiresAxiomAudit": true
  }
}
```

The audit can emit:

- `ladon.proof_surface.spec_stub_used_as_authority`
- `ladon.proof_surface.missing_no_drift_gate`
- `ladon.proof_surface.missing_axiom_audit`
- `ladon.proof_surface.suspicious_axiom`
- `ladon.proof_surface.clean_endpoint`
- `ladon.proof_surface.frozen_spec_hub`
- `ladon.proof_surface.proof_hole_outside_quarantine`

`clean_endpoint` means the evidence route has acceptable source attachment and
the required quoted gate and axiom-audit rows are present and clean. It is not a
theorem-truth verdict.

## Witness Generation

Project-local verifier scripts can generate witness rows from checks such as:

- `lake build` or target-specific Lean build commands.
- source path, source range, and content hash collection.
- no-drift identity gates accepted by Lean.
- `#print axioms` or equivalent axiom-footprint commands.
- banned proof-hole scans with explicit quarantine rules.

Those scripts own the verifier authority. Ladon consumes their compact witness
output and checks whether public claims cite proof endpoints rather than frozen
spec stubs, whether advertised no-drift and axiom evidence is present, and
whether suspicious quoted metadata needs review.

## Composition With ProofIR

ProofIR route authority answers whether a public claim's status and required
evidence authorities align, for example whether a Lean-closed claim still
depends on imported interval evidence.

Proof-surface witness audit answers whether a public claim cites an appropriate
proof endpoint route, with quoted source pins, no-drift gates, axiom audits, and
proof-hole quarantine metadata.

The two layers compose in the bridge report. Both remain route-governance
evidence. Neither layer makes Ladon the authority for theorem truth, proof
correctness, witness adequacy, or mathematical scope.
