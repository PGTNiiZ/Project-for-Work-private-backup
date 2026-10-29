"""SYNTHETIC differential verification against reviewed source TEXT only.

Never imports or executes source top-level. AST allowlist includes pure function
bodies only. Synthetic labels are required by the legacy reference API only;
production adapter receives no labels. No historical scientific artifact read.
"""
import math
import re
from urllib.parse import urlparse
from typing import Any
import ast
import pathlib
import types
import unittest
import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler, Levenshtein
import hist_features as h

ROOT=pathlib.Path(__file__).resolve().parents[4]
SOURCE=ROOT/'research_v2_review_workspace/research_v2/review/_work/agentA/source/main/train_data'


def pure_namespace(path,names,extra=None) -> dict[str,Any]:
    tree=ast.parse(path.read_text())
    tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if len(tree.body)!=len(names):
        raise AssertionError('missing allowlisted source function')
    ns=dict(np=np,pd=pd,fuzz=fuzz,JaroWinkler=JaroWinkler,Levenshtein=Levenshtein,
        PLATFORM_PAIR_CODES=h.PLATFORM_CODES,KEY_COLS=['profile_row_id_a','profile_row_id_b','label','pair_type','split_name','profile_id'])
    ns.update(extra or {})
    exec(compile(tree,str(path),'exec'),ns)
    return ns


def fixture():
    return pd.DataFrame(dict(username=['aa','zz','aa','',''],fullname=['alpha','omega','alpha','',''],
        bio=['SYNTHETIC shared #tag!', 'synthetic different #other', 'SYNTHETIC shared #tag!','',''],
        location=['north','','north','',''],
        links=["['https://www.example.invalid/a/', 'second.invalid']",'https://example.invalid/b','https://www.example.invalid/a/','',''],
        platform=['twitter','instagram','googleplus','unknown','twitter'],
        bio_mentions=['@fake_a | @fake_b','@fake_b','@fake_a','','']))


def legacy_bundle(df,embeddings):
    records={}
    helpers=pure_namespace(SOURCE/'stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py.txt',
        {'clean_text','lower_text','parse_list_field','parse_urls','extract_domains',
         'parse_mentions','extract_hashtags','punct_ratio','avg_word_len'},
        dict(math=math,re=re,urlparse=urlparse))
    lower,clean=helpers['lower_text'],helpers['clean_text']
    for i,r in enumerate(df.to_dict('records')):
        bio=lower(r['bio'])
        urls=helpers['parse_urls'](r['links'])
        records[i]=dict(userName_norm=lower(r['username']),fullName_norm=lower(r['fullname']),bio_norm=bio,
            location_norm=lower(r['location']),urls_set=urls,domains_set=helpers['extract_domains'](urls),
            bio_mentions_set=helpers['parse_mentions'](r['bio_mentions']),hashtags_set=helpers['extract_hashtags'](bio),
            caps_ratio=sum(c.isupper() for c in clean(r['bio']))/max(len(clean(r['bio'])),1),
            avg_word_len=helpers['avg_word_len'](bio),punct_ratio=helpers['punct_ratio'](bio),
            platform=r['platform'],profile_id=100+i,_tfidf_idx=i)
    bundle=h.fit_text(df)
    return dict(records=records,sbert_embeddings=embeddings,
        tfidf_matrix=bundle.vectorizer.transform(df.bio.str.strip().str.lower()))


