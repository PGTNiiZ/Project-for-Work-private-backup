# Leakage Audit — EXPLORATORY

{
  "entity_overlap": 0,
  "component_overlap": 0,
  "same_platform_username_cross_identity_components": 17,
  "folds": [
    {
      "fold": 0,
      "entities": 3060,
      "profiles": 7356,
      "ground_truth_pairs": 5841
    },
    {
      "fold": 1,
      "entities": 3059,
      "profiles": 7365,
      "ground_truth_pairs": 5858
    },
    {
      "fold": 2,
      "entities": 3060,
      "profiles": 7358,
      "ground_truth_pairs": 5842
    },
    {
      "fold": 3,
      "entities": 3059,
      "profiles": 7362,
      "ground_truth_pairs": 5850
    },
    {
      "fold": 4,
      "entities": 3059,
      "profiles": 7363,
      "ground_truth_pairs": 5852
    }
  ],
  "routing": "both endpoints same fold; no negative edges across folds"
}

Split manifest SHA-256: 9134cae8dc8039a1e8a80dfedcb81dafabc31d3706a72bb2c8c970f862c1fdcc
Identity IDs/row mappings อยู่เฉพาะ data_derived ที่ gitignore; ไม่มี identifiers ในรายงาน. Primary features ไม่ใช้ original profile_id, user_folder หรือ historical predecessor scores. Same-account aliases ใช้ connected component เฉพาะ split grouping ไม่แก้ ground truth.
