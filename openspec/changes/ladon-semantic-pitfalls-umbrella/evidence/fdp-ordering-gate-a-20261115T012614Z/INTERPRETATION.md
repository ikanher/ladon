# Gate A interpretation before new checks

The source defines replace-one adjacency of equal-length tuples but sampling as a uniform subset, with no explicit tuple enumeration. The appendix uses both same-subset neighboring inputs and neighboring inputs on replaced subsets. These are different obligations.

Check the following conditional model: an ordered injective selection e:Fin m→Fin n, selected tuple D∘e. A changed source slot affects at most one selected coordinate. Replacing one selected slot in place preserves injection if the new slot was absent, and changes at most one tuple coordinate. Uniform ordered selections would require a separate distributional/coupling proof; it is not assumed equivalent to inherited ordering.

Controls: increasing enumeration can change two coordinates after subset replacement; a mechanism reading the first coordinate can distinguish increasing versus uniformly randomized ordering. These controls concern representation, not a privacy counterexample.

Stop if source inspection cannot uniquely determine ordering: deliver conditional checked facts and exact ambiguity, leaving Gate B and full theorem open. No donor edits or external search.
