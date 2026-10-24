# E1–E3 feature contract

This contract is about model-input columns, not dataset/population or model outcome equivalence. Under the proposed Gate 9 design, E1 is Logistic Regression + corrected 17 features, E2 is Gradient Boosting + corrected 17 features, and E3 is Gradient Boosting + corrected 18 features (the same 17 plus MiniLM cosine `bert_cos`). E2 and E3 must preserve the first 17 columns byte-for-byte and differ by exactly the final `bert_cos` column. Model family changes between E1 and E2; E2/E3 hold model family fixed and add one feature.

| Experiment | Ordered feature input | Expected count |
|---|---|---:|
| E1 | `FEATURE17_COLUMNS` exactly as registered; Logistic Regression | 17 |
| E2 | `FEATURE17_COLUMNS` exactly as registered; Gradient Boosting | 17 |
| E3 | `FEATURE17_COLUMNS` followed by `bert_cos`; Gradient Boosting | 18 |

### Required checks

1. Assert `E1 == E2 == FEATURE17_COLUMNS` byte-for-byte as ordered names.
2. Assert `E3[:-1] == E2` and `E3[-1] == "bert_cos"`; the ordered schema difference E2→E3 is exactly one appended column.
3. Keep Gradient Boosting, pair population, split, TRAIN sample keys, and all other protocol settings equal between E2 and E3; the intended treatment is MiniLM cosine only. E1 is the Logistic Regression + 17-feature baseline and is not a model-family-controlled comparison to E2.
4. Require identical pair-key population/order and the same 17 base feature values before claiming an E2/E3 feature ablation. Feature-cache verification must be label-free; this Gate has not compared E2/E3 data caches.
5. Do not retroactively assign these new-study E1/E2/E3 labels to historical workbook/source artifacts that reused E2/E3 names. Any source conflict or historical E2/E3 alias must be separately traced to pair-keyed models/features and escalated rather than silently relabeled.

### Independence

All base feature values are deterministic profile-text/platform formulas and do not accept predictions/labels. `name_sim` is unconditional. `bert_cos` is a frozen-embedding comparison in the documented historical lineage; its encoder provenance remains incomplete (see `MINILM_LINEAGE.md`). Neither contract establishes upstream split or cache integrity.
