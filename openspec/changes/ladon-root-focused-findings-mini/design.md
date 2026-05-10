# Design

Findings are small dictionaries with stable keys:

- `kind`
- `severity`
- `message`
- `subject`
- `count`

The initial heuristics are deliberately simple:

- fan-in >= 5 means likely shared kernel pressure;
- fan-out >= 5 means likely orchestration or duplicated proof skeleton;
- unresolved candidate count >= 5 means name-resolution or parser-noise hotspot;
- unreachable declarations from chosen roots become an informational finding.

Each hotspot family is capped to the top three findings. Detailed graph tables
still carry more rows.

The thresholds are not mathematical claims. They exist to put actionable root
signals above raw inventory tables.
