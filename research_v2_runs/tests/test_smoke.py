"""SYNTHETIC integration smoke: features -> model -> calibration -> policy -> CI."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/representation'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/statistics'))
import rep
from training import fit_estimator,predict
from analysis_tools import optimize_policy,decide,metrics,bootstrap_contrast
from sklearn.linear_model import LogisticRegression

def test_full_synthetic_pipeline_smoke():
    rows=[]
    for person in range(30):
        for platform in ['a','b']:
            rows.append({'username':f'SYNTHETIC token {person}','fullname':f'SYNTHETIC fullname {person}','bio':f'SYNTHETIC description {person%3}','location':'SYNTHETIC place','links':'','domain':'','platform':platform,'entity':person})
    df=pd.DataFrame(rows)
    vectors=rep.fit_tfidf(df.iloc[:40].reset_index(drop=True))
    pairs=np.array([(a,b) for a in range(0,60,2) for b in range(1,60,2)],dtype=np.int32)
    pairs=np.sort(pairs,axis=1)
    X,_,_=rep.lexical_features(df,pairs,vectors)
    e=df.entity.to_numpy()
    y=(e[pairs[:,0]]==e[pairs[:,1]]).astype(np.int8)
    train=(e[pairs[:,0]]<20)&(e[pairs[:,1]]<20)
    val=(e[pairs[:,0]]>=20)&(e[pairs[:,1]]>=20)
    model,_=fit_estimator(X[train],y[train],'GBDT',dict(learning_rate=.1,max_leaf_nodes=15,max_iter=10,min_samples_leaf=5,l2_regularization=.1),42)
    p=predict(model,X[val])
    cal=LogisticRegression().fit(p[:,None],y[val])
    p=cal.predict_proba(p[:,None])[:,1]
    nsim=np.max(X[val][:,[1,8]],axis=1).astype(float)
    result=optimize_policy(p,nsim,y[val],'ga',42,budget=32)
    assert result['evaluations']==32
    out=metrics(y[val],p,decide(p,nsim,result['genome']),total_positives=10)
    assert out['total_positives']==10
    _,entities=np.unique(e[pairs[val]],return_inverse=True)
    entities=entities.reshape(-1,2)
    contrast=bootstrap_contrast(y[val],p,p,entities[:,0],entities[:,1],n_entities=10,B=32,seed=42)
    assert abs(contrast['delta'])<1e-10
