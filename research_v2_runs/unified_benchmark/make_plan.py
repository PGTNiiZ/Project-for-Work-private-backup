"""Write PLAN.json for the unified development-only benchmark (run once, before any experiment)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEEDS = [11, 23, 42, 71, 101]
FIX = ['name_sim computed for every pair (max Jaro-Winkler over username/fullname cross combinations), never gated by an earlier model score',
       'all TF-IDF/vocabularies fit on outer training folds only (unlabeled text of the evaluated fold never used)',
       'labels: canonical V2 definition (same exact user_folder, different platform); 23,391 development positives']

harness = {
    'classification': 'POST-HOC EXPLORATORY (development reuse; no confirmatory claim)',
    'folds': [0, 1, 2, 3], 'never_read': ['data_derived/sealed_test.parquet', 'data_derived/final', 'data_derived/split_manifest.parquet', 'metrics/final_summary.json', 'metrics/primary_contrasts.json'],
    'ledger_lines_required': 21,
    'labels': 'canonical cross-platform same-entity pairs; total 29,243; development 23,391',
    'outer_evaluation': '4-fold entity-disjoint out-of-fold over folds 0-3; candidate pairs never cross folds',
    'nested_inner_split': {
        'definition': 'for outer fold f, T = other three folds; c = (f+1) mod 4 is the inner selection fold; A = T minus c',
        'hyperparameter_tuning': 'fit on rows of A, AP on rows of c (labels of f never read)',
        'inner_scores': 'for every g in T: model fit on T minus g, scores rows of g (cross-fitted, never scores own training rows)',
        'calibration_fit': 'on inner scores of A only; method chosen by pooled Brier of a 2-way swap inside A (fit on one fold of A, score the other, both directions); chosen method refit on all of A',
        'decision_rule_tuning': 'on calibrated inner scores of c only (labels, blocking misses of c)',
        'outer_scores': 'model fit on all of T scores fold f; the A-fitted calibrator and c-tuned rule are applied unchanged',
        'disclosed_shift': 'outer model uses 3 folds while calibrator/rule inputs come from 2-fold models'},
    'calibration_methods': ['platt', 'isotonic'], 'calibration_rule': 'minimum pooled Brier on the inner 2-way swap; ties -> platt',
    'score_space': 'probability models: logit of clipped probability; LinearSVM: raw decision value',
    'model_tuning': {'optimizer': 'optuna TPE seed 42', 'configs': 200, 'objective': 'AP on inner selection fold c', 'train_negative_ratio': 3},
    'model_seeds': SEEDS, 'rule_seeds': SEEDS, 'rule_search_budget': 2048,
    'metrics': ['blocking PC (per fold and pooled)', 'candidate AP (raw outer scores pooled over 4 folds, mean/SD over seeds)',
                'end-to-end automatic recall = automatic true matches / 23,391', 'recall if review is perfect = (automatic TP + reviewed positives) / 23,391',
                'automatic precision', 'false merges (automatic FP)', 'review count',
                'cost per pair at FP:FN:REVIEW = 2:1:0.1; FN = true pairs neither auto-matched nor reviewed, including blocking misses; denominator = all cross-platform pairs inside the four development folds',
                'cost sensitivity: the same frozen decisions re-costed at 5:1:0.02'],
    'candidate_budget': 'primary = 1x sparse budget (fold-local count of V2 sparse matched candidates = B0 native count); 2x reported as a secondary PC-only table',
    'bug_fixes_applied_to_all_historical_methods': FIX,
    'parallelism': 'up to 4 concurrent model jobs, 2 threads each; runtime per row logged',
    'append_only': 'metrics/<row>.json and ledger/runs.jsonl refuse to overwrite',
    'stage0_smoke': 'one row with 2 configs and 1 seed to check plumbing; written to work/smoke only and never reported',
}

spaces = {
    'GBDT': 'protocol.json GBDT space (learning_rate {0.03,0.1}, max_leaf_nodes {15,31,63}, max_iter {50,100,150}, min_samples_leaf {20,50}, l2 log[1e-6,10])',
    'LR': 'protocol.json LR space (C log[1e-3,100], class_weight {None,balanced}) + StandardScaler fit on training rows',
    'RF': 'n_estimators {200,400}, max_depth {8,12,18,None}, min_samples_leaf {1,5,20}, max_features {sqrt,0.5} (pre-declared here; no historical space recorded)',
    'ExtraTrees': 'same space as RF',
    'MLP': 'sklearn MLP hidden {(64,),(128,64),(256,128,64)}, alpha log[1e-6,1e-2], learning_rate_init log[1e-4,1e-2], early_stopping on 10% of training rows, max_iter 100, StandardScaler',
    'AdaBoost': 'n_estimators {50,100,200}, learning_rate log[0.05,1.5], depth-1 stumps',
    'LinearSVM': 'LinearSVC C log[1e-3,100], class_weight {None,balanced}, StandardScaler; scores = decision_function',
}

rows = []
def row(id_, layer, stage, name, job, rule, **kw):
    rows.append(dict(id=id_, layer=layer, stage=stage, name_th=name, model_job=job, rule=rule, **kw))

# ---- model jobs (each trained once, reused by rows) ----
jobs = {}
def job(id_, blocker, features, learner, tuning='TPE200', note=''):
    jobs[id_] = dict(blocker=blocker, features=features, learner=learner, tuning=tuning, note=note)

REF = 'J_sparse_FLEX35_GBDT'
for b in ['B0', 'sparse', 'dense', 'hybrid_union', 'hybrid_rrf', 'multipass', 'embhash']:
    job(f'J_{b}_FLEX35_GBDT', b, 'FLEX35', 'GBDT')
for f in ['FSEM', 'FUSION41', 'H23', 'R17', 'R18', 'BLOOM250', 'BLOOM500', 'BLOOM1000', 'BLOOM2000', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'H23_FLEX35']:
    job(f'J_sparse_{f}_GBDT', 'sparse', f, 'GBDT')
for m in ['LR', 'RF', 'ExtraTrees', 'MLP', 'AdaBoost', 'LinearSVM']:
    job(f'J_sparse_FLEX35_{m}', 'sparse', 'FLEX35', m)
job('J_B0_H23_GBfixed', 'B0', 'H23', 'GBfixed', 'none (documented fixed config)', 'thesis/production GB n=300 lr=0.05 depth=6 -> HistGradientBoosting(max_iter=300, learning_rate=0.05, max_depth=6); image features unavailable')
job('J_B0_R17_GBfixed', 'B0', 'R17', 'GBfixed', 'none (documented fixed config)', 'GB-17')
job('J_B0_R18_GBfixed', 'B0', 'R18', 'GBfixed', 'none (documented fixed config)', 'GB-18 / ICSEC v2 model')
job('J_B0_R18_IdentityMLP', 'B0', 'R18', 'IdentityMLP', 'none (documented fixed config)', 'R2/R3 IdentityMLP [256,128,64], FocalLoss(0.25,2), Adam 1e-3, wd 1e-5, cosine LR, 30 epochs, patience 5, neg ratio 3; early stopping on a 15% entity-hash slice of the training rows')
job('J_multipass2x_H23_FLEX35_GBDT', 'multipass2x', 'H23_FLEX35', 'GBDT')

# ---- Layer 1: blockers (features FLEX35, GBDT, three-way rule) ----
names_b = {'B0': 'คัดคู่ด้วยคีย์ 3 ตัวอักษรแรก + โดเมน (B0)', 'sparse': 'TF-IDF ทั้งโปรไฟล์ (sparse) — ค่าอ้างอิง', 'dense': 'เวกเตอร์ความหมาย MiniLM (dense)',
           'hybrid_union': 'รวม sparse + dense แบบ union', 'hybrid_rrf': 'รวม sparse + dense แบบจัดอันดับ (RRF)', 'multipass': 'หลายเส้นทาง (post-hoc)',
           'embhash': 'hash ของ embedding แบบ R6 (MiniLM ตรึง + hash head 64 บิต)'}
for b, n in names_b.items():
    row(f'L1_block_{b}', 1, 'blocking', n, f'J_{b}_FLEX35_GBDT', 'three_way', budget='1x',
        source={'B0': 'protocol.json B0; pairs_<f>_B0.npy', 'sparse': 'pairs_<f>_sparse_matched.npy (V2)', 'dense': 'pairs_<f>_dense_matched.npy', 'hybrid_union': 'pairs_<f>_hybrid_union_matched.npy',
                'hybrid_rrf': 'pairs_<f>_hybrid_rrf_matched.npy', 'multipass': 'posthoc multipass_dev_fold<f>_1.0x.npy', 'embhash': 'new: experiments/code/exp_r6_bert_er.py design re-implemented'}[b],
        deviations=(['frozen MiniLM retrieval embeddings instead of frozen DistilBERT; hash head trained per fold on the other three folds; candidates ranked by Hamming distance then code cosine and cut at the 1x budget (original used radius buckets with no budget)'] if b == 'embhash' else []))
for b in ['sparse', 'multipass', 'embhash']:
    row(f'L1_pc2x_{b}', 1, 'blocking_2x', f'PC ที่งบ 2 เท่า: {names_b[b]}', None, None, budget='2x', metrics_only='PC')

# ---- Layer 1: features (sparse 1x, GBDT, three-way) ----
names_f = {'FLEX35': 'feature ความคล้ายของข้อความ 35 ตัว (F-LEX35) — ค่าอ้างอิง', 'FSEM': 'feature ความหมาย 6 ตัว (F-SEM)', 'FUSION41': 'ข้อความ + ความหมาย 41 ตัว (V2 fusion)',
           'H23': 'feature งานก่อน 23 ตัว (historical-23 = ฐานของ N0)', 'R17': 'feature ชุด R 17 ตัว (name_sim แก้แล้ว)', 'R18': 'feature ชุด R 17 + ความคล้าย MiniLM (18 ตัว)',
           'BLOOM250': 'ชื่อเข้ารหัส Bloom L=250 + 10 feature ที่ไม่ใช่ชื่อ', 'BLOOM500': 'Bloom L=500', 'BLOOM1000': 'Bloom L=1000', 'BLOOM2000': 'Bloom L=2000',
           'N1': 'งานก่อน 23 + Damerau ของชื่อ (N1)', 'N2': 'งานก่อน 23 + char n-gram ของชื่อ (N2)', 'N3': 'งานก่อน 23 + token set ของชื่อ (N3)', 'N4': 'งานก่อน 23 + handle (N4)',
           'N5': 'งานก่อน 23 + ชื่อข้ามช่อง (N5)', 'N6': 'งานก่อน 23 + char n-gram + handle (N6)', 'H23_FLEX35': 'ชุดรวม งานก่อน 23 + ข้อความ 35 (58 ตัว)'}
fdev = {'H23': ['bio_mentions constant empty (not in dev schema)', 'bio embedding = frozen MiniLM, not MPNet', 'bio TF-IDF fit on training folds only'],
        'R17': ['rapidfuzz Jaro-Winkler/Levenshtein instead of jellyfish (same formulas)', 'text = V2-normalized fields', 'same_platform is constant 0 for cross-platform candidates', 'name_sim ungated (bug fix)'],
        'R18': ['as R17', 'bert_cos = cosine of MiniLM (pinned revision) of "fullname bio location" from V2-normalized text'],
        'BLOOM': ['salt, k=10, bigrams as original; non-name columns from R17', 'text = V2-normalized fields'],
        'N': ['original base = multimodal model with images; here base = historical-23 (images unavailable), so N0 == H23 row', 'name primitives imported from src/identity_resolution/core/name_similarity.py on V2-normalized username/fullname', 'N6 groups = char_ngram + handle (from original N6 config)']}
for f, n in names_f.items():
    if f == 'FLEX35':
        continue
    key = 'BLOOM' if f.startswith('BLOOM') else ('N' if f[0] == 'N' and f[1:].isdigit() else f)
    row(f'L1_feat_{f}', 1, 'features', n, f'J_sparse_{f}_GBDT', 'three_way', deviations=fdev.get(key, []))
row('L1_feat_FLEX35', 1, 'features', names_f['FLEX35'], REF, 'three_way', alias_of='L1_block_sparse')

# ---- Layer 1: models (sparse 1x, FLEX35, three-way) ----
names_m = {'GBDT': 'GBDT (HistGradientBoosting) — ค่าอ้างอิง', 'LR': 'logistic regression', 'RF': 'random forest', 'ExtraTrees': 'extra trees', 'MLP': 'MLP (sklearn)', 'AdaBoost': 'AdaBoost', 'LinearSVM': 'linear SVM'}
for m, n in names_m.items():
    row(f'L1_model_{m}', 1, 'model', n, REF if m == 'GBDT' else f'J_sparse_FLEX35_{m}', 'three_way', space=spaces[m], **({'alias_of': 'L1_block_sparse'} if m == 'GBDT' else {}))

# ---- Layer 1: decision rules (on REF scores) ----
rules = {
    'manual_098_095': ('เกณฑ์มือ 0.98/0.95 (R0)', 'fixed'), 'stage18': ('กฎ stage 18 genome [0.98,0.95,0.9,0.7]', 'fixed'), 'fixed_05': ('คงที่ 0.5', 'fixed'),
    'f1max': ('threshold ที่ F1 สูงสุดบน fold เลือก (grid protocol 99 ค่า)', 'grid'), 'closed_cost': ('threshold สูตรปิด FP/(FP+FN)=2/3', 'fixed'), 'chow': ('Chow ต้นทุน 2:1:0.1', 'fixed'),
    'dual_sobol': ('สองเกณฑ์ ค้นด้วย Sobol ไม่สุ่มสลับ (ICSEC B1)', '2048'), 'three_way': ('สองเกณฑ์ ค้นแบบสุ่ม (V2 three-way) — ค่าอ้างอิง', '2048'),
    'genome_GA': ('กฎ 4 ยีน + name_sim ค้นด้วย GA', '2048'), 'genome_sobol': ('กฎ 4 ยีน ค้นด้วย Sobol สุ่มสลับ', '2048'), 'genome_TPE': ('กฎ 4 ยีน ค้นด้วย TPE', '2048'),
    'genome_random': ('กฎ 4 ยีน ค้นแบบสุ่ม', '2048'), 'feature_aware_GA': ('GA ที่ให้น้ำหนักกลุ่มหลักฐาน (7 ยีน)', '2048')}
for r, (n, b) in rules.items():
    extra = {'alias_of': 'L1_block_sparse'} if r == 'three_way' else {}
    dev = []
    if r == 'feature_aware_GA':
        dev = ['original 10 genes over probability/name/bio/url/location/social/image/style; social, image and style unavailable in F-LEX35 -> 7 genes (t_match, t_review, w_probability, w_name, w_bio, w_url, w_location)',
               'group score = max of that group\'s Jaro-Winkler/TF-IDF/exact columns, availability = both_present', 'GA population 64, elites 12, uniform crossover, mutation p=0.4 sigma=0.05, 2048 evaluations (original pop 128 x 100 generations)']
    if r == 'dual_sobol':
        dev = ['original budget 12,000; harness budget 2,048; unscrambled Sobol is seed-free so all rule seeds coincide']
    row(f'L1_rule_{r}', 1, 'decision_rule', n, REF, r, search_budget=b, deviations=dev, **extra)

# ---- Layer 2: historical systems ----
EXACT = 'exact tier: pairs with identical username (>=3 chars) or identical non-empty link are automatic MATCH regardless of score (as in production/R-series/ICSEC)'
L2 = [
    ('L2_R0', 'R0: คะแนนเดิม + เกณฑ์มือ 0.98/0.95', 'J_B0_H23_GBfixed', 'manual_098_095', True, ['original score came from the 41-feature multimodal model with images; re-implemented with the 23 text/attribute features of the same thesis suite', 'model trained inside the harness (original production model saw the whole corpus)', 'harness calibration (original isotonic)']),
    ('L2_R1', 'R1: คะแนนเดิม + GA 4 ยีน (ต้นทุน 5:1:0.02)', 'J_B0_H23_GBfixed', 'genome_GA_5_1_002', True, ['as R0', 'GA harness settings, 2,048 evaluations (original pop 60 x 40 generations ~1,980)', 'objective cost 5:1:0.02 as original']),
    ('L2_R3', 'R3: MiniLM feature 18 + IdentityMLP + GA (5:1:0.02)', 'J_B0_R18_IdentityMLP', 'genome_GA_5_1_002', True, ['MLP trained on entity-disjoint inner folds (original: 85% of val pairs, pair-level split)', 'GA tuned on held inner fold (original: on rows used for training)', 'R18 feature deviations']),
    ('L2_GB17', 'GB-17: GB 17 feature + เกณฑ์มือ', 'J_B0_R17_GBfixed', 'manual_098_095', True, ['HistGradientBoosting equivalent of GradientBoosting(300,0.05,6)', 'name_sim ungated']),
    ('L2_GB18GA', 'GB-18 + GA (ICSEC v1, ต้นทุน 2:1:0.1)', 'J_B0_R18_GBfixed', 'genome_GA', True, ['as GB-17', 'GA harness settings and 2,048 evaluations']),
    ('L2_ICSEC_B1', 'ICSEC v2 B1: GB-18 + สองเกณฑ์ Sobol', 'J_B0_R18_GBfixed', 'dual_sobol', True, ['budget 2,048 instead of 12,000', 'ICSEC v2 routing dropped cross-role pairs; harness keeps fold-local candidates']),
    ('L2_ICSEC_B3', 'ICSEC v2 B3: GB-18 + กฎขยาย GA', 'J_B0_R18_GBfixed', 'genome_GA', True, ['original GA mutation-only pop 60 at 12,000 evaluations; harness GA with crossover at 2,048']),
    ('L2_thesis23', 'วิทยานิพนธ์: GB 23 feature + threshold F1 สูงสุด', 'J_B0_H23_GBfixed', 'f1max', True, ['original evaluated on sampled pairs without blocking; here deployed on B0 candidates', 'image features unavailable']),
    ('L2_V2final', 'V2 ระบบสุดท้าย: sparse + fusion GBDT + สามทาง', 'J_sparse_FUSION41_GBDT', 'three_way', False, ['V2 calibrator/policy were selected on reused development OOF; here nested', 'alias of L1_feat_FUSION41']),
    ('L2_posthoc_combined', 'post-hoc: หลายเส้นทาง 2× + ชุดรวม 58 + Chow', 'J_multipass2x_H23_FLEX35_GBDT', 'chow', False, ['own nested calibrator (original transported the V2 calibrator)', 'budget 2x (its native configuration), so not equal-budget with Layer 1']),
]
for id_, n, j, r, ex, dev in L2:
    row(id_, 2, 'historical_system', n, j, r, exact_tier=ex, deviations=FIX + dev + ([EXACT] if ex else []), **({'alias_of': 'L1_feat_FUSION41'} if id_ == 'L2_V2final' else {}))

excluded = [
    ('image features (thesis 37/41, historical-41, feature-aware image gene)', 'no development-only image linkage can be verified; raw/image caches contain sealed-test profiles'),
    ('#1 first name-similarity matching (Jan 2026)', 'no result artifact and no recoverable split/config'),
    ('#3 SBERT/MPNet bio-vector notebooks', 'no recoverable metric/config'),
    ('N7 phonetic name group', 'excluded as instructed by the researcher; NOTE: code exists (feature_registry N7, latin_soundex_match) so it is recoverable in principle'),
    ('bigram top-1 ranking (#2)', 'different task (top-1 per source profile) and different label files'),
    ('R2, R4, R5 as full systems', 'not requested in Layer 2; their representations are covered in Layer 1 (R18, Bloom)'),
    ('R6 hash head + match head end-to-end (R6-GA)', 'match head on frozen DistilBERT not requested; blocking part covered by L1_block_embhash'),
    ('notebook IdentityMLP v1/v2 (#4)', 'notebooks absent from checkout; config only partially recoverable'),
    ('strict MLP 22 / leak-safe 22 features / 7-family benchmark as originally configured', 'feature lists live in absent run directories; model families covered in Layer 1 on F-LEX35'),
]

plan = {'title': 'Unified development-only benchmark', 'created_utc': None, 'harness': harness, 'model_spaces': spaces,
        'model_jobs': jobs, 'rows': rows, 'excluded': [dict(item=a, reason=b) for a, b in excluded],
        'rule_cost_variants': {'genome_GA_5_1_002': 'genome GA with objective cost 5:1:0.02 (R-series original weights)'}}
import datetime as dt
plan['created_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
out = ROOT / 'PLAN.json'
if out.exists():
    raise SystemExit('PLAN.json exists; plan is frozen')
out.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + '\n')
print(len(rows), 'rows;', len(jobs), 'model jobs')
