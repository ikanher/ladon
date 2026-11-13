# Exposed source-consistency recipe qualification

Four authored scalar cases qualify use of the existing v2 rational witness checker. Inputs, assignments and expectations are frozen before execution. This is supplied-goal/supplied-witness checking, not discovery, held-out evaluation, Lean probability verification or a new regression-population score. Historical pitfall baselines are unchanged.

The inverse case abstracts y=a*x with a>0 and x>0. a=2,x=1,y=2 refutes x=a*y. The repaired claim x=y/a follows universally because a is nonzero; a sampled non-counterexample alone would not prove this. The unit case explicitly fixes a=1, giving a valid degenerate control. The invalid assignment violates y=a*x and must be rejected as outside assumptions. Never use that rejection as evidence for the original conclusion.

The PLD source is real-valued with a=exp(t). This rational projection does not supply probability normalization, differentiation, law realizability or source fidelity; its assigned x,y are arbitrary scalars. The separately reviewed smooth Gaussian witness owns the source refutation. No case here substitutes for it.

Execution: current checkout .venv Python and ladon.entrypoint, existing scripts/demo_derivation_challenges.py for source-bound plans/challenges, then investigation witness with the frozen assignments. No Lean process. Record commands, exit codes, elapsed subprocess time and full outputs. Tokens are unavailable. Acceptance: all four returned outcome kinds match, exact premise/conclusion values are retained, repaired and unit controls receive separate mathematical explanations, and independent source/arithmetic review upholds scope. No advantage claim follows from four matching outcomes. Failed preparation is retained and diagnosed before any rerun.
