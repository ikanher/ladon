# Constructed development passages

These are complete standalone passages authored for this comparison. No unstated earlier theorem or ambient provider may be supplied to them. Labels A–C identify inputs, not judgments. The Lean files are unchanged existing fixtures. These passages are not excerpts from DP-SGD.

## A

Let P be an arbitrary proposition. A provider for P has a field named proof whose type is P. Applying this field projection establishes P. Thus P holds.

## B

Let P be an arbitrary proposition. A provider for P has a field named proof whose type is P. Assume that a provider for P has been supplied as a type-class instance. Applying this field projection establishes P. Thus P holds under that assumption.

## C

First establish the arithmetic identity 2 + 2 = 4 by decision. Package that proof as a provider for the identity. Applying the provider's proof projection establishes 2 + 2 = 4.
