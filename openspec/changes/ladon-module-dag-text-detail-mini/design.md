# Design

This is renderer-only. It consumes existing `module_dag` JSON fields:

- `top_fan_in`
- `top_fan_out`
- `facade_modules`
- `source_modules_not_reachable_from_chosen_roots`

Sections are appended after pipeline timing so the summary/findings stay first.
The goal is readable grouping, not new analysis.
