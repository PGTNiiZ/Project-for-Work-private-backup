"""Development-only frozen encoder, retrieval and fold-specific features."""
from pathlib import Path
import itertools
import json
import os
import pickle
import sys
import time
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/representation'))
import rep
from preflight import ground_truth
from runtime import job,commit_files,elapsed_fraction
from integrity import sha256


def pair_summary(df,pairs):
    pairs=np.asarray(pairs,dtype=np.int32).reshape(-1,2)
    e=df.entity.to_numpy()
    found=int(np.sum(e[pairs[:,0]]==e[pairs[:,1]])) if len(pairs) else 0
    gt=len(ground_truth(df))
    c=df.platform.value_counts().tolist()
    all_pairs=sum(a*b for a,b in itertools.combinations(c,2))
    return {'ground_truth_pairs':gt,'candidate_pairs':int(len(pairs)),'found_positives':found,'blocking_misses':gt-found,'pc':found/gt if gt else 0.,'pq':found/len(pairs) if len(pairs) else 0.,'rr':1-len(pairs)/all_pairs if all_pairs else 0.,'all_cross_platform_pairs':int(all_pairs),'profiles':int(len(df))}


def encode_scope(model,df):
    out={}
    for field in ['fullname','bio','retrieval']:
        texts=rep.profiletext(df) if field=='retrieval' else df[field].tolist()
        present=np.array([bool(s) for s in texts])
        embeddings=np.zeros((len(df),model.get_sentence_embedding_dimension()),np.float32)
        if present.any():
            embeddings[present]=model.encode([texts[i] for i in np.flatnonzero(present)],batch_size=128,show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
        out[field]=embeddings
    return out


def load_encoder():
    import torch
    from sentence_transformers import SentenceTransformer
    p=json.loads((R/'protocol.json').read_text())['encoder']
    torch.set_num_threads(2)
    model=SentenceTransformer(p['name'],revision=p['revision'],device=p['device'],cache_folder=str(R/'cache/huggingface'),token=False,trust_remote_code=False)
    model.max_seq_length=p['max_seq_length']
    return model


def prepare():
    for key,folder in [('HF_HOME','huggingface'),('TORCH_HOME','torch'),('XDG_CACHE_HOME','xdg'),('MPLCONFIGDIR','matplotlib'),('NUMBA_CACHE_DIR','numba')]:
        os.environ[key]=str(R/'cache'/folder)
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    protocol=json.loads((R/'protocol.json').read_text())
    folds=[pd.read_parquet(R/f'data_derived/dev_fold_{f}.parquet') for f in range(4)]
    data=R/'data_derived/representation'
    data.mkdir(exist_ok=True)
    with job('E4-1','frozen-encoder-development',{'encoder':protocol['encoder'],'scopes':[0,1,2,3]},category='frozen_encoder_inference') as rec:
        model=load_encoder()
        for f,df in enumerate(folds):
            emb=encode_scope(model,df)
            np.savez(data/f'embeddings_{f}.npz',**emb)
            print(json.dumps({'encoding_scope':f,'profiles':len(df),'complete':True}),flush=True)
        rec.update({'profile_count':int(sum(len(df) for df in folds)),'encoder_revision':protocol['encoder']['revision'],'training':False,'test_profile_access':False})
        files=[p for p in (R/'cache/huggingface').rglob('*') if p.is_file() and p.suffix in {'.safetensors','.bin','.json'}]
        rec['model_file_sha256']={str(p.relative_to(R/'cache/huggingface')):sha256(p) for p in files}
    del model
    for f in range(4):
        train=pd.concat([df for g,df in enumerate(folds) if g!=f],ignore_index=True)
        vectorizer=rep.fit_retriever(train)
        with (data/f'retriever_{f}.pkl').open('wb') as out: pickle.dump(vectorizer,out)
    curves=[]
    for f,df in enumerate(folds):
        emb=np.load(data/f'embeddings_{f}.npz')['retrieval']
        with (data/f'retriever_{f}.pkl').open('rb') as inp: vec=pickle.load(inp)
        b0=rep.b0_pairs(df)
        np.save(data/f'pairs_{f}_B0.npy',b0)
        with job('E1-1',f'fold{f}-B0',{'fold':f,'method':'B0'},validation_evals=1) as rec:
            rec.update(pair_summary(df,b0))
            curves.append(dict(fold=f,method='B0',k=None,budget_mode='native',**rec))
        for method,exp in [('sparse','E1-3'),('dense','E1-4'),('hybrid_union','E1-5'),('hybrid_rrf','E1-5')]:
            for k in protocol['retrieval_k']:
                with job(exp,f'fold{f}-{method}-k{k}',{'fold':f,'method':method,'k':k},validation_evals=1) as rec:
                    pairs=rep.retrieval(df,vec,emb,k,method)
                    np.save(data/f'pairs_{f}_{method}_k{k}.npy',pairs)
                    rec.update(pair_summary(df,pairs))
                    curves.append(dict(fold=f,method=method,k=k,budget_mode='k',**rec))
            with job(exp,f'fold{f}-{method}-matched',{'fold':f,'method':method,'budget':len(b0)},validation_evals=1) as rec:
                pairs=rep.retrieval(df,vec,emb,50,method,budget=len(b0))
                np.save(data/f'pairs_{f}_{method}_matched.npy',pairs)
                rec.update(pair_summary(df,pairs))
                curves.append(dict(fold=f,method=method,k=None,budget_mode='matched',**rec))
        if elapsed_fraction()>=.85:
            raise TimeoutError('reporting cutoff reached; no new retrieval scopes')
    (R/'metrics/blocking_development.json').write_text(json.dumps({'classification':protocol['status'],'rows':curves},indent=2)+'\n')
    def pooled(rows):
        return sum(r['found_positives'] for r in rows)/sum(r['ground_truth_pairs'] for r in rows)
    matched={m:pooled([r for r in curves if r['method']==m and r['budget_mode']==('native' if m=='B0' else 'matched')]) for m in ['B0','sparse','dense','hybrid_union','hybrid_rrf']}
    hybrid=sorted(['hybrid_union','hybrid_rrf'],key=lambda m:(-matched[m],m))[0]
    lex=sorted(['B0','sparse'],key=lambda m:(-matched[m],m))[0]
    best=sorted([lex,hybrid],key=lambda m:(-matched[m],m))[0]
    kstar=20
    for k in protocol['retrieval_k']:
        rows=[r for r in curves if r['method']=='sparse' and r['budget_mode']=='k' and r['k']==k]
        if pooled(rows)>=.95:
            kstar=k
            break
    selection={'k_star':kstar,'best_lexical':lex,'hybrid':hybrid,'B_star':best,'matched_PC':matched,'selection_population':'pooled development folds only','classification':protocol['status']}
    (R/'metrics/blocker_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    print(json.dumps({'selection':selection}),flush=True)
    all_dev=pd.concat(folds,ignore_index=True)
    pairs_by_scope=[]
    offset=0
    for f,df in enumerate(folds):
        tag='B0' if best=='B0' else f'{best}_matched'
        pair=np.load(data/f'pairs_{f}_{tag}.npy')
        pairs_by_scope.append(pair+offset)
        offset+=len(df)
    pairs=np.concatenate(pairs_by_scope)
    scope=np.concatenate([np.full(len(p),f,dtype=np.int8) for f,p in enumerate(pairs_by_scope)])
    y=(all_dev.entity.to_numpy()[pairs[:,0]]==all_dev.entity.to_numpy()[pairs[:,1]]).astype(np.int8)
    np.savez(data/'pair_metadata_dev.npz',pairs=pairs,fold=scope,y=y)
    embeddings={g:np.concatenate([np.load(data/f'embeddings_{f}.npz')[g] for f in range(4)]) for g in ['fullname','bio']}
    semantic=rep.semantic_features(embeddings,pairs,all_dev)
    np.save(data/'semantic_dev.npy',semantic)
    with job('E2-1','fold-specific-lexical',{'groups':protocol['lexical_groups'],'scope':'four OOF vocabularies + development refit vocabulary'},validation_evals=1,category='unsupervised_feature_fit') as rec:
        for f in range(5):
            train=all_dev if f==4 else all_dev[all_dev.fold.ne(f)].reset_index(drop=True)
            vectors=rep.fit_tfidf(train)
            with (data/f'lexical_vectors_cv{f}.pkl').open('wb') as out: pickle.dump(vectors,out)
            X,names,groups=rep.lexical_features(all_dev,pairs,vectors)
            np.save(data/f'lexical_dev_cv{f}.npy',X)
            print(json.dumps({'lexical_cv_vocabulary':f,'pairs':len(pairs),'columns':X.shape[1]}),flush=True)
        (data/'feature_schema.json').write_text(json.dumps({'lexical_names':names,'groups':groups,'semantic_names':['fullname_cosine','fullname_both_present','fullname_one_missing','bio_cosine','bio_both_present','bio_one_missing']},indent=2))
        rec.update({'n_pairs':len(pairs),'positive_pairs':int(y.sum()),'n_lexical_features':len(names),'n_semantic_features':int(semantic.shape[1]),'test_profile_access':False})
    # Final refit retrieval vocabulary is trained on development only, never test.
    with (data/'retriever_refit.pkl').open('wb') as out: pickle.dump(rep.fit_retriever(all_dev),out)
    return selection

if __name__=='__main__':
    prepare()
