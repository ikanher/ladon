"""Compile a source-owned conditional target in an isolated compatible context."""

import json
import time
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_binding import _alpha_expression
from ladon.real_prose_connection_commitment import commit_target, validate_commitment
from ladon.real_prose_connection_inputs import authored_observation
from ladon.real_prose_connection_resources import stop_on_limits
from ladon.real_prose_expression import parse_worker
from ladon.real_prose_inputs import HELPER, generated_source, sha
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_association_io import _read_regular
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

MODULE = 'LadonConnection'
WITNESS = 'LadonCheckedConnectionWitness'
HELPERS = ('LadonProseExactGoal', 'LadonProseConnectionWitness')


def remaining(job):
    value = job['deadlineMonotonic'] - time.monotonic()
    if value <= 0:
        raise TimeoutError('shared Real prose connection deadline expired')
    return value


def stage_context(job, prose_root, workspace):
    context = pinned_toolchain(prose_root)
    root = Path(workspace)/'context'
    root.mkdir()
    (root/'lean-toolchain').write_bytes((prose_root/'lean-toolchain').read_bytes())
    (root/'.lake/build/lib/lean').mkdir(parents=True)
    for i, library in enumerate(context.library_roots):
        if any((library/(name+'.olean')).exists() for name in HELPERS):
            raise ValueError('reserved connection helper already exists in selected libraries')
        target = root/f'.lake/packages/import{i}/.lake/build/lib/lean'
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    return root


def run_lean(job, root, arguments):
    execution = prepare_direct_lean_execution(root, None, pinned_toolchain(root), require_compiled_module=False)
    result = run_bounded_target_process([*execution.command, *arguments], cwd=root,
        env=execution.environment, timeout_seconds=remaining(job),
        max_output_bytes=job['maxOutputBytes'], max_rss_bytes=job['maxRssBytes'])
    stop_on_limits([asdict(result)],job)
    return result


def compile_helpers(job, root):
    receipts = []
    for name in HELPERS:
        source = Path(__file__).parent/'lean'/f'{name}.lean'
        (root/source.name).write_bytes(source.read_bytes())
        result = run_lean(job, root, ['-o', f'.lake/build/lib/lean/{name}.olean', source.name])
        receipt = asdict(result)
        receipt['command'] = list(result.command)
        receipts.append(receipt)
        if not result.succeeded:
            break
    return receipts


def shifted_range(value):
    result = deepcopy(value)
    for key in result:
        if key.endswith('Line'):
            result[key] += 1
    return result


def owner_request(formal, authored, premises):
    snapshot = formal['request']['plan']['bindingPlan']['observation']['statementSnapshot']
    observation = authored_observation(authored)
    return {'schema':'ladon-prose-exact-goal-v1','module':MODULE,
            'formal':{'name':snapshot['selection']['declaration'],'kind':'theorem-type',
                      'range':shifted_range(snapshot['observation']['declarationRange']),
                      'expression':_alpha_expression(snapshot['observation']['normalizedTypeExpr'])},
            'authored':{'name':observation['generated']['declaration'],'kind':'proposition-value',
                        'range':shifted_range(observation['observation']['declarationRange']),
                        'expression':_alpha_expression(observation['observation']['propositionExpr'])},
            'premises':[{'name':row['target'],'kind':'proposition-value','range':row['declarationRange'],
                         'expression':_alpha_expression(row['propositionExpr'])} for row in premises]}


def base_source(authored):
    observation = authored_observation(authored)
    request = {k:authored['request'][k] for k in ('interpretation','context')}
    source, generated = generated_source(request, observation['contextSource']['text'].encode())
    if generated != observation['generated']:
        raise ValueError('connection regenerated a different authored definition')
    return 'import LadonProseConnectionWitness\n'+source.decode()


