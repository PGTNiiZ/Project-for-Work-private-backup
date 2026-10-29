# Results Summary — Research V2

ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.

## เหตุใดต้องแยกหลักฐาน

งานนี้ทดสอบผลของ attributes, learner, frozen semantic representation, decision policy และ candidate generation แยกกัน ไม่เปรียบ AP ของ sampled historical test กับ natural candidate test. ประสิทธิภาพปลายทางรวม blocking misses และ REVIEW positives ที่ยังไม่ถูกเชื่อมอัตโนมัติ. [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#results]

## Primary contrasts

H1–H3 ใช้ Δcandidate AP, H4 ใช้ relative cost reduction (GA เทียบ best non-GA ที่เลือกบน development), H5 ใช้ ΔPC ที่ exact candidate budget เท่ากัน. ค่าบวกสนับสนุนทิศทางที่เสนอ; ไม่ใช่ F1 ของทั้ง pipeline. B=10,000 paired identity/pigeonhole bootstrap; positive edges ใช้ identity multiplicity ครั้งเดียว และ negative dyads ใช้ product ของทั้งสอง endpoint.

| H | Contrast | Δ | 95% CI | Holm p | TOST Holm p | seed Δ SD | Decision | Evidence |
|---|---|---|---|---|---|---|---|---|
| H1 | lexical GBDT minus best dev-selected single lexical group AP | 0.0983 | [0.0886, 0.1081] | 0.0005 | 1 | 0.0011 | supported | [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#H1] |
| H2 | lexical GBDT minus tuned rule AP | 0.0553 | [0.0488, 0.0617] | 0.0005 | 1 | 0.0008 | supported | [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#H2] |
| H3 | fusion GBDT minus lexical GBDT AP | 0.0003 | [-0.0014, 0.0010] | 1 | 0.0005 | 0.0007 | equivalent | [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#H3] |
| H4 | relative cost reduction GA vs dev-selected best non-GA policy | -0.0904 | [-0.1279, -0.0555] | 0.0005 | 1 | 0.0004 | not supported | [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#H4] |
| H5 | hybrid PC minus dev-selected best lexical PC at exact B0 budget | -0.0003 | [-0.0048, 0.0040] | 1 | 0.0005 | 0.0000 | equivalent | [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#H5] |

Decision supported ต้องมีขอบล่าง CI สูงกว่า SESOI และ primary Holm p<0.05 พร้อม seed stability; equivalence ใช้ approximate centered-bootstrap TOST และ CI90 ใน margin พร้อม Holm ของ equivalence family แยก. ไม่อ้าง joint FWER ของสอง families. ค่า p ไม่ใช่ศูนย์; ดู resolution ตาม B ใน JSON. [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#results]

## Secondary results และขอบเขต

ค่า thresholds, calibration และ optimizer ถูกเลือกจาก development เท่านั้น. H4 cost ใช้ ASSUMPTION 2:1:0.1 และ perfect-review utility; automatic recall ไม่นับ reviewed positives เป็น recovered links. Cost sensitivity ใช้ policy ที่ freeze แล้ว ไม่ optimize ใหม่จาก test. [MAIN@1bc4a8c:research_v2_runs/metrics/secondary_analyses.json#results]

Univariate features, model/seed summaries, leave-one-attribute-out, learning curves และ robustness strata อยู่ใน THESIS_TABLES_TH.md. Development OOF เป็น selection evidence ที่ถูกใช้ซ้ำ ไม่ใช่ nested independent estimate. ไม่มี human audit จึงรายงาน S1/S2 เท่านั้น; S2 precision=1 เป็นผลเชิงกลจากการเอา unlabeled negatives ออก ไม่ใช่การพิสูจน์ label correctness. [MAIN@1bc4a8c:research_v2_runs/metrics/secondary_analyses.json#label_sensitivity]

H4 เลือก best non-GA จาก development โดยรวม closed-form Chow. Comparator นี้อยู่นอก historical four-gene policy family จึงเป็น overall policy-system comparison ไม่ใช่ isolated GA-versus-search causal effect; การเปรียบเทียบ optimizer แบบ bounds/budget เดียวกันจำกัดที่ GA, random, Sobol และ TPE ใน policy table. H3 equivalence ภายใน margin ไม่ได้แปลว่า semantic ไม่มีประโยชน์ในทุก stratum/ภาษา; near-zero effect อาจติด seed-instability flag โดยไม่ขัดกับ margin-equivalence.

Aggregation clarification: H1–H3 ใช้ AP ของ frozen seed-ensemble probabilities ใน paired bootstrap; matcher table แสดง mean/SD ของ AP แยกแต่ละ seed และ PR curvesใช้ensemble. APเป็น nonlinear metric จึงไม่ควรลบ table means เพื่ออ้างว่าเท่ากับ primary Δพอดี. CI ไม่ได้รวม uncertainty จากการเลือก upstream configuration ใหม่.
