#!/usr/bin/env python3
"""Plot saved measurements only; never rerun inference."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'evaluation/current/scalability/performance_summary.json').read_text())['cases']
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arimo','DejaVu Sans'],'font.size':11,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(6.5,5.5));grid=fig.add_gridspec(2,2,hspace=.70,wspace=.42)
colors={'explicit':'#356B8C','partial':'#358579','automatic':'#BC6743'}
names={'explicit':'Explicit','partial':'Partial auto','automatic':'Full auto'}
for col,fam in enumerate(['chain','rank']):
 ax=fig.add_subplot(grid[0,col])
 for mode in ['explicit','partial','automatic']:
  rs=sorted([r for r in rows if r['family']==fam and r['mode']==mode],key=lambda r:r['size'])
  if not rs:continue
  scale=1000 if fam=='chain' else 1
  good=[r for r in rs if r['status']=='proved'];bad=[r for r in rs if r['status']!='proved']
  ax.plot([r['size'] for r in rs],[r['median_total_ms']/scale if r['status']=='proved' else float('nan') for r in rs],marker='o',markersize=3,label=names[mode],color=colors[mode])
  ax.errorbar([r['size'] for r in good],[r['median_total_ms']/scale for r in good],yerr=[[(r['median_total_ms']-r['min_total_ms'])/scale for r in good],[(r['max_total_ms']-r['median_total_ms'])/scale for r in good]],fmt='none',color=colors[mode],capsize=2,lw=.8)
  ax.scatter([r['size'] for r in bad],[r['median_total_ms']/scale for r in bad],marker='x',color=colors[mode],s=22)
 ax.grid(axis='y',alpha=.2);ax.tick_params(labelsize=9)
 if fam=='chain':
  ax.set_yscale('log');ax.set_xticks([1,2,4,6,8,10]);ax.set_xlabel('Dots per side');ax.set_ylabel('Attempt time (s, log scale)');ax.set_title('(a) Chain length',loc='left',fontsize=12)
  ax.scatter([],[],marker='x',color=colors['automatic'],label='Deadline reached');ax.legend(fontsize=8,loc='lower right',frameon=False)
 else:
  ax.set_xscale('log',base=2);ax.set_xticks([2,4,8,16,32]);ax.xaxis.set_major_formatter(ScalarFormatter());ax.set_xlabel('Tensor rank');ax.set_ylabel('Pipeline time (ms)');ax.set_title('(b) Transpose rank',loc='left',fontsize=12)
ax=fig.add_subplot(grid[1,:]);rs=sorted([r for r in rows if r['family']=='chain' and r['mode']=='automatic'],key=lambda r:r['size']);bottom=[0]*len(rs)
for field,label,color in [('construction_ms','Construction','#356B8C'),('verification_ms','Verification','#BC6743'),('other_ms','Other','#B5B8BD')]:
 vals=[r['mean_'+field]/1000 for r in rs];ax.bar([r['size'] for r in rs],vals,bottom=bottom,color=color,width=.68,label=label);bottom=[a+b for a,b in zip(bottom,vals)]
for r in rs:
 if r['status']!='proved':ax.bar(r['size'],r['mean_total_ms']/1000,width=.68,facecolor='none',edgecolor='black',linewidth=.5,hatch='///')
handles,labels=ax.get_legend_handles_labels();handles.append(Patch(facecolor='white',edgecolor='black',hatch='///'));labels.append('Deadline reached')
ax.legend(handles,labels,ncol=4,loc='lower left',bbox_to_anchor=(0,1.0),fontsize=8,frameon=False)
ax.set_xticks(range(1,11));ax.set_xlabel('Dots per side');ax.set_ylabel('Mean attempt time (s)');ax.set_title('(c) Full-auto phase cost',loc='left',fontsize=12,pad=30);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.savefig(root/'evaluation/current/scalability/figures/scalability.pdf',bbox_inches='tight');fig.savefig(root/'evaluation/current/scalability/figures/paper-scalability.png',dpi=180,bbox_inches='tight')
