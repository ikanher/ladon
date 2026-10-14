import Lean

theorem modusPonens (P Q : Prop) (hp : P) (hpq : P → Q) : Q := by
  exact hpq hp

theorem result (P Q : Prop) (hp : P) (hpq : P → Q) : Q := by
  exact modusPonens P Q hp hpq
