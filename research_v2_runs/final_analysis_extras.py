"""Additional predeclared aggregate diagnostics on frozen artifacts only."""
from pathlib import Path
import json
import numpy as np
from sklearn.metrics import average_precision_score
from runtime import job,commit_files
from integrity import sha256
R=Path(__file__).resolve().parent


def main():
    commit_files([R/'final_analysis_extras.py'],'Register frozen-artifact blocking recovery and supporting summary diagnostics')
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    hybrid=np.load(R/f"data_derived/final/blocking-{lock['selection']['hybrid']}.npz")
    rows=[]
    for method in ['B0',lock['selection']['best_lexical']]:
        baseline=np.load(R/f'data_derived/final/blocking-{method}.npz')
        assert np.array_equal(hybrid['gt_pairs'],baseline['gt_pairs'])
        recovered=int((hybrid['found']&~baseline['found']).sum())
        lost=int((~hybrid['found']&baseline['found']).sum())
        missed=int((~baseline['found']).sum())
        rows.append({'baseline':method,'hybrid':lock['selection']['hybrid'],'recovered_positives':recovered,'lost_positives':lost,'baseline_missed_positives':missed,'recovery_fraction_of_baseline_misses':recovered/missed if missed else 0.,'GT_denominator':len(hybrid['gt_pairs'])})
    with job('E1-5','frozen-final-blocking-recovery',{'metric':'recovery fraction of missed positives','population':'same frozen GT pairs; no test reopening'},category='aggregate_statistics') as rec:
        rec['rows']=rows
    meta=np.load(R/'data_derived/representation/pair_metadata_dev.npz')
    for path in sorted((R/'metrics').glob('model_*.json')):
        summary=json.loads(path.read_text())
        name=summary['name']
        metric=R/f"metrics/{summary['exp_id']}--ensemble-summary-{name}.json"
        if metric.exists():continue
        with job(summary['exp_id'],'ensemble-summary-'+name,{'summary_sha256':sha256(path),'oof_sha256':summary['oof_sha256'],'aggregation':'all frozen seeds'},validation_evals=1,category='aggregate_statistics') as rec:
            scores=np.load(R/summary['oof_path'])['mean']
            value=float(average_precision_score(meta['y'],scores))
            if not np.isclose(value,summary['mean_score_AP']):raise ValueError('supporting ensemble summary mismatch')
            rec.update({'candidate_AP':value,'summary_sha256':sha256(path),'name':name,'ARTIFACT_CHECK':'ARTIFACT_CONSISTENT'})

if __name__=='__main__':main()
