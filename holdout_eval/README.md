# holdout_eval — การประเมินแบบสามชั้นสำหรับ Research V2

รันทุกคำสั่งจากโฟลเดอร์นี้  ติดตั้ง: `pip install pandas numpy scikit-learn requests recordlinkage`

## ลำดับการรัน
1. Freeze pipeline (ก่อนเปิด holdout ใดๆ) แล้ว commit `freeze_manifest.json`
   `python -m common.freeze --repo <repo> --files <model> <config> --threshold <t> --decision-rule "<กฎ>"`
2. เตรียมข้อมูล → `records.csv` (schema กลาง ดู `common/schema.py`)
   - ชั้น 1A: `python tier1/collect_github_social.py --target bluesky --pairs 1200`
   - ชั้น 1B: `python tier1/prepare_cosnet.py --inspect <folder>` แล้วเติม parser
   - ชั้น 2:  `python tier2/prepare_febrl4.py` และ `python tier2/prepare_ncvoters.py --inspect <folder>`
   - ชั้น 3:  `python tier3/synth_usernames.py --records tier2/out/febrl4_records.csv --out tier3/out/febrl4`
3. รัน pipeline ที่ freeze แล้วกับ `records.csv` → `scores.csv` (left_id,right_id,score)
   *ส่วนนี้ต้องเขียน adapter เชื่อมกับ pipeline ใน Project-for-Work*
4. ประเมิน
   `python -m common.evaluate --records <records.csv> --scores scores.csv --left <src> --right <src> --manifest freeze_manifest.json`

ชั้น 2 ใช้โมเดลย่อย 5 ฟีเจอร์ (ชื่อ + location) ชั้น 3 เป็น sensitivity analysis ห้ามรายงานเป็นผล confirmatory
