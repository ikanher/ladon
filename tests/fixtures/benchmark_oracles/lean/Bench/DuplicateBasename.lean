namespace Bench

def local_helper : Nat := 0
def root : Nat := local_helper

namespace A
def shared : Nat := 1
end A

namespace B
def shared : Nat := 2
end B

def ambiguousUse : Nat := shared

end Bench
