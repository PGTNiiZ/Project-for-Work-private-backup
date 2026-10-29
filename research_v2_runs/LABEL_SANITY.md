# Label Sanity — EXPLORATORY

Source: protocol.json raw_input + raw SHA-256. Code: preflight.py prepare_frame/ground_truth.

{
  "input_rows": 36807,
  "eligible_rows": 36804,
  "quarantined_rows": 3,
  "missing_key_rows": 3,
  "distinct_entities": 15297,
  "group_size_histogram": {
    "1": 1526,
    "2": 6039,
    "3": 7728,
    "4": 4
  },
  "max_group_size": 4,
  "cross_platform_positive_pairs": 29243,
  "platform_counts": {
    "twitter": 13959,
    "googleplus": 11889,
    "instagram": 10956
  },
  "million_positive_guard": true
}

ใช้ canonical normalized source เท่านั้น; ไม่ใช้ nomalized_profiles.csv ที่มี degenerate null grouping ในหลักฐาน Round3. ไม่ได้พิสูจน์ว่า historical models ทุกตัวใช้ labels ชุดเสีย จึงยังไม่เรียก historical impact ว่า CONFIRMED_DEFECT. G0 เป็น researcher declaration ไม่ใช่การรับรอง identity ภายนอก.