def observe_premises(job, root, names):
    rows = []
    for index, name in enumerate(names):
        destination = root/f'premise-{index}.json'
        result = run_lean(job, root, ['--run',str(HELPER),MODULE,MODULE+'.lean',
                                      str(root/(MODULE+'.lean')),name,str(destination)])
        if not result.succeeded:
            raise ValueError('connection premise observation process failed')
        row = parse_worker(_read_regular(destination,job['maxOutputBytes']).decode())
        if row['status'] != 'observed' or row['target'] != name or row['sourceModuleOwned'] is not True:
            raise ValueError('connection premise is not an exact local proposition definition')
        rows.append(row)
    return rows


def generated_goal_source(authored, request, connection):
    encoded = json.dumps(request,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    quoted = json.dumps(encoded,ensure_ascii=False)
    proof = json.dumps(connection['term'],ensure_ascii=False)
    source = base_source(authored)
    source += f'\n#ladon_connection_witness {quoted} {proof}\n'
    source += f'example : ladon_prose_exact_goal% {quoted} := by\n  skip\n'
    if len(source.encode()) > 8*1024**2:
        raise ValueError('connection generated source exceeds 8 MiB')
    return source


def check_goal(job, formal, authored, connection, prose_root):
    root = stage_context(job,prose_root,job['workspace'])
    compilations = compile_helpers(job,root)
    result = {'status':'unresolved','request':None,'sourceText':None,'premiseObservations':[],
              'compilations':compilations,'capture':None,'completion':None,'completionTerm':WITNESS,'commitment':None}
    if len(compilations) != len(HELPERS) or any(row['returncode'] != 0 for row in compilations):
        return result
    path = root/(MODULE+'.lean')
    path.write_text(base_source(authored))
    premises = observe_premises(job,root,connection['premises'])
    request = owner_request(formal,authored,premises)
    source = generated_goal_source(authored,request,connection)
    path.write_text(source)
    result.update({'request':request,'sourceText':source,'premiseObservations':premises})
    context = pinned_toolchain(root)
    capture = capture_source_goal(SourceGoalCaptureRequest(root,MODULE+'.lean',MODULE,
        len(source.splitlines()),4,context,timeout_seconds=remaining(job),
        max_rss_bytes=job['maxRssBytes'],max_output_bytes=job['maxOutputBytes']),
        workspace_parent=Path(job['workspace'])/'scratch')
    result['capture'] = capture
    stop_on_limits(capture['processReceipts'],job)
    if capture['status'] != 'captured':
        return result
    commitment = commit_target(job,root,source,request,connection['term'],run_lean,capture=capture['capture'])
    result['commitment'] = commitment
    if commitment['certificate'] is None:
        return result
    validate_commitment(commitment,request,connection['term'],source,capture['capture']['goal']['typeStructural'],
                        environment=capture['capture']['environment'])
    completion = complete_source_goal(SourceGoalCompletionRequest(root,capture['capture'],WITNESS,context,
        timeout_seconds=remaining(job),max_rss_bytes=job['maxRssBytes'],max_output_bytes=job['maxOutputBytes']),
        workspace_parent=Path(job['workspace'])/'scratch')
    result['completion'] = completion
    stop_on_limits(completion['processReceipts'],job)
    if completion['status'] == 'completed':
        result['status'] = 'checked'
    remaining(job)
    return result


def verify_imports(goal, formal, authored, workspace):
    captured = goal['capture']['capture']['environment']['compiledInventory']['modules']
    actual = {row['module']:row['digest'] for row in captured}
    expected = list(authored_observation(authored)['compiledInventory']['inventory']['modules'])
    for check in formal['check']['result']['checks']:
        rows = check['evidence']['capture']['capture']['environment']['compiledInventory']['modules']
        expected.extend(row for row in rows if not Path(row['path']).is_relative_to(workspace))
    if any(actual.get(row['module']) != row['digest'] for row in expected):
        raise ValueError('connection copied context changed an exact source-owner import')
    content = goal['sourceText'].encode()
    source = goal['capture']['capture']['source']
    if source['digest'] != 'sha256:'+sha(content) or source['byteLength'] != len(content):
        raise ValueError('connection capture differs from exact generated source')
