# Historical Comparison — ขอบเขตที่เปรียบได้

ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.

ไม่มี historical row ที่ใช้ split, candidate cohort, prior, decision semantics และ thresholds เดียวกับรอบใหม่ครบทุกข้อ จึงไม่รายงาน numerical delta หรือ ranking ข้ามรุ่น.

| Historical result | Population / limitation | การใช้ที่อนุญาต |
|---|---|---|
| R3 F1=0.8373 | md5 entity-test30%; historical exact tier + misses; test reused ≥15 | REFERENCE_ONLY; ไม่เทียบกับ candidate F1 |
| Thesis GB AP=0.9789 / F1=0.9340 | sampled test8,313 pairs; positives4,387; isotonic; threshold0.35 | REFERENCE_ONLY; natural candidate prior ต่างกัน |
| Production precision=0.9550 | whole corpus automatic MATCH; ไม่ใช่ heldout fold | REFERENCE_ONLY; ไม่ยืนยัน generalization |
| ICSEC v2 decision F1=0.8903 / revised e2e F1=0.8610 | 3 historical partitions; REVIEW-positive denominator ต่างกัน | REFERENCE_ONLY; ต้องแยก decision/e2e |

แหล่ง historical ทั้งหมด: [V2R:METRIC_POPULATION_MAP.md#Metric–Population Map] [V2R:METHODOLOGICAL_RISKS.md#R-15] [V2R:METHODOLOGICAL_RISKS.md#R-18]. ข้อมูลใหม่: [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#results]

B0 รอบใหม่ replicate key union ใน S1 แต่ exact candidates ไม่ได้รับ privileged AUTO_EXACT MATCH bypass; ทุกคู่ผ่าน matcher/policy เดียวกัน. ดังนั้นแม้ PC ใกล้เดิม ก็ไม่ใช่การ replicate production decision workflow ทั้งเส้น. [MAIN@1bc4a8c:research_v2_runs/final_run.py#FinalContext]
