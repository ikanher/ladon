Initial commands before the persistent command runner was installed (all exit 0):
1. `cat [arm A]/PROMPT.md` — complete prompt returned, 6000 token output allowance.
2. `mkdir -p [arm A]/OUTPUT/evidence`; Python created ROLE-ACK.json and start-time.txt exclusively; `cat [arm A]/INPUT/RECIPE.md` — complete recipe returned.
3. `find [arm A]/INPUT -type f | sort` — 147 lines returned; UI output truncated at 6000 tokens. No other directory inspected.
4. Python wrote OUTPUT/run-command.py and this log. All remaining audit shell commands use the runner and retain their exact command/output in commands.jsonl and numbered txt files.
