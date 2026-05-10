# Design

The declaration graph analyzer already computes classified unresolved rows. It
will additionally emit:

```json
"unresolved_reference_classes": [
  {"classification": "local_or_field_candidate", "count": 123},
  ...
]
```

Counts are total unresolved occurrences, not distinct candidate spellings.
Rendering uses this summary so a human can quickly distinguish noise reduction
from an empty analyzer.
