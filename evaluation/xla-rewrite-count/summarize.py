#!/usr/bin/env python3
"""Convert raw success notifications to audited transformation applications."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json
root=Path(__file__).resolve().parent
raw=json.loads((root/'raw-results.json').read_text())
by_line={r['original_line']:r for r in raw['rules']}
# This is visitor-state bookkeeping immediately before the same branch's
# successful ReplaceWithNewInstruction at original line 9023. It is not
# another rewrite. Every completed branch has exactly one of each record.
assert by_line.get(9009,{}).get('applications',0)==by_line.get(9023,{}).get('applications',0)
labels={
1405:('boolean','true && x -> x'),
5605:('broadcast','element-count-preserving broadcast -> reshape'),
5645:('broadcast','remove unit-inserting reshape before broadcast'),
5681:('broadcast','permutation/subset of scalar broadcast -> broadcast'),
5723:('broadcast','remove unit dimensions from broadcast operand'),
5761:('compare','known nonnegative x < 0 -> false'),
5767:('compare','known nonnegative x >= 0 -> true'),
2317:('constant','iota-valued literal -> iota'),
2478:('divide','x / 1 -> x'),
2614:('divide','divide by broadcast -> multiply by broadcast reciprocal'),
5389:('tuple','get_tuple_element(tuple(...), i) -> operand i'),
5025:('multiply','x * 1 -> x'),
5056:('multiply','(-x) * (-y) -> x * y'),
5132:('multiply','reassociate multiplication of constants'),
5165:('multiply','move scalar constant into broadcasted multiply'),
8870:('reduce','move negate through sum reduction'),
9023:('reduce','move reshape through reduction'),
6744:('reshape','remove shape-preserving reshape'),
6750:('reshape','compose consecutive reshapes'),
6898:('reshape','reshape(broadcast(x)) -> broadcast(x)'),
6945:('reshape','reshape(iota) -> coordinate arithmetic'),
9840:('select','select(false, x, y) -> y'),
10114:('transpose','remove identity transpose'),
10118:('transpose','compose consecutive transposes'),
2742:('dot','remove unit dimensions from dot; unchanged output shape'),
2744:('dot','remove unit dimensions from dot; reshape output'),
8661:('reduce','element-count-preserving reduction -> reshape'),
3785:('dot','dot without contracting dimensions -> broadcast multiply'),
2824:('transpose','transpose(broadcast(x)) -> broadcast(x)'),
6358:('broadcast','sink elementwise operation through broadcasts; per user'),
2590:('divide','division by constant -> multiplication by reciprocal'),
10187:('transpose','transpose(dot(x, y)) -> dot(y, x)'),
}
rows=[]
for r in raw['rules']:
 line=r['original_line']
 if line==9009:continue
 family,label=labels[line]
 rows.append(dict(rule_id=f'AS-{line}',family=family,description=label,**r))
rows.sort(key=lambda r:(-r['applications'],r['original_line']))
assert sum(r['applications'] for r in rows)==raw['total_applications']-by_line.get(9009,{}).get('applications',0)
assert len(rows)==len(raw['rules'])-(9009 in by_line)
with (root/'rules.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['rule_id','family','description','function','original_line','applications']);w.writeheader();w.writerows(rows)
families=defaultdict(lambda:dict(distinct_rule_variants=0,applications=0))
for r in rows:
 families[r['family']]['distinct_rule_variants']+=1;families[r['family']]['applications']+=r['applications']
summary=dict(workload='DLRM FP32 training step',batch=6272,scope=raw['scope'],model_compilations=raw['model_compilations'],pass_invocations=raw['pass_invocations'],distinct_rule_variants=len(rows),total_applications=sum(r['applications'] for r in rows),rule_identity=raw['rule_identity'],normalization=dict(raw_notifications=raw['total_applications'],excluded_bookkeeping_line=9009,paired_replacement_line=9023,excluded_notifications=by_line.get(9009,{}).get('applications',0),reason='MarkAsChanged followed by successful replacement in the same reduce/reshape rewrite branch; count the rewrite once.'),families=dict(sorted(families.items())),rules=rows,tepl_support_classification='Not measured')
if (root/'semantic-support-summary.json').exists():
 summary['tepl_support_classification']='Static semantic audit only; TEPL validation and delegation remain unmeasured'
 summary['semantic_audit']='semantic-support-summary.json'
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['rules','families']},indent=2))
