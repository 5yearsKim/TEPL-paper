#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
from collections import Counter
import argparse

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Recount saved source tokens for all 31 inference-successful rules; no compiler execution.')
parser.add_argument('--code-root',type=Path,default=root.parent.parent/'tepl')
code=parser.parse_args().code_root.resolve()
sys.path.insert(0,str(code/'labs/xla_rewrite/specification_size/scripts'))
import responsibility as r
paths={'coverage':root/'evaluation/unified-construction/results.json','originals':root/'evaluation/recorded-results.json','measurement':root/'evaluation/current/specification_size/results/measurement.json','responsibility':root/'evaluation/current/specification_size/results/responsibility.json'}
coverage=json.loads(paths['coverage'].read_text())['records']
selected={x['case'] for x in coverage if x['requested_axis_fields'] and x['default']['accepted']}
assert len(selected)==31
originals=json.loads(paths['originals'].read_text())['source_snapshots']
measurement={x['case']:x for x in json.loads(paths['measurement'].read_text())['cases']}
responsibility={x['case']:x for x in json.loads(paths['responsibility'].read_text())['cases']}
rows=[];explicit=Counter();inferred=Counter()
for name in sorted(selected):
 source=originals[name]['original']; compact=responsibility[name]['sources']['compact']
 a=r.tepl_parts(source);b=r.tepl_parts(compact)
 assert hashlib.sha256(source.encode()).hexdigest()==measurement[name]['variants']['original']['source_sha256'],name
 assert sum(a.values())==measurement[name]['variants']['original']['rule']['tokens'],name
 assert b==responsibility[name]['variants']['compact']['parts'],name
 explicit.update(a);inferred.update(b)
 rows.append(dict(case=name,explicit_source=source,inferred_source=compact,explicit_sha256=hashlib.sha256(source.encode()).hexdigest(),inferred_sha256=hashlib.sha256(compact.encode()).hexdigest(),explicit_parts=a,inferred_parts=b,historical_explicit_accepted=measurement[name]['variants']['original']['accepted'],historical_compact_accepted=responsibility[name]['variants']['compact']['accepted'],normalizations=measurement[name]['normalizations']))
a=sum(explicit.values());b=sum(inferred.values())
result=dict(protocol='all_31_inference_successes_static_source_footprint_v1',scope='All 31 default-backend inference successes in the retained coverage run; no selection by explicit-baseline acceptance or XLA audit availability.',measurement_kind='Static source-token recount, not a new compiler validation experiment.',notes=['Five original explicit variants and one compact variant did not validate in the historical size run; no validation claim is added here.','Saved inferred forms include unit-axis normalization and unused-label/empty-block cleanup. Two normalized cases add 48 legality tokens relative to the original forms.','The historical XLA excerpt comparison is not used in the current 31-rule source-footprint evaluation.'],dependencies={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},counting_scripts={str(p.relative_to(code)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [code/'labs/xla_rewrite/specification_size/scripts/measure.py',code/'labs/xla_rewrite/specification_size/scripts/responsibility.py']},totals=dict(cases=31,explicit_parts=dict(explicit),inferred_parts=dict(inferred),explicit_tokens=a,inferred_tokens=b,saved_tokens=a-b,reduction_percent=100*(a-b)/a),cases=rows)
out=root/'evaluation/current/specification_size/results/all_31_source_footprint.json';out.write_text(json.dumps(result,indent=2)+'\n')
lines=['# Source footprints of all 31 inference-successful rules','','This is a static recount of saved source variants, selected by the current coverage run. It is not a new compilation or validation experiment. All 31 rule identities are included regardless of the historical explicit-baseline outcome.','','| Responsibility | Original explicit TEPL | Inferred TEPL |','|---|---:|---:|']
for key,label in [('matching','Matching (LHS)'),('legality','Legality checks'),('attributes','Attribute reasoning'),('construction','Replacement construction'),('management','Other syntax')]:lines.append(f'| {label} | {explicit[key]:,} | {inferred[key]:,} |')
lines += [f'| **Total** | **{a:,}** | **{b:,}** |','',f'The difference is {a-b:,} tokens ({100*(a-b)/a:.1f}%). Saved inferred forms include normalization and compaction; the difference is not attributed solely to inference.','',*['- '+n for n in result['notes']],'','The JSON contains all counted source bytes, hashes, responsibility counts and historical acceptance flags. Original measurement files remain unchanged.','']
(root/'evaluation/current/specification_size/reports/all_31_source_footprint.md').write_text('\n'.join(lines))
print(result['totals'])
