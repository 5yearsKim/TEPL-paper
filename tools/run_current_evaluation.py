#!/usr/bin/env python3
"""Rerun the paper's exact frozen tasks in an isolated TEPL source snapshot."""
import argparse, concurrent.futures, hashlib, json, os, platform, shutil, subprocess, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone
PAPER=Path(__file__).resolve().parents[1]
def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
 root=a.snapshot.resolve(); binary=a.compiler.resolve();out=PAPER/'evaluation/current'
 sys.path.insert(0,str(root/'labs/xla_rewrite/coverage'))
 from scripts import run_synthesis as runner
 runner.ROOT=root
 frozen=json.loads((PAPER/'evaluation/recorded-results.json').read_text())
 tasks=root/'labs/xla_rewrite/tepl/rules/paper_current';tasks.mkdir(exist_ok=True)
 records=[]
 for old in frozen['records']:
  row=dict(old);name=row['case'];source=frozen['source_snapshots'][name]['task'];path=tasks/(name+'.tepl');path.write_text(source)
  row['file']=str(path.relative_to(root));row['file_sha256']=sha(path)
  for key in ['check','compile','validation','seconds','outcome','search_path','artifact_sha256','validated_json','inferred_descriptors']:row.pop(key,None)
  row['previous_outcome']=old['outcome'];row['task_source']=source;records.append(row)
 save(out/'planned-tasks.json',[{'case':r['case'],'source_sha256':r['file_sha256'],'axis_fields':r['axis_fields']} for r in records])
 binary_hash=sha(binary)
 artifacts=out/'compiled';artifacts.mkdir(exist_ok=True)
 def work(row):
  result=runner.measure_case(row,binary,30,artifacts)
  print(row['case']+': '+result['outcome'],flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool: measured=list(pool.map(work,records))
 assert sha(binary)==binary_hash
 save(out/'coverage.json',dict(protocol='paper_frozen_123_current_v1',run_at_utc=datetime.now(timezone.utc).isoformat(),compiler_sha256=binary_hash,jobs=a.jobs,timeout_seconds=30,platform=platform.platform(),cpu=next(s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),records=measured))
if __name__=='__main__':main()
