#!/usr/bin/env python3
"""Predeclare and evaluate the complete pinned TASO axiom suite without tuning TEPL."""
import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

PAPER = Path(__file__).resolve().parents[1]
SUPPORTED = {'ewadd_0', 'ewmul_0', 'scalar_mul_0', 'matmul_0', 'transpose_0', 'relu_0'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def helper(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def graph_key(lhs, rhs):
    aliases = {'dot': 'dot_general', 'mul': 'multiply'}
    def direction(a, b):
        names = {}
        def visit(n):
            if n.kind == 'capture':
                return ('input', names.setdefault(n.name, len(names)))
            return (aliases.get(n.name.split('.')[-1], n.name.split('.')[-1]), tuple(visit(c) for c in n.children))
        return repr((visit(a), visit(b)))
    return min(direction(lhs, rhs), direction(rhs, lhs))


def prepare(args):
    out = args.output.resolve()
    if (out / 'plan.json').exists():
        raise ValueError('plan already exists; use a fresh directory')
    for name in ['upstream', 'inputs/dialects', 'parser']:
        (out / name).mkdir(parents=True, exist_ok=True)
    # Freeze the binary before preparing any translated task or inspecting outcomes.
    binary = args.frozen_compiler.resolve()
    binary.parent.mkdir(parents=True, exist_ok=True)
    if binary.exists():
        raise ValueError('choose a fresh frozen compiler path')
    shutil.copy2(args.compiler, binary)
    freeze = dict(time_utc=datetime.now(timezone.utc).isoformat(), compiler=str(binary),
                  compiler_sha256=sha(binary), original_compiler_sha256=sha(args.compiler),
                  policy='No compiler, checker, certificate, or dialect changes after freeze.')
    save(out / 'freeze.json', freeze)
    upstream = args.upstream.resolve()
    for name in ['verify.py', 'validate_axioms.py']:
        shutil.copy2(upstream / 'verify' / name, out / 'upstream' / name)
    shutil.copy2(upstream / 'LICENSE', out / 'upstream/LICENSE')
    dialects = PAPER / 'evaluation/backend-comparison/inputs/dialects'
    shutil.copytree(dialects, out / 'inputs/dialects', dirs_exist_ok=True)
    parser = args.code_root / 'labs/xla_rewrite/coverage/scripts'
    for name in ['synthesis_cases.py', 'paths.py', 'hlo_support.py']:
        shutil.copy2(parser / name, out / 'parser' / name)
    sys.path.insert(0, str(out / 'parser'))
    Rule = helper(out / 'parser/synthesis_cases.py', 'external_rule_parser').Rule
    old = json.loads((PAPER / 'evaluation/recorded-results.json').read_text())
    development = {}
    for name, texts in old['source_snapshots'].items():
        rule = Rule(texts['task'])
        development.setdefault(graph_key(rule.lhs, rule.rhs), []).append(name)
    for path in sorted((PAPER / 'evaluation/current/families').glob('*.tepl')) + sorted((PAPER / 'evaluation/accepted-core/original-rules').glob('*.tepl')):
        rule = Rule(path.read_text())
        development.setdefault(graph_key(rule.lhs, rule.rhs), []).append(str(path.relative_to(PAPER)))
    source = (out / 'upstream/verify.py').read_text()
    # Parse data only; never import/execute the upstream Python-2 verifier.
    tree = ast.parse(source[:source.index('# lemmas are implied')])
    axioms = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'axioms' for t in n.targets))
    records = []
    for index, entry in enumerate(axioms.elts, 1):
        formula, shape_lambda = entry.elts
        ops = sorted({n.func.id for n in ast.walk(formula) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id != 'ForAll'})
        row = dict(case=f'taso_{index:02}', upstream_line=entry.lineno,
                   axiom=ast.get_source_segment(source, formula), operations=ops,
                   unsupported_operations=sorted(set(ops) - SUPPORTED), variants=[])
        if row['unsupported_operations']:
            row['model_status'] = 'unsupported_operation_semantics'
            records.append(row)
            continue
        row['model_status'] = 'modeled'
        variables = [n.id for n in formula.args[0].elts]
        equation = formula.args[1]
        shapes = shape_lambda.body.elt.elts
        assert len(shapes) == len(variables)
        rank_choices = [None]
        if any(isinstance(s, ast.Name) for s in shapes):
            repeats = [kw.value for n in ast.walk(shape_lambda.body) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'product' for kw in n.keywords if kw.arg == 'repeat']
            repeat = next(v for v in repeats if isinstance(v, (ast.Name, ast.Constant)))
            if isinstance(repeat, ast.Constant):
                rank_choices = [repeat.value]
            else:
                rank_choices = next([n.value for n in g.iter.elts] for g in shape_lambda.body.generators if isinstance(g.target, ast.Name) and g.target.id == repeat.id)
        for rank in rank_choices:
            case = row['case'] + (f'_rank{rank}' if rank is not None else '')
            constraints = []
            dimensions = set()
            declarations = []
            for variable, shape in zip(variables, shapes):
                if isinstance(shape, ast.Name):
                    dims = [f'S{i}' for i in range(rank)]
                else:
                    assert isinstance(shape, ast.Tuple)
                    dims = [n.id.upper() for n in shape.elts]
                dimensions.update(dims)
                declarations.append(variable.upper() + ': [' + ', '.join(dims) + ']')
            constraints += [d + ' > 0' for d in sorted(dimensions)]
            next_id = 0
            fields = 0
            def lower(node, rhs):
                nonlocal next_id, fields
                if isinstance(node, ast.Name):
                    return node.id.upper()
                assert isinstance(node, ast.Call)
                op = node.func.id
                if op == 'relu_0':
                    # Expand the pure operation twice with independent node labels.
                    # Both copies retain the same captured tensor leaves.
                    x = lower(node.args[0], rhs)
                    z = lower(node.args[0], rhs)
                    return f'(h.maximum {x} (h.zero_like {z}))'
                children = [lower(n, rhs) for n in node.args]
                operation = {'ewadd_0': 'add', 'ewmul_0': 'multiply', 'scalar_mul_0': 'dot', 'matmul_0': 'dot', 'transpose_0': 'transpose'}[op]
                label = f'n{next_id}'
                next_id += 1
                if op in {'scalar_mul_0', 'matmul_0'}:
                    if rhs:
                        fields += 4
                    else:
                        lists = [[], [], [1], [0]] if op == 'matmul_0' else [[], [], [], []]
                        for field, values in zip(['lhs_batching_dimensions', 'rhs_batching_dimensions', 'lhs_contracting_dimensions', 'rhs_contracting_dimensions'], lists):
                            constraints.append(f'{label}.attrs.{field} == {values}')
                elif op == 'transpose_0':
                    if rhs:
                        fields += 1
                    else:
                        constraints.append(f'{label}.attrs.permutation == [1, 0]')
                return f'({label}: h.{operation} ' + ' '.join(children) + ')'
            lhs = lower(equation.left, False)
            rhs = lower(equation.comparators[0], True)
            text = 'from "dialects/hlo.tepl" import HLO as h;\nrule ' + case + ' {\n  ' + '\n  '.join(declarations) + '\n  ' + lhs + ' => ' + rhs + '\n  where { ' + '\n    && '.join(constraints) + ' }\n}\n'
            path = out / 'inputs' / (case + '.tepl')
            path.write_text(text)
            rule = Rule(text)
            overlap = development.get(graph_key(rule.lhs, rule.rhs), [])
            row['variants'].append(dict(case=case, source=str(path.relative_to(out)), source_sha256=sha(path),
                                        requested_axis_fields=fields, development_graph_overlaps=overlap,
                                        rank=rank))
        row['development_graph_overlaps'] = sorted({name for v in row['variants'] for name in v['development_graph_overlaps']})
        records.append(row)
    plan = dict(protocol='taso_complete_active_axioms_frozen_compiler_v1',
                prepared_utc=datetime.now(timezone.utc).isoformat(), freeze=freeze,
                upstream_url='https://github.com/jiazhihao/TASO',
                upstream_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip(),
                upstream_sha256=sha(out / 'upstream/verify.py'), source_population=len(records),
                selection='Every active entry in upstream axioms; forward equality orientation; no outcome-based selection.',
                overlap='Alpha-renamed ordered graph pairs, either orientation, ignoring attributes/guards; compared with all 123 frozen task graphs, six symbolic families, and retained accepted-core original rules. Not an exhaustive historical-development audit.',
                models='Tensor values and ordered shapes, excluding TASO split annotations. Matrix transpose is rank-two swap; scalar multiplication is dot with a rank-zero right operand; ReLU is max(x,0). All RHS axis fields are omitted. Every rank in the upstream validation rank list is included; positive extents remain symbolic.',
                records=records)
    save(out / 'plan.json', plan)
    (out / 'runner.py').write_bytes(Path(__file__).read_bytes())
    shutil.copy2(PAPER / 'tools/run_backend_comparison.py', out / 'backend_helpers.py')
    print(json.dumps(dict(axioms=len(records), modeled=sum(r['model_status'] == 'modeled' for r in records), variants=sum(len(r['variants']) for r in records)), indent=2))


