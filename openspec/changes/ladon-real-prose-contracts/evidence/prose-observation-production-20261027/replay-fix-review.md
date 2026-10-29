One additional resource-boundary fix reopens finalaudit: replay previously called
inspect_prose_observation(root) before its supervised observation budget began.
Root moved freshness checking into the existing supervised worker job, with
previous snapshot embedded, one deadline initialized at replay entry, and exact
request equality. Parent performs only bounded historical-structure validation;
all filesystem/toolchain/compiled freshness checking runs in the supervised tree.
No deadline reset for stages. Regression tests the replay job contains original
snapshot and exact shared deadline and a simulated stop prevents downstream work.
FINAL-REVISION.json refreshed; priorhashes retained BEFORE-REPLAY-FIX. Please
recheck _observe/replay in real_prose_observation.py and _prepare worker path plus
29newtests declaration (including parser3 and replay1). Public first Naviercase
passed33.26sec peak5.07GiB on previousversion, preserved and will not receive final
runtimecredit; finalversion currentNavierobservation underway under same original
600sec qualificationclock, followed by inspect/replay. No resource capincrease or
clockreset. No further codeeditsplanned after checks. Soft2min hard4min.
