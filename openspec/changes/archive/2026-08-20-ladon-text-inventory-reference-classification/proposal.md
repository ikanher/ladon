# Proposal

After unresolved-reference classification, the remaining actionable row on the
BIFR packed-profile owner is `BIFRGammaMultiParticipationConfig`. That name is
not missing: text discovery sees it in another module.

Use text-discovered declaration names as a broad inventory index for unresolved
candidate classification. This should not create declaration graph edges, because
text discovery does not know exact Lean namespace elaboration. It should only
classify candidates as `known_inventory_candidate` and keep them out of
actionable unresolved findings.

# Scope

- Add optional known-reference inventory names to declaration graph analysis.
- Build the inventory from text-discovered module declaration names.
- Classify matching unresolved candidates as `known_inventory_candidate`.
- Keep root helper declaration graph nodes root-scoped.

# Non-Goals

- No edge creation to text-only declaration rows.
- No namespace reconstruction from text parsing.
- No claim that the candidate is imported into the root file.
