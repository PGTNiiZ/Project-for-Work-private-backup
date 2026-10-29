"""Train-only negative sampling and scaling for frozen classical learners."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def fit_estimator(X,y,learner,params,seed=42):
    X=np.asarray(X,dtype=np.float32)
    y=np.asarray(y,dtype=np.int8)
    if len(X)!=len(y) or set(np.unique(y))!={0,1}:
        raise ValueError('training scope must contain aligned positive and negative labels')
    rng=np.random.default_rng(seed)
    pos=np.flatnonzero(y==1)
    neg=np.flatnonzero(y==0)
    neg=rng.choice(neg,size=min(len(neg),3*len(pos)),replace=False)
    ix=np.sort(np.r_[pos,neg])
    if learner=='GBDT':
        model=HistGradientBoostingClassifier(**params,early_stopping=False,random_state=seed)
    elif learner=='LR':
        model=make_pipeline(StandardScaler(),LogisticRegression(**params,max_iter=500,random_state=seed))
    else:
        raise ValueError('learner not in frozen classical configuration')
    model.fit(X[ix],y[ix])
    return model,{'training_rows':int(len(ix)),'training_positives':int(len(pos)),'training_negatives':int(len(neg)),'train_negative_ratio_limit':3}


def attribute_columns(schema,n_columns,group=None,exclude_group=None):
    def indices(name):
        base=len(schema['lexical_names'])
        return [*schema['groups'][name],*[base+i for i,n in enumerate(schema['semantic_names']) if n.startswith(name+'_') and base+i<n_columns]]
    if group is not None:
        return indices(group)
    if exclude_group is not None:
        dropped=set(indices(exclude_group))
        return [i for i in range(n_columns) if i not in dropped]
    return list(range(n_columns))


def predict(model,X):
    return model.predict_proba(np.asarray(X,dtype=np.float32))[:,1].astype(np.float64)
