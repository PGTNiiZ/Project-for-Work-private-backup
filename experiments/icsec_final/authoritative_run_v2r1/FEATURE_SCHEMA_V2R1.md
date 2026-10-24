# V2R1 Feature Schema (corrects v2 FEATURE_SCHEMA.md documentation errors)

Feature COMPUTATION is unchanged from v2 (`authoritative_run_v2/features.py`
and the frozen caches). Only the documentation is corrected here.

## GB-17 (ordered)
1. username_jaro          — Jaro similarity of normalized usernames, [0,1]
2. username_lev_sim       — normalized Levenshtein similarity, [0,1]
3. username_token_sort    — token-sort similarity, [0,1]
4. fullname_jaro          — Jaro similarity of normalized full names, [0,1]
5. fullname_lev_sim       — normalized Levenshtein similarity, [0,1]
6. fullname_token_sort    — token-sort similarity, [0,1]
7. name_sim               — see below
8. bio_jaccard            — token Jaccard of biographies, [0,1]
9. bio_len_ratio          — min/max biography length ratio, [0,1]
10. both_have_bio         — {0,1}
11. location_jaro         — Jaro similarity of locations, [0,1]
12. location_exact        — {0,1}
13. both_have_location    — {0,1}
14. same_platform         — {0,1}; constant 0 in this cross-platform corpus
15. username_len_diff     — length difference divided by the larger length
16. fullname_wordcount_diff — word-count difference divided by larger count
17. username_prefix3_match  — {0,1}

Normalization: NFKC + casefold + whitespace collapse + leading '@' stripped.

## name_sim (corrected description)
The UNCONDITIONAL MAXIMUM **Jaro-Winkler** similarity across the four
implemented cross-field name comparisons (username_a/fullname_a versus
username_b/fullname_b), computed over nonempty operands; comparisons with a
missing operand are omitted. Default is 0.0 when no comparison is possible.
NOTE: name_sim can also be 0 for nonempty but entirely dissimilar strings —
zero does NOT imply missing evidence.

## GB-18 = GB-17 + bert_cos (exactly one addition)
18. bert_cos — cosine similarity of normalized all-MiniLM-L6-v2 embeddings
    of "fullName + bio + location" (empty profile text → "[empty]" sentinel).
    CONCEPTUAL RANGE [-1, 1], NOT [0, 1]. The frozen cache contains negative
    values (observed minimum ≈ -0.265). The encoder is not fine-tuned and
    receives no labels. The "[empty]" sentinel means missing semantic text is
    represented by the sentinel's embedding, not an explicit zero.
