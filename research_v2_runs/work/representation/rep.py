"""Pure, label-blind text representations and cross-platform retrieval.

Inputs use positional RangeIndex rows. Fit functions accept training rows only;
feature and retrieval functions never fit on their inference dataframe.
"""
from collections import defaultdict
from itertools import combinations
import unicodedata
import numpy as np
import pandas as pd


def normalize(text):
    """NFKC, lowercase and collapse whitespace; missing scalars become empty."""
    if text is None or pd.isna(text):
        return ''
    value = ' '.join(unicodedata.normalize('NFKC', str(text)).lower().split())
    return '' if value in {'nan', 'null', 'none', '<na>'} else value


ATTRS = ('username', 'fullname', 'bio', 'location', 'links')
GENERIC_DOMAINS = frozenset({'about.me', 'twitter.com', 'facebook.com',
    'instagram.com', 'youtube.com', 'linkedin.com', 'plus.google.com',
    'google.com', 'bit.ly', 'goo.gl', 'youtu.be', 'fb.com', 't.co', 'ow.ly'})


def _check_df(df):
    if not isinstance(df.index, pd.RangeIndex) or not df.index.equals(pd.RangeIndex(len(df))):
        raise ValueError('Expected RangeIndex 0..n-1; reset rows before use')


def _texts(df, attr):
    return [normalize(x) for x in df[attr].tolist()]


def _pair_array(pairs):
    return np.asarray(pairs, dtype=np.int32).reshape(-1, 2)


def b0_pairs(df):
    """Union historical exact/prefix/domain blocks, excluding same-platform pairs."""
    _check_df(df)
    platforms = _texts(df, 'platform')
    buckets = defaultdict(list)
    for attr in ('username', 'fullname', 'links', 'domain'):
        for i, text in enumerate(_texts(df, attr)):
            keys = []
            if attr == 'username' and len(text) >= 3:
                keys.append(('exact_username', text))
            if attr in ('username', 'fullname'):
                import re
                prefix = re.sub(r'[^a-z0-9]+', '', text)[:3]
                if len(prefix) == 3:
                    keys.append((attr + '_prefix', prefix))
            elif attr == 'links' and text:
                keys.append(('links', text))
            elif attr == 'domain' and text and text not in GENERIC_DOMAINS:
                keys.append(('domain', text))
            for key in keys:
                buckets[key].append(i)
    pairs = { (a,b) for rows in buckets.values() for a,b in combinations(rows,2)
              if platforms[a] != platforms[b] }
    return _pair_array(sorted(pairs))


def _fit_vectorizer(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    v = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,4), min_df=2,
                        max_features=60000, dtype=np.float32)
    # A fixed non-text vocabulary gives zero transforms when training has no
    # eligible ngrams; never inject artificial text into the training corpus.
    try:
        v.fit(texts)
    except ValueError as exc:
        if not any(t in str(exc) for t in ('empty vocabulary', 'no terms remain',
                                           'After pruning', 'max_df corresponds')):
            raise
        v = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,4), min_df=2,
                            max_features=60000, dtype=np.float32,
                            vocabulary={'\x00\x00\x00': 0})
        v.fit([''])
    return v


def fit_tfidf(train_df):
    """Fit five independent vectorizers on training profiles only."""
    _check_df(train_df)
    return {g: _fit_vectorizer(_texts(train_df,g)) for g in ATTRS}


def _validate_pairs(pairs, n):
    p = np.asarray(pairs)
    if p.ndim != 2 or p.shape[1] != 2 or p.dtype.kind not in 'iu':
        raise ValueError('pairs must be an integer (N,2) array')
    if p.size and (p.min() < 0 or p.max() >= n):
        raise ValueError('pair index out of bounds')
    return p


def lexical_features(df, pairs, vectors):
    """Return 35 float32 features, names and per-attribute column groups.

    Pair order is preserved, including duplicate or reversed query pairs.
    """
    from rapidfuzz.distance import JaroWinkler, Levenshtein
    _check_df(df)
    p = _validate_pairs(pairs,len(df))
    X = np.zeros((len(p),35),np.float32)
    names,groups = [],{}
    suffixes = ('exact','jaro_winkler','normalized_levenshtein','token_jaccard',
                'tfidf_cosine','both_present','one_missing')
    for gi,g in enumerate(ATTRS):
        start = 7 * gi
        groups[g] = list(range(start,start+7))
        names.extend(g + '_' + s for s in suffixes)
        texts = _texts(df,g)
        if not len(p):
            continue
        mat = vectors[g].transform(texts)
        cos = np.asarray(mat[p[:,0]].multiply(mat[p[:,1]]).sum(axis=1)).ravel()
        for row,(a,b) in enumerate(p):
            s,t = texts[a],texts[b]
            both = bool(s) and bool(t)
            X[row,start+5] = both
            X[row,start+6] = bool(s) != bool(t)
            if both:
                ss,tt = set(s.split()),set(t.split())
                X[row,start:start+5] = (s==t, JaroWinkler.normalized_similarity(s,t),
                    Levenshtein.normalized_similarity(s,t),len(ss & tt)/len(ss | tt),
                    np.clip(cos[row],0,1))
    return X,names,groups


def _unit_dense(emb, n):
    e = np.asarray(emb,dtype=np.float32)
    if e.ndim != 2 or len(e) != n or not np.isfinite(e).all():
        raise ValueError('embeddings must be finite (n,d) arrays aligned to rows')
    norms = np.linalg.norm(e,axis=1,keepdims=True)
    return np.divide(e,norms,out=np.zeros_like(e),where=norms != 0)


