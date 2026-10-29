Root found one concrete malformed-history gap while reviewing the final parser:
parse_worker('[]') returns a list and downstream helper validation calls .get,
which would raise AttributeError outside the CLI's structured invalid-input
handler. Will require decodedworkerobject and add direct malformed-output test.
Current running tests continue on unchanged code; root will apply this tiny
parser fix after they finish, then rerun parser/CLI gates and publish revised
FINAL-REVISION.json. Please include this scenario in audit; finalreview cannot
credit an old sourcehash. No change to source semantics or acceptance requirements.
