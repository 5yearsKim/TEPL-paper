#!/usr/bin/env python3
"""Rerun frozen automatic scalability workloads through --certified.

Build first: bazel build -c opt //:tepl //labs/reasoning_scalability:certified_benchmark
This runner preserves the historical default-backend measurements unchanged.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('total_ms', 'preparation_ms', 'certification_ms', 'lowering_ms', 'other_ms')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def validate(data):
    cases = data['manifest']['cases']
    expected = {f'chain_automatic_{n}' for n in range(1, 11)}
    expected |= {f'rank_{n}_automatic' for n in (2, 4, 8, 16, 32)}
    assert data['backend'] == 'certified'
    assert {c['case_id'] for c in cases} == expected
    assert len(cases) == len(expected)
    assert len(data['controls']) == len(cases)
    assert all(c['public_pipeline_equal'] and c['portable_roundtrip'] for c in data['controls'])
    assert len(data['records']) == len(cases) * (data['warmups'] + data['repetitions'])
    for case in cases:
        rows = [r for r in data['records'] if r['case_id'] == case['case_id']]
        assert Counter(r['stage'] for r in rows) == Counter(
            warmup=data['warmups'], measured=data['repetitions'])
        assert {r['round'] for r in rows} == set(range(-data['warmups'], data['repetitions']))
        for row in rows:
            assert row['status'] == 'accepted'
            assert all(row[f] >= 0 for f in FIELDS)
            assert abs(sum(row[f] for f in FIELDS[1:]) - row['total_ms']) < 1e-9


def summarize(data):
    summaries = []
    for case in data['manifest']['cases']:
        samples = [r for r in data['records'] if r['case_id'] == case['case_id'] and r['stage'] == 'measured']
        row = {**case, 'status': 'accepted', 'accepted_repetitions': len(samples)}
        for field in FIELDS:
            values = [r[field] for r in samples]
            for name, fn in [('median', statistics.median), ('mean', statistics.mean), ('min', min), ('max', max)]:
                row[f'{name}_{field}'] = fn(values)
        summaries.append(row)
    return summaries


def report(data, output):
    validate(data)
    rows = summarize(data)
    save(output / 'performance_summary.json', {'backend': 'certified', 'cases': rows})
    lines = [
        '# Certified compilation scalability', '',
        'All RHS axis fields are inferred. Frozen automatic workloads: 1–10 dots per side at rank three, '
        'and three source transposes composed into one replacement at ranks 2, 4, 8, 16, 32. '
        'Rule bodies, original guards, and dialect bytes are preserved from the earlier experiment; '
        'imports are embedded to make inputs self-contained. Explicit and partial variants are outside '
        'this automatic-only experiment; historical 39-configuration default results are retained separately.', '',
        f"Backend: `--certified --semantic-policy algebraic`. {len(rows)}/{len(rows)} configurations "
        f"accept in all {data['repetitions']} measured rounds; one public compile/portable-roundtrip control per case. "
        f"{data['manifest']['dense_reference_checks']} independent dense-integer workload checks pass.", '',
        '## Timing boundary', '',
        'An optimized in-process driver executes the exact API sequence of `core::compile(SourceProject, '
        'SemanticOptions{algebraic,false,true})`. Parsing and import loading occur once before timing. '
        'Every measured call starts with the loaded syntax project, not a previously prepared proof plan. '
        'No previous proof or compiled program is reused.', '',
        '- Preparation: resolution and type checking, including copying the input project as in the public pipeline.',
        '- Certify / construct: semantic-plan preparation, certified admission, guard certification, '
        'and materialization of the portable metadata program.',
        '- Lower / validate: executable lowering, metadata emission and final executable validation.',
        '- Other: return/dispatch and destruction of intermediate compilation objects before the timer stops. '
        'Destruction of the resulting executable occurs after timing.', '',
        'These are measured API boundaries, not inferred subdivisions. Guard checking and metadata '
        'construction can occur in more than one phase. Portable loading, CLI process startup, '
        'reference execution and graph rewriting are excluded. Public-pipeline serialization equality '
        'and portable load/serialization equality are checked outside timing for every input.', '',
        f"Warmups: {data['warmups']}; measured rounds: {data['repetitions']}. Serial, seeded shuffled case order "
        f"(seed {data['manifest']['seed']}). The normal compiler work budgets remain unchanged; "
        'there is no historical ten-second proof deadline. The driver process has an external 300-second limit.', '',
        'Panel (a) combines arithmetic mean phase times in stacked bars with overlaid median total '
        'latency and min/max whiskers. Stacked segments add exactly to mean total compilation latency. '
        'Panel (b) shows transpose-rank medians and min/max whiskers. All axes use milliseconds. '
        'One machine and ten rounds do not establish broad throughput or numerical-kernel speedups.', '',
        f"CPU: {data['provenance']['cpu']}. Platform: {data['provenance']['platform']}.", '',
        '![Two horizontally aligned panels: dot-chain phases and transpose rank](figures/scalability.png)', '',
        '## Complete results', '',
        '| Case | Accepted rounds | Median total (ms) | Prepare | Certify / construct | Lower / validate | Other |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for r in rows:
        lines.append(f"| {r['case_id']} | {r['accepted_repetitions']}/{data['repetitions']} | " +
                     ' | '.join(f"{r['median_' + f]:.5f}" for f in FIELDS) + ' |')
    lines += ['', 'Phase medians need not add to the median total; the figure instead stacks phase means.', '',
              'Raw samples and provenance: [performance.json](performance.json). '
              'The source archive and patch preserve the implementation used for this run.', '']
    (output / 'performance.md').write_text('\n'.join(lines))
    table = [r'\section{Complete Certified Scalability Configurations}',
             r'All 15 automatic configurations use the certified backend. The historical default-backend results remain in the artifact.',
             r'\input{supplement/03-scalability-protocol}',
             r'\begin{table}[!htbp]',
             r'\caption{Certified compilation: median milliseconds over ten measured rounds. Parsing and import loading are excluded. Phase medians need not sum to the median total.}',
             r'\label{supp-tab:scalability-results}', r'\small',
             r'\begin{tabularx}{\linewidth}{@{}Yrrrrr@{}}\toprule',
             r'Case & Success & Total & Prepare & Certify/construct & Lower/validate\\\midrule']
    for r in rows:
        table.append(r'\code{' + r['case_id'] + '} & ' + f"{r['accepted_repetitions']}/{data['repetitions']} & " +
                     ' & '.join(f"{r['median_' + f]:.3f}" for f in FIELDS[:-1]) + r'\\')
    table += [r'\bottomrule\end{tabularx}', r'\end{table}', '']
    (output / 'scalability-table.tex').write_text('\n'.join(table))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-root', type=Path, default=ROOT.parent.parent / 'tepl')
    parser.add_argument('--output', type=Path, default=ROOT / 'evaluation/certified-scalability')
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--repetitions', type=int, default=10)
    parser.add_argument('--report', action='store_true', help='Only validate/report saved measurements')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.report:
        report(json.loads((output / 'performance.json').read_text()), output)
        return
    if args.warmups < 0 or args.repetitions < 1:
        parser.error('invalid repetitions')
    if (output / 'performance.json').exists():
        parser.error('choose a fresh output directory to preserve existing measurements')
    for directory in ('inputs', 'programs', 'logs', 'bin', 'figures', 'source'):
        (output / directory).mkdir(parents=True, exist_ok=True)
    code = args.code_root.resolve()
    original = ROOT / 'evaluation/certified-scalability/source/original-inputs'
    dialect = ROOT / 'evaluation/certified-scalability/source/tensor.tepl'
    assert sha(dialect) == sha(code / 'examples/semantic/dialects/tensor.tepl')
    # Reuse the original independent reference oracles, without regenerating rules.
    sys.path.insert(0, str(code / 'labs/reasoning_scalability/scripts'))
    import benchmark as historical
    references = historical.validate_workloads()
    assert references == 60
    baseline = json.loads((original / 'manifest.json').read_text())
    cases = []
    for row in baseline['cases']:
        if row['mode'] != 'automatic':
            continue
        source_path = original / (row['case_id'] + '.tepl')
        text = source_path.read_text()
        body = '\n'.join(line for line in text.splitlines() if not line.startswith(('from ', 'use '))) + '\n'
        source = dialect.read_text() + '\nuse TensorLang::{dot,transpose};\n' + body
        destination = output / 'inputs' / source_path.name
        destination.write_text(source)
        cases.append({**row, 'file': str(destination), 'input_hash': sha(destination),
                      'original_file': str(source_path.relative_to(ROOT)), 'original_hash': sha(source_path),
                      'rule_body_hash': hashlib.sha256(body.encode()).hexdigest(),
                      'program_file': str(output / 'programs' / (row['case_id'] + '.json'))})
    manifest = {'backend': 'certified', 'seed': baseline['seed'], 'cases': cases,
                'dense_reference_checks': references, 'dialect_sha256': sha(dialect)}
    save(output / 'manifest.json', manifest)
    # Preserve all production source bytes, not only tracked changes.
    paths = sorted(p for p in (code / 'src').rglob('*') if p.is_file())
    paths += [code / name for name in ('BUILD.bazel', 'MODULE.bazel', 'MODULE.bazel.lock', '.bazelrc',
              'labs/reasoning_scalability/BUILD.bazel', 'labs/reasoning_scalability/certified_benchmark.cc',
              'labs/reasoning_scalability/scripts/benchmark.py', 'labs/reasoning_scalability/scripts/workloads.py',
              'examples/semantic/dialects/tensor.tepl') if (code / name).is_file()]
    hashes = {str(p.relative_to(code)): sha(p) for p in paths}
    with tarfile.open(output / 'implementation-source.tar.gz', 'w:gz') as archive:
        for p in paths:
            archive.add(p, arcname=str(p.relative_to(code)))
    (output / 'implementation.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=code))
    for name in ('BUILD.bazel', 'certified_benchmark.cc'):
        shutil.copy2(code / 'labs/reasoning_scalability' / name, output / 'source' / name)
    shutil.copy2(Path(__file__), output / 'source' / Path(__file__).name)
    for source, name in [('bazel-bin/tepl', 'tepl'), ('bazel-bin/labs/reasoning_scalability/certified_benchmark', 'benchmark')]:
        shutil.copy2(code / source, output / 'bin' / name)
    provenance = {'run_at_utc': datetime.now(timezone.utc).isoformat(),
                  'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=code, text=True).strip(),
                  'cpu': next(s.split(':', 1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),
                  'platform': platform.platform(), 'python': platform.python_version(),
                  'source_hashes': hashes, 'binary_hashes': {p.name: sha(p) for p in (output / 'bin').iterdir()},
                  'build_command': 'bazel build -c opt //:tepl //labs/reasoning_scalability:certified_benchmark'}
    save(output / 'provenance.json', provenance)
    # Exercise the actual CLI --certified flag and portable validator for every case.
    commands = []
    for case in cases:
        target = output / 'programs' / (case['case_id'] + '.cli.json')
        for phase, cmd in [
            ('check', [str(output / 'bin/tepl'), 'check', case['file'], '--certified', '--semantic-policy', 'algebraic']),
            ('compile', [str(output / 'bin/tepl'), 'compile', case['file'], '--certified', '--semantic-policy', 'algebraic', '-o', str(target)]),
            ('validate', [str(output / 'bin/tepl'), 'validate', str(target)])]:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            (output / 'logs' / f"{case['case_id']}.{phase}.txt").write_text(result.stdout + result.stderr)
            commands.append({'case_id': case['case_id'], 'phase': phase, 'argv': cmd, 'returncode': result.returncode})
            save(output / 'cli-results.json', commands)
            if result.returncode:
                raise RuntimeError(f"{case['case_id']} {phase}: {result.stderr}")
    raw = output / 'raw.json'
    command = [str(output / 'bin/benchmark'), str(output / 'manifest.json'), str(raw),
               str(args.warmups), str(args.repetitions), '--certified']
    env = dict(os.environ)
    env.pop('TEPL_INDEX_PROFILE', None)
    run = subprocess.run(command, capture_output=True, text=True, timeout=300, env=env)
    (output / 'logs/benchmark.txt').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(run.stderr)
    assert hashes == {str(p.relative_to(code)): sha(p) for p in paths}, 'source changed during run'
    data = {**json.loads(raw.read_text()), 'manifest': manifest, 'provenance': provenance,
            'warmups': args.warmups, 'repetitions': args.repetitions, 'argv': command}
    validate(data)
    save(output / 'performance.json', data)
    raw.unlink()
    report(data, output)
    print(f"Accepted {len(cases)} configurations, {len(data['records'])} samples, {len(commands)} CLI checks; {output}")


if __name__ == '__main__':
    main()
