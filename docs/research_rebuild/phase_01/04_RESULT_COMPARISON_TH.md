# 04 — เปรียบเทียบผลประวัติด้วยการคำนวณใหม่จาก persisted artifacts

## สถานะและขอบเขต

นี่เป็น **read-only retrospective audit** ไม่ใช่การทดลองใหม่ ไม่ train, optimize, download, unpickle model หรือเรียก evaluator ของประวัติ ทุก output อยู่ใน `docs/research_rebuild/phase_01/` เท่านั้น

- Script: `recompute_historical_metrics.py`; ตารางเครื่องอ่าน: `verified_metrics.csv` / `verified_metrics.json`
- รันด้วย `uv run --offline --python 3.11 python docs/research_rebuild/phase_01/recompute_historical_metrics.py`
- อ่าน source/hash และคำนวณ counts จาก granular decisions โดยตรง ไม่คัดลอก counts จาก audit วันที่ก่อน
- Numerical agreement ไม่รับรอง raw provenance, label-access history, scorer independence, licensing หรือ causal superiority

- FULL2M_10GENE: 48 metric rows — INDEPENDENTLY_RECOMPUTED
- FULL2M_10GENE: 4 metric rows — RECOMPUTED_PLUS_INDEPENDENT_GT_MISSES
- ICSEC_V2: 60 metric rows — INDEPENDENTLY_RECOMPUTED
- ICSEC_V2R1: 60 metric rows — INDEPENDENTLY_RECOMPUTED
- MULTIMODAL_REPORTED: 3 metric rows — REPORTED_NOT_INDEPENDENTLY_VERIFIED
- REVIEWER_REVISION: 18 metric rows — INDEPENDENTLY_RECOMPUTED
- R_SERIES_REPORTED: 28 metric rows — REPORTED_NOT_INDEPENDENTLY_VERIFIED

## นิยามที่ใช้

`TP/FP` คือ positive/negative MATCH, `FN` คือ positive NO_MATCH (รวม blocking misses เมื่อ scope เป็น WORKFLOW), `R+`/`R−` คือ positive/negative REVIEW. `TN_candidate` นับเฉพาะ negative NO_MATCH ที่มีแถว ไม่ใช่ true negatives ทั้ง universe.

- precision = TP/(TP+FP)
- conditional recall = TP/(TP+FN); conditional F1 = 2TP/(2TP+FP+FN)
- automatic recall = TP/(TP+FN+R+); automatic F1 = 2TP/(2TP+FP+FN+R+)
- U = 2FP + FN + 0.1(R+ + R−), เป็น declared scenario ไม่ใช่ต้นทุนธุรกิจที่พิสูจน์แล้ว
- candidate coverage = 1−REVIEW/(EXACT_TIER+MODEL_SCORED); ตัวส่วนไม่รวม missed positives
- ไม่สมมติว่า human review แก้ R+ ถูกทั้งหมด

## ICSEC V2/V2R1 และ reviewer revision

V2 และ V2R1 มี 5 methods × 3 outer seeds ต่อ family; ตรวจ workflow, exact, scored และ miss แยกกัน ส่วน reviewer revision เป็น 6 methods × 3 seeds = **18 cases** (5 methods เดิม reuse V2R1 + Chow ที่บันทึกเพิ่ม) ไม่ใช่ 18 การทดลองอิสระ.

ตรวจด้วย stable `pair_key` ที่ sort/index และ one-to-one joins: ไม่มี duplicate key, key set/labels/pair_type เหมือนกันข้าม methods, label ตรงกับ sealed persisted labels, exact/scored components ตรง workflow และ misses ตรง SEALED_TEST routes. V2/V2R1 decisions ตรงกันเมื่อเทียบด้วย key ทุก method/seed. Chow saved decisions ตรง argmin `[p,.1,2(1−p)]` โดย tie order NO_MATCH→REVIEW→MATCH. ไม่ใช้ positional joins.

### Mean ข้าม 3 partitions (ค่าเฉลี่ย per-partition ไม่ใช่ pooled confusion)

