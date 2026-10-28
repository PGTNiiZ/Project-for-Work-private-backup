"""Build candidate sets and feature matrices for every blocker/feature set. POST-HOC EXPLORATORY.
usage: build_inputs.py candidates | bertcos | features <blocker> <featureset>
Outputs are private arrays under data_derived/ (pair indices, labels, features); never reported."""
import json
import math
import sys
import numpy as np
import pandas as pd
from ub_common import (DATA, POSTHOC, REPD, FOLDS, all_dev, ground_truth, rep, run, digest, ledger)

BLOCKERS = ('B0', 'sparse', 'dense', 'hybrid_union', 'hybrid_rrf', 'multipass', 'embhash', 'multipass2x')


def _local_pairs(blocker, f, mult=1.0):
    if blocker == 'B0':
        return np.load(REPD / f'pairs_{f}_B0.npy')
    if blocker in ('sparse', 'dense', 'hybrid_union', 'hybrid_rrf'):
        if mult == 1.0:
            return np.load(REPD / f'pairs_{f}_{blocker}_matched.npy')
        return np.load(POSTHOC / f'data_derived/{blocker}_dev_fold{f}_{mult}x.npy')
    if blocker == 'multipass':
        return np.load(POSTHOC / f'data_derived/multipass_dev_fold{f}_{mult}x.npy')
    if blocker == 'multipass2x':
        return np.load(POSTHOC / 'data_derived/multipass_dev_fold{}_2.0x.npy'.format(f))
    if blocker == 'embhash':
        return np.load(DATA / f'cands_embhash_f{f}_{mult}x.npy')
    raise ValueError(blocker)


# ---------------------------------------------------------------- embedding-hash blocker (R6 style)
def _train_hash(train_folds, folds, emb, seed=42):
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(4)
    rng = np.random.default_rng(seed)
    X, pa, pb, lab = [], [], [], []
    base = 0
    for g in train_folds:
        df = folds[g]
        e = emb[g]
        gt = ground_truth(df)
        plat = df.platform.to_numpy()
        n = len(df)
        neg_a = rng.integers(0, n, 6 * len(gt))
        neg_b = rng.integers(0, n, 6 * len(gt))
        keep = plat[neg_a] != plat[neg_b]
        neg = np.stack([neg_a[keep], neg_b[keep]], 1)[:3 * len(gt)]
        X.append(e)
        for arr, l in ((gt, 1.0), (neg, -1.0)):
            pa.append(arr[:, 0] + base); pb.append(arr[:, 1] + base); lab.append(np.full(len(arr), l))
        base += n
    E = torch.tensor(np.concatenate(X), dtype=torch.float32)
    pa, pb, lab = (torch.tensor(np.concatenate(v)) for v in (pa, pb, lab))
    head = torch.nn.Sequential(torch.nn.Linear(E.shape[1], 64), torch.nn.LayerNorm(64), torch.nn.Tanh())
    opt = torch.optim.Adam(head.parameters(), lr=1e-3)
    loss_fn = torch.nn.CosineEmbeddingLoss(margin=0.2)
    gen = torch.Generator().manual_seed(seed)
    for _ in range(20):
        order = torch.randperm(len(lab), generator=gen)
        for s in range(0, len(order), 1024):
            ix = order[s:s + 1024]
            ha, hb = head(E[pa[ix]]), head(E[pb[ix]])
            loss = loss_fn(ha, hb, lab[ix].float())
            opt.zero_grad(); loss.backward(); opt.step()
    return head


