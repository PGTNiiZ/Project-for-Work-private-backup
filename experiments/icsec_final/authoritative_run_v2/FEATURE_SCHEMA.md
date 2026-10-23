# v2 feature schema

Feature values are pair-keyed and generated from the authoritative normalized profile snapshot. All missing text is normalized to the empty string. No feature reads `actual`, `user_folder`, split roles, predecessor scores, model outputs, or policy decisions. Similarities are deterministic and bounded in [0, 1]; unavailable evidence uses 0.0. `bert_cos` is the cosine of normalized all-MiniLM-L6-v2 profile embeddings and is the sole learned feature.

## GB-17 (17 handcrafted features)

| # | Name | Source fields | Formula / logic | Learned? | Label-dependent? |
|---|---|---|---|---|---|
| 1 | username_jaro | userName_a, userName_b | Jaro similarity after Unicode NFKC, case-fold, trim, empty normalization | No | No |
| 2 | username_lev_sim | userName_a, userName_b | 1 - normalized Levenshtein distance | No | No |
| 3 | username_token_sort | userName_a, userName_b | token-sort similarity / 100 | No | No |
| 4 | fullname_jaro | fullName_a, fullName_b | Jaro similarity after the same normalization | No | No |
| 5 | fullname_lev_sim | fullName_a, fullName_b | 1 - normalized Levenshtein distance | No | No |
| 6 | fullname_token_sort | fullName_a, fullName_b | token-sort similarity / 100 | No | No |
| 7 | name_sim | userName_a, fullName_a, userName_b, fullName_b | max of four Jaro-Winkler cross-field similarities; 0.0 if no non-empty pair | No | No |
| 8 | bio_jaccard | bio_a, bio_b | Jaccard of normalized whitespace token sets; 0.0 if either set empty | No | No |
| 9 | bio_len_ratio | bio_a, bio_b | min length / max length; 0.0 if either empty | No | No |
| 10 | both_have_bio | bio_a, bio_b | 1.0 iff both normalized values are non-empty, else 0.0 | No | No |
| 11 | location_jaro | location_a, location_b | Jaro similarity after the same normalization | No | No |
| 12 | location_exact | location_a, location_b | 1.0 iff both are non-empty and equal after normalization | No | No |
| 13 | both_have_location | location_a, location_b | 1.0 iff both normalized values are non-empty | No | No |
| 14 | same_platform | platform_a, platform_b | 1.0 iff platform values match, else 0.0 | No | No |
| 15 | username_len_diff | userName_a, userName_b | absolute normalized-string length difference | No | No |
| 16 | fullname_wordcount_diff | fullName_a, fullName_b | absolute normalized whitespace-token count difference | No | No |
| 17 | username_prefix3_match | userName_a, userName_b | 1.0 iff both have at least 3 chars and first 3 chars match | No | No |

`name_sim` is not gated by a predecessor score and is never replaced with zero because of a decision source. Missing values are the only reason for its zero boundary.

## GB-18

GB-18 is exactly the GB-17 ordered representation above plus feature 18, `bert_cos`:

- source: pair profile texts built from full name, bio, and location;
- formula: dot product of normalized all-MiniLM-L6-v2 embeddings;
- missing profile text: the deterministic `[empty]` sentinel before embedding;
- learned: yes (fixed pretrained model, no task-label fitting);
- label-dependent: no.

Feature artifacts must contain non-identifying pair keys plus feature columns. Do not publish names, usernames, biographies, URLs, images, entity IDs, or linkable raw profile IDs.
