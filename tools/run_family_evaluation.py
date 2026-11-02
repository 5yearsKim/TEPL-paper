#!/usr/bin/env python3
"""Fixed symbolic rewrite family cases, without fixed-rank specializations."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
PAPER=Path(__file__).resolve().parents[1]
CASES=[
 ('batched_reassociation',8,'(outer: dot (inner: dot X Y) Z) => (dot X (dot Y Z))','outer.attrs.lhs_batching_dimensions == inner.axes.B.positions'),
 ('sum_move',5,'(dot (reduce_sum X) Y) => (reduce_sum (dot X Y))',''),
 ('transpose_reduce',2,'(reduce_sum (transpose X)) => (transpose (reduce_sum X))',''),
 ('sum_distribute',2,'(reduce_sum (add X Y)) => (add (reduce_sum X) (reduce_sum Y))',''),
 ('dot_distribute',8,'(dot (add X Y) Z) => (add (dot X Z) (dot Y Z))',''),
 ('merge_reductions',1,'(reduce_sum (reduce_sum X)) => (reduce_sum X)','')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);a=p.parse_args()
 out=PAPER/'evaluation/current/families';out.mkdir(parents=True,exist_ok=True)
 dialect=(a.snapshot/'examples/semantic/dialects/tensor.tepl').read_text()
 (out/'dialects').mkdir(exist_ok=True);(out/'dialects/tensor.tepl').write_text(dialect);(out/'tepl.toml').write_text('tepl-version = "0.1.0"\n')
 plan=[dict(case=n,fields=f,pattern=s,guard=g) for n,f,s,g in CASES];(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 records=[]
 for n,f,s,g in CASES:
  source='from "dialects/tensor.tepl" import TensorLang as t;\nuse t::{dot, reduce_sum, transpose, add};\nrule '+n+' {\n '+s+('\n where { '+g+' }' if g else '')+'\n}\n'
  file=out/(n+'.tepl');file.write_text(source)
  row=dict(case=n,requested_fields=f,source=source,source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),commands=[])
  for cmd in [['check',str(file),'--semantic-policy','algebraic','--rule',n],['compile',str(file),'--semantic-policy','algebraic','-o',str(out/(n+'.json'))],['validate',str(out/(n+'.json'))]]:
   start=time.perf_counter()
   try:
    r=subprocess.run([str(a.compiler),*cmd],text=True,capture_output=True,timeout=30);entry=dict(command=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.perf_counter()-start)
   except subprocess.TimeoutExpired:entry=dict(command=cmd,returncode=None,stdout='',stderr='timeout',seconds=time.perf_counter()-start)
   row['commands'].append(entry)
   if entry['returncode']!=0:break
  row['accepted']=len(row['commands'])==3 and all(c['returncode']==0 for c in row['commands']) and 'status=proved' in row['commands'][0]['stdout'] and 'additional-guard: true' in row['commands'][0]['stdout']
  print(n,row['accepted'],flush=True);records.append(row)
 (out/'results.json').write_text(json.dumps(dict(compiler_sha256=hashlib.sha256(a.compiler.read_bytes()).hexdigest(),records=records),indent=2)+'\n')
if __name__=='__main__':main()
