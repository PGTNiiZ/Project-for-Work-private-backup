# Threats to Validity — Research V2

ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.

## Label และ authorization

user_folder เป็น operational identity assumption; G0/G1 ไม่มี documentary references ใน header. มี same-platform username keys ที่พบหลาย identity labels 17 buckets (field ชื่อ components ใน artifact นับ key buckets ไม่ใช่จำนวน final connected components) ตาม aggregate audit จึงใช้ connected components ใน split ไม่ merge ground truth ตามชื่อ. ไม่มี manual positive/negative audit; URL/link features ยังเสี่ยง label proxy. S1/S2 เป็น sensitivity ไม่ใช่การยืนยัน label. [MAIN@1bc4a8c:research_v2_runs/metrics/leakage_audit.json#results]

## Retrospective exposure และ selection

G5 NOT MET; random split ใหม่ไม่ลบ historical exposure. Development ถูกใช้เลือก blocker/tune classifiers/calibrator/policy ซ้ำ; OOF ไม่ได้เป็น nested independent estimate ของ full pipeline. การเปิด sealed resource ถูก guard ต่อ configuration หลัง commit FINAL_CONFIGS แต่ไม่ได้ทำให้ข้อมูลกลายเป็น confirmatory. [MAIN@1bc4a8c:research_v2_runs/manifests/final_lock.json#results]

## Population และ prior

คู่ข้าม folds ไม่เข้าชุด candidate ของการประเมิน จึงไม่ใช่ whole-graph production prior. E7-4 มี full-graph prior reweight ตาม frozen plan แต่สมมติ conditional error/review rates ไม่เปลี่ยน ไม่ใช่ข้อมูลใหม่ที่สังเกตได้. AP sampled historical test และ AP natural candidate เทียบตรงไม่ได้. [MAIN@1bc4a8c:research_v2_runs/metrics/secondary_analyses.json#prior]

## Cost, calibration และ review

Cost2:1:0.1 รวม sensitivity อีกสามค่าเป็น ASSUMPTION; ไม่มี conversion/outcome labels. REVIEW utility สมมติ perfect review แต่ automatic recall ถือ reviewed positives เป็นยังไม่เชื่อม. Calibration method selection บน reused development OOF ไม่พิสูจน์ calibration ในประชากรอื่น. [MAIN@1bc4a8c:research_v2_runs/metrics/policy_selection.json#results]

## Statistical limits

Bootstrap เป็น paired identity/pigeonhole บน frozen predictions; negative edges ใช้ multiplicity ของ endpoint ทั้งสอง. CI conditional ต่อ models ที่ freeze; seed SD แยกต่างหาก ไม่ใช่ CI ที่ครอบคลุม split/domain uncertainty. TOST เป็น approximate centered-bootstrap; Holm primary differences และ Holm equivalence แยก family ไม่อ้าง joint guarantee10 tests. Secondary ablations/strata/factorial เป็น descriptive exploratory; ไม่ถือเป็น additional confirmatory discoveries. [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#results]

## Scope และ implementation

CPU MiniLM English revisionถูกตรึง ไม่ครอบคลุม encoder/model families ทั้งหมด; frozen encoderไม่มี fine-tuning. ข้อมูลเป็น LinkSocial เท่านั้น. ไม่มี T9 image-to-image, privacy attack, Lead Scoring หรือ entity-clustering proof. Hyperparameters ของ learning curves ถูกเลือกจาก full development ก่อน freeze จึงเป็น conditional learning curves ไม่ใช่ nested sample-efficiency proof. [MAIN@1bc4a8c:research_v2_runs/manifests/TIER2_FIXED_PLAN.json#results]

## Privacy และ operational deviations

GitHub metadata ยังเป็น PUBLICทั้งสองrepo; ไม่ push หรือแก้visibility. มี terminal metadata incidentที่เผยชื่อไฟล์ภาพเก่าซึ่งอาจมีhandles; ไม่ลบหรืออ้างว่าไม่เคยเกิด. Output-file PII scan แยกจาก incident นี้; ไม่รับรองzero disclosureของทั้งsession. Operational clockต่อใหม่ตามคำสั่งcontinue; G4 original protocolไม่ถูกแก้. k*freezeเป็นselectionruleและTOST numeric implementation/conservative correctionก่อนfinal เป็นclarifications/deviationsที่เปิดเผย ไม่อ้าง strict literal protocol adherenceทุกข้อ. ดู DEVIATIONS.md และ GATE_RECORD.md.

## ขอบเขต protocol compliance ที่ยังต้อง review

Technical checks ไม่เท่ากับ full strict-v4 compliance. G4 ตรึง k* selection rule แทน numeric k ล่วงหน้า; primary AP ใช้ frozen ensemble aggregation ส่วน table ใช้ seed mean. Supporting summaries คำนวณ validation-only operating-point diagnostics หลัง final แต่ไม่ได้ใช้เปลี่ยน primary system หรือประเมิน thresholds เหล่านั้นบน test. จึงรับรอง no primary retuning ไม่ใช่ zero diagnostic selection ทั้ง session; validation counter นับ ledger-accounted held-fold/objective events ไม่รวมทุก supplemental threshold/metric call. LR และ semantic-only มี development evidence แต่ไม่มี standalone final-test configuration; ไม่เปิดเพิ่มหลัง unblinding.

Branch ยังมี inherited concurrent commit c68c9d20 ซึ่งเปลี่ยน16pathsนอก runs; owned commitsตรวจแยกและไม่ rewrite งานอื่น. ก่อนเผยแพร่ต้อง review branch scope. File-output PII scan ไม่ลบ metadata incident ใน terminal. รายละเอียด DEVIATIONS.md.
