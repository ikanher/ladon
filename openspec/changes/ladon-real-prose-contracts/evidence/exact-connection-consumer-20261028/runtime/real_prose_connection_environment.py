"""Bind the independent commitment to the original capture's loaded imports."""

from ladon._source_goal_inventory import capture_inventory, verify_inventory
from ladon.lean_toolchain import verify_toolchain_identities
from ladon.proof_slice import pinned_toolchain

FIELDS = ('leanVersion','leanCommit','leanExecutablePath','namespace',
          'openDeclarationsStructural','optionsStructural')


def prepare_environment(root,capture):
    context = pinned_toolchain(root)
    verify_toolchain_identities(context)
    if capture is None:
        return context,None
    expected = capture['environment']
    if (expected['executionContextRef'] != context.context_identity
            or expected['executableDigest'] != context.lean_identity):
        raise ValueError('commitment toolchain differs from original capture')
    rows = expected['compiledInventory']['modules']
    frame = {'importedModules':[row['module'] for row in rows],
             'compiledModulePaths':[{k:row[k] for k in ('module','path')} for row in rows]}
    files,environment,inventory = capture_inventory(context,frame)
    if inventory != expected['compiledInventory']:
        raise ValueError('commitment imports differ before invocation')
    return context,(files,environment,inventory,expected)


def finish_environment(context,binding,frame):
    verify_toolchain_identities(context)
    if binding is not None:
        files,environment,inventory,expected = binding
        verify_inventory(files,environment,inventory)
        validate_environment(frame,expected)
        return expected
    _,_,inventory = capture_inventory(context,frame)
    expected = {key:frame[key] for key in FIELDS}
    expected.update({'executionContextRef':context.context_identity,
                     'executableDigest':context.lean_identity,'compiledInventory':inventory})
    validate_environment(frame,expected)
    return expected


def validate_environment(frame,expected):
    if any(frame[key] != expected[key] for key in FIELDS):
        raise ValueError('commitment source scope or executable differs from capture')
    names,paths = frame['importedModules'],frame['compiledModulePaths']
    if (names != [row['module'] for row in paths] or len(set(names)) != len(names)):
        raise ValueError('commitment import names and paths disagree')
    rows = expected['compiledInventory']['modules']
    wanted = [{key:row[key] for key in ('module','path')} for row in rows]
    if sorted(paths,key=lambda row:row['module']) != wanted:
        raise ValueError('commitment loaded a different compiled import inventory')