| method | TP | FP | FN | R_positive | R_negative | REVIEW | conditional_recall | automatic_recall | conditional_F1 | automatic_F1 | U |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 | 6759.67 | 107.67 | 1557.67 | 513.33 | 339.00 | 852.33 | 0.812652 | 0.765323 | 0.890293 | 0.861031 | 1858.23 |
| B2 | 6760.67 | 107.67 | 1560.33 | 509.67 | 334.00 | 843.67 | 0.812413 | 0.765436 | 0.890149 | 0.861105 | 1860.03 |
| B1 | 6843.00 | 115.33 | 1557.67 | 430.00 | 332.33 | 762.33 | 0.814565 | 0.774848 | 0.891037 | 0.866722 | 1864.57 |
| Chow | 6659.33 | 96.00 | 1281.00 | 890.33 | 3170.00 | 4060.33 | 0.838423 | 0.753990 | 0.906145 | 0.854216 | 1879.03 |
| GB17_B0 | 6349.33 | 89.00 | 2137.33 | 344.00 | 22.33 | 366.33 | 0.746588 | 0.718739 | 0.849436 | 0.829952 | 2351.97 |
| B0 | 6498.67 | 88.00 | 2171.33 | 160.67 | 8.00 | 168.67 | 0.748619 | 0.735744 | 0.850965 | 0.841952 | 2364.20 |


### Winner เฉพาะกลุ่มเทียบได้: U ต่ำสุด / automatic F1 สูงสุด

| seed | min-U method | U | max automatic-F1 method | automatic F1 | U(B3)−U(B2) |
|---|---|---:|---|---:|---:|
| 101 | Chow | 1823.4 | B1 | 0.872210 | -5.5 |
| 202 | B2/B3 | 1861.2 | B1 | 0.856333 | +0.0 |
| 303 | B1 | 1823.0 | B2/B3 | 0.874240 | +0.1 |

B3 เป็น mean-U ต่ำสุดของ frozen reviewer group แต่ paired differences B3−B2 เล็ก/กลับทิศ และจำนวน outer partitions เพียง 3; ไม่ใช่หลักฐาน GA superiority, equivalence หรือ deployment recommendation. U winner ไม่จำเป็นต้องเป็น automatic-F1 winner. GB-17/GB-18 เปลี่ยน representation จึงไม่ใช่ optimizer-only comparison.

### Exact-tier errors ไม่เท่ากับศูนย์

- outer 101: exact N=3631, TP=3622, FP=9, precision=0.997521344
- outer 202: exact N=3680, TP=3667, FP=13, precision=0.996467391
- outer 303: exact N=3728, TP=3727, FP=1, precision=0.999731760

## Full2M 10-gene: candidate ไม่ใช่ workflow

ยืนยัน unordered endpoint key identity ระหว่าง projection parquet, legacy cache และ V2 global candidate artifact ครบทุกแถว; labels/split/decision_source ตรงกันและไม่มี duplicate/self pair. Labels คำนวณซ้ำจาก endpoint→user_folder ผ่าน profile-row ID map ไม่จับคู่ตามตำแหน่ง. Positive universe คำนวณจาก eligible profile groups และ platform โดยไม่ใช้ constants จาก summary.

| policy | scope | TP | FP | FN | R+ | R− | automatic recall | automatic F1 | U |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| one_stage_weighted_10gene | CANDIDATE | 20095 | 183 | 2626 | 3210 | 7326 | 0.774941 | 0.869744 | 4045.6 |
| legacy_name_guard_4threshold | CANDIDATE | 20812 | 240 | 3114 | 2005 | 20342 | 0.802591 | 0.885937 | 5828.7 |
| score_only_2threshold | CANDIDATE | 14460 | 91 | 3114 | 8357 | 20492 | 0.557634 | 0.714392 | 6180.9 |
| original_pipeline | CANDIDATE | 19624 | 925 | 2242 | 4065 | 82231 | 0.756778 | 0.844406 | 12721.6 |
| one_stage_weighted_10gene | WORKFLOW_CROSS_PLATFORM | 20095 | 183 | 5938 | 3210 | 7326 | 0.687173 | 0.811575 | 7357.6 |
| legacy_name_guard_4threshold | WORKFLOW_CROSS_PLATFORM | 20812 | 240 | 6426 | 2005 | 20342 | 0.711692 | 0.827597 | 9140.7 |
| score_only_2threshold | WORKFLOW_CROSS_PLATFORM | 14460 | 91 | 6426 | 8357 | 20492 | 0.494477 | 0.660364 | 9492.9 |
| original_pipeline | WORKFLOW_CROSS_PLATFORM | 19624 | 925 | 5554 | 4065 | 82231 | 0.671067 | 0.788239 | 16033.6 |


