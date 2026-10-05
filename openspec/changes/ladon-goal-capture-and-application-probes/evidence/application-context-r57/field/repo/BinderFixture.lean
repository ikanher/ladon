namespace BinderFixture
theorem use {α : Type} ⦃β : Type⦄ [Inhabited α]
    (x : α) (y : β) (h : x = x) (k : y = y) : (x = x) ∧ (y = y) :=
  And.intro h k
end BinderFixture
