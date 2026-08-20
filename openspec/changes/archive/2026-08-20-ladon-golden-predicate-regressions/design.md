# Design

## Predicate Types

The first slice supports:

- `module_count_between`
- `acyclic`
- `top_module_fan_in`
- `top_module_fan_out`
- `finding_kind_present`
- `declaration_count_between`
- `declaration_fan_in`
- `declaration_family_present`
- `proof_similarity_suffix_present`
- `proof_similarity_absent`
- `packet_status`

Predicates return structured pass/fail rows. They do not raise on normal
predicate failure.

## Built-In Layout

The built-in suite targets reports generated under:

```text
temp/ladon-live-runs/
  quux/project-quux.json
  quux/owner-propagation-lean.json
  matrix-factorization/project-mf.json
  matrix-factorization/owner-bifr-packed-profile-lean.json
  matrix-factorization/owner-bifr-r37-packet.json
```

Missing files are reported as failed suite entries.
