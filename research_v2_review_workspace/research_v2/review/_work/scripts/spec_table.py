"""Per-experiment specification table for the master plan (reads the matrix for IDs/priority/deps)."""
import csv, sys
rows = {r["exp_id"]: r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
# order: execution step from dependency graph
ORDER = {"D0-1":1,"D0-2":1,"D0-3":2,"D0-4":2,"D0-5":2,"E1-1":4,"E1-2":4,"E1-3":4,"E1-4":4,"E1-5":5,"E1-6":11,
 "E2-1":5,"E4-1":5,"E2-3":6,"E2-4":11,"E3-1":6,"E3-2":6,"E3-3":11,"E5-1":6,"E4-2":7,"E5-2":7,"E5-3":7,"E5-4":7,"E5-5":7,
 "E5-6":11,"E4-3":11,"E4-4":11,"E4-5":11,"E6-7":8,"E6-1":8,"E6-2":8,"E6-3":8,"E6-4":8,"E6-5":8,"E6-6":8,"E6-8":11,
 "E7-1":10,"E7-2":10,"E7-3":10,"E7-4":10,"E7-5":10,"E7-6":10,"E7-7":10,"E8-1":12,"E8-2":12,"E8-3":12,"E9-1":12,"E10-1":12,"E2-2":0}
# objective | proposed vs baseline | data/GT requirement | runtime ASSUMPTION | artifacts | acceptance | failure/exclusion
S = {
"D0-1":("ยืนยันที่มาของ GT (LinkSocial) + κ ของ positive ≥200 คู่","—","สิทธิ์ G1; ผู้ตรวจ 2 คน","ASSUMPTION: 3–5 วันคน","label_audit.md, κ","κ ≥ 0.80 และกลไกสร้าง GT มีเอกสาร","κ < 0.80 → แก้ label policy ก่อน; ไม่พบกลไก → H ทุกข้อเป็น exploratory"),
"D0-2":("datasheet ต่อแพลตฟอร์ม","—","G1","ASSUMPTION: 1–2 วัน","datasheet.md","missingness/ภาษา/1:n ครบทุก attribute","—"),
"D0-3":("ประมาณ π_hidden จากคู่ similarity สูงที่ไม่มี label","—","G1, ผู้ตรวจ","ASSUMPTION: 2–3 วันคน","pi_hidden.json + CI","CI กว้าง ≤ ±0.05","ทำไม่ได้ → E7-6 ทำเฉพาะ S1/S2"),
"D0-4":("ตรวจ leakage/บัญชีซ้ำ/การถูกใช้ใน test เดิม","—","split manifest เดิม (md5, icsec-outer, entity_nested_v2)","ASSUMPTION: 1 วัน","leakage_report.md","0 entity ข้าม split; รายการ label-proxy features","พบ leakage → แก้ split ก่อน G3"),
"D0-5":("CI ย้อนหลังของผลประวัติศาสตร์จาก prediction ที่เก็บไว้","—","G1; prediction artifacts","ASSUMPTION: < 1 วัน CPU","historical_ci.json","ติดป้าย exploratory/HIST","ไม่ได้ G1 → ข้าม"),
"E1-1":("replicate B0 (exact tier + prefix3/domain keys) ภายใต้ split V2","B0 (baseline)","positive ทั้งหมดใน fold (รวมที่ blocking พลาด)","ASSUMPTION: นาที CPU","candidates_B0.parquet (ภายใน), pc_report.json","PC ภายใน ±0.005 ของ HIST 0.8867 (sanity)","ต่างมาก → หยุดและตรวจ pipeline"),
"E1-2":("token blocking + purging","E1-1","เหมือน E1-1","ASSUMPTION: นาที","pc_curve.json","ทำเมื่อ E1-3 ไม่ครอบงำ (ตัดสินที่ G4)","—"),
"E1-3":("TF-IDF char n-gram top-k (fit บน D_train)","E1-1","เหมือน E1-1","ASSUMPTION: 5–30 นาที CPU","pc_curve.json","PC–|C| รายงานครบ k∈{1,5,10,20,50}","vocab fit ปน test → EXCLUDE run"),
"E1-4":("dense kNN ด้วย frozen encoder ≤2 ตัว","best lexical","เหมือน E1-1 + model revision","ASSUMPTION: encode 36.8k ข้อความ ~2–10 นาที CPU","pc_curve.json, index stats","PC–|C| ครบ","—"),
"E1-5":("hybrid union/RRF ที่ budget = |C_B0|","best lexical","เหมือน E1-1","ASSUMPTION: นาที","pc_curve.json, recovery.json","ΔPC ตาม H5 (CI)","—"),
"E1-6":("supervised meta-blocking (GSM)","E1-5","label D_train","ASSUMPTION: ชั่วโมง CPU","pc_curve.json","ทำเมื่อ best PC < 0.90 บน validation","—"),
"E2-1":("F-LEX per attribute + univariate PR-AUC","—","D_train/D_dev","ASSUMPTION: 1–5 นาที CPU (~0.6M คู่ within-fold)","features_lex.parquet (ภายใน), feature_report.json","ทุก feature มี unit test; ไม่มี label-proxy ที่ยังไม่ตัดสิน","feature ที่เป็น proxy → รายงานสองแบบ (G2)"),
"E2-3":("tuned weighted rule (200 configs)","rule (baseline H2)","D_dev grouped CV","ASSUMPTION: < 1 ชม. CPU","rule_config.json","budget = T3","—"),
"E2-4":("Fellegi–Sunter EM","E2-3","ไม่ใช้ label ใน fit","ASSUMPTION: นาที","fs_params.json","—","EM ไม่ลู่เข้า → รายงาน"),
"E3-1":("LR บน F-LEX","E2-3","D_dev","ASSUMPTION: < 1 ชม.","model+config hash","—","—"),
"E3-2":("GBDT บน F-LEX (= E5-1)","E2-3 (H2) / reference ของ H1,H3","D_dev","ASSUMPTION: 5–20 CPU-ชม. รวม tuning","model+OOF scores","seed SD < |Δ|/2","—"),
"E3-3":("RF บน F-LEX","E3-2","D_dev","ASSUMPTION: ชั่วโมง","—","ทำเมื่อ LR กับ GBDT ต่างมาก","—"),
"E4-1":("F-SEM cosine (frozen)","—","model revision ตรึง","ASSUMPTION: encode นาที","embeddings cache (ภายใน)","revision hash บันทึก","—"),
"E4-2":("semantic-only classifier (เดิม E5-2)","E3-2","D_dev","ASSUMPTION: 5–20 CPU-ชม.","OOF scores","—","—"),
"E4-3":("fine-tune bi-encoder","E4-1 ใน E5-3","positive ≥ ~1,000 ใน D_train","ASSUMPTION: 2–5 GPU-ชม.","model","เข้าเมื่อผ่าน inclusion rule T4","ไม่ผ่าน → ไม่ทำ"),
"E4-4":("fine-tune cross-encoder","E5-3","เหมือน E4-3","ASSUMPTION: 2–4 GPU-ชม.","model","เหมือน E4-3","เหมือน E4-3"),
"E4-5":("local LLM บน sample","E5-3","G1 อนุมัติชัดเจน","ASSUMPTION: 1–3 GPU-ชม.","—","—","ห้ามใช้ hosted API"),
"E5-1":("alias ของ E3-2/E3-1","—","—","0 (ไม่มี job ใหม่)","—","—","—"),
"E5-2":("alias ของ E4-2","—","—","0","—","—","—"),
"E5-3":("F-LEX ∪ F-SEM","E5-1 (=E3-2)","D_dev","ASSUMPTION: 5–20 CPU-ชม.","OOF scores; ms/คู่","ΔPR-AUC ตาม H3 + cost ratio","—"),
"E5-4":("leave-one-group-out 5 กลุ่ม","E5-3","D_dev","ASSUMPTION: 2–6 CPU-ชม.","ablation.json","explanatory เท่านั้น","—"),
"E5-5":("single lexical group 5 กลุ่ม","E5-1 vs best group","D_dev","ASSUMPTION: 2–6 CPU-ชม.","ablation.json","ΔPR-AUC ตาม H1","—"),
"E5-6":("missingness-aware","E5-3","D0-2 strata","ASSUMPTION: 1–3 CPU-ชม.","—","—","—"),
"E6-7":("Platt vs isotonic บน OOF ที่ prior เท่ากับ test fold","uncalibrated","OOF scores ของ M*","ASSUMPTION: นาที","calibrator + reliability","ECE ต่างระหว่าง dev-OOF และ fold อื่น ≤ 0.01","prior shift > 1.5× → ปรับ split ก่อน (บทเรียน ICSEC v2)"),
"E6-1":("t=0.5, R0 0.98/0.95, stage18 manual rule","—(reference)","OOF calibrated scores","ASSUMPTION: วินาที","policy_eval.json","—","—"),
"E6-2":("threshold ที่ให้ F1 สูงสุดบน dev","E6-1","เหมือน E6-1","ASSUMPTION: วินาที","policy.json","—","—"),
"E6-3":("closed-form cost threshold + Chow three-way","E6-1","cost model freeze","ASSUMPTION: วินาที","policy.json ×4 cost scenarios","—","—"),
"E6-4":("random / scrambled Sobol / TPE × 10 seeds × 2,048","E6-3","เหมือน E6-1","ASSUMPTION: นาที","traces.parquet, policy.json","budget audit ผ่าน (นับ evaluation จริง)","budget ไม่เท่ากัน → rerun"),
"E6-5":("GA genome 4 ยีน × 10 seeds × 2,048","best of E6-2/E6-3/E6-4","เหมือน E6-1","ASSUMPTION: นาที","traces.parquet, policy.json","budget audit ผ่าน; config GA ตรึงก่อนเห็น E6-4","ปรับ GA หลังเห็น E6-4 → ผลเป็น exploratory"),
"E6-6":("three-way (t_low,t_high)","best two-way","cost รวม review","ASSUMPTION: นาที","policy.json","—","—"),
"E6-8":("one-to-one assignment","best policy","1:1 ยืนยันใน D0-2","ASSUMPTION: นาที","—","ทำเมื่อ 1:1 ยืนยัน (คาดว่าใช่: 4/15,297)","—"),
"E7-1":("REF และ BEST-VAL บน test ครั้งเดียว","REF","test fold ที่ lock + G5","ASSUMPTION: < 1 ชม.","final_metrics.json + CI","เปิด test ครั้งเดียว มี log","test ถูกเปิดก่อน → ลดเป็น exploratory"),
"E7-2":("2×2×2 factorial","cell (B0, rule, fixed)","เหมือน E7-1","ASSUMPTION: < 1 ชม.","factorial.json","8 cells ประกาศก่อน G5","—"),
"E7-3":("strata + perturbation","unperturbed","D0-2 strata","ASSUMPTION: < 1 ชม.","strata.json","strata เล็ก = exploratory","—"),
"E7-4":("prior sensitivity (natural, ×0.5, ×0.1, full-graph prior)","natural","—","ASSUMPTION: นาที","prior.json","—","—"),
"E7-5":("วัด ms/1k คู่ต่อ stage","—","ฮาร์ดแวร์ระบุ","ASSUMPTION: ชั่วโมง","cost.json","median 5 ครั้ง","—"),
"E7-6":("label sensitivity S1/S2/S3","S1","π_hidden จาก D0-3","ASSUMPTION: นาที","label_sens.json","—","—"),
"E7-7":("error taxonomy","—","validation; test นับตาม taxonomy ที่ freeze","ASSUMPTION: 1–2 วันคน","taxonomy.json (ไม่มีตัวอย่างจริง)","ตัวอย่างในเล่มเป็น SYNTHETIC","—"),
"E8-1":("keyed Bloom vs plaintext","E5-1","GX-T8","ASSUMPTION: ชั่วโมง","—","ต้องมี E8-3 เสมอ","ไม่มี threat model → ไม่ทำ"),
"E8-2":("Bloom + best policy","E8-1","GX-T8","ASSUMPTION: นาที","—","เหมือน E8-1","—"),
"E8-3":("attack evaluation","—","ethics approval","ASSUMPTION: ชั่วโมง","attack.json (ไม่มีค่าที่ re-identify ได้)","re-identification rate รายงานพร้อม threat model","—"),
"E9-1":("image similarity feature","E5-3","GX-T9 + coverage ≥ 50%","ASSUMPTION: 1–2 GPU-ชม.","—","coverage ผ่าน","coverage ประวัติศาสตร์ = Twitter เท่านั้น → คาดว่าไม่ผ่าน"),
"E10-1":("clustering จาก pairwise","connected components","1:n > 5%","ASSUMPTION: นาที","—","ทำเมื่อ 1:n > 5%","สถิติ schema 0.03% → คาดว่าไม่ทำ"),
"E2-2":("RETIRED → E6-1","—","—","—","—","—","—"),
}
print("| ID | Priority | ลำดับ | Stage | Objective / Proposed | IV | Baseline | Data/GT | Training (GPU) | Primary metric / สถิติ | Runtime | Dependencies | Reusable code | Artifacts | Acceptance | Failure/Exclusion |")
print("|"+"---|"*16)
for eid, r in rows.items():
    o = S[eid]
    stat = "paired entity-grouped bootstrap (Δ, 95% CI)" if r["priority"] in ("ESSENTIAL","SUPPORTING") and eid.startswith("E") else "—"
    print(f"| {eid} | {r['priority']} | {ORDER[eid]} | {r['pipeline_stage']} | {o[0]} | {r['independent_variable']} | {o[1]} | {o[2]} | {r['training_required']} ({r['gpu_required']}) | {r['primary_metric']}; {stat} | {o[3]} | {r['depends_on']} | {r['reusable_code'] or '—'} | {o[4]} | {o[5]} | {o[6]} |")
