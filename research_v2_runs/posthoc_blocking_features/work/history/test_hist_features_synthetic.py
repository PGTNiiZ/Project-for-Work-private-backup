"""SYNTHETIC ONLY: no real profiles, images, caches, scores or labels read."""
import importlib.util
import pathlib
import sys
import unittest
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

class SyntheticTextContract(unittest.TestCase):
    def test_synthetic_text_exact_order_training_scope_and_semantic_requirement(self):
        self.assertIsNotNone(importlib.util.find_spec('hist_features'), 'historical pure feature module missing')
        import hist_features as h
        frame = pd.DataFrame(dict(username=['aa','zz'], fullname=['alpha','omega'],
            bio=['SYNTHETIC shared #x!', 'synthetic shared #y'], location=['north',''],
            links=['https://www.example.invalid/a/', 'https://www.example.invalid/b'],
            domain=['ignored.invalid','ignored.invalid'],platform=['twitter','instagram'],
            bio_mentions=['@fake_a | @fake_b', '@fake_b']))
        bundle = h.fit_text(frame.iloc[:1].reset_index(drop=True))
        vocab = dict(bundle.vectorizer.vocabulary_)
        with self.assertRaisesRegex(ValueError, 'embedding'):
            h.text_features(frame, np.array([[0,1]]), bundle)
        x, names = h.text_features(frame, np.array([[0,1]]), bundle,
                                  embeddings=np.array([[1.,0.],[0.,1.]]))
        self.assertEqual(x.shape,(1,23))
        self.assertEqual(len(set(names)),23)
        self.assertEqual(names[0],'username_jaro')
        self.assertEqual(names[-1],'platform_pair_code')
        self.assertEqual(x[0,names.index('bio_sbert_cosine')],0.)
        self.assertEqual(x[0,names.index('mention_jaccard')],0.5)
        self.assertEqual(x[0,names.index('domain_jaccard')],1.)
        self.assertEqual(x[0,names.index('url_jaccard')],0.)
        self.assertEqual(x[0,names.index('location_jaro')],0.)
        self.assertGreater(x[0,names.index('bio_tfidf_cosine')],0.)
        self.assertEqual(bundle.vectorizer.vocabulary_,vocab)
        self.assertNotIn('y',vocab)

class SyntheticImageContract(unittest.TestCase):
    def test_synthetic_image_legacy_hex_character_distance_and_context(self):
        import hist_features as h
        self.assertTrue(hasattr(h,'image_features'), 'image feature API missing')
        frame = pd.DataFrame(dict(username=['aa','zz'],fullname=['alpha','omega'],bio=['shared','shared'],
            location=['',''],links=['',''],platform=['twitter','instagram'],bio_mentions=['','']))
        descriptors = pd.DataFrame([dict(has_local_image=1,has_image_metadata=1,
            local_phash='0f', local_dhash='aa', local_brightness=0.2,local_contrast=0.3,
            local_entropy=2.,local_avg_r=0.1,local_avg_g=0.2,local_avg_b=0.3,
            local_file_size_kb=2.,num_faces=1,face_area_ratio=0.5,blur_score=4.,
            caption_emb_idx=0,caption_en='omega'),dict(has_local_image=1,has_image_metadata=1,
            local_phash='00',local_dhash='ab',local_brightness=0.4,local_contrast=0.2,
            local_entropy=3.,local_avg_r=0.2,local_avg_g=0.4,local_avg_b=0.6,
            local_file_size_kb=4.,num_faces=2,face_area_ratio=0.2,blur_score=6.,
            caption_emb_idx=-1,caption_en='')])
        x,names=h.image_features(frame,np.array([[0,1]]),descriptors,
            bio_embeddings=np.array([[1.,0.],[0.,1.]]),caption_embeddings=np.array([[0.,1.]]))
        self.assertEqual(x.shape,(1,18))
        self.assertEqual(len(set(names)),18)
        self.assertEqual(x[0,names.index('image_phash_sim')],0.5)
        self.assertEqual(x[0,names.index('image_filesize_ratio')],0.5)
        self.assertEqual(x[0,names.index('image_caption_bio_sbert_cross')],1.)
        self.assertEqual(x[0,names.index('image_caption_fullname_token_cross')],1.)
        with self.assertRaises(ValueError):
            h.image_features(frame,np.array([[0,1]]),None)

if __name__ == '__main__':
    unittest.main(verbosity=2)
