"""SYNTHETIC classifier contract (no project data)."""
from pathlib import Path
import sys
import importlib.util
import pytest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_train_only_scaling_sampling_and_scoring():
    if importlib.util.find_spec('training') is None:
        pytest.fail('fold-isolated classifier implementation missing')
    from training import fit_estimator,predict
    rng=np.random.default_rng(42)
    X=rng.normal(size=(200,4)).astype(np.float32)
    y=(X[:,0]+X[:,1]>0).astype(np.int8)
    for learner,params in [('GBDT',dict(learning_rate=.1,max_leaf_nodes=15,max_iter=10,min_samples_leaf=5,l2_regularization=.1)),('LR',dict(C=1.,class_weight=None))]:
        model,meta=fit_estimator(X[:160],y[:160],learner,params,seed=42)
        prob=predict(model,X[160:])
        assert prob.shape==(40,) and np.all((prob>=0)&(prob<=1))
        assert meta['training_rows']<=160
        assert meta['training_positives']==int(y[:160].sum())


def test_leave_one_attribute_out_removes_its_semantic_features_too():
    import training
    assert hasattr(training,'attribute_columns'), 'attribute-wide ablation selector missing'
    schema={'lexical_names':[str(i) for i in range(35)],'groups':{'fullname':list(range(7,14)),'bio':list(range(14,21))},'semantic_names':['fullname_cosine','fullname_both_present','fullname_one_missing','bio_cosine','bio_both_present','bio_one_missing']}
    kept=training.attribute_columns(schema,41,exclude_group='fullname')
    assert len(kept)==31
    assert not set(kept)&set(list(range(7,14))+[35,36,37])
    assert all(i in kept for i in [38,39,40])
