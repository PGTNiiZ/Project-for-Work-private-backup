# Gate 4 — corrected feature contract v1

## Scope and authority

This is the corrected authoritative-run-v2 schema in `experiments/icsec_final/authoritative_run_v2/features.py`, not the historical Stage 9 notebook's unrelated 17-column schema and not the legacy R2 score-gated variant. Inputs are the profile fields `userName`, `fullName`, `bio`, `location`, `platform` selected by `profile_row_id`; pair identifiers are metadata, never model features. `FEATURE17_COLUMNS` order is authoritative and exact. All values are cast to float32 by the builder.

Normalization for every source field: null/float NaN → empty string; otherwise Unicode NFKC, `casefold`, trim, remove leading `@` characters (`lstrip('@')`), collapse internal whitespace. No labels, probabilities, model outputs, entity IDs or row IDs enter feature formulas.

| # | Column | Formula after normalization | Range / missing and symmetry |
|---:|---|---|---|
|1|`username_jaro`|RapidFuzz Jaro similarity of the two usernames, or 0 if either is empty|[0,1]; empty→0; symmetric|
|2|`username_lev_sim`|`1 - Levenshtein.distance(a,b)/max(len(a),len(b))`; empty input→0|[0,1]; symmetric|
|3|`username_token_sort`|RapidFuzz `fuzz.token_sort_ratio(a,b)/100`; empty→0|[0,1]; symmetric|
|4|`fullname_jaro`|Jaro similarity of full names, or 0 if either empty|[0,1]; symmetric|
|5|`fullname_lev_sim`|Levenshtein similarity as #2 on full names; empty→0|[0,1]; symmetric|
|6|`fullname_token_sort`|token-sort ratio /100 on full names; empty→0|[0,1]; symmetric|
|7|`name_sim`|Maximum Jaro-Winkler over available comparisons in `{username_a, fullName_a} × {username_b, fullName_b}`; default 0|[0,1]; missing candidate omitted; all missing→0; symmetric under swapping endpoints|
|8|`bio_jaccard`|Jaccard of sets of whitespace-split normalized bio tokens; empty union→0|[0,1]; empty/empty→0; symmetric|
|9|`bio_len_ratio`|`min(len(a),len(b))/max(len(a),len(b))`; both empty→0|[0,1]; one empty→0; symmetric|
|10|`both_have_bio`|1 iff both normalized bios nonempty, else 0|{0,1}; symmetric|
|11|`location_jaro`|Jaro similarity of locations, or 0 if either empty|[0,1]; symmetric|
|12|`location_exact`|1 iff location A is nonempty and equal to B, else 0|{0,1}; symmetric|
|13|`both_have_location`|1 iff both locations nonempty, else 0|{0,1}; symmetric|
|14|`same_platform`|1 iff platform A is nonempty and equals platform B, else 0|{0,1}; symmetric|
|15|`username_len_diff`|`abs(len(a)-len(b))/max(len(a),len(b))`; both empty→0|[0,1]; symmetric|
|16|`fullname_wordcount_diff`|`abs(len(a.split())-len(b.split()))/max(len(a.split()),len(b.split()))`; both zero→0|[0,1]; symmetric|
|17|`username_prefix3_match`|1 iff both usernames have length ≥3 and first 3 characters equal, else 0|{0,1}; symmetric|

Bounds follow metric definitions and binary flags; generated NaN/infinity are not intentional missing-value encodings. Missing text is mapped to deterministic zero/false as specified, so the 17-vector has no null feature values. Symmetry is intended for unordered pair scoring. The profile-row identifiers are retained in output as keys only.

## Independence / exclusions

Builder signature accepts `pairs, profiles`; it requires endpoint row IDs and looks up the five named text/platform fields. There is no score, label, target, entity-group, embedding or pretrained-model argument. `name_sim` is unconditional maximum cross-field Jaro-Winkler, not the historical `score >= .5` gated feature. This is formula-level score independence; it does not establish that upstream profile text or pair selection was generated without information leakage. MiniLM cosine is a separate optional 18th column, not part of this 17-vector.

## Evidence boundary

Phase 1 reports all 17 corrected columns replayed against the existing 2,073,842-row GB17 cache with 0 mismatches and max absolute difference 0. That is an audit result recorded in `dataset_v2_feature_verification.json`; this Gate did not access caches or labels and does not independently reproduce that result.
