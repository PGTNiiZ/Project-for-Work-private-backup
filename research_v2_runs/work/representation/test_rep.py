"""Synthetic-only representation contracts; no profile files are opened."""
import importlib
import numpy as np
import pandas as pd
import pytest


def frame(**values):
    n = len(next(iter(values.values()))) if values else 0
    d = {c: [''] * n for c in ['username','fullname','bio','location','links','domain','platform']}
    d.update(values)
    return pd.DataFrame(d)


def test_b0_blocking_label_blind():
    import rep
    df = frame(username=['a-bc', 'abcx', '', '', '', '', ''],
               fullname=['', '', '', '', '', '', ''],
               links=['', '', 'site/x', 'site/x', '', '', ''],
               domain=['', '', '', '', 'custom.test', 'custom.test', 'google.com'],
               platform=['a','b','a','b','a','b','b'])
    p = rep.b0_pairs(df)
    assert p.dtype == np.int32
    assert p.tolist() == [[0,1], [2,3], [4,5]]
    assert rep.b0_pairs(frame(username=['ab','ab'], platform=['a','b'])).shape == (0,2)
    with pytest.raises(ValueError, match='RangeIndex'):
        rep.b0_pairs(df.set_axis(range(10,17)))


def test_lexical_train_only_and_missing_alignment():
    import rep
    train = frame(username=['alpha','alpha'], fullname=['test name','test name'])
    vectors = rep.fit_tfidf(train)
    assert set(vectors) == set(rep.ATTRS)
    assert all(v.min_df == 2 and v.dtype == np.float32 for v in vectors.values())
    before = {g: dict(v.vocabulary_) for g,v in vectors.items()}
    df = frame(username=['alpha','','alpha','zzzz'], fullname=['','','',''])
    pairs = np.array([[0,2],[1,3],[1,1],[3,0]], dtype=np.int32)
    X,names,groups = rep.lexical_features(df,pairs,vectors)
    assert X.shape == (4,35) and X.dtype == np.float32
    np.testing.assert_allclose(X[0,:7], np.ones(7) * [1,1,1,1,1,1,0], atol=1e-6)
    np.testing.assert_array_equal(X[1,:7], [0,0,0,0,0,0,1])
    assert not X[2].any()
    assert X[3,0] == 0 and X[3,5] == 1
    assert groups['username'] == list(range(7)) and len(names) == len(set(names)) == 35
    assert before == {g: dict(v.vocabulary_) for g,v in vectors.items()}
    assert vectors['username'].transform(['zzzz']).nnz == 0
    empty = rep.fit_tfidf(frame(username=[]))
    assert all(v.transform(['']).nnz == 0 for v in empty.values())
    assert rep.lexical_features(df, np.empty((0,2),int), vectors)[0].shape == (0,35)


def test_semantic_masks_and_zero_embeddings():
    import rep
    df = frame(fullname=['present','','other','present'],bio=['','','b','b'])
    emb = np.array([[2,0],[9,0],[0,0],[2,0]],np.float32)
    pairs = np.array([[0,3],[0,1],[1,1],[0,2]],np.int32)
    X = rep.semantic_features({'fullname':emb,'bio':emb},pairs,df)
    assert X.dtype == np.float32 and X.shape == (4,6)
    np.testing.assert_array_equal(X[:,:3],[[1,1,0],[0,0,1],[0,0,0],[0,1,0]])
    assert np.isfinite(X).all()


@pytest.mark.parametrize('method',['sparse','dense','hybrid_union','hybrid_rrf'])
def test_retrieval_crossplatform_budget_deterministic(method):
    import rep
    df = frame(username=['alpha','beta','alpha','beta'],platform=['a','a','b','b'])
    v = rep.fit_retriever(df)
    emb = np.array([[1,0],[0,1],[1,0],[0,1]],np.float32)
    p = rep.retrieval(df,v,emb,1,method)
    assert sorted(p.tolist()) == [[0,2],[1,3]]
    full = rep.retrieval(df,v,emb,1,method,budget=3)
    assert full.shape == (3,2) and full.dtype == np.int32
    assert sorted(full[:2].tolist()) == [[0,2],[1,3]]
    assert len(set(map(tuple,full))) == 3 and (full[:,0]<full[:,1]).all()
    assert all(df.platform[a] != df.platform[b] for a,b in full)
    np.testing.assert_array_equal(full,rep.retrieval(df,v,emb,1,method,budget=3))
    with pytest.raises(ValueError,match='budget'):
        rep.retrieval(df,v,emb,1,method,budget=5)
    assert rep.retrieval(df,v,emb,0,method).shape == (0,2)