จำนวน global candidate positives=25,931; independent cross-platform universe=29,243; blocking misses=3,312 (opaque keys ตรง persisted V2 miss artifact). All-platform positives=29,247 มี same-platform positives 4 คู่ ต้องไม่ปนกับ cross-platform denominator. exact=12,403 และ scored=2,073,842 รวม candidates=2,086,245.

10-gene แถว `all` candidate recall/F1/U คำนวณซ้ำตรง summary แต่เมื่อนับ misses workflow recall/F1/U เปลี่ยนตามตาราง. U เพิ่ม 3,312 สำหรับทุก policy เพราะ misses เป็น FN ร่วมกัน; ranking ในกลุ่มนี้ไม่เปลี่ยน. 10-gene เป็น U ต่ำสุดใน full2M frozen group ขณะที่ legacy_name_guard เป็น automatic-F1 สูงสุด (ไม่ใช่ claim superiority ของ optimizer). Full projection รวม validation/drop rows จึงไม่ใช่ held-out generalization. `val/test/drop` รายงาน candidate เท่านั้น: ไม่เติม V2 per-role misses ให้ legacy split เพราะเป็นคนละ split protocol. Model-scored/exact metrics แยกใน CSV.

## R-series และ multimodal: reported ไม่ใช่ independently verified

