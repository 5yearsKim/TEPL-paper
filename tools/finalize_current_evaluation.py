#!/usr/bin/env python3
"""Collect historical default phases and native metadata costs without replacing active results."""
import argparse,csv,hashlib,json,shutil,statistics,subprocess,time
from pathlib import Path
PAPER=Path(__file__).resolve().parents[1];OUT=PAPER/'evaluation/current';SNAP=Path('/tmp/tepl-paper-evaluation')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--snapshot',type=Path,default=SNAP);parser.add_argument('--runtime-binary',type=Path,default=PAPER.parent.parent/'tepl/bazel-bin/labs/paper_metadata_cost/metadata_cost');args=parser.parse_args()
 src=args.snapshot/'labs/reasoning_scalability/output'
 while not (src/'performance.json').exists():time.sleep(10)
 # Reporting is generated after the measurements, so wait for its completion too.
 while not (src/'performance_summary.json').exists():time.sleep(1)
 shutil.copytree(src,OUT/'scalability',dirs_exist_ok=True)
 binary=args.runtime_binary
 runtime=OUT/'runtime';records={}
 for variant in ['explicit','inferred']:
  run=subprocess.run([str(binary),str(runtime/(variant+'.json'))],capture_output=True,text=True,check=True)
  (runtime/(variant+'.samples.json')).write_text(run.stdout);records[variant]=json.loads(run.stdout)
 (runtime/'provenance.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((runtime/'metadata_cost.cc').read_bytes()).hexdigest(),warmup_batches=1,measured_batches=10,matches_per_batch=1000,order=['explicit','inferred']),indent=2)+'\n')
 lines=[r'\begin{table}[!htbp]',r'\caption{Native metadata evaluation, median microseconds per match over ten batches. Includes fresh bindings and evaluation context; excludes matching and loading.}',r'\label{tab:metadata-runtime}',r'\small',r'\begin{tabularx}{\linewidth}{@{}Yrr@{}}\toprule',r'Rank & Explicit & Inferred\\\midrule']
 for rank in [0,2,8,32,128]:
  vals={v:[r['ns_per_match']/1000 for r in rs if r['rank']==rank and r['round']>=0] for v,rs in records.items()}
  lines.append(f"{rank} & {statistics.median(vals['explicit']):.2f} & {statistics.median(vals['inferred']):.2f}"+r'\\')
 lines += [r'\bottomrule\end{tabularx}',r'\end{table}']
 (PAPER/'sections/current-runtime-summary.tex').write_text('\n'.join(lines)+'\n')
 data=json.loads((src/'performance.json').read_text());rows=json.loads((src/'performance_summary.json').read_text())['cases']
 n=sum(r['status']=='proved' for r in rows)
 phase=[r'\section{Scalability Evaluation}',r'\label{app:scalability}',
 f"The current optimized phase experiment measures 39 configurations with one warmup and ten repetitions per configuration. {n}/39 configurations prove in every measured repetition. The generator passes {data['manifest']['dense_reference_checks']} independent dense integer reference checks before timing.",
 r'Parsing, imports, and initial plan preparation are excluded. Each timed call creates fresh reasoning contexts and includes all candidate strategies, fallback, and independent verification. The global work cap is replaced by a 10-second deadline shared across these phases; local bounds remain active. Cases are shuffled in serial rounds with a fixed seed. Raw samples and machine/source provenance are retained in \code{evaluation/current/scalability/}.',
 r'\begin{figure}[!htbp]\centering',r'\includegraphics[width=\linewidth]{figures/scalability.pdf}',r'\caption{Fresh phase measurements: chain size at rank three, transpose rank, and full-auto phase cost. Successful curves show medians with minimum--maximum whiskers. Unsuccessful attempts are marked separately; hatched phase bars indicate configurations that did not prove in every repetition.}',r'\label{fig:scalability}',r'\Description{Three panels report chain cost, rank cost, and mean phase costs, distinguishing successful and unsuccessful proof attempts.}',r'\end{figure}',
 r'\begin{table}[!htbp]',r'\caption{All current phase configurations. Success is proved repetitions out of ten. Times are median milliseconds per attempt, including unresolved attempts.}',r'\label{tab:scalability-results}',r'\small',r'\begin{tabularx}{\linewidth}{@{}Yrrrr@{}}\toprule',r'Case & Success & Total & Construct & Verify\\\midrule']
 for r in rows:
  phase.append(r'\code{'+r['case_id']+'}'+f" & {r['proved_repetitions']}/10 & {r['median_total_ms']:.2f} & {r['median_construction_ms']:.2f} & {r['median_verification_ms']:.2f}"+r'\\')
 phase += [r'\bottomrule\end{tabularx}',r'\end{table}',r'The workload fixes contraction inputs to rank three and varies chain depth; the rank experiment composes three symbolic transposes into one. These synthetic cases characterize metadata proof cost, not numerical execution. Time-limited attempts do not establish infeasibility, and phase costs for failed attempts must not be interpreted as successful synthesis latency. One machine and ten repetitions provide limited evidence about variability; minimum--maximum whiskers are not confidence intervals.',r'\FloatBarrier']
 # Section 9.4 and its active figure now belong to the certified rerun.
 (OUT/'scalability/appendix-historical.tex').write_text('\n'.join(phase)+'\n')
 for filename,rs in [('phase-samples.csv',data['records']),('phase-summary.csv',rows)]:
  with (OUT/filename).open('w') as f:
   w=csv.DictWriter(f,fieldnames=rs[0].keys());w.writeheader();w.writerows(rs)
 print(json.dumps(dict(phase_fully_proved=n,phase_statuses={s:sum(r['status']==s for r in rows) for s in set(r['status'] for r in rows)},runtime_medians={v:{rank:statistics.median([r['ns_per_match']/1000 for r in rs if r['rank']==rank and r['round']>=0]) for rank in [0,2,8,32,128]} for v,rs in records.items()}),indent=2))
if __name__=='__main__':main()
