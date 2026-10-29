"""Trace development-only univariate and ensemble aggregates to the ledger."""
from pathlib import Path
import json
import sys
import numpy as np
from sklearn.metrics import average_precision_score
from runtime import job,commit_files
from integrity import sha256
R=Path(__file__).resolve().parent
D=R/'data_derived/representation'


def main():
    commit_files([R/'aggregate_pretest.py'],'Register development feature and ensemble aggregate evidence')
    meta=np.load(D/'pair_metadata_dev.npz')
    y,fold=meta['y'],meta['fold']
    schema=json.loads((D/'feature_schema.json').read_text())
    X=np.zeros((len(y),len(schema['lexical_names'])),np.float32)
    for f in range(4):
        data=np.load(D/f'lexical_dev_cv{f}.npy',mmap_mode='r')
        X[fold==f]=data[fold==f]
    with job('E2-1','univariate-OOF-lexical',{'feature_names':schema['lexical_names'],'fit_scope':'train profiles only per held development fold'},validation_evals=len(schema['lexical_names']),category='aggregate_statistics') as rec:
        rec['features']=[{'feature':name,'candidate_AP':float(average_precision_score(y,X[:,i]))} for i,name in enumerate(schema['lexical_names'])]
        rec['n_pairs']=len(y)
        rec['positive_pairs']=int(y.sum())
    sem=np.load(D/'semantic_dev.npy',mmap_mode='r')
    with job('E4-1','univariate-semantic',{'feature_names':schema['semantic_names'],'encoder_revision':json.loads((R/'protocol.json').read_text())['encoder']['revision']},validation_evals=len(schema['semantic_names']),category='aggregate_statistics') as rec:
        rec['features']=[{'feature':name,'candidate_AP':float(average_precision_score(y,sem[:,i]))} for i,name in enumerate(schema['semantic_names'])]
        rec['n_pairs']=len(y)
    (R/'manifests/feature_schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    for path in sorted((R/'metrics').glob('model_*.json')):
        summary=json.loads(path.read_text())
        if not summary.get('oof_path'): continue
        key=summary['name']
        if (R/f"metrics/{summary['exp_id']}--ensemble-summary-{key}.json").exists(): continue
        with job(summary['exp_id'],'ensemble-summary-'+key,{'source_summary_sha256':sha256(path),'OOF_sha256':summary['oof_sha256'],'aggregation':'mean of every declared seed score'},validation_evals=1,category='aggregate_statistics') as rec:
            data=np.load(R/summary['oof_path'])
            ap=float(average_precision_score(y,data['mean']))
            reported=summary.get('mean_score_AP',summary.get('development_metrics',{}).get('candidate_ap'))
            if reported is not None and not np.isclose(ap,reported): raise ValueError('ensemble summary AP mismatch')
            rec.update({'candidate_AP':ap,'name':key,'source_summary':str(path.relative_to(R)),'source_summary_sha256':sha256(path),'n_pairs':len(y),'seed_count':len(data['seeds']),'ARTIFACT_CHECK':'ARTIFACT_CONSISTENT'})

if __name__=='__main__': main()
