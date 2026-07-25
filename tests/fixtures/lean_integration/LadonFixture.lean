import LadonFixture.Core
import LadonFixture.Helper

namespace LadonFixture

theorem fixtureIdentity (value : Nat) : value = value := rfl

theorem fixtureUsesCore : Core.value = Helper.identity Core.value := by
  rfl

end LadonFixture
