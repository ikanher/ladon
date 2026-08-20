# Design

## Profiles

- `generic`: all current checks required.
- `review_packet`: metadata, tests, and owner references required.
- `witness_bundle`: metadata, witness JSON, checker script, tests, verification
  commands, and owner references required.
- `release_bundle`: metadata, verification commands, and owner references
  required.

The report keeps `status`, `score`, and `max_score` for the generic score, and
adds:

```json
{
  "profile": "review_packet",
  "profile_status": "complete",
  "required_checks": ["metadata", "tests", "owner_references"],
  "missing_required_checks": []
}
```
