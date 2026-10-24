# Full 2M Feature-Aware GA Report

## Scope

- Source rows: 2,086,245
- Model-scored candidates: 2,073,842
- Exact tier held constant: 12,403
- Feature chunks: 42
- Policy selection: validation only
- Held-out test: evaluated once after policy freeze

## Evidence coverage on validation

| Group | Coverage | Positive support | High-score positive rate |
|---|---:|---:|---:|
| name | 100.00% | 9,558 | 0.0095 |
| bio | 65.70% | 6,195 | 0.2996 |
| url | 70.41% | 6,849 | 0.2951 |
| location | 0.00% | 0 | 0.0000 |
| image | 11.16% | 1,067 | 0.0000 |
| style | 65.70% | 6,195 | 0.0094 |

## Selector GA on validation

| Guard | Cost | Precision | Recall | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|
| style | 2550.74 | 0.9887 | 0.1556 | 17 | 2089 | 18,837 |
| image | 2551.02 | 0.9886 | 0.1544 | 17 | 2089 | 18,851 |
| score_only | 2551.06 | 0.9886 | 0.1545 | 17 | 2089 | 18,853 |
| url | 2560.84 | 0.9874 | 0.1554 | 19 | 2089 | 18,842 |
| bio | 2565.80 | 0.9868 | 0.1566 | 20 | 2089 | 18,840 |
| name | 2834.72 | 0.9848 | 0.6254 | 92 | 2089 | 14,286 |

## Frozen winner

```json
{
  "policy": "selector:style",
  "validation_cost": 2550.74,
  "guard": "style",
  "thresholds": [
    0.9966566711660273,
    0.9641082008999179,
    0.9990748438029837,
    0.2710219517914981
  ],
  "selection_rule": "lower validation decision cost; no test metric was read before freeze"
}
```

## Sealed test and full projection

```json
{
  "policy": {
    "policy": "selector:style",
    "validation_cost": 2550.74,
    "guard": "style",
    "thresholds": [
      0.9966566711660273,
      0.9641082008999179,
      0.9990748438029837,
      0.2710219517914981
    ],
    "selection_rule": "lower validation decision cost; no test metric was read before freeze"
  },
  "scored_test_metrics": {
    "fp": 1,
    "fn": 879,
    "review": 4975,
    "precision": 0.9984567901234568,
    "recall": 0.16042648152739897,
    "f1": 0.2764366588335826,
    "cost": 983.5
  },
  "system_test_metrics": {
    "TP": 4383,
    "FP": 12,
    "FN": 1885,
    "REVIEW": 4975,
    "precision": 0.9973,
    "recall": 0.4995,
    "F1": 0.6656,
    "cost": 2044.5
  },
  "full_projection_metrics": {
    "TP": 14474,
    "FP": 92,
    "FN": 6284,
    "REVIEW": 34955,
    "precision": 0.9937,
    "recall": 0.4949,
    "F1": 0.6607,
    "cost": 7443.1
  },
  "test_evaluation_count": 1
}
```

## Interpretation

ผล test แบบ `system_test_metrics` รวม exact-tier constants และ blocking-missed false negatives แล้ว ส่วน `scored_test_metrics` วัดเฉพาะคู่ที่ model เคย score. Full projection ใช้ policy ที่ freeze แล้วกับ scored candidates ทั้งหมดโดยไม่มีการ tune เพิ่ม

Image evidence รุ่นนี้ใช้ pHash และ caption-to-name token similarity เท่านั้น เนื่องจาก historical caption embedding cache ไม่มีและ dimension ของ legacy paths ไม่สอดคล้องกัน ข้อจำกัดนี้ถูกบันทึกใน manifest และ missing evidence ถูกควบคุมด้วย availability masks