def semantic_features(embeddings, pairs, df):
    """Six columns: fullname then bio, each cosine/both_present/one_missing."""
    _check_df(df)
    p = _validate_pairs(pairs,len(df))
    X = np.zeros((len(p),6),np.float32)
    for gi,g in enumerate(('fullname','bio')):
        e = _unit_dense(embeddings[g],len(df))
        present = np.array([bool(t) for t in _texts(df,g)])
        a,b = present[p[:,0]],present[p[:,1]]
        X[:,3*gi] = np.clip(np.einsum('ij,ij->i',e[p[:,0]],e[p[:,1]]),-1,1) * (a & b)
        X[:,3*gi+1] = a & b
        X[:,3*gi+2] = a ^ b
    return X


def profiletext(df):
    """Serialize retrieval fields with literal markers, excluding metadata."""
    _check_df(df)
    attrs = ('username','fullname','bio','location')
    cols = [_texts(df,g) for g in attrs]
    return [' '.join('[' + g + '] ' + cols[j][i] for j,g in enumerate(attrs))
            if any(c[i] for c in cols) else '' for i in range(len(df))]


def fit_retriever(train_df):
    """Fit a separate full-profile TF-IDF retriever on training rows only."""
    return _fit_vectorizer(profiletext(train_df))


def _top_indices(scores, count):
    """Partial selection with deterministic ascending-index tie breaks."""
    count = min(count,len(scores))
    if count <= 0:
        return np.empty(0,dtype=np.int64)
    if count == len(scores):
        ids = np.arange(len(scores))
    else:
        cutoff = np.partition(scores,len(scores)-count)[len(scores)-count]
        better = np.flatnonzero(scores > cutoff)
        ties = np.flatnonzero(scores == cutoff)[:count-len(better)]
        ids = np.concatenate((better,ties))
    return ids[np.lexsort((ids,-scores[ids]))]


def _proposals(sparse, dense, platforms, pool, method, output_k=None):
    """Materialize at most 256 queries by one target platform at a time."""
    result = {}
    by_platform = [np.flatnonzero(platforms == g) for g in sorted(set(platforms))]
    for src in by_platform:
        for dst in by_platform:
            if src[0] == dst[0]:
                continue
            for offset in range(0,len(src),256):
                queries = src[offset:offset+256]
                ss = (sparse[queries] @ sparse[dst].T).toarray() if sparse is not None else None
                dd = dense[queries] @ dense[dst].T if dense is not None else None
                for row,q in enumerate(queries):
                    if method == 'hybrid_union' and output_k is not None:
                        sk,dk = output_k//2,(output_k+1)//2
                    else:
                        sk = dk = pool
                    si = _top_indices(ss[row],sk) if ss is not None else []
                    di = _top_indices(dd[row],dk) if dd is not None else []
                    selected = set(map(int,si)) | set(map(int,di))
                    if method == 'hybrid_rrf':
                        scores = defaultdict(float)
                        for ranking in (si,di):
                            for rank,j in enumerate(ranking,1):
                                scores[int(j)] += 1.0/(60+rank)
                        ordered = sorted(selected,key=lambda j:(-scores[j],int(dst[j])))
                        if output_k is not None:
                            ordered = ordered[:output_k]
                    else:
                        scores = {j: float(ss[row,j]) if method == 'sparse' else
                                  float(dd[row,j]) if method == 'dense' else
                                  max(float(ss[row,j]),float(dd[row,j])) for j in selected}
                        ordered = selected
                    for j in ordered:
                        a,b = sorted((int(q),int(dst[j])))
                        result[a,b] = max(result.get((a,b),-np.inf),scores[j])
    return result


def retrieval(df, sparse_vectors, dense_embeddings, k, method, budget=None):
    """Return unique cross-platform int32 pairs ranked score-desc/pair-asc.

    sparse_vectors is a fitted full-text vectorizer from fit_retriever, NOT
    fit_tfidf's dictionary. k applies per query per other platform. Union uses
    floor(k/2) sparse and ceil(k/2) dense. RRF(c=60) retains k fused neighbours
    per directed query/platform. Undirected RRF score is the maximum directed
    fused score, avoiding duplicate-direction bonuses. Union score is the max
    sparse/dense cosine. Budget mode pools 50 per retriever, doubling until
    enough unique pairs exist, then ranks/truncates that pool (not the complete
    cross-product). All ties are broken by ascending positional canonical pair.
    """
    _check_df(df)
    if method not in {'sparse','dense','hybrid_union','hybrid_rrf'}:
        raise ValueError('unknown retrieval method')
    if not isinstance(k,(int,np.integer)) or k < 0:
        raise ValueError('k must be a nonnegative integer')
    if budget is not None and (not isinstance(budget,(int,np.integer)) or budget < 0):
        raise ValueError('budget must be a nonnegative integer')
    platforms = np.asarray(_texts(df,'platform'))
    counts = [int(np.sum(platforms == g)) for g in set(platforms)]
    possible = sum(a*b for a,b in combinations(counts,2))
    if budget is not None and budget > possible:
        raise ValueError('budget exceeds possible unique cross-platform pairs')
    if budget == 0 or (budget is None and k == 0) or not possible:
        return _pair_array([])
    sparse = sparse_vectors.transform(profiletext(df)) if method != 'dense' else None
    dense = _unit_dense(dense_embeddings,len(df)) if method != 'sparse' else None
    if budget is None:
        scores = _proposals(sparse,dense,platforms,k,method,output_k=k)
    else:
        pool = 50
        while True:
            scores = _proposals(sparse,dense,platforms,pool,method)
            if len(scores) >= budget:
                break
            if pool >= max(counts):
                raise ValueError('budget could not be satisfied')
            pool *= 2
    ordered = sorted(scores,key=lambda p:(-scores[p],p))
    return _pair_array(ordered if budget is None else ordered[:budget])
