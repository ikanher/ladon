namespace Owner
variable {α : Type} [Inhabited α]
example (x : α) (h : x = x) : x = x := by
  have z : x = x := h
  skip
end Owner
