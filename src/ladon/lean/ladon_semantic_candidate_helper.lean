import Lean

/-! Candidate verification is supervised by the Python protocol.  This helper
identity is kept separate so a compiled module environment can be checked
against the request before any candidate rows are published. -/

def ladonSemanticCandidateProtocol : String := "ladon-lean-semantic-v1/check-candidates"
