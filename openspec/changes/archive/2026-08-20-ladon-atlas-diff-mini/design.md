# Design Notes

## Diff Unit

The first implementation compares normalized rows, not raw graph structure. This
keeps diffs explainable:

- report summary rows
- finding rows
- review-region rows
- signal rows
- declaration-highlight rows
- module-highlight rows

## Change Rule

Rows with the same category/key but different numeric value or payload are
reported as changed. Rows only in the after atlas are added; rows only in the
before atlas are removed.

## Category Hints

Specialized architecture-evolution questions such as unresolved-reference class
changes or root-scope shifts are represented when those rows exist in findings
or signals. The diff engine itself stays generic.