def _hash_candidates(df, e, head, budgets, pool=50):
    import torch
    with torch.no_grad():
        h = head(torch.tensor(e, dtype=torch.float32)).numpy()
    b = np.where(h >= 0, 1.0, -1.0).astype(np.float32)
    hn = h / np.maximum(np.linalg.norm(h, axis=1, keepdims=True), 1e-9)
    empty = ~np.any(e != 0, axis=1)
    plat = df.platform.to_numpy()
    n = len(df)
    keys, ham, cos = [], [], []
    groups = [np.flatnonzero((plat == p) & ~empty) for p in sorted(set(plat))]
    for src in groups:
        for dst in groups:
            if plat[src[0]] == plat[dst[0]]:
                continue
            for off in range(0, len(src), 512):
                q = src[off:off + 512]
                H = (64 - b[q] @ b[dst].T) / 2
                C = hn[q] @ hn[dst].T
                score = H - 0.5 * C          # Hamming first, code cosine breaks ties
                k = min(pool, len(dst))
                idx = np.argpartition(score, k - 1, axis=1)[:, :k]
                rows = np.repeat(q, k)
                cols = dst[idx.ravel()]
                x, y = np.minimum(rows, cols), np.maximum(rows, cols)
                keys.append(x.astype(np.int64) * n + y)
                ham.append(np.take_along_axis(H, idx, 1).ravel())
                cos.append(np.take_along_axis(C, idx, 1).ravel())
    keys, ham, cos = np.concatenate(keys), np.concatenate(ham), np.concatenate(cos)
    order = np.lexsort((keys, -cos, ham))
    keys = keys[order]
    _, first = np.unique(keys, return_index=True)
    first.sort()
    ranked = keys[first]
    out = {}
    for m, bud in budgets.items():
        ch = ranked[:bud]
        out[m] = np.stack([ch // n, ch % n], 1).astype(np.int32)
        out[m + '_shortfall'] = int(max(0, bud - len(ranked)))
    return out


def build_candidates():
    with run('inputs', 'candidates') as rec:
        folds, dev, offs = all_dev()
        emb = {f: np.load(REPD / f'embeddings_{f}.npz')['retrieval'] for f in FOLDS}
        info = {}
        for f in FOLDS:
            base = len(np.load(REPD / f'pairs_{f}_sparse_matched.npy'))
            head = _train_hash([g for g in FOLDS if g != f], folds, emb)
            res = _hash_candidates(folds[f], emb[f], head, {'1.0': base, '2.0': math.ceil(2 * base)})
            for m in ('1.0', '2.0'):
                np.save(DATA / f'cands_embhash_f{f}_{m}x.npy', res[m])
            info[f] = {'budget_1x': base, 'shortfall_1x': res['1.0_shortfall'], 'shortfall_2x': res['2.0_shortfall']}
        pc = {}
        for blocker, mult in [(b, 1.0) for b in BLOCKERS if b != 'multipass2x'] + [('sparse', 2.0), ('multipass', 2.0), ('embhash', 2.0)]:
            found = gt_tot = cand = 0
            for f in FOLDS:
                df = folds[f]; n = len(df)
                gt = ground_truth(df)
                p = _local_pairs(blocker, f, mult)
                k = np.minimum(p[:, 0], p[:, 1]).astype(np.int64) * n + np.maximum(p[:, 0], p[:, 1])
                gk = gt[:, 0].astype(np.int64) * n + gt[:, 1]
                found += int(np.isin(gk, k).sum()); gt_tot += len(gt); cand += len(p)
            pc[f'{blocker}@{mult}x'] = {'found': found, 'ground_truth': gt_tot, 'PC': found / gt_tot, 'candidates': cand}
        json.dump({'embhash': info, 'pc': pc}, open(DATA / 'candidates_summary.json', 'w'), indent=1)
        rec['pc'] = pc


# ---------------------------------------------------------------- MiniLM cosine for R18
def build_bertcos():
    with run('inputs', 'bertcos') as rec:
        from sentence_transformers import SentenceTransformer
        _, dev, _ = all_dev()
        text = [' '.join(x for x in (a, b, c) if x).strip() or '[empty]' for a, b, c in zip(rep._texts(dev, 'fullname'), rep._texts(dev, 'bio'), rep._texts(dev, 'location'))]
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu', revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
        e = model.encode(text, batch_size=256, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        np.save(DATA / 'r18_text_embeddings.npy', e)
        rec['profiles'] = len(e)


# ---------------------------------------------------------------- feature sets
def _meta(blocker):
    path = DATA / f'meta_{blocker}.npz'
    if path.exists():
        z = np.load(path)
        return {k: z[k] for k in z.files}
    folds, dev, offs = all_dev()
    pairs, fold, misses = [], [], []
    for f in FOLDS:
        p = _local_pairs(blocker, f).astype(np.int64)
        n = len(folds[f]); gt = ground_truth(folds[f])
        k = p.min(1) * n + p.max(1)
        misses.append(int((~np.isin(gt[:, 0].astype(np.int64) * n + gt[:, 1], k)).sum()))
        pairs.append(p + offs[f]); fold.append(np.full(len(p), f, np.int8))
    pairs = np.concatenate(pairs).astype(np.int32); fold = np.concatenate(fold)
    ent = dev.entity.to_numpy(); plat = dev.platform.to_numpy()
    y = ((ent[pairs[:, 0]] == ent[pairs[:, 1]]) & (plat[pairs[:, 0]] != plat[pairs[:, 1]])).astype(np.int8)
    u = rep._texts(dev, 'username'); fn = rep._texts(dev, 'fullname'); ln = rep._texts(dev, 'links')
    from rapidfuzz.distance import JaroWinkler
    jw = JaroWinkler.normalized_similarity
    nsim = np.zeros(len(pairs)); exact = np.zeros(len(pairs), bool)
    for i, (a, b) in enumerate(pairs):
        best = 0.0
        for x in (u[a], fn[a]):
            if x:
                for z in (u[b], fn[b]):
                    if z:
                        best = max(best, jw(x, z))
        nsim[i] = best
        exact[i] = (len(u[a]) >= 3 and u[a] == u[b]) or (bool(ln[a]) and ln[a] == ln[b])
    out = dict(pairs=pairs, fold=fold, y=y, misses=np.array(misses), nsim=nsim, exact=exact)
    np.savez(path, **out)
    return out


def _r17(dev, pairs):
    from rapidfuzz.distance import JaroWinkler, Levenshtein
    jw = JaroWinkler.normalized_similarity
    t = {g: rep._texts(dev, g) for g in ('username', 'fullname', 'bio', 'location', 'platform')}
    X = np.zeros((len(pairs), 17), np.float32)
    for i, (a, b) in enumerate(pairs):
        ua, ub, fa, fb = t['username'][a], t['username'][b], t['fullname'][a], t['fullname'][b]
        ba, bb, la, lb = t['bio'][a], t['bio'][b], t['location'][a], t['location'][b]
        r = X[i]
        if ua and ub:
            r[0] = jw(ua, ub); r[1] = Levenshtein.normalized_similarity(ua, ub)
            r[2] = 1.0 if ua == ub else jw(''.join(sorted(ua)), ''.join(sorted(ub)))
        if fa and fb:
            r[3] = jw(fa, fb); r[4] = Levenshtein.normalized_similarity(fa, fb)
            r[5] = jw(' '.join(sorted(fa.split())), ' '.join(sorted(fb.split())))
        best = 0.0
        for x in (ua, fa):
            if x:
                for z in (ub, fb):
                    if z:
                        best = max(best, jw(x, z))
        r[6] = best
        sa, sb = set(ba.split()), set(bb.split())
        r[7] = len(sa & sb) / len(sa | sb) if (sa or sb) else 0.0
        mx = max(len(ba), len(bb)); r[8] = min(len(ba), len(bb)) / mx if mx else 0.0
        r[9] = float(bool(ba) and bool(bb))
        if la and lb:
            r[10] = jw(la, lb)
        r[11] = float(bool(la) and la == lb); r[12] = float(bool(la) and bool(lb))
        r[13] = float(t['platform'][a] == t['platform'][b])
        mx = max(len(ua), len(ub)); r[14] = abs(len(ua) - len(ub)) / mx if mx else 0.0
        wa, wb = len(fa.split()), len(fb.split()); mx = max(wa, wb); r[15] = abs(wa - wb) / mx if mx else 0.0
        r[16] = float(len(ua) >= 3 and len(ub) >= 3 and ua[:3] == ub[:3])
    return X


def _bloom(dev, pairs, L):
    import hashlib
    salt = 'identity-resolution-r4-bloom-salt-fixed'
    cache = {}

    def enc(s):
        if s in cache:
            return cache[s]
        bits = np.zeros(L, bool)
        padded = f' {s} '
        for i in range(len(padded) - 1):
            g = padded[i:i + 2]
            for j in range(10):
                bits[int(hashlib.md5(f'{salt}|{j}|{g}'.encode()).hexdigest(), 16) % L] = True
        cache[s] = (np.packbits(bits), int(bits.sum()))
        return cache[s]
    pop8 = np.array([bin(i).count('1') for i in range(256)], np.uint16)
    out = np.zeros((len(pairs), 3), np.float32)
    for col, g in enumerate(('username', 'fullname')):
        t = rep._texts(dev, g)
        P = np.stack([enc(s)[0] for s in t]); C = np.array([enc(s)[1] for s in t])
        for s in range(0, len(pairs), 200000):
            a, b = pairs[s:s + 200000, 0], pairs[s:s + 200000, 1]
            inter = pop8[P[a] & P[b]].sum(1)
            den = C[a] + C[b]
            d = np.where(den > 0, 2 * inter / np.maximum(den, 1), 0.0)   # empty names encode the padding bigram, as in the original
            out[s:s + 200000, col] = d
    out[:, 2] = out[:, :2].max(1)
    return out


def _name_variants(dev, pairs):
    from identity_resolution.core import name_similarity as ns
    u = rep._texts(dev, 'username'); fn = rep._texts(dev, 'fullname')
    cols = ['name_damerau_username', 'name_damerau_fullname', 'name_char_ngram_username', 'name_char_ngram_fullname',
            'name_token_set_username', 'name_token_set_fullname', 'name_handle_exact', 'name_handle_prefix', 'name_handle_suffix',
            'name_handle_length_ratio', 'name_handle_available', 'name_cross_damerau_max', 'name_cross_damerau_mean']
    X = np.zeros((len(pairs), len(cols)), np.float32)
    for i, (a, b) in enumerate(pairs):
        ua, ub, fa, fb = u[a], u[b], fn[a], fn[b]
        cross = (ns.damerau_similarity(ua, fb), ns.damerau_similarity(fa, ub))
        h = ns.handle_features(ua, ub)
        X[i] = (ns.damerau_similarity(ua, ub), ns.damerau_similarity(fa, fb), ns.char_ngram_cosine(ua, ub), ns.char_ngram_cosine(fa, fb),
                ns.token_set_similarity(ua, ub), ns.token_set_similarity(fa, fb), h['exact'], h['prefix'], h['suffix'], h['length_ratio'],
                h['available'], max(cross), sum(cross) / 2)
    return X, cols


NGROUPS = {'N1': [0, 1], 'N2': [2, 3], 'N3': [4, 5], 'N4': [6, 7, 8, 9, 10], 'N5': [11, 12], 'N6': [2, 3, 6, 7, 8, 9, 10]}


def build_features(blocker, fs):
    target = [DATA / f'X_{blocker}_{fs}_cv{cv}.npy' for cv in FOLDS]
    if all(t.exists() for t in target):
        return
    with run('inputs', f'features-{blocker}-{fs}') as rec:
        folds, dev, offs = all_dev()
        if blocker == 'multipass2x' and fs == 'H23_FLEX35':
            meta = np.load(POSTHOC / 'data_derived/pair_meta.npz')
            mine = _meta('multipass2x')
            if not np.array_equal(meta['pairs'], mine['pairs']):
                raise ValueError('post-hoc pair order mismatch')
            for cv in FOLDS:
                np.save(target[cv], np.load(POSTHOC / f'data_derived/H23+LEX35_cv{cv}.npy'))
            rec['source'] = 'reused post-hoc H23+LEX35 matrices (same functions, training-fold TF-IDF)'
            return
        m = _meta(blocker)
        pairs = m['pairs']
        fold_of_row = dev.fold.to_numpy()

        def emb_dict():
            z = [np.load(REPD / f'embeddings_{f}.npz') for f in FOLDS]
            return {k: np.concatenate([q[k] for q in z]) for k in ('fullname', 'bio')}
        static = None
        if fs in ('R17', 'R18') or fs.startswith('BLOOM'):
            r17 = _r17(dev, pairs)
            if fs == 'R17':
                static = r17
            elif fs == 'R18':
                e = np.load(DATA / 'r18_text_embeddings.npy')
                static = np.concatenate([r17, np.einsum('ij,ij->i', e[pairs[:, 0]], e[pairs[:, 1]])[:, None]], 1)
            else:
                static = np.concatenate([_bloom(dev, pairs, int(fs[5:])), r17[:, 7:17]], 1)
        elif fs == 'FSEM':
            static = rep.semantic_features(emb_dict(), pairs, dev)
        for cv in FOLDS:
            if static is not None:
                np.save(target[cv], static.astype(np.float32)); continue
            parts = []
            train = dev[fold_of_row != cv].reset_index(drop=True)
            if fs in ('FLEX35', 'FUSION41', 'H23_FLEX35'):
                lex, _, _ = rep.lexical_features(dev, pairs, rep.fit_tfidf(train))
                parts.append(lex)
            if fs == 'FUSION41':
                parts.append(rep.semantic_features(emb_dict(), pairs, dev))
            if fs == 'H23' or fs == 'H23_FLEX35' or fs in NGROUPS:
                import hist_features as H
                prof = dev[['username', 'fullname', 'bio', 'location', 'links', 'platform']].copy()
                prof['bio_mentions'] = ''
                bundle = H.fit_text(prof[fold_of_row != cv].reset_index(drop=True))
                h23, _ = H.text_features(prof, pairs, bundle, embeddings=emb_dict()['bio'])
                parts.insert(0, h23.astype(np.float32))
            if fs in NGROUPS:
                cache = DATA / f'namevar_{blocker}.npy'
                if not cache.exists():
                    np.save(cache, _name_variants(dev, pairs)[0])
                parts.append(np.load(cache)[:, NGROUPS[fs]])
            np.save(target[cv], np.concatenate(parts, 1).astype(np.float32))
        rec['columns'] = int(np.load(target[0], mmap_mode='r').shape[1])
        rec['pairs'] = int(len(pairs))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'candidates':
        build_candidates()
    elif cmd == 'bertcos':
        build_bertcos()
    elif cmd == 'meta':
        _meta(sys.argv[2])
    elif cmd == 'features':
        build_features(sys.argv[2], sys.argv[3])
