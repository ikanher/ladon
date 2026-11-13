# Common source-first audit recipe

This recipe is identical in both arms. Start from the two supplied TeX notes
and the supplied Lean capsule; do not start from a guessed fault or a theorem
name.

1. Read both notes broadly. Inventory mathematical claims, displayed formulas,
   assumptions, parameter ranges, definitions, intermediate assertions, and
   uses of prior results. Mark each source span examined, mapped, unresolved,
   or unexamined. State how complete the inventory is.
2. For every proposed correspondence, record the exact source span and Lean
   declaration(s). Compare objects, assumptions, domains, quantifier order,
   conclusion, and dependencies. Inspect relevant definitions and proof bodies.
3. Keep statement support separate from method correspondence. A checked
   theorem may prove a conclusion by a different route; a failed tactic is not
   a counterexample.
4. For any concern, state the original obligation without changing its
   assumptions. Give an argument or Lean check that addresses that obligation;
   distinguish a real counterexample from an unsuccessful proof attempt. If
   interpretation, source mapping, or an operation is uncertain, abstain and
   state exactly what remains unresolved.
5. Report useful findings, faithful correspondences, justified abstentions,
   unresolved items, and unexamined source explicitly. For each finding give
   source location, formal support, reasoning/evidence, consequence for the
   mathematical claim or reader, and confidence. Do not claim whole-note
   certification.

Do not modify either source note or Lean source. Keep source claims, proposed
interpretations, checks, and any proposed repair distinct.
