#!/usr/bin/env python3
"""Static semantic-representation audit; does not run or verify TEPL rules."""
from pathlib import Path
from collections import defaultdict
import csv,json
root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'rules.csv').open()))
# Current paper profile: hlo.tepl value/axis clauses and AxisViews singleton
# reduction. Unit-normalized entries are port candidates, not validated ports.
M={
'AS-5165':('direct','catalog_broadcast_multiply_constant_into_broadcast','Product and broadcast semantics; an accepted algebraic counterpart exists.'),
'AS-2614':('direct','catalog_broadcast_divide_broadcast','Divide, Product and broadcast have value semantics. Existing counterpart is modeled but its default proof is unresolved.'),
'AS-10187':('direct','dot_transpose_output;dot_swap_operands','Dot and transpose value/axis contracts; existing counterparts retain output-order/batch conditions.'),
'AS-2478':('direct','expr_divide_one','Pointwise divide and fixed literal one; host retains literal/splat recognition.'),
'AS-2824':('direct','catalog_broadcast_transpose_broadcast','Transpose/broadcast coordinate contracts.'),
'AS-9840':('direct','HLO.select','Select has a value clause. Fixed false predicate; host retains literal/splat recognition. This exact workload port has not been checked.'),
'AS-1405':('direct','catalog_elementwise_and_true','Boolean and has a value clause and a scalar accepted counterpart; retain source PRED/literal conditions.'),
'AS-3785':('direct','dot_no_contraction','Dot without contraction is representable using Product and Broadcast. Keep source precision/type conditions.'),
'AS-5025':('direct','expr_multiply_one','Pointwise Product and fixed one; host retains literal/splat recognition.'),
'AS-5056':('direct','multiply_negatives','Negate and Product have value clauses; existing algebraic counterpart.'),
'AS-5132':('direct','multiply_constants','Product reassociation is represented with captured constants; retain arithmetic policy and host constant recognition.'),
'AS-8870':('direct','reduce_negate','Source branch explicitly checks add combiner and zero initializer, matching reduce_sum and Negate.'),
'AS-10114':('direct','transpose_identity','Permutation identity guard and transpose contract.'),
'AS-10118':('direct','transpose_compose','Transpose composition contract and accepted counterpart.'),
'AS-5605':('unit_view_candidate','HLO.broadcast;AxisViews','Positive-size element-count-preserving sorted broadcast inserts only unit axes. Model output reshape as a unit-axis view; audit zero-element cases separately.'),
'AS-5645':('unit_view_candidate','catalog_broadcast_inserted_unit_dims','Source reshape is restricted to inserting unit axes; normalize it as a broadcast/view. Existing representative case is narrower than full branch.'),
'AS-5723':('unit_view_candidate','catalog_broadcast_drop_unit_dims','Source explicitly removes only size-one axes. Existing AxisViews.remove_unit_axes models this restriction.'),
'AS-2742':('unit_view_candidate','AxisViews;HLO.dot_general','Dot operand reshapes remove only unit dimensions. Needs a restricted view-normalized port; no claim of general reshape support.'),
'AS-2744':('unit_view_candidate','AxisViews;HLO.dot_general;HLO.broadcast','Remove unit dimensions from operands and restore result unit dimensions; needs view-normalized port and guards.'),
'AS-6744':('unit_view_candidate','AxisViews','Shape-preserving reshape can normalize to identity (empty unit-axis removal); native general reshape has no value clause.'),
'AS-5681':('conditional','scalar_broadcast_transpose;scalar_broadcast_reverse','One source branch covers several indexing/permutation operations. Only modeled cases are supported; event log does not identify the affected operation for each of five applications.'),
'AS-6358':('conditional','broadcast_add;broadcast_multiply','Source accepts generic elementwise f, including operations without a current value contract. Need the concrete user opcode; it was not logged.'),
'AS-5761':('conditional','HLO.compare','Compare operation is modeled, but general IsNonNegative value-analysis facts are not supplied to TEPL by the current rule interface.'),
'AS-5767':('conditional','HLO.compare','Same missing nonnegative-value applicability fact; predicate semantics alone does not validate this rewrite.'),
'AS-2590':('conditional','HLO.divide;HLO.multiply','Arithmetic expressions are representable, but the source branch evaluates and materializes a reciprocal constant payload; general literal-value lowering is missing.'),
'AS-8661':('conditional','HLO.reduce_sum;AxisViews','Unit-axis reduction can use current semantics for zero-initialized sum, but the source helper accepts generic reducers. Reducer/init details for the 22 applications were not logged.'),
'AS-6750':('outside','HLO.reshape','General reshape composition requires coordinate linearization; reshape declaration has no value/axis semantics.'),
'AS-5389':('outside','tuple/get_tuple_element','No tuple/projection tensor-value contracts in the current HLO semantic profile.'),
'AS-9023':('outside','HLO.reshape;HLO.reduce','Source combines general reshape and generic reduction. Both exceed the current profile; restricted specializations would be new ports.'),
'AS-6898':('outside','HLO.reshape','Existing native reshape declaration has no value semantics. A context-specific broadcast-only coordinate adapter would require an additional semantic port beyond existing unit views.'),
'AS-2317':('outside','HLO.iota;literal payload','Iota has shape/dtype declarations only; coordinate-to-value and general literal-payload semantics are missing.'),
'AS-6945':('outside','HLO.iota;HLO.reshape','Iota coordinate values and mixed-radix reshape semantics are missing.'),
}
assert set(M)=={r['rule_id'] for r in rows}
audit=[];counts=defaultdict(lambda:dict(rule_variants=0,applications=0))
for r in rows:
 status,evidence,reason=M[r['rule_id']]
 r=dict(r);r['applications']=int(r['applications']);r.update(semantic_status=status,evidence=evidence,reason=reason)
 audit.append(r);counts[status]['rule_variants']+=1;counts[status]['applications']+=r['applications']
with (root/'semantic-support.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0]));w.writeheader();w.writerows(audit)
summary=dict(scope='Static semantic representation under the paper HLO and AxisViews profiles, with existing XLA literal/type/precision checks retained. Not a standalone TEPL matcher/guard port or successful validation count.',total_rule_variants=32,total_applications=201,categories=dict(counts),direct_semantic_variants=counts['direct']['rule_variants'],additional_unit_view_candidates=counts['unit_view_candidate']['rule_variants'],direct_plus_unit_view_candidates=counts['direct']['rule_variants']+counts['unit_view_candidate']['rule_variants'],important_limit='Applications are weights attached to source variants, not verified supported workload applications. Conditional source sites cover multiple operations/reducers and the previous event log lacks per-application details.',xla_reruns=0,tepl_checks_run=0)
(root/'semantic-support-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