def run(args):
    out = args.output.resolve()
    if (out / 'results.json').exists():
        raise ValueError('results already exist')
    plan = json.loads((out / 'plan.json').read_text())
    binary = Path(plan['freeze']['compiler'])
    assert sha(binary) == plan['freeze']['compiler_sha256']
    before = sha(out / 'plan.json')
    helper_module = helper(out / 'backend_helpers.py', 'external_backend_helpers')
    for name in ['logs', 'programs/default', 'programs/core']:
        (out / name).mkdir(parents=True, exist_ok=True)
    work = [(r, v) for r in plan['records'] for v in r['variants']]
    def attempt(item):
        row, variant = item
        result = dict(variant)
        source = out / variant['source']
        assert sha(source) == variant['source_sha256']
        for backend in ['default', 'core']:
            artifact = out / 'programs' / backend / (variant['case'] + '.json')
            flags = ['--core'] if backend == 'core' else []
            commands = [('check', [str(binary), 'check', str(source), '--semantic-policy=algebraic', '--rule', variant['case'], *flags]),
                        ('compile', [str(binary), 'compile', str(source), '--semantic-policy=algebraic', *flags, '-o', str(artifact)]),
                        ('validate', [str(binary), 'validate', str(artifact)])]
            measured = dict(accepted=False, commands=[])
            for phase, argv in commands:
                started = time.monotonic()
                try:
                    p = subprocess.run(argv, text=True, capture_output=True, timeout=30)
                    status, text = p.returncode, p.stdout + '\n' + p.stderr
                except subprocess.TimeoutExpired:
                    status, text = 'timeout', '30-second command timeout'
                log = out / 'logs' / f'{variant["case"]}.{backend}.{phase}.txt'
                log.write_text(text)
                measured['commands'].append(dict(phase=phase, argv=argv, returncode=status, seconds=time.monotonic()-started, log=str(log.relative_to(out))))
                if phase == 'check':
                    measured['reason'] = '\n'.join(line.strip().removeprefix('reason:').strip() for line in text.splitlines() if line.strip().startswith('reason:'))
                    proved = text.count('status=proved') == 1 and 'additional-guard: true' in text
                else:
                    proved = True
                if status != 0 or not proved:
                    measured.update(outcome=helper_module.classify(measured.get('reason', ''), phase, status), failure_stage=phase)
                    break
            else:
                program = json.loads(artifact.read_text())
                if backend == 'core':
                    assert 'tepl.core-dag.v1' in program['capabilities']
                measured.update(accepted=True, outcome='accepted', artifact=str(artifact.relative_to(out)), artifact_sha256=sha(artifact))
            result[backend] = measured
        print(variant['case'], result['default']['outcome'], result['core']['outcome'], flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:
        measured = list(pool.map(attempt, work))
    assert sha(binary) == plan['freeze']['compiler_sha256'] and sha(out / 'plan.json') == before
    by_name = {r['case']: r for r in measured}
    rows = []
    for original in plan['records']:
        row = dict(original)
        row['variants'] = [by_name[v['case']] for v in row['variants']]
        for b in ['default', 'core']:
            row[b + '_accepted'] = bool(row['variants']) and all(v[b]['accepted'] for v in row['variants'])
        rows.append(row)
    result = dict(plan_sha256=before, completed_utc=datetime.now(timezone.utc).isoformat(), records=rows)
    save(out / 'results.json', result)
    summary = dict(population=len(rows), modeled=sum(bool(r['variants']) for r in rows), variants=len(measured),
                   axis_schemas=sum(bool(r['variants']) and any(v['requested_axis_fields'] for v in r['variants']) for r in rows),
                   overlap_schemas=sum(bool(r['variants']) and bool(r['development_graph_overlaps']) for r in rows),
                   nonoverlap_modeled=sum(bool(r['variants']) and not r['development_graph_overlaps'] for r in rows),
                   **{b: dict(accepted_schemas=sum(r[b+'_accepted'] for r in rows), accepted_variants=sum(v[b]['accepted'] for v in measured),
                              accepted_axis_schemas=sum(r[b+'_accepted'] and any(v['requested_axis_fields'] for v in r['variants']) for r in rows),
                              nonoverlap_accepted=sum(r[b+'_accepted'] and not r.get('development_graph_overlaps') for r in rows),
                              outcomes=dict(Counter(v[b]['outcome'] for v in measured))) for b in ['default', 'core']})
    save(out / 'summary.json', summary)
    with (out / 'cases.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['case','upstream_line','operations','unsupported_operations','variants','axis_fields','graph_overlaps','default_accepted','core_accepted'])
        for r in rows:
            writer.writerow([r['case'],r['upstream_line'],';'.join(r['operations']),';'.join(r['unsupported_operations']),len(r['variants']),sum(v['requested_axis_fields'] for v in r['variants']),';'.join(r.get('development_graph_overlaps',[])),r['default_accepted'],r['core_accepted']])
    helper_module.archive_programs(out, measured)
    save(out / 'manifest.json', {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name!='manifest.json'})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare','run'])
    parser.add_argument('--output', type=Path, default=PAPER/'evaluation/external-taso')
    parser.add_argument('--upstream', type=Path, default=Path('/tmp/tepl-taso-upstream'))
    parser.add_argument('--compiler', type=Path, default=Path('/home/onion/Projects/tepl/bazel-bin/tepl'))
    parser.add_argument('--frozen-compiler', type=Path, default=Path('/tmp/tepl-external-taso/tepl'))
    parser.add_argument('--code-root', type=Path, default=Path('/home/onion/Projects/tepl'))
    args = parser.parse_args()
    (prepare if args.phase == 'prepare' else run)(args)
