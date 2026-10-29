"""Audited historical feature formulas; NEW POST-HOC DEVELOPMENT-ONLY adapter.

No IO, inference, labels, scores, decisions or split inputs. Caller must supply
only authorized development frames. Exact legacy SBERT was all-mpnet-base-v2,
NOT MiniLM; other frozen embeddings are explicitly a representation adaptation.
Fit vocabulary on train development profiles ONLY. See MAPPING_TH.md.
"""
from dataclasses import dataclass
import ast
import math
import re
from urllib.parse import urlparse
import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler, Levenshtein
from sklearn.feature_extraction.text import TfidfVectorizer

TEXT_NAMES = ('username_jaro', 'username_lev', 'username_token_sort',
 'fullname_jaro', 'fullname_lev', 'fullname_token_sort', 'bio_tfidf_cosine',
 'bio_sbert_cosine', 'domain_jaccard', 'url_jaccard', 'domain_count_a',
 'domain_count_b', 'location_jaro', 'location_token_sort', 'mention_jaccard',
 'hashtag_jaccard', 'hashtag_count_a', 'hashtag_count_b', 'style_caps_diff',
 'style_avgword_diff', 'style_biolen_ratio', 'style_punct_diff', 'platform_pair_code')
PLATFORM_CODES = {('googleplus','instagram'):0, ('googleplus','twitter'):1,
                  ('instagram','twitter'):2}
PROFILE_COLS = {'username','fullname','bio','location','links','domain','platform','bio_mentions'}
REQUIRED_COLS = PROFILE_COLS - {'domain'}

@dataclass(frozen=True)
class TextBundle:
    vectorizer: object
    empty_vocabulary: bool = False


def _clean(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ''
    return str(value).strip()


def _validate_frame(df):
    if not isinstance(df.index, pd.RangeIndex) or not df.index.equals(pd.RangeIndex(len(df))):
        raise ValueError('profiles require zero-based contiguous RangeIndex')
    if set(df.columns) - PROFILE_COLS:
        raise ValueError('unexpected profile columns: project feature-only columns first')
    if not REQUIRED_COLS.issubset(df.columns):
        raise ValueError('missing historical profile columns (bio_mentions must be explicit)')


def _pairs(pairs, n):
    if isinstance(pairs, pd.DataFrame):
        if list(pairs.columns) != ['profile_row_id_a','profile_row_id_b']:
            raise ValueError('pairs must contain endpoint columns only; no labels/scores/splits')
        pairs = pairs.to_numpy()
    p = np.asarray(pairs)
    if p.ndim != 2 or p.shape[1] != 2 or not np.issubdtype(p.dtype, np.integer):
        raise ValueError('pairs require integer shape (n,2)')
    if p.size and (p.min() < 0 or p.max() >= n):
        raise ValueError('pair endpoint outside supplied development frame')
    return p


def fit_text(train_dev_df):
    """Fit only supplied TRAIN-development bio; no IO or semantic inference.

    Empty-vocabulary training is an explicit adapter extension: TF-IDF outputs
    zero, whereas historical sklearn fit would fail. Not historical equivalence.
    """
    _validate_frame(train_dev_df)
    vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1,2), min_df=1)
    texts = [_clean(x).lower() for x in train_dev_df.bio]
    try:
        vectorizer.fit(texts)
    except ValueError as exc:
        if 'empty vocabulary' not in str(exc):
            raise
        return TextBundle(None, True)
    return TextBundle(vectorizer)


def _urls(value):
    if isinstance(value, (list,tuple,set)):
        items = value
    else:
        text = _clean(value)
        items = [text] if text else []
        if text.startswith('[') and text.endswith(']'):
            try:
                items = ast.literal_eval(text)
            except (ValueError,SyntaxError):
                items = [text]
    return {_clean(x).lower().rstrip('/') for x in items if _clean(x)}


def _record(row):
    bio = _clean(row['bio'])
    norm = bio.lower()
    urls = _urls(row['links'])
    domains = {urlparse(u if '://' in u else 'https://' + u).netloc.lower().replace('www.','') for u in urls}
    words = norm.split()
    return dict(username=_clean(row['username']).lower(), fullname=_clean(row['fullname']).lower(),
        location=_clean(row['location']).lower(), bio=norm, urls=urls, domains=domains-{''},
        mentions={p.strip().lstrip('@') for p in re.split(r'\s*\|\s*|\s+',_clean(row['bio_mentions']).lower()) if p.strip()},
        hashtags={x.lower() for x in re.findall(r'#(\w+)',norm)},
        caps=sum(c.isupper() for c in bio)/max(len(bio),1),
        wordlen=sum(map(len,words))/len(words) if words else 0.,
        punct=sum(not c.isalnum() and not c.isspace() for c in norm)/max(len(norm),1),
        platform=row['platform'])