- R0–R5 tidy summary และ R6 summaries อยู่ในตารางพร้อม status `REPORTED_NOT_INDEPENDENTLY_VERIFIED`; ไม่เติม R+/R− จากการเดาย้อนสูตร ไม่ประกาศ key/label equivalence ข้าม R variants เมื่อไม่มี row-level decisions ที่ตรวจใน package นี้
- R-series ใช้ harness historical automatic denominator และต้นทุนเก่า (FP,FN,REVIEW)=(5,1,.02) ไม่ใช่ U=(2,1,.1) ของ ICSEC; script ไม่ปลอม U ใหม่จาก incomplete review-class counts. R3 F1=0.8373 เป็น reported test-F1 leader เฉพาะ numbered R0–R6 methods; manual_stage18 control มี reported test F1=0.8439 สูงกว่า แต่ FP=632 เทียบ R3 FP=38 และใช้ cost/rule ต่างกัน (experiments/r1_results.json#/rules/test/manual_stage18; experiments/r3_results.json#/rules/test/R3_ga). จึงไม่ใช่ R3 ชนะทุก metric หรือทุก historical control ไม่พิสูจน์ว่า GA เป็นเหตุของ gain และไม่รับรองคำว่า unbiased ในรายงานเก่า
- Multimodal suite เป็น sampled supervised pairs, ไม่ใช่ cross-platform workflow. Summary image_stats test F1=0.9340467605 มากกว่า image_context 0.9340136843; image_context เป็น reported composite/validation-F1 leader และมี AP สูงสุด แต่ไม่ใช่ test-F1 leader. ห้ามเลือก best model ใหม่จาก test
- ตรวจ arithmetic ของ persisted confusion matrices กับ F1 ใน base/img_stats/main reports เท่านั้น; **SUMMARY_ARITHMETIC_ONLY ไม่ใช่ independent row-level reproduction**. ไม่โหลด missing historical models/รัน inference เพื่อกลบช่องว่าง

## แปลความเปลี่ยนแปลงทีละ comparable development group

| Contrast | สิ่งเปลี่ยน/สิ่งคงไว้ตาม historical protocol | ผล/การตีความที่อนุญาต |
|---|---|---|
| R0→R1 | เปลี่ยน downstream four-parameter policyบน oldscore/cache; predictorไม่ฝึกใหม่ | reportedtest TP5864→6231,FP88→23,REVIEW8783→3116,F1.7964→.8292 จึงไม่ใช่เพิ่มF1ด้วยreviewมากขึ้นอย่างเดียว แต่ scorerindependenceยังไม่ยืนยัน |
| R2→R3 | ใช้ reconstructed17+MiniLM scorerเดียวในresultfamilyแล้วเปลี่ยน policy | reportedtest TP5157→6347,FP19→38,REVIEW1115→640,F1.7393→.8373 เป็นtrade-offอัตโนมัติที่reported ไม่ใช่ row-reproducedcleanablation |
| R4→R5 | Bloomrepresentationต่อLเดียวกันแล้วเปลี่ยนmanual→GApolicy | ที่L2000 reportedtestF1.7397→.8329,TP5158→6303,FP14→57,REVIEW766→700; Lต่างกันเปลี่ยนrepresentation/privacyscenarioด้วย ห้ามเอามาปนoptimizer-only |
| R6 manual→R6 GA | semantic/hashmodelprobabilityเดิมปรับpolicy; retrievalevaluationเป็นอีกpopulation | reportedtestF1.6053→.7801,TP3817→5620,REVIEW224→3712; gainมีทั้งMATCHเพิ่มและREVIEWเพิ่ม แต่retrievalmissrecoveryต่ำและไม่ใช่V2blockingcomparator |
| multimodal text→stats→context | เปลี่ยนfeaturemodalityภายในsampled-suiteprotocol; savedpairidentities/orderยังไม่ได้reproduceทั้งsuite | imagecontextreportedvalidation/composite/APleader; imgstatstestF1สูงกว่านิดเดียว ไม่มีหลักฐานว่าimagebranchชนะfullworkflow |
| GB17_B0→GB18_B0 | representationเพิ่มbert_cos; sameV2pairs/roles/trainindices/modelparams,B0policy; models/calibratorsต้องfitแยก | conditionalF1.849436→.850965,automaticF1.829952→.841952 แต่ meanU2351.97→2364.20 แย่ขึ้น; ไม่สรุปfeature18ดีกว่าทุกmetric |
| B0→B1 | fixed→validation-tunedtwothreshold; sameGB18 probabilities | automaticF1.841952→.866722 และpositiveREVIEW160.67→430.00; seed202/303มีMATCHเพิ่มเพียงเล็กน้อย ต้องแยกabstentionbenefit |
| B1→B2 | expandednamepolicy+searchdomainเปลี่ยน; notstrictlynested | meanUลดแต่automaticF1ลดจาก.866722เป็น.861105; ไม่ใช่pureoptimizercontrast |
| B2→B3 | identicalexpandedclass/bounds/data/objective/budget ต่างoptimizer | meanU1860.03→1858.23 แต่automaticF1.861105→.861031; pairedU −5.5/0/+.1 จึงยังไม่พิสูจน์GA superiority |
| full2Mpolicycontrols→10gene | weightedpolicyclass/evidenceเปลี่ยน ไม่ใช่เฉพาะoptimizer | lowerU/lessREVIEWกว่าlegacyguard แต่automaticF1ต่ำกว่า;รวมmissesและdevelopmentprojectionก่อนตีความ |

Sources exact results: `experiments/r1_results.json#/rules/test`, `experiments/r2_results.json#/splits/test`, `experiments/r3_results.json#/rules/test`, `experiments/r4_privacy_tradeoff.json#/per_L/2000`, `experiments/r6_results.json#/splits/test` และ `#/ga_rules/test`; V2/fullsourcesตามSHA-256tableและ`verified_metrics.json`. สองทางแรกเป็นreportedhistoricalcontrastsเท่านั้น ไม่รับรองpairedkeysโดยดูcountsตรงกัน

Historicalclassifierbenchmark/tuning/strict/sigmoidvariantsในmatrix02เปลี่ยนtrainingpopulation/config/calibrationจนไม่ควรรวมกับsuite3variants: GBเป็นreportedmainselection,strictlogreg+sigmoidเป็นอีกselectionlineage ไม่มีexternalresultสำหรับwinnerใหม่ และpost-hoctestthresholdsweepsไม่เป็นfairselectionevidence [02_HISTORICAL_EXPERIMENT_MATRIX.md:29–33; experiment_lineage.json] Phase1ไม่เลือกmodel/policyจากtestหรือทำcontrolledevaluationใหม่

## เทียบ historical summaries

ทั้งหมด 76 comparisons; agree=76, disagree=0 ภายใต้ tolerance 1e−10. รายละเอียด mapping และ raw deltas ทุก field อยู่ใน JSON. V2/R1 เปรียบ recall/F1 กับ conditional นิยามเดิม, reviewer กับ conditional+automatic (รวม independent mean/sample SD จาก 3 partitions), full2M summary กับ automatic candidate. Agreement ต่าง scope ไม่แปลว่า headline เก่าเป็น workflow.

## ข้อจำกัด/การใช้ผล

ผลนี้ยืนยัน numerical layer ของแถวประวัติเท่านั้น ไม่เปลี่ยน policy หรือแก้ frozen sources. ไม่เปรียบ F1 ข้าม ICSEC/R-series/multimodal เป็น leaderboard เดียว. สำหรับ scientific claims ใหม่ต้องใช้ protocol ใหม่ที่ freeze ก่อนรัน โดย phase นี้ไม่ได้อนุญาตการรันนั้น.

## แหล่งข้อมูลและ SHA-256 ของ bytes ที่อ่าน

Hashes ด้านล่างถูกคำนวณก่อนอ่านและตรวจอีกครั้งก่อนเขียน outputs; identifiers/path เป็น repository-relative. Script hash และ environment อยู่ใน JSON. รายการนี้เป็น source list ไม่ใช่ manifest ของทั้ง repo.

| exact path | SHA-256 |
|---|---|
| `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_metrics_by_split.csv` | `a15fd38db041ef212fad4565ffff099ca88cacefcf55670efdb912b1fb5d143e` |
| `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet` | `716267a9c413cceaf2a875d382f0277ac55d15c63585dcb126af54af2f211b6c` |
| `data_for_project/normalized_profiles_with_profile_id.csv` | `17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1` |
| `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md` | `acdd2f4e0fe93f23e9ed70a29fb15e73393c5728e582a063b3afd64e33560dc9` |
| `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md` | `3311ea2c97d371b8d2ad9a5f3b4b485a2b88e67c642d339169f5b578ef6f79f8` |
| `experiments/REPORT_R0_R5.md` | `2b69ee392fd0386eff397c2585bbb27d8a56dc60914fc94356c9f9799fbe1233` |
| `experiments/code/exp_lib.py` | `984adb9cf584210f5c2cbbae15062346388211df4812f0f32f91dcfd0f661db4` |
| `experiments/code/project_one_stage_to_full_2m.py` | `a9096bf8b43716ca0d8b744e5b268856974e2f5ddad9c0573a1bbc528dd5f704` |
| `experiments/code/reviewer_revision.py` | `d83bc84fe4a0dbe2d7477be45dcbab6cc3c7d7477171bfc58536c720f70e41db` |
| `experiments/icsec_final/authoritative_run_v2/candidates/workflow.parquet` | `30d168d48d8ca610ce3be5ea46bfccd124aa6676044ab68d58f56a8ef5b480b0` |
| `experiments/icsec_final/authoritative_run_v2/final_runner.py` | `61bf80f161172177b124ceece4ceb6c2930c76617d0a371d656deb86eab46b37` |
| `experiments/icsec_final/authoritative_run_v2/preflight/candidate_scope.json` | `f7f16b47dc08b1f2f1d00a7942f49da290ac37c5bd696b5410f650a60f7f91dd` |
| `experiments/icsec_final/authoritative_run_v2/real_adapters.py` | `59c4a3f65266a3f25c1e07da5a056c2f87732cbb723e0720075123d1493b4c67` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/blocking_misses/positive_pairs.parquet` | `3fb42afde05d3f3a949a4bd41f7c7db414dac6db5a4ffdb2782f62352712e12f` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/blocking_misses/same_role_routes.parquet` | `e440181e2d2c344f205ea7858c318f7bf0bf6836a5ecc51a8e9b89bf08be66c9` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/sealed_test_labels/labels.parquet` | `5aed2ffaa590a2b9724671540d9ce64785a2edb87bf7369f1fc8f37461ac2dfe` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_202/blocking_misses/same_role_routes.parquet` | `91839a0d42d99d87f65f74eca0e504d9168a7611a46093fe4844149907a97f86` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_202/sealed_test_labels/labels.parquet` | `15ac532abe97ac875c323f826c4cfcd2713b68d08aa5bcafd12f9c1a30901559` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_303/blocking_misses/same_role_routes.parquet` | `88f90dcdc4af40846743150225c1fabbdaf1f0dcfb720d53f8bb8ce1a436b7af` |
| `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_303/sealed_test_labels/labels.parquet` | `715ea204b93e38e8c93fbda71190db4edef1bd855e959c2b16768543b2155906` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B0_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B0_model_scored.parquet` | `2c1a947e23f77a0893363622c793abcc72a8fd641863df8d2ab4163eeafb0a54` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B0_workflow.parquet` | `bc565dd3a88e0441d4418437cbe2f5bad7c3b1a56eef45b90df545c1355dd678` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B1_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B1_model_scored.parquet` | `6c0659ff5f9ff9fb6522bc8cd09d727fa84b62f45f503cff694482af7defef46` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B1_workflow.parquet` | `9431ca697c45e7156223cdf839a89c9d3bd97853f28db84fc8e753d005df8c5a` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B2_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B2_model_scored.parquet` | `04077c487060e8d3790f2fd960cf76c4e3b027c6689c4b13d76698733b0d8900` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B2_workflow.parquet` | `ca2edbdae328fde96cbc066c8ac763cb2efb345b2d506457913787a6ea495117` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B3_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B3_model_scored.parquet` | `0be4b83fb8ad20a54600a119f3aa5a62275f52314bfacecc0402bf93c3a51df9` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/B3_workflow.parquet` | `8d5dda8d82d8c6eba04f2a385b22fd6ab17171097facf7feb3744e65eeb1d2f8` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/GB17_B0_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/GB17_B0_model_scored.parquet` | `3ba3ffc50f3a39247cb9ad90bd1868102244ca8252ca49f939fdc350dd7d9df9` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/decisions/GB17_B0_workflow.parquet` | `5f07bc169a14334792ba0110127c210d26f7a59d8e20ae9ce2489f9398b18292` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json` | `c6c23600adbe05f6946ccbd6f13fa9cdf1d39185f91dec65d327325b1de8a66d` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B0_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B0_model_scored.parquet` | `f2dc84d6074f87c7bf646a44a8e05fc30916ad52730185f7bb4216552be51718` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B0_workflow.parquet` | `90771662439ed9aa461bc31f018f21f92a18e73daa148c51021322d4f3832933` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B1_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B1_model_scored.parquet` | `4ef6a14aa8c83507c27c77f274c2bd11efecba290dbed356a193b32e84ce9bf3` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B1_workflow.parquet` | `442db401ef0b8478c5c0f0ebed0efbcd2cf72f704f5352f10046461deccd909c` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B2_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B2_model_scored.parquet` | `ace255189ea19b7d6df4b5175a00b396f79309bb445d372864c85fc7dd4b79bb` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B2_workflow.parquet` | `b90dd3174dcedfe9255453c0a85d1e3d3dea24fab24c0b56e0e78d2c0ba6cbb4` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B3_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B3_model_scored.parquet` | `baa1e0991df2037b00ea3b37b7703a54d9234289d37ac095a945617a0a40998e` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/B3_workflow.parquet` | `6545b65dcffc4c2950bf0c6aa50cd5e9de949f7a5033b06ce80254599be81c5f` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/GB17_B0_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/GB17_B0_model_scored.parquet` | `093bfc2a219f60675ca68dea66fe42bf7c8432ef958c049e7ca08939adc46353` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/decisions/GB17_B0_workflow.parquet` | `2b265a1c60e0a2cf51ed43edd3dd6e3ec1f14c93ac12948637f435be3124d2ba` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json` | `a98317339252d0da152a181bf31530762d4766402b347ef78b8d8d2cd902fa19` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B0_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B0_model_scored.parquet` | `eea7b66ddd0724037da2cf57f1bb4089079db5db106d15c867e41a6cd696a8b0` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B0_workflow.parquet` | `7045ccf52c4f8b19d2250160c9016715729eae7846b5b493d63dc14f5757c48c` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B1_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B1_model_scored.parquet` | `8d2fbf0e19c2422ae555861b97f3688e4b99ab1c9fba2195257617971b78a3fc` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B1_workflow.parquet` | `35d5680d511deca484d8e54a859cb91591fa0c513f466ad19ae1c3e394f4d89a` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B2_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B2_model_scored.parquet` | `9069b06059ec0907e30dc44efd4dcbb5e71a23a55c3969b3bef04f16b798968d` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B2_workflow.parquet` | `235be553eff67a9796c03056b4835f2f7626379f2cc732d32666c16a72cf02ee` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B3_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B3_model_scored.parquet` | `7f4eb71e60bdc1832e1042b338c69bc2439ef72e45fa60f52f046cfd0e1173de` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/B3_workflow.parquet` | `62cd32832a0bb8d5e888a35f9d747520631ad2b3d18a4e8144ecc6fdb1b59ae8` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/GB17_B0_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/GB17_B0_model_scored.parquet` | `721738449bc33c052e628f96e609dd5e6882e408194f56874029a76b3aeee3c5` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/decisions/GB17_B0_workflow.parquet` | `918513ea32a317bd4f3eb6895704819b071d37348711ba429c4474fbcc246a86` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json` | `e6fd5c1ad4bc103745a3bc1350bba73904cd5fcbdcacf8dd2176a93975298fb6` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B0_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B0_model_scored.parquet` | `0d90b1417a4a4927f0bdabdb4f94d6886158bbeceaf42a098a2359034436397a` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B0_workflow.parquet` | `3427e2cedefe15c34a3942b70881aaff9d8824b2ca15fce6975792e74eda4263` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B1_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B1_model_scored.parquet` | `87d0ed4a23423dec91e057b3b2b0d359997d29ba6ffb0218558f40fecedccfe2` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B1_workflow.parquet` | `9041aa7704947955403da3e5f092e38c561f9a0353e89956b80eab56e7fc6c9d` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B2_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B2_model_scored.parquet` | `e87fe7469b5d2c14b34edb7479cba2c11bf9a733ede1f4a96813fafa0cae3d2f` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B2_workflow.parquet` | `1d4da564193e4af9e3e24d60b1422842a49082c10aea3d057c772079b303ad26` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B3_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B3_model_scored.parquet` | `fba7d5556efdcd9a2e02da9f9c103afcd3a883b566241cb97000321aa617b6c6` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B3_workflow.parquet` | `fa8e6a08f26399d9fdcda683ef9d10f0ba36461ecfb36d57c9428261e3cee1fb` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/GB17_B0_exact_tier.parquet` | `39923a96af1aa653cb7cfe4b274fa059666d04b8722ec24ac160511efaf407be` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/GB17_B0_model_scored.parquet` | `825050842df2ecc4d78c3cb29363864ef77a1c46208e2711f48e575fbce45132` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/GB17_B0_workflow.parquet` | `d5005938df6e5eeb7910a3705fe7f041b70654baeee3c182a8330890a8fb638f` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json` | `c6c23600adbe05f6946ccbd6f13fa9cdf1d39185f91dec65d327325b1de8a66d` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B0_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B0_model_scored.parquet` | `ba78116e696027f65ef8ddf59b870ab2b720a92a4d9ada49557ab42a51d96708` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B0_workflow.parquet` | `6012d9b16dde1ef731f5f47ff03c6dc15f4ea2cb8071df6ea2a725c32d783484` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B1_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B1_model_scored.parquet` | `ac847165e4497eda694d4ab691eb618b9e685cb7f13af0249326990daf0a5052` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B1_workflow.parquet` | `266285866238c20b72300286e32c2df1c4c5cc0b9d18db6e08684ea31dbc458e` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B2_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B2_model_scored.parquet` | `0b0cd74445484dfe942e3d142461b1990805499f159e88d9c68a15b059e76a1f` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B2_workflow.parquet` | `be272264e444ca214527ee7dd52a3a85bd6c4d8c982faebf226901d759572437` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B3_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B3_model_scored.parquet` | `55bc763b46e32488910580628b1e4c66674eddfa6d029b6f2a570ee31d927a19` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B3_workflow.parquet` | `e4cef1130028bb0af29de0ac425bf0772763e07319cd05ae95912d41ffab75ca` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/GB17_B0_exact_tier.parquet` | `bc963b651801f5527c8356cb0f622c3e1c0e493e0c6505dacf685ea6df839d74` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/GB17_B0_model_scored.parquet` | `ce2fb9a313f38bae57325eee71d94caa3b76011e006d9abc77a19abce25ade17` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/GB17_B0_workflow.parquet` | `294b81bd24ceaeab93f8ec34924a9d666e6005b3a1aeb5a1cffbee86ade46f10` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json` | `a98317339252d0da152a181bf31530762d4766402b347ef78b8d8d2cd902fa19` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B0_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B0_model_scored.parquet` | `4a0f44ffe9fca71ba0d70e18fe5af0b3a8d091bd4759d53f1eb56ee346757ff5` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B0_workflow.parquet` | `59f3473baadd01a906911fb2c5de31bc2b08e234bff7e5dca02a33625f4c3822` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B1_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B1_model_scored.parquet` | `b15509aa1f6d4c8f143034598adcace77cdb79a89f74e0e41f7f5481cb4d1624` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B1_workflow.parquet` | `140119997db4d9919c6131d32d8f3bb4122df036af95eaaefd588a81be8e0305` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B2_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B2_model_scored.parquet` | `11a58e60cffb491d9e33cc7c27a49c16f36470522ebcad60f9613eac001df66c` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B2_workflow.parquet` | `db9068f77476165cd716ddffad950d0ee2d61ab83752d8dd39ae60ef4e3eb470` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B3_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B3_model_scored.parquet` | `419e30fda1a005a89248cbce0bafd80799fe90ec1bc0f60542ad680a2d3f314b` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B3_workflow.parquet` | `51be89fdd346b6fe69aa939f6aa0b95c507ea1d2eb450fd5721cc11e67f73580` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/GB17_B0_exact_tier.parquet` | `d2d0fe11f9f7038789b7f5d517e2118e03ecceef145b73a827bbe3de9b228250` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/GB17_B0_model_scored.parquet` | `53d818f6da2a431284967e213b3abc93e02e7eb16e06d9f7c3425df15fd87819` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/GB17_B0_workflow.parquet` | `024db60b09d5cecf2ef529500f6432ddfd48d9b0dc68596202ec7638b9f088e9` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json` | `e6fd5c1ad4bc103745a3bc1350bba73904cd5fcbdcacf8dd2176a93975298fb6` |
| `experiments/icsec_final/reviewer_revision/aggregate.json` | `d3c2250c996ff7a8fc0f479a144fd3beb928e2057ab1e3ce33c7caae6eb905e1` |
| `experiments/icsec_final/reviewer_revision/metrics_per_seed.csv` | `acac02a4a978c8f7830d8c33ba7e693ed1d5d86d39c264b84443f62c61972cb2` |
| `experiments/icsec_final/reviewer_revision/outer_101/Chow_workflow.parquet` | `ae462ec7d2c730d153a52295b3655afec9f1d73676dbda94af9c1d217489e492` |
| `experiments/icsec_final/reviewer_revision/outer_202/Chow_workflow.parquet` | `5a16ab1c13abbce165abeb84acc2162e8de91fc24e33610dce9219648028887d` |
| `experiments/icsec_final/reviewer_revision/outer_303/Chow_workflow.parquet` | `6dd2114cb9efb5a09dfbdd215b4f6d3567946b242b8019d374a3698c71197363` |
| `experiments/r0_r5_summary_tidy.csv` | `6648f69da8aa78e9bc496129639f433ff57cc3ddc1d4feb01f189e603a218df2` |
| `experiments/r1_results.json` | `1d00499d136f32fb5b16954339254660ff61701ac4da49a9f5049850b7b73b05` |
| `experiments/r2_results.json` | `435bbc05775e126bee12e5937a8404715de3eeeabeb9f2fe1770fc87763cee5c` |
| `experiments/r3_results.json` | `a34ed05ff455370073b90412c6a0b792dbd00ac2c1544f3f9ff48e8203770523` |
| `experiments/r4_privacy_tradeoff.json` | `7384075d3a8783e0e62a0c3acc08389baecf5b6174dfd23e476277b7837ed5ec` |
| `experiments/r6_results.json` | `82173f645de9a828395874515c549c9d9139ad4816dc224c983da88e12dc386a` |
| `experiments/scored_pairs_enriched.parquet` | `396884be39c3aca894df8db56115dbe78b45694737dcb04fb3190974a5f53801` |
| `pub_multi/ref/base_report.json` | `27760e483f1d25b1c8d142dbdefad3d715dd50ca488d503215386033a017216f` |
| `pub_multi/ref/img_stats_report.json` | `ce39c70ebafeaec3458af358c34bea5abcac9282ad4dfa9ce2f618b6dc2d5424` |
| `pub_multi/ref/main_report.json` | `5ca507f49d4e60774f456328d6c7887d263e451aa7f15f298aecbd7551ecc435` |
| `pub_multi/ref/suite_lb.csv` | `d50364cdc911058eae8897312b992a4a851b8bb18c1b937f57b2b67b34c28a66` |
| `pub_multi/ref/suite_report.json` | `496d9e33d3a1ed807d2871af27e675aef62da6d74feb09072830001948f6fbdb` |
