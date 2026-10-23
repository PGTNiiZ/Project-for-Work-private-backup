"""Regenerate revised result figures from persisted reviewer analysis only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'experiments/icsec_final/reviewer_revision'
OUT=Path(__file__).parent/'figures'
plt.rcParams.update({'font.size':7,'pdf.fonttype':42,'svg.fonttype':'none'})
a=json.loads((DATA/'aggregate.json').read_text())
methods=['GB17_B0','B0','B1','B2','B3','Chow']
labels=['17+B0','18+B0','B1','B2','B3','Chow']
x=np.arange(len(methods))
f,axs=plt.subplots(2,1,figsize=(3.45,2.8),layout='constrained')
for metric,label,style in [('decision_F1','Decision F1','o-'),('end_to_end_F1','Automatic F1','s--')]:
 axs[0].errorbar(x,[a[m][metric]['mean'] for m in methods],yerr=[a[m][metric]['sample_sd'] for m in methods],fmt=style,color='black' if metric=='decision_F1' else '.5',capsize=2,markersize=3,linewidth=.8,label=label)
axs[0].set_ylabel('Workflow F1'); axs[0].legend(frameon=False,fontsize=6)
axs[1].errorbar(x,[a[m]['U']['mean'] for m in methods],yerr=[a[m]['U']['sample_sd'] for m in methods],fmt='o-',color='black',capsize=2,markersize=3,linewidth=.8)
axs[1].set_ylabel('Loss U (lower better)')
for ax in axs:
 ax.set_xticks(x,labels); ax.grid(axis='y',alpha=.25); ax.spines[['top','right']].set_visible(False)
for ext in ['pdf','svg']: f.savefig(OUT/f'controlled_results.{ext}',bbox_inches='tight')
plt.close(f)
f,axs=plt.subplots(3,1,figsize=(3.45,3.6),layout='constrained',sharex=True)
for ax,seed in zip(axs,[101,202,303]):
 for method,style,color in [('B2','-', 'black'),('B3','--','.45')]:
  t=pd.read_csv(DATA/f'outer_{seed}'/f'{method}_anytime.csv')
  # Each point is an actual call; draw the observed running minimum.
  ax.step(t.evaluations,t.best_U,where='post',linestyle=style,color=color,linewidth=.9,label='Sobol' if method=='B2' else 'GA')
 ax.set_xscale('log'); ax.set_xlim(100,12000)
 tails=[pd.read_csv(DATA/f'outer_{seed}'/f'{m}_anytime.csv').query('evaluations >= 100').best_U for m in ['B2','B3']]
 lo=min(float(t.min()) for t in tails); hi=max(float(t.max()) for t in tails)
 ax.set_ylim(lo-.3,hi+.3); ax.set_title(f'Outer seed {seed}',fontsize=7); ax.set_ylabel('Best val. U')
 ax.spines[['top','right']].set_visible(False); ax.grid(alpha=.2)
axs[0].legend(frameon=False,fontsize=6)
axs[-1].set_xlabel('Realized objective evaluations (log scale)')
for ext in ['pdf','svg']: f.savefig(OUT/f'optimizer_anytime.{ext}',bbox_inches='tight')
plt.close(f)
print('Regenerated controlled_results and optimizer_anytime from aggregate.json and six traces')
