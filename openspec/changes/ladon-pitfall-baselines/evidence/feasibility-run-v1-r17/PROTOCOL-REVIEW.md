# Protocol audit: feasibility r17

Independent review confirmed the policy, runner, lock and acceptance-index hashes agree. All four case records bind 41 evidence files apiece; the reviewer recomputed all 164 file hashes. Each generated polarity source has a retained path and digest, and CLI receipts retain capture/completion argv.

The case deadline starts before fixture preparation, passes as an absolute monotonic deadline through runtime-custody startup, and bounds worker execution. Expiry sends TERM to the worker process group, waits five seconds, then sends KILL. The synthetic timeout countercheck records a stopped child and terminal receipt. A separate partial-index countercheck verifies a failed case leaves a terminal record and hashed interrupted index.

Each case records selected import success, exact missing-module diagnostics for excluded imports, an unrelated compiler-error receipt, and a successful exposed-module import receipt. The full r17 batch completed; no protocol defect was found. The index remains pending independent adjudication until this review is appended.
