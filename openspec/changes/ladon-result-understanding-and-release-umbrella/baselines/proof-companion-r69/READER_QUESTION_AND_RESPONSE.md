# First reader question and proposed response

## Actual question

The user asked:

> Why is the divergence in the paper? Isn't it obvious that as T goes to infinity,
> the limit WILL diverge?

This is an independently supplied reader question, not a synthetic control.
We interpret divergence as the manuscript's privacy variance $v_{E,T}$, not its
finite offset limit or the raw standard deviation, which tends to zero.

## Response

Once the calibrated noise scaling is established, divergence is an elementary
consequence. Before that, $T\to\infty$ does not suffice: the noise is recalibrated
at every horizon. The variance is $T\sigma_{E,T}^2/E^2$, and the theorem proves
$\sigma_{E,T}\sim\Delta/\sqrt{2\log T}$. Thus the product grows like $T/\log T$.
A hypothetical $T^{-1/2}$ raw-noise scale would instead leave bounded variance.
The asymptotic establishes eventual dominance by full batch; the average-only
uniform bound shows that divergence is specific to the protected output.

## Proposed correction

COMPANION_BEFORE_QUESTION.md preserves the original draft. COMPANION.md now
explains the distinction between shrinking raw noise and diverging calibrated
variance, and why the divergence matters for the full-batch comparison.
The manuscript itself and its formal coverage records are unchanged.

This is conventional mathematical explanation, checked against the source
formulas and theorem statements. No new Lean operation, canonical capture,
human understanding certification, priority claim or formal-coverage promotion
is asserted. The offset adapter's historical scope remains unchanged.

## Reader follow-up and outcome

After the explanation, the user replied: “Sure, do continue then.” This
acknowledges the response and authorizes continuation. It does not explicitly
confirm mathematical understanding, acceptance of every claim, or adoption of a
manuscript edit. No further objection or question was supplied in that reply.

The question, response, revised companion and proposed manuscript paragraph are
now a bounded editorial handoff. Human editorial adoption remains pending. No
Ladon software advantage is demonstrated by this editing alone.

## r09 editorial follow-through

The recorded response above is preserved as history. The reviewer supplied a
shorter conventional detectability argument for divergence alone; the current
companion includes it and distinguishes it from the sharp asymptotic. The revised
paragraph and offline source navigation are ready for the responsible author.
The cycle is closed as a reviewed proposal, with adoption pending and no new
formal-coverage claim, Lean run or measured comprehension result.
