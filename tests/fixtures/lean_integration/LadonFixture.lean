import LadonFixture.Core
import LadonFixture.Helper

namespace LadonFixture

theorem fixtureIdentity (value : Nat) : value = value := rfl

theorem fixtureTrue : True := True.intro

theorem identité (value : Nat) : value = value := rfl

theorem twoIdentity (x y : Nat) : x = x := rfl

theorem fixtureUsesCore : Core.value = Helper.identity Core.value := by
  rfl

end LadonFixture
