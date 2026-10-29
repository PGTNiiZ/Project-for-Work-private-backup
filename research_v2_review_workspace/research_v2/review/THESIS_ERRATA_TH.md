# Thesis Errata — Round 3

สถานะ NO-GO. รายการนี้เสนอแก้เอกสาร ไม่แก้ PDF และไม่วินิจฉัยเจตนาของผู้เขียน. PDF page เป็น one-based, printed page = PDF−15 สำหรับ body. รายละเอียดและ hash ของหลักฐานอยู่ใน THESIS_EVIDENCE_RECONCILIATION.md.

## A. Factual / data corrections

| ID | PDF / printed | ประเด็น | หลักฐาน | ข้อเสนอแก้ |
|---|---|---|---|---|
| E01 | 70 /55;100 /85 | ข้อความปกติยังเรียกแหล่งข้อมูลว่า Synthetic/company-template ขัด LinkSocial | TC-01/02; [P38]; [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#A5] | ระบุ transformed LinkSocial-derived corpus และแยก provenance ที่ยัง UNKNOWN; template เป็น schema ไม่ทำให้ records เป็น synthetic |
| E02 |70–71 /55–56 | platform counts15,234/12,871/8,702 ถูกขีดฆ่า แต่ extraction อ่านเสมือน active | raster pp70–71; canonical [MAIN@1e0a2db:pub_multi/ref/full_report.json#L1-L40 data_report] | ลบ deleted revisions หลังเจ้าของยอมรับ tracked changes;ใช้13,959/10,956/11,889เฉพาะeligible scope;ไม่ลบโดยอัตโนมัติในรอบนี้ |
| E03 |70–71 /55–56 | HITL labeling assertion อยู่ใน deleted paragraph;ไม่พบannotation ledger | [MAIN@1e0a2db:train_data/v2/stage8_labeling_v2.ipynb#L148-L184 build_positive_pairs] | แยก corpus annotation จาก future review workflow;ไม่อ้างHITLเกิดขึ้นเพียงเพราะมีreview queue |
| E04 |43–44 /28–29 | active4,060,200positivesและderived20,301,000/8,120,400/302,433/24,663,633 | `pair_stats.json`/`train_data/pair_stats.json` malformed แต่มีตัวเลขจริง; aggregate log canonical29,243 | ระงับตัวเลขนี้จากmainmethodจนมีinputhash/runmanifest/labelconstruction;เก็บhistorical claimพร้อมคำเตือน ไม่เรียก fabricated |
| E05 |45–46 /30–31;54 /39 | 70/15/15profile assertionกับrows10,133,486/4,511,311/462,908และ48columnsปนกับmain41-feature | [MAIN@1e0a2db:pub_multi/ref/strict_report.json#L1-L64 train_meta];TC-17 | สร้างgeneration table: pre-sampling matrix, sampledtrain, supervised final suite;ระบุ48รวมmetadataไม่เท่ากับ41features;train10,133,486ยังไม่มีmatchingmanifestที่ยืนยันรอบนี้ |
| E06 |70 /55 | Table4.2oldsplit12,103entities/162,442pairsไม่ใช่finalsuite | [MAIN@1e0a2db:train_data/stage10_dataset.ipynb#L1-L460 saved_output] | ตัวเลขเก่ามีexecutionevidenceจริง เก็บในhistoricalappendix;อย่าระบุว่าไร้artifact;finalใช้Table4.3/ main_report |
| E07 |71 /56 |36,807vs36,804 | aggregate logและ [MAIN@1e0a2db:pub_multi/ref/full_report.json#L1-L40 data_report] | อธิบาย3แถวinvalidprofile_id;อย่าบอกrawprofilesหายไปโดยไม่ระบุfilter;29,247vs29,243ยังpartial |
| E08 |72 /57 |Figure4.1caption36,604 | Table4.1 +full_report36,804 | แก้เป็น36,804 |
| E09 |71,85 /56,70 | RR99.54ทั้งscored-onlyและexact+scored | TC-15;stored99.53551184798958ใช้2,086,245retained | เขียนnumeratorชัด;ไม่ใช้roundingกลบpopulationต่างกัน |
| E10 |82 /67 |“optimize...F1บนtest”ขัดvalidationselectioncode | TC-16 | เปลี่ยนเป็นthresholdเลือกบนvalidationแล้วรายงานtest;sweepบนtestเป็นdescriptivehistoricalไม่ใช้เลือก |
| E11 |83–84 /68–69 |ECEvalidation≈0เพราะfitเอง;อ้างcalibrationพอใช้productionกว้างเกิน | [V2R:METHODOLOGICAL_RISKS.md#R-10b];TC-08 | ระบุin-samplecalibrationdiagnostic;testECE.0044เป็นsummaryที่ยังไม่ได้ตรวจprimaryscores;ห้ามสรุปtransferจากsampledpriorไปnaturalprior |
| E12 |80,93,97 /65,78,82 |“imageช่วยจริง/อย่างมีนัย/เสถียร”เกินหลักฐาน | main_report both-imagepairs0;ไม่มีpairedCI | ใช้“observedassociationในpartialmultimodalsetting”;ไม่กล่าวimage-to-imagematchingหรือcausalbenefit |
| E13 |88–89 /73–74 |NO_MATCHpositive5,554รวมblockingmissแต่decisiontablecountดูเหมือนcandidate-only;negative1,973,846ขัดcandidate matrix1,977,158 | [MAIN@1e0a2db:analysis_decision_matrix/summary.json#L1-L35 confusion_matrix];full_report | แยกcandidateNO_MATCHpositive2,242กับmissing3,312;อย่าหักmissedpositivesจากcandidateTNเพื่อให้tabletotalลงตัว;derivedTN1,973,846ไม่มีตรงartifactที่ตรวจพบ |
| E14 |95 /80 |oldMLP3-class/F1.93/P.97/R.90/AUC.982ผสมfinalGBstory | pipeline_reportมีdecisioncountsแต่model_metricsว่าง;TC-14 | ย้ายoldsummaryเป็นhistorical;ตรวจว่าเป็นbinaryclassifier+3policytiers ไม่เรียก3-classโดยไม่มีloss/outputheadรองรับ |
| E15 |96–99 /81–84 |AP.9789และ.9797เป็นคนละrun;สรุปGBเหนือMLPทุกมิติกว้างเกิน | main_report vs model_compare;METRIC_POPULATION_MAP | บอกselectioncriterionและrunhash;ไม่รวมsampled/strict/fullcandidate/productionในrankingเดียว |
| E16 |99,101–102 /84,86–87 |LeadtiersHOT4,937/WARM9,039/COLD5,823เป็นheuristic ไม่ใช่conversionperformance | [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L373-L403 build_lead_scores] | คงoutputcountsเป็นimplementationevidence;ย้ายpredictiveLeadScoringไว้นอกproofscopeV2;ต้องมีoutcomelabelsก่อนอ้างbusinessvalidity |
| E17 |103 /88 |ref[3]authorsผิด;ref[6]DOIชี้landslide;ref[1]pages260–269ไม่ตรงupstream260–267 | Bibliography auditในreconciliation; [P01][P38][P52] | แก้recordจากprimarysources;ถอด[6]จากlead-scoringclaimจนหาpaperที่ตรงจริง;ไม่สร้างcitationแทนโดยคาดเดา |
| E18 |100 /85 |11.5%images/5.9%captionถูกต้องแต่pre-checkบอกPDF103ด้วย | main_report/ PDF93;PDF103คือbibliography | อ้างPDF93/78และ100/85;อย่าปะปนPDFindexกับprintedpage |

## B. Formatting / document errata — ไม่ใช่ scientific findings

| ID | PDF / printed | Issue / evidence | Suggested fix |
|---|---|---|---|
| F01 |12 /VI vs53 /38,54 /39,55 /40 | ListTable3.7เป็นmergedmatricesแต่body3.7เป็น41-featuretable;List3.8เป็นexperimenttracksแต่body3.8เป็นmatrixsizes | regenerateListofTablesจากcaptionsหลังfinalizeเลข |
| F02 |70–71 /55–56 |Table4.2ใช้ทั้งoldsplitและcandidatefunnel;ลักษณะblue strike-throughเห็นชัดในraster | accept/rejecttrackedchangesโดยเจ้าของ;เหลือuniquecaption;ส่งออกcleanPDFอีกชุดโดยไม่เปลี่ยนfrozenhistoricalPDF |
| F03 |49–51 /34–36 |cosineequationซ้ำและmathrenderingซ้อน;“16.”ค้างท้ายPDF51 | regenerateequationsด้วยeditorเดียวและตรวจcross-referenceทุกสมการ |
| F04 |60–62 /45–47 |ข้อความอ้างTable3.10/3.11แต่actualhyperparameter3.12และresults3.13 | ใช้auto-crossreferences ไม่แก้ด้วยการเปลี่ยนตัวเลขเฉพาะหน้า |
| F05 |77–94 /62–79 |Figurecaptionsและreferencesเลื่อนหนึ่งเลขหลายจุด เช่นcaption4.3แต่textกล่าว4.2;productionmatrixcaption4.15แต่text4.14 | ตรวจfigureanchorครบทุกภาพแล้วregenerateListofFigures |
| F06 |72 /57 |คำตก/อักขระ“การใคก”และbacktickหลงในnarrative | proofreadingภาษาไทยหลังfreezeเชิงข้อเท็จจริง |
| F07 |62 /47 |Neuralreferenceresultsrowตัดค้าง“Avg_Prec” | เติมเฉพาะค่าที่มีartifactกับscope;ถ้าไม่พบให้UNKNOWNไม่คาดเดา |
| F08 |12–13 /VI–VII |เลขหน้าtableหลายรายการไม่ตรงbody;pre-checkPDF6จริงเป็นfrontmatterไม่ใช่ListofTables | ระบุทั้งPDFindexและprintedpageในaudit;regenerateสารบัญหลังจัดหน้า |

## Privacy erratum

PDFมีตัวอย่างโปรไฟล์จริงในตารางcleaningและตัวอย่างerror (บริเวณPDF35–42และ90). รอบนี้ไม่คัดลอกค่าตัวอย่างลงreports. สำหรับฉบับเผยแพร่เสนอแทนด้วยSYNTHETICตัวอย่างที่ไม่เชื่อมกลับบัญชีจริง และให้อาจารย์/ผู้รับผิดชอบข้อมูลตัดสินก่อนrelease. ไม่แก้PDFหรือrepositoryในรอบนี้. [V2R:METHODOLOGICAL_RISKS.md#§P]
