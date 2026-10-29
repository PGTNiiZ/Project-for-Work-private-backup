# Execution Handoff — Research V2

ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.

## 1. สถานะและที่มาหลักฐาน

Original G4 freeze commit932cf956; all final configurations commit81171fd9 ก่อน sealed test access. ไม่แก้ raw data, thesis, immutable v1 หรือ design. Source/metrics evidence commit: 1bc4a8cea720e6631adb88072ac1f8dcbf01196c. [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#results]

## 2. งานที่เสร็จในแต่ละ tier

| Tier | DONE IDs | NOT RUN / partial IDs |
|---|---|---|
| 1 | D0-2, D0-4, E1-1, E1-3, E1-4, E1-5, E2-1, E2-3, E3-1, E3-2, E4-1, E4-2, E5-3, E5-5, E6-7, E6-1, E6-2, E6-3, E6-4, E6-5, E6-6, E7-1, E7-2, E7-4, E7-5, E7-6 | D0-1, D0-3 |
| 2 | E5-4 | E7-3, E7-7 |
| 3 |  | E1-2, E1-6, E4-3, E4-4, E6-8, E9-1, E10-1 |

รายละเอียดเหตุผลราย ID: EXPERIMENT_COVERAGE.csv. D0-1/D0-3 ไม่มี human audit; ไม่ปลอม κ หรือ hidden-positive rate. Tier2 learning-curve rule baselineไม่ได้ลดinformationbudgetอย่างเท่าเทียม จึงไม่อ้างsampleefficiencyเหนือrule. Tier3/optionalไม่ถูกเปิดโดยใช้testผลเป็นtrigger; T9และLeadScoring EXCLUDE.

## 3. Actual counts เทียบ plan

| ปริมาณ | MVP plan | MVP+support plan | Actual measured |
|---|---|---|---|
| Selected-model fits | 217 | 414 | 414 |
| Tuning fits | 2400 | 4800 | 4800 |
| Final configuration bundles | 19 | 21 | 21 |
| Final operating-point/seed evaluations | หน่วยต่างจากbundle | แยกนับ | 111 |
| Validation atomic evaluations | planนับconfigต่างหน่วย | ไม่เทียบตรง | 108627 |
| Search config evaluations | ไม่รวมfoldmultiplier | แยกจากatomic | 1400 |

Actual source = ACTUAL_EXECUTION_COUNTS.json + append-only ledger; trainingไม่รวมcalibration/TF-IDF/tuning. Final bundlesรวมหลายpredeclaredseeds/families; จึงเปิดเผยoperating-point countแยกและไม่กล่าวว่าbundlecountเท่ากับindependentreplications. Originalplannedcounts: [V2R:../design/EXPERIMENTAL_MASTER_PLAN_TH.md#10].

## 4. ข้อค้นพบหลักห้าข้อสำหรับกรรมการ

1. H1: หลาย lexical attributes เหนือกว่า best single group ที่เลือกจาก development; Δ=0.0983, CI95=[0.0886,0.1081], decision=supported (EXPLORATORY).
2. H2: GBDT เทียบ tuned rule ที่ selection budget เท่ากัน; Δ=0.0553, CI95=[0.0488,0.0617], decision=supported (EXPLORATORY).
3. H3: incremental frozen semantic contribution เทียบ lexical-only; Δ=0.0003, CI95=[-0.0014,0.0010], decision=equivalent (EXPLORATORY).
4. H4: GA เทียบ best non-GA (selected on development), positive Δ หมายถึงลด cost; Δ=-0.0904, CI95=[-0.1279,-0.0555], decision=not supported (EXPLORATORY).
5. H5: hybrid เทียบ best lexical ที่ matched candidate budget; Δ=-0.0003, CI95=[-0.0048,0.0040], decision=equivalent (EXPLORATORY).

ทุกข้อมีSESOI, Holm p, CI, seed SDและTOSTใน RESULTS_SUMMARY_TH.md; ไม่มีข้อใดเป็นconfirmatoryหรือuniversallybest. [MAIN@1bc4a8c:research_v2_runs/metrics/primary_contrasts.json#results]

## 5. สิ่งที่ขาดและเหตุผล

เอกสารG0/G1, independentfreshholdout, humanlabelaudit, trueconversionoutcomes, perturbationprogramและmanualcauseattributionยังขาด. รายงานstrataที่มีอยู่เป็นmechanicalaggregateไม่วินิจฉัยimpersonation. ไม่มีisolatedincrementalsemanticfeaturizercostratio; ไม่แทนค่าที่ไม่ได้วัดด้วยestimate. รายละเอียด BLOCKER_REGISTER.csv และ THREATS_TO_VALIDITY_TH.md.

## 6. Verification

ผลตรวจ executable จะ append จาก reports/consistency_check.txt หลังสร้างเอกสารและสแกน PII; ไม่มีการเติมPASSล่วงหน้า.

## 7. ลำดับถัดไป

แก้public-repository/transcript exposureกับเจ้าของระบบ → แนบเอกสารG0/G1 → humanlabel/proxy audit → เลือกlicensed/consented independentcohort → preregisternewconfirmatoryprotocolก่อนแตะlabels → ทำreplicationตามbudgetที่ประกาศ. ระหว่างนี้ใช้ตาราง/รูปเป็นEXPLORATORYเท่านั้นและห้ามpushderivedprofileartifacts.

## ขอบเขต protocol compliance ที่ยังต้อง review

Technical checks ไม่เท่ากับ full strict-v4 compliance. G4 ตรึง k* selection rule แทน numeric k ล่วงหน้า; primary AP ใช้ frozen ensemble aggregation ส่วน table ใช้ seed mean. Supporting summaries คำนวณ validation-only operating-point diagnostics หลัง final แต่ไม่ได้ใช้เปลี่ยน primary system หรือประเมิน thresholds เหล่านั้นบน test. จึงรับรอง no primary retuning ไม่ใช่ zero diagnostic selection ทั้ง session; validation counter นับ ledger-accounted held-fold/objective events ไม่รวมทุก supplemental threshold/metric call. LR และ semantic-only มี development evidence แต่ไม่มี standalone final-test configuration; ไม่เปิดเพิ่มหลัง unblinding.

Branch ยังมี inherited concurrent commit c68c9d20 ซึ่งเปลี่ยน16pathsนอก runs; owned commitsตรวจแยกและไม่ rewrite งานอื่น. ก่อนเผยแพร่ต้อง review branch scope. File-output PII scan ไม่ลบ metadata incident ใน terminal. รายละเอียด DEVIATIONS.md.

## Executed verification output

Synthetic tests:

....................................................                     [100%]
52 passed in 3.18s

PASS report RESULTS_SUMMARY_TH.md
PASS report THESIS_TABLES_TH.md
PASS report HISTORICAL_COMPARISON_TH.md
PASS report THREATS_TO_VALIDITY_TH.md
PASS report EXECUTION_HANDOFF_TH.md
PASS root artifact DEVIATIONS.md
PASS root artifact GATE_RECORD.md
PASS root artifact PREREGISTRATION_FREEZE.md
PASS root artifact LABEL_SANITY.md
PASS root artifact ENVIRONMENT.md
PASS root artifact FINAL_CONFIGS.md
PASS G4 committed before first scientific run 932cf9569abb38dfd9c3aa55e258da299e5290e6
PASS FINAL_CONFIGS committed before final access 81171fd998721c168ba2f8192264fef675993497
PASS final access matches exact frozen configurations
PASS final declaration unchanged
PASS frozen artifacts unchanged
PASS all DONE metrics trace by SHA256
PASS all scientific results EXPLORATORY
PASS every run config hash matches
PASS each run config committed before run timestamp
PASS run configurations exist verbatim in their recorded commits mismatches=0
PASS raw input/thesis/v1/design/historical SHA256 unchanged 870 protected files; mismatches=0
PASS additional raw datasets and images match pinned Git SHA256 files=4265; no filenames output
PASS five primary contrasts CI/Holm/decision
PASS equivalence decisions have TOST support
PASS policy budgets exactly 2048 per seed
PASS six model searches at 200 configs each
PASS every Tier1 DONE or explicit reason
PASS independent frozen metric recomputation
PASS no primary hyperparameter/policy/calibration jobs after test opened supporting model-summary validation-only threshold diagnostics disclosed separately
PASS all post-final supporting fits use pre-final frozen hyperparameters
PASS inference timing stages have five measured repetitions
PASS tuned rule has exactly 200 configurations
PASS public-output PII scan classified, zero profile-value hits unclassified=0; terminal incident separately disclosed
PASS all owned committed additions confined to research_v2_runs inherited concurrent c68c9d20 has16 outside paths; explicitly retained, not counted as owned writes
PASS concurrent outside delta exactly documented whole branch includes unrelated holdout_eval changes; review before any future release
PASS no private data/model/embedding/prediction committed
PASS push remains disabled
PASS=38 FAIL=0 EXPLORATORY; G5 NOT MET; terminal privacy incident disclosed

PASS ในรายการนี้มีขอบเขตตามแต่ละcheck; ไม่ใช่ ethics verification, fresh confirmatory evidence หรือการรับรอง strict protocol ทั้งหมด.
