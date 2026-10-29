"""Label-blind multi-pass blocking and feature-defined miss diagnostics.
POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY. No labels are used by any retrieval function."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'work/representation'))
import rep

HIGH, LOW_NAME, LOW_SIGNAL = 0.85, 0.5, 0.2
PASSES = ('username_tfidf', 'fullname_tfidf', 'cross_field_username_fullname', 'link_domain_key')


def assign_causes(flags):
    n = len(flags['u'])
    result = np.full(n, 'f', dtype='<U1')
    tests = {
        'e': (flags['max_text'] < LOW_SIGNAL) & ~flags['link'],
        'd': flags['link'] & (flags['max_text'] < HIGH),
        'c': flags['missing'],
        'a': (flags['u'] >= HIGH) & (flags['n'] < LOW_NAME),
        'b': flags['cross'] >= HIGH,
    }
    assigned = np.zeros(n, bool)
    for key in ['e', 'd', 'c', 'a', 'b']:
        mask = tests[key] & ~assigned
        result[mask] = key
        assigned |= mask
    return result


def fit_passes(df):
    """One shared char-ngram vectorizer on username+fullname text of the TRAINING frame."""
    rep._check_df(df)
    texts = [t for t in rep._texts(df, 'username') + rep._texts(df, 'fullname') if t]
    return {'name': rep._fit_vectorizer(texts)}


def _cos(ma, mb, pa, pb):
    return np.asarray(ma[pa].multiply(mb[pb]).sum(axis=1)).ravel()


def _jac(s, q):
    x, y = set(s.split()), set(q.split())
    return len(x & y) / len(x | y) if x and y else 0.0


def similarity_flags(df, pairs, vec):
    from rapidfuzz.distance import JaroWinkler
    rep._check_df(df)
    p = rep._validate_pairs(pairs, len(df))
    t = {g: rep._texts(df, g) for g in ('username', 'fullname', 'bio', 'location', 'links', 'domain')}
    mu = vec['name'].transform(t['username'])
    mf = vec['name'].transform(t['fullname'])
    a, b = p[:, 0], p[:, 1]
    cos_u, cos_f = _cos(mu, mu, a, b), _cos(mf, mf, a, b)
    cos_x1, cos_x2 = _cos(mu, mf, a, b), _cos(mf, mu, a, b)
    n = len(p)
    u = np.zeros(n); nm = np.zeros(n); cross = np.zeros(n); other = np.zeros(n)
    link = np.zeros(n, bool); missing = np.zeros(n, bool)
    jw = JaroWinkler.normalized_similarity
    for i, (x, y) in enumerate(p):
        ua, ub, fa, fb = t['username'][x], t['username'][y], t['fullname'][x], t['fullname'][y]
        missing[i] = not (ua and ub and fa and fb)
        if ua and ub:
            u[i] = max(jw(ua, ub), cos_u[i], _jac(ua, ub))
        if fa and fb:
            nm[i] = max(jw(fa, fb), cos_f[i], _jac(fa, fb))
        c = 0.0
        if ua and fb:
            c = max(c, jw(ua, fb), cos_x1[i])
        if ub and fa:
            c = max(c, jw(ub, fa), cos_x2[i])
        cross[i] = c
        o = 0.0
        for g in ('bio', 'location'):
            s, q = t[g][x], t[g][y]
            if s and q:
                o = max(o, jw(s, q), _jac(s, q))
        other[i] = o
        la, lb, da, db = t['links'][x], t['links'][y], t['domain'][x], t['domain'][y]
        link[i] = bool((la and la == lb) or (da and da == db and da not in rep.GENERIC_DOMAINS))
    return {'u': u, 'n': nm, 'cross': cross, 'link': link, 'missing': missing,
            'max_text': np.maximum.reduce([u, nm, cross, other])}


def _mix(a, b):
    a = np.asarray(a, np.uint64)
    b = np.asarray(b, np.uint64)
    with np.errstate(over='ignore'):
        h = (a * np.uint64(2654435761)) ^ ((b + np.uint64(42)) * np.uint64(40503))
        return (h * np.uint64(11400714819323198485)) >> np.uint64(32)


def _text_pass(Q, T, platforms, pool):
    keys, rounds = [], []
    n = Q.shape[0]
    groups = [np.flatnonzero(platforms == g) for g in sorted(set(platforms))]
    for src in groups:
        for dst in groups:
            if platforms[src[0]] == platforms[dst[0]]:
                continue
            Td = T[dst].T
            for off in range(0, len(src), 256):
                qs = src[off:off + 256]
                S = (Q[qs] @ Td).toarray()
                for row, q in enumerate(qs):
                    ids = rep._top_indices(S[row], pool)
                    ids = ids[S[row, ids] > 0]
                    if not len(ids):
                        continue
                    x = np.minimum(q, dst[ids]).astype(np.int64)
                    y = np.maximum(q, dst[ids]).astype(np.int64)
                    keys.append(x * n + y)
                    rounds.append(np.arange(len(ids)))
    if not keys:
        return np.empty(0, np.int64), np.empty(0, np.int64)
    return np.concatenate(keys), np.concatenate(rounds)


def _link_pass(df, platforms, pool):
    buckets = {}
    t = {g: rep._texts(df, g) for g in ('links', 'domain')}
    for i in range(len(df)):
        if t['links'][i]:
            buckets.setdefault(('l', t['links'][i]), []).append(i)
        if t['domain'][i] and t['domain'][i] not in rep.GENERIC_DOMAINS:
            buckets.setdefault(('d', t['domain'][i]), []).append(i)
    member = {}
    for k, ids in buckets.items():
        if len(ids) > 1:
            for i in ids:
                member.setdefault(i, []).append(k)
    n = len(df)
    keys, rounds = [], []
    for q, ks in member.items():
        cand = {}
        for k in ks:
            size = len(buckets[k])
            for j in buckets[k]:
                if platforms[j] != platforms[q]:
                    cand[j] = min(cand.get(j, 10 ** 9), size)
        by_platform = {}
        for j, size in cand.items():
            by_platform.setdefault(platforms[j], []).append((size, j))
        for lst in by_platform.values():
            lst.sort(key=lambda sj: (sj[0], int(_mix(q, sj[1]))))
            for r, (_, j) in enumerate(lst[:pool]):
                keys.append(min(q, j) * n + max(q, j))
                rounds.append(r)
    return np.array(keys, np.int64), np.array(rounds, np.int64)


def multipass_ranked(df, vec, pool=50):
    """Unique undirected pairs ranked by (round, seeded hash); label-blind. Returns keys, per-pass key sets."""
    rep._check_df(df)
    platforms = np.asarray(rep._texts(df, 'platform'))
    n = len(df)
    mu = vec['name'].transform(rep._texts(df, 'username')).tocsr()
    mf = vec['name'].transform(rep._texts(df, 'fullname')).tocsr()
    parts = {
        'username_tfidf': [_text_pass(mu, mu, platforms, pool)],
        'fullname_tfidf': [_text_pass(mf, mf, platforms, pool)],
        'cross_field_username_fullname': [_text_pass(mu, mf, platforms, pool), _text_pass(mf, mu, platforms, pool)],
        'link_domain_key': [_link_pass(df, platforms, pool)],
    }
    all_k, all_r = [], []
    for name in PASSES:
        for k, r in parts[name]:
            all_k.append(k)
            all_r.append(r)
    k, r = np.concatenate(all_k), np.concatenate(all_r)
    order = np.lexsort((_mix(k // n, k % n), r))
    k = k[order]
    uniq, first = np.unique(k, return_index=True)
    first.sort()
    pass_keys = {}
    for name in PASSES:
        pass_keys[name] = np.unique(np.concatenate([x for x, _ in parts[name]])) if any(len(x) for x, _ in parts[name]) else np.empty(0, np.int64)
    return k[first], pass_keys


def multipass_pairs(df, vec, budget, pool=50, max_pool=400):
    n = len(df)
    while True:
        keys, pass_keys = multipass_ranked(df, vec, pool)
        if len(keys) >= budget or pool >= max_pool:
            break
        pool *= 2
    chosen = keys[:budget]
    pairs = np.stack([chosen // n, chosen % n], axis=1).astype(np.int32)
    return pairs, {'pool': pool, 'available_unique': int(len(keys)), 'budget': int(budget),
                   'shortfall': int(max(0, budget - len(keys)))}, pass_keys