def test_retrieval_ties_zero_and_per_other_platform():
    import rep
    df = frame(username=['']*6,platform=['a','a','b','b','c','c'])
    v = rep.fit_retriever(df)
    z = np.zeros((6,3),np.float32)
    p = rep.retrieval(df,v,z,1,'dense')
    assert p.tolist() == [[0,2],[0,3],[0,4],[0,5],[1,2],[1,4],[2,4],[2,5],[3,4]]
    assert rep.retrieval(df,v,z,1,'dense',budget=12).shape == (12,2)
    with pytest.raises(ValueError):
        rep.retrieval(df,v,z[:-1],1,'dense')


def test_dense_ranking_matches_independent_full_oracle():
    import rep
    from itertools import combinations
    rng = np.random.default_rng(19)
    df = frame(username=['synthetic']*15,platform=['a']*5+['b']*5+['c']*5)
    emb = rng.normal(size=(15,8)).astype(np.float32)
    emb /= np.linalg.norm(emb,axis=1,keepdims=True)
    # Reproduce float32 normalization performed at the public boundary.
    unit = emb / np.linalg.norm(emb,axis=1,keepdims=True)
    allpairs = [(a,b) for a,b in combinations(range(15),2) if df.platform[a]!=df.platform[b]]
    scores = unit @ unit.T
    expected = sorted(allpairs,key=lambda p:(-float(scores[p]),p))[:20]
    actual = rep.retrieval(df,None,emb,2,'dense',budget=20)
    assert actual.tolist() == [list(p) for p in expected]


def test_budget_pool_extends_and_batch_boundary():
    import rep
    df = frame(username=['']*522,platform=['a']*261+['b']*261)
    dense = np.zeros((522,2),np.float32)
    p = rep.retrieval(df,None,dense,1,'dense',budget=68000)
    assert p.shape == (68000,2)
    assert len(set(map(tuple,p))) == 68000
    assert p.tolist() == sorted(p.tolist())


def test_label_column_never_accessed_and_duplicate_pair_order():
    import rep
    class Guard(pd.DataFrame):
        def __getitem__(self,key):
            if isinstance(key,str) and key == 'entity':
                raise AssertionError('label access')
            return super().__getitem__(key)
    df = Guard(frame(username=['same','same'],fullname=['name','name'],
                     bio=['bio','bio'],platform=['a','b']))
    df['entity'] = [123,456]
    vectors = rep.fit_tfidf(df)
    p = np.array([[1,0],[0,1],[1,0]],np.int32)
    X,_,_ = rep.lexical_features(df,p,vectors)
    np.testing.assert_array_equal(X[0],X[1])
    np.testing.assert_array_equal(X[0],X[2])
    v = rep.fit_retriever(df)
    for method in ['sparse','dense','hybrid_union','hybrid_rrf']:
        assert rep.retrieval(df,v,np.ones((2,3)),1,method).tolist() == [[0,1]]
    assert rep.b0_pairs(df).tolist() == [[0,1]]
    assert rep.semantic_features({'fullname':np.ones((2,2)),'bio':np.ones((2,2))},p,df).shape == (3,6)
    with pytest.raises(ValueError,match='out of bounds'):
        rep.lexical_features(df,np.array([[0,2]]),vectors)


def test_normalization_contract():
    rep = importlib.import_module('rep')
    assert rep.normalize('  ＡＢＣ\t Foo\n') == 'abc foo'
    for value in [None, np.nan, pd.NA, 'NaN', ' NULL ', 'none', '']:
        assert rep.normalize(value) == ''
