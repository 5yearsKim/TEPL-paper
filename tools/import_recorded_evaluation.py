#!/usr/bin/env python3
"""Import existing TEPL measurements without rerunning or modifying them."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tepl-root', type=Path, default=ROOT.parent.parent / 'tepl')
    parser.add_argument('--check', action='store_true', help='compare generated files without writing')
    args = parser.parse_args()
    source_root = args.tepl_root / 'labs/xla_rewrite/coverage/results'
    runs, records, source_snapshots = {}, [], {}
    for tag, filename in [('A', 'broadcast_update.json'), ('B', 'expanded_semantics.json')]:
        path = source_root / filename
        raw = path.read_bytes()
        data = json.loads(raw)
        rows = [r for r in data['results'] if not r.get('control')]
        counts = Counter((bool(r.get('requested_axis_fields', 0)), r['outcome']) for r in rows)
        runs[tag] = {
            'source': str(path.relative_to(args.tepl_root)),
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'run_at_utc': data['run_at_utc'],
            'revision': data['revision'],
            'compiler_sha256': data['compiler_sha256'],
            'timeout_seconds_per_command': data['timeout_seconds_per_command'],
            'jobs': data['jobs'],
            'cases': len(rows),
            'axis_cases': sum(bool(r.get('requested_axis_fields', 0)) for r in rows),
            'inferred': counts[(True, 'inferred')],
            'verification_only_successes': counts[(False, 'verified')],
            'controls': data.get('controls', []),
            'note': data.get('note', ''),
        }
        for row in rows:
            records.append(dict(run=tag, **row))
            original_path = source_root.parent / row['source_file']
            original_source = original_path.read_text()
            assert hashlib.sha256(original_path.read_bytes()).hexdigest() == row['source_sha256'], original_path
            if row.get('generated_source') is not None:
                task_source = row['generated_source']
            else:
                task_source = (args.tepl_root / row['file']).read_text()
            assert hashlib.sha256(task_source.encode()).hexdigest() == row['file_sha256'], row['case']
            source_snapshots[row['case']] = {'run': tag, 'original': original_source, 'task': task_source}
    assert runs['A']['cases'] == 112 and runs['B']['cases'] == 11
    assert runs['A']['inferred'] == 31 and runs['B']['inferred'] == 0
    assert runs['A']['verification_only_successes'] == 65
    assert runs['B']['verification_only_successes'] == 2
    assert len({r['case'] for r in records}) == 123
    for row in records:
        if row['outcome'] in ('inferred', 'verified'):
            assert row['check']['returncode'] == 0
            assert row['compile']['returncode'] == 0
            assert row['validation']['returncode'] == 0
            assert row['validated_json']
            assert 'additional-guard: true' in row['check']['stdout']
    manifest = {
        'description': 'Imported historical measurements, not a new experiment. The two runs use different compiler hashes. Source paths inside records are historical.',
        'runs': runs,
        'totals': {'modeled_cases': 123, 'axis_cases': 38, 'inferred': 31,
                   'verification_only_cases': 85, 'verification_only_successes': 67},
        'records': records,
        'source_snapshots': source_snapshots,
    }
    targets = {
        ROOT / 'evaluation/recorded-results.json': json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
    }
    for path, content in targets.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f'stale generated file: {path.relative_to(ROOT)}')
        else:
            path.write_text(content)
    print('Recorded evidence checked: 123 cases; 31/38 axis and 67/85 verification-only successes across two runs.')


if __name__ == '__main__':
    main()
