"""Summarize saved counts; never compile or execute a model."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


models = []
union = {}
for key, label in [('dlrm', 'DLRM training FP32'),
                   ('vit', 'ViT mixed BF16/FP32'),
                   ('resnet', 'ResNet-50 FP32'),
                   ('gpt2', 'GPT-2 small FP32')]:
    folder = ROOT / 'reviewed' / key
    result = read(folder / 'summary.json')
    assert not result['semantic_profile_mismatches']
    assert result['semantic_categories']['unreviewed']['rule_variants'] == 0
    for filename, digest in read(folder / 'manifest.json').items():
        assert sha(folder / filename) == digest, filename
    coverage = result['semantic_model_coverage']
    with (folder / 'rules.csv').open() as stream:
        rules = list(csv.DictReader(stream))
    assert len(rules) == result['distinct_rule_variants']
    assert sum(int(r['applications']) for r in rules) == result['total_applications']
    for rule in rules:
        old = union.setdefault(rule['rule_id'], rule['semantic_status'])
        assert old == rule['semantic_status']
    models.append(dict(
        workload=label, rule_variants=result['distinct_rule_variants'],
        applications=result['total_applications'],
        semantic_model_variants=coverage['rule_variants'],
        associated_native_applications=coverage['associated_native_applications'],
        direct_variants=result['semantic_categories']['direct']['rule_variants'],
        unit_view_candidates=coverage['unit_view_candidates'],
        conditional_variants=result['semantic_categories']['conditional']['rule_variants'],
        outside_variants=result['semantic_categories']['outside']['rule_variants'],
        pass_invocations=result['pass_invocations']))

resnet_baseline = ROOT / 'reference-baselines/resnet50.final.hlo'
resnet_current = ROOT / 'resnet/hlo/final.hlo'
assert resnet_current.read_bytes() == resnet_baseline.read_bytes()
report = dict(
    scope='All AlgebraicSimplifier invocations in one normal XLA CPU compilation per workload',
    additional_model_compilations=3, numerical_executions=0,
    dlrm_measurement='Previously recorded result, replayed without recompilation',
    semantic_model_coverage='Direct semantic representations plus restricted unit-axis normalization candidates; not TEPL acceptance or delegation',
    rule_identity='Successful source-branch variant; equivalent branches remain separate variants',
    workloads=models,
    union=dict(distinct_variants=len(union),
               semantic_model_variants=sum(s in ('direct', 'unit_view_candidate') for s in union.values())),
    validation=dict(frozen_manifests_valid=True, per_rule_totals_valid=True,
                    semantic_reviews_complete=True,
                    resnet_final_matches_prior_uninstrumented_hlo=True,
                    resnet_final_sha256=sha(resnet_current),
                    vit_uninstrumented_comparison_measured=False,
                    gpt2_uninstrumented_comparison_measured=False,
                    classification_pipeline_offline_checks='6 passed'))
(ROOT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
with (ROOT / 'summary.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(models[0]))
    writer.writeheader()
    writer.writerows(models)
table = ['| Workload | Rule variants | Native applications | Semantic coverage candidates | Associated native applications |',
         '|---|---:|---:|---:|---:|']
for m in models:
    table.append(f"| {m['workload']} | {m['rule_variants']} | {m['applications']} | {m['semantic_model_variants']}/{m['rule_variants']} | {m['associated_native_applications']}/{m['applications']} |")
(ROOT / 'results.md').write_text('\n'.join(table) + '\n')
print('\n'.join(table))
print('Validated frozen manifests, semantic review completeness, totals, and ResNet baseline agreement.')