class SyntheticSourceParity(unittest.TestCase):
    def test_synthetic_23_columns_equal_allowlisted_original(self):
        df=fixture()
        embeddings=np.eye(len(df))
        pairs=np.array([[0,1],[0,2],[3,4],[0,3],[1,0]],dtype=int)
        ref=pure_namespace(SOURCE/'stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py.txt',
            {'compute_features','jaccard','biolen_ratio'})
        reference_pairs=pd.DataFrame(pairs,columns=['profile_row_id_a','profile_row_id_b'])
        reference_pairs=reference_pairs.assign(label=0,pair_type='SYNTHETIC',split_name='SYNTHETIC')
        expected,names=ref['compute_features'](reference_pairs,legacy_bundle(df,embeddings))
        actual,actual_names=h.text_features(df,pairs,h.fit_text(df),embeddings=embeddings)
        self.assertEqual(names,actual_names)
        np.testing.assert_allclose(actual,expected[names].to_numpy(),rtol=0,atol=1e-12)
        current=pure_namespace(ROOT/'src/identity_resolution/stages/train_base.py',
            {'compute_features','jaccard','biolen_ratio'},extra={'FEATURE_PROGRESS_HOOK':None})
        expected_current,current_names=current['compute_features'](reference_pairs,legacy_bundle(df,embeddings))
        self.assertEqual(current_names,actual_names)
        np.testing.assert_allclose(actual,expected_current[current_names].to_numpy(),rtol=0,atol=1e-12)

    def test_synthetic_18_columns_equal_allowlisted_original(self):
        df=fixture()
        bios=np.eye(len(df))
        caps=np.array([bios[1],-bios[0]])
        rows=[]
        for i in range(len(df)):
            r={k:0. for k in h.DESCRIPTOR_COLS}
            r.update(has_local_image=int(i<2),has_image_metadata=int(i<3),
                local_phash=['0f','00','','',''][i],local_dhash=['aa','ab','','',''][i],
                caption_emb_idx=[0,1,-1,-1,-1][i],caption_en=['omega','alpha','','',''][i],
                local_file_size_kb=float(i+1),local_brightness=i/5.,local_contrast=i/7.,
                local_entropy=float(i),local_avg_r=i/9.,local_avg_g=i/8.,local_avg_b=i/7.,
                num_faces=i,face_area_ratio=i/5.,blur_score=float(i))
            rows.append(r)
        descriptors=pd.DataFrame(rows)
        pairs=np.array([[0,1],[0,2],[3,4],[0,3],[1,0]],dtype=int)
        ref=pure_namespace(SOURCE/'stage7_13_multimodal_suite/run_multimodal_suite.py.txt',
            {'hash_similarity','make_multimodal_wrappers'})
        base=types.SimpleNamespace(make_profile_bundle=lambda x:legacy_bundle(x,bios),
            compute_features=lambda p,b:(pd.DataFrame(index=range(len(p))),[]),KEY_COLS=[])
        image_df=descriptors.assign(profile_row_id=np.arange(len(df)))
        make,compute=ref['make_multimodal_wrappers'](base,'image_context',image_df,caps)
        expected,names=compute(pd.DataFrame(pairs,columns=['profile_row_id_a','profile_row_id_b']),make(df))
        actual,actual_names=h.image_features(df,pairs,descriptors,bio_embeddings=bios,caption_embeddings=caps)
        self.assertEqual(names,actual_names)
        np.testing.assert_allclose(actual,expected.to_numpy(),rtol=0,atol=1e-12)
        current=pure_namespace(ROOT/'src/identity_resolution/stages/train_multimodal.py',
            {'hash_similarity','make_multimodal_wrappers'})
        current_make,current_compute=current['make_multimodal_wrappers'](base,'image_context',image_df,caps)
        expected_current,current_names=current_compute(pd.DataFrame(pairs,columns=['profile_row_id_a','profile_row_id_b']),current_make(df))
        self.assertEqual(current_names,actual_names)
        np.testing.assert_allclose(actual,expected_current.to_numpy(),rtol=0,atol=1e-12)

    def test_synthetic_boundary_rejects_sensitive_columns_bad_pairs_and_missing_mentions(self):
        df=fixture()
        b=h.fit_text(df)
        for col in ('label','score','decision','fold','entity','component'):
            with self.subTest(col=col), self.assertRaises(ValueError):
                h.text_features(df.assign(**{col:0}),np.array([[0,1]]),b,embeddings=np.eye(len(df)))
        with self.assertRaises(ValueError):
            h.fit_text(df.drop(columns=['bio_mentions']))
        for pairs in (np.array([[-1,0]]),np.array([[0,5]]),np.array([[0.,1.]]),
                      pd.DataFrame({'profile_row_id_a':[0],'profile_row_id_b':[1],'label':[0]})):
            with self.assertRaises(ValueError):
                h.text_features(df,pairs,b,embeddings=np.eye(len(df)))
        with self.assertRaises(ValueError):
            h.text_features(df.set_axis([9,8,7,6,5]),np.array([[0,1]]),b,embeddings=np.eye(len(df)))
        with self.assertRaises(ValueError):
            h.text_features(df,np.array([[0,1]]),b,embeddings=np.ones((len(df),2)))
        x,names=h.text_features(df,np.empty((0,2),dtype=int),b,embeddings=np.eye(len(df)))
        self.assertEqual(x.shape,(0,23))


if __name__=='__main__':
    unittest.main(verbosity=2)
