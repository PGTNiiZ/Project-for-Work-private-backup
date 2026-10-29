# D0 — EXPLORATORY

D0-1: DECLARED provenance; ไม่มี independent dual annotation.
D0-2: aggregate schema/coverage ใน metrics/dataset_profile.json (development only).
D0-3: NOT RUN — ไม่มี annotation capacity; ใช้ E7-6 S1/S2; ไม่แต่ง hidden-positive rate.
D0-4: identity/component overlap = 0; split hashใน manifests/split_summary.json. Reused historical population ไม่ใช่ pristine holdout.

{
  "scope": "development folds only",
  "attributes": {
    "username": {
      "missing_rate": 0.002207805441391257,
      "median_length": 11.0,
      "non_ascii_rows": 0,
      "thai_script_rows": 0
    },
    "fullname": {
      "missing_rate": 0.023572568866546652,
      "median_length": 13.0,
      "non_ascii_rows": 0,
      "thai_script_rows": 0
    },
    "bio": {
      "missing_rate": 0.17907000441561088,
      "median_length": 90.0,
      "non_ascii_rows": 3025,
      "thai_script_rows": 21
    },
    "location": {
      "missing_rate": 0.6519819299616182,
      "median_length": 0.0,
      "non_ascii_rows": 706,
      "thai_script_rows": 3
    },
    "links": {
      "missing_rate": 0.16935566047348935,
      "median_length": 19.0,
      "non_ascii_rows": 7,
      "thai_script_rows": 0
    }
  },
  "language_detection": "Unicode script proxy, not validated language identification"
}