def _jac(a,b):
    return len(a & b)/len(a | b) if a | b else 0.


def _embeddings(embeddings,n):
    if embeddings is None:
        raise ValueError('frozen embedding array required; never silently substitute zeros')
    e = np.asarray(embeddings)
    if e.ndim != 2 or e.shape[0] != n or not np.isfinite(e).all():
        raise ValueError('embedding array must be finite, 2D and profile-row aligned')
    norms = np.linalg.norm(e,axis=1)
    if not np.all(np.isclose(norms,1.,atol=1e-4) | np.isclose(norms,0.,atol=1e-8)):
        raise ValueError('embedding rows must already be unit-normalized (or zero for empty text)')
    return e


def text_features(df,pairs,bundle,*,embeddings=None):
    """Return (float64 (n_pairs,23), ordered names); never fit or infer here.

    embeddings: frozen normalized bio embeddings aligned to df RangeIndex.
    Providing MiniLM instead of historical MPNet changes the representation.
    domain input is ignored: legacy domains derive from links, not domain column.
    bio_mentions is mandatory: absent historical mentions are NOT inferred.
    """
    _validate_frame(df)
    p = _pairs(pairs,len(df))
    e = _embeddings(embeddings,len(df))
    records = [_record(r) for r in df.to_dict('records')]
    tfidf = None if bundle.empty_vocabulary or len(df)==0 else bundle.vectorizer.transform([r['bio'] for r in records])
    rows = []
    for i,j in p:
        a,b = records[i],records[j]
        out = []
        for field in ('username','fullname'):
            u,v = a[field],b[field]
            out.extend([JaroWinkler.normalized_similarity(u,v),
                1.-Levenshtein.distance(u,v)/max(len(u),len(v),1),fuzz.token_sort_ratio(u,v)/100.])
        out.extend([float(tfidf[i].multiply(tfidf[j]).sum()) if tfidf is not None else 0.,
            float(np.dot(e[i],e[j])), _jac(a['domains'],b['domains']),_jac(a['urls'],b['urls']),
            min(len(a['domains']),10)/10.,min(len(b['domains']),10)/10.])
        u,v = a['location'],b['location']
        out.extend([JaroWinkler.normalized_similarity(u,v) if u and v else 0.,
            fuzz.token_sort_ratio(u,v)/100. if u and v else 0.,
            _jac(a['mentions'],b['mentions']),_jac(a['hashtags'],b['hashtags']),
            min(len(a['hashtags']),10)/10.,min(len(b['hashtags']),10)/10.,
            abs(a['caps']-b['caps']),abs(a['wordlen']-b['wordlen']),
            min(len(a['bio']),len(b['bio']))/max(len(a['bio']),len(b['bio'])) if a['bio'] or b['bio'] else 1.,
            abs(a['punct']-b['punct']),PLATFORM_CODES.get(tuple(sorted([a['platform'],b['platform']])),-1)])
        rows.append(out)
    return np.asarray(rows,dtype=np.float64).reshape(-1,23),list(TEXT_NAMES)


IMAGE_STATS_NAMES = ('image_any_local','image_both_local','image_one_local_only',
    'image_phash_sim','image_dhash_sim','image_brightness_diff','image_contrast_diff',
    'image_entropy_diff','image_rgb_l1','image_filesize_ratio','image_face_count_diff',
    'image_face_area_diff','image_blur_diff','image_metadata_any')
IMAGE_CONTEXT_NAMES = ('image_caption_any','image_caption_bio_sbert_cross',
    'image_caption_fullname_token_cross','image_caption_username_token_cross')
DESCRIPTOR_COLS = {'has_local_image','has_image_metadata','local_phash','local_dhash',
    'local_brightness','local_contrast','local_entropy','local_avg_r','local_avg_g',
    'local_avg_b','local_file_size_kb','num_faces','face_area_ratio','blur_score',
    'caption_emb_idx','caption_en'}


