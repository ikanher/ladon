# Design

Pipeline behavior:

1. text discovery reads module declarations across the inventory;
2. Lean helper extraction reads exact root declarations;
3. declaration graph analysis receives helper declarations plus a set of text
   declaration names;
4. unresolved candidates matching the inventory set, or whose final dotted
   segment matches the inventory set, are classified as
   `known_inventory_candidate`.

This is a triage classification only. It reduces false "missing declaration"
signals without adding unsound graph edges.
