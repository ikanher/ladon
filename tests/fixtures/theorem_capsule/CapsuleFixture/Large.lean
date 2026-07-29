namespace CapsuleFixture

def chain0 : Nat := 0
def chain1 : Nat := chain0
def chain2 : Nat := chain1
def chain3 : Nat := chain2
def chain4 : Nat := chain3
def chain5 : Nat := chain4
def chain6 : Nat := chain5
def chain7 : Nat := chain6
def chain8 : Nat := chain7
def chain9 : Nat := chain8
def chain10 : Nat := chain9
def chain11 : Nat := chain10
def chain12 : Nat := chain11
def chain13 : Nat := chain12
def chain14 : Nat := chain13
def chain15 : Nat := chain14
def chain16 : Nat := chain15
def chain17 : Nat := chain16
def chain18 : Nat := chain17
def chain19 : Nat := chain18
def chain20 : Nat := chain19
def chain21 : Nat := chain20
def chain22 : Nat := chain21
def chain23 : Nat := chain22
def chain24 : Nat := chain23
def chain25 : Nat := chain24
def chain26 : Nat := chain25
def chain27 : Nat := chain26
def chain28 : Nat := chain27
def chain29 : Nat := chain28
def chain30 : Nat := chain29
def chain31 : Nat := chain30
def chain32 : Nat := chain31
def chain33 : Nat := chain32
def chain34 : Nat := chain33
def chain35 : Nat := chain34
def chain36 : Nat := chain35
def chain37 : Nat := chain36
def chain38 : Nat := chain37
def chain39 : Nat := chain38
def chain40 : Nat := chain39
def chain41 : Nat := chain40
def chain42 : Nat := chain41
def chain43 : Nat := chain42
def chain44 : Nat := chain43
def chain45 : Nat := chain44
def chain46 : Nat := chain45
def chain47 : Nat := chain46
def chain48 : Nat := chain47
def chain49 : Nat := chain48
def chain50 : Nat := chain49
def chain51 : Nat := chain50
def chain52 : Nat := chain51
def chain53 : Nat := chain52
def chain54 : Nat := chain53
def chain55 : Nat := chain54
def chain56 : Nat := chain55
def chain57 : Nat := chain56
def chain58 : Nat := chain57
def chain59 : Nat := chain58
def chain60 : Nat := chain59
def chain61 : Nat := chain60
def chain62 : Nat := chain61
def chain63 : Nat := chain62
def chain64 : Nat := chain63
def chain65 : Nat := chain64
def chain66 : Nat := chain65
def chain67 : Nat := chain66
def chain68 : Nat := chain67
def chain69 : Nat := chain68
def chain70 : Nat := chain69

mutual
  inductive Even : Nat → Prop where
    | zero : Even 0
    | succ {n} : Odd n → Even (n + 1)

  inductive Odd : Nat → Prop where
    | succ {n} : Even n → Odd (n + 1)
end

end CapsuleFixture
