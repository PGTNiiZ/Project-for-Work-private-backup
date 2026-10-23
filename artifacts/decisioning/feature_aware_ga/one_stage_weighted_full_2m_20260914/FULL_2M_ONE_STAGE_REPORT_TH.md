# One-Stage Weighted GA บนข้อมูล 2.086 ล้านคู่

GA จูนและเลือก policy จาก validation population ของ full cache จำนวน 1,010,926 model-scored คู่ แล้ว freeze ก่อนเปิด test จากนั้น project กับ
`scored_pairs_enriched.parquet` ทั้งหมด 2,086,245 คู่ ประกอบด้วย model-scored
2,073,842 คู่และ exact tier 12,403 คู่. Exact tier คงคำตัดสิน MATCH เดิม.

Thresholds: `t_match=0.993055, t_review=0.906208`

| Feature | Frozen weight |
|---|---:|
| probability | 0.168553 |
| name | 0.822958 |
| bio | 0.005054 |
| url | 0.000000 |
| location | 0.000000 |
| social | 0.000000 |
| image | 0.003436 |
| style | 0.000000 |

## ผลรวมทุกคู่

| Policy | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|
| one_stage_weighted_10gene | 4,045.6 | 0.9910 | 0.7749 | 0.8697 | 183 | 2,626 | 10,536 |
| legacy_name_guard_4threshold | 5,828.7 | 0.9886 | 0.8026 | 0.8859 | 240 | 3,114 | 22,347 |
| score_only_2threshold | 6,180.9 | 0.9937 | 0.5576 | 0.7144 | 91 | 3,114 | 28,849 |
| original_pipeline | 12,721.6 | 0.9550 | 0.7568 | 0.8444 | 925 | 2,242 | 86,296 |

## One-Stage แยกตาม Split ของ Full Cache

| Split | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| val | 1,019,553 | 2,571.6 | 0.9943 | 0.7755 | 0.8713 | 81 | 1,827 | 5,826 |
| test | 195,440 | 1,000.4 | 0.9967 | 0.7737 | 0.8712 | 20 | 799 | 1,614 |
| drop | 871,252 | 473.6 | 0.0000 | 0.0000 | 0.0000 | 82 | 0 | 3,096 |
| all | 2,086,245 | 4,045.6 | 0.9910 | 0.7749 | 0.8697 | 183 | 2,626 | 10,536 |

Full feature cache รุ่นนี้ไม่มี feature `social` และ location ไม่มี observation; ทั้งสองตัวจึง inactive.
สูตร normalize น้ำหนักใหม่เฉพาะ feature ที่มีข้อมูลต่อคู่. Test ถูกอ่านหลังเขียน freeze manifest และ
ไม่ได้ใช้ย้อนกลับไปปรับ genome.