def _hash_similarity(a,b):
    # Preserve the historical HEX-CHARACTER mismatch, NOT bit-Hamming distance.
    if not a or not b:
        return 0.
    return 1.-sum(x != y for x,y in zip(a,b))/max(len(a),1)


def image_features(df,pairs,descriptors,*,bio_embeddings=None,caption_embeddings=None):
    """Return (float64 (n_pairs,18), ordered names), pure historical formulas.

    descriptors MUST be explicitly supplied, safely dev-linked, one row per df
    row with identical zero-based RangeIndex; never interpret inability to link
    as genuine missing image. Absent modality requires explicit zero flags in
    a caller-audited descriptor table. This API does NOT resolve any image path.
    Caption arrays must use the same frozen normalized encoder as bio arrays.
    """
    _validate_frame(df)
    p = _pairs(pairs,len(df))
    if not isinstance(descriptors,pd.DataFrame) or not descriptors.index.equals(df.index):
        raise ValueError('explicit development-linked descriptor frame required')
    if set(descriptors.columns) != DESCRIPTOR_COLS:
        raise ValueError('descriptor columns must match feature-only descriptor schema exactly')
    for flag in ('has_local_image','has_image_metadata'):
        if not descriptors[flag].isin([0,1]).all():
            raise ValueError('image availability flags must be explicit binary values')
    idxs = descriptors.caption_emb_idx.to_numpy()
    if not np.issubdtype(idxs.dtype,np.integer) or np.any(idxs < -1):
        raise ValueError('caption indices require integer -1 or valid array position')
    caps_present = bool(np.any(idxs >= 0))
    bios = caps = np.empty((0,0),dtype=np.float64)
    if caps_present:
        bios = _embeddings(bio_embeddings,len(df))
        if caption_embeddings is None:
            raise ValueError('caption embedding array required for caption indices')
        caps = np.asarray(caption_embeddings)
        caps = _embeddings(caps,len(caps))
        if caps.shape[1] != bios.shape[1] or idxs.max() >= len(caps):
            raise ValueError('caption embedding dimension/index mismatch')
    records = [_record(r) for r in df.to_dict('records')]
    images = descriptors.to_dict('records')
    rows=[]
    for i,j in p:
        a,b=images[i],images[j]
        both=bool(a['has_local_image'] and b['has_local_image'])
        any_local=bool(a['has_local_image'] or b['has_local_image'])
        meta=bool(a['has_image_metadata'] and b['has_image_metadata'])
        out=[int(any_local),int(both),int(any_local and not both),
            _hash_similarity(a['local_phash'],b['local_phash']) if both else 0.,
            _hash_similarity(a['local_dhash'],b['local_dhash']) if both else 0.]
        out.extend(abs(float(a[k])-float(b[k])) if both else 0.
                   for k in ('local_brightness','local_contrast','local_entropy'))
        out.extend([sum(abs(float(a[k])-float(b[k])) for k in ('local_avg_r','local_avg_g','local_avg_b'))/3. if both else 0.,
            min(float(a['local_file_size_kb']),float(b['local_file_size_kb']))/max(float(a['local_file_size_kb']),float(b['local_file_size_kb']),1e-6) if both else 0.])
        out.extend(abs(float(a[k])-float(b[k])) if meta else 0.
                   for k in ('num_faces','face_area_ratio','blur_score'))
        out.append(int(bool(a['has_image_metadata'] or b['has_image_metadata'])))
        ca,cb=int(a['caption_emb_idx']),int(b['caption_emb_idx'])
        cross_a=float(np.dot(caps[ca],bios[j])) if ca >= 0 else 0.
        cross_b=float(np.dot(caps[cb],bios[i])) if cb >= 0 else 0.
        out.extend([int(ca>=0 or cb>=0),max(cross_a,cross_b)])
        for field in ('fullname','username'):
            out.append(max(fuzz.token_sort_ratio(a['caption_en'],records[j][field])/100. if a['caption_en'] else 0.,
                           fuzz.token_sort_ratio(b['caption_en'],records[i][field])/100. if b['caption_en'] else 0.))
        rows.append(out)
    result=np.asarray(rows,dtype=np.float64).reshape(-1,18)
    if not np.isfinite(result).all():
        raise ValueError('non-finite historical image features')
    return result,list(IMAGE_STATS_NAMES+IMAGE_CONTEXT_NAMES)
