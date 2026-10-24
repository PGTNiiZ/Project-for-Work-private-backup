# 01 — Dataset และ Feature Lineage: สิ่งที่มีอยู่ไม่ใช่ chain เดียวกันทั้งหมด

## ขอบเขต/หลักฐาน

ตรวจ `thesis_rebuild/07_dataset_raw_to_features.xlsx` แบบ read-only, source builder, archived notebook code, current production/V2 code และ present CSV/parquet/embeddings ไม่รัน notebookทั้งเล่ม ไม่ train/fine-tune classifier ไม่ regenerate embeddings ไม่ optimizepolicy การ replay TF-IDF เป็นตรวจ preprocessing formulaของartifactเดิมเท่านั้น ไม่ใช่ newMLexperiment

แหล่ง calculated evidence: `dataset_inventory.csv/json`, `transformation_verification.csv`, `dataset_audit_outputs.json`, `dataset_reconciliation_outputs.json`, `dataset_candidate_accounting.json`, `dataset_v2_feature_verification.json`, `dataset_workbook07_evidence.json`. แต่ละรายการมี exactartifactpaths/SHA-256/codecell locators ตรวจ sourcehashอีกครั้งด้วย `verify_phase01_package.py` ไม่มีrawpersonalrowsส่งออก

Source referencesหลัก: `thesis_rebuild/build_dataset_excel.py:12–42,93–158`; `src/identity_resolution/stages/prepare.py:28–69,76–161`; notebookcellsที่ extractเป็น`dataset_notebook_evidence.json` (cellnumbersเป็น1-based); `experiments/icsec_final/authoritative_run_v2/features.py:12–113`.

## 1. Dataset inventory และความสัมพันธ์ที่พิสูจน์ได้

| Artifact | Rows / columns | หน้าที่และสถานะ |
|---|---:|---|
| data_for_project/combined_profiles.csv |36,807 /11| CSVใกล้rawที่สุดที่มี ไม่ใช่originalJSON |
| data_for_project/nomalized_profiles.csv |36,807 /21| derivativeจากhistoricalnormalization;สะกดชื่อไฟล์ตามจริงไม่แก้เป็นnormalized |
| data_for_project/normalized_profiles.csv |36,807 /19| anothernormalizedsnapshot;ไม่identicalกับ21-columnfile |
| data_for_project/merged_profiles.csv |36,807 /22| notebookgroundtruthsource;entityfolderต่างจากstoredindexบางrows |
| data_for_project/normalized_profiles_with_profile_id.csv |36,807 /21| numericentity/profile_rowID snapshotของcanonicalpipeline |
| data/processed/all_profiles_cleaned.csv |24,729 /15| cleanedpopulationอีกสาย;ไม่พิสูจน์ว่าเป็นsubsetที่ทำให้36,807เกิดขึ้น |
| data/processed/all_profiles_with_blocking_keys.csv |36,807 /30| cleaned/blockingfieldsที่workbook07นำมาแสดงข้างraw |
| data/processed/candidate_pairs.csv |873,956 /3| legacynotebookstring-IDcandidatepopulation |
| data/processed/labeled_pairs.csv |204,701 /6| positives29,243+negatives175,458;ไม่ได้แปลว่าlabelทุกcandidate873,956แล้ว |
| data/processed/feature_matrix.csv |204,701 /21|4metadata+17Stage9v2features;unorderedduplicateexcess30 |
| data/processed/train_dataset.csv |143,316 /25| persistedsplitไม่ใช่proofsplitของfitmodelทุกรุ่น |
| data/processed/test_dataset.csv |30,558 /25| differจากsavednotebooktest30,713;ห้ามเอาsavedmetricมาผูกโดยชื่อไฟล์ |
| data/processed/val_dataset.csv |MISSING| pathนี้หายตามinventory ไม่เดาว่าไม่มีvalidationในทุกสาย |
| data/final/profiles_with_images.csv |24,729 /39|imageenrichmentบนอีกpopulation |
| data/final/image_features_complete.csv |2,459 /25|image-levelrecords ไม่ใช่pairfeatures |
| data/profiles_with_enriched_text.csv |24,530 /13|anotherbranchsnapshot;ไม่มีprovencompletechainเทียบnormalized36,807 |
| train_data/ground_truth_matrix_index.csv |36,807 /3|matrixindex metadata |
| train_data/ground_truth_pairs.csv |58,500 /5|directedpositivepairsของhistoricalmatrixexport |
| train_data/ground_truth_matrix.npz |MISSING|ไม่สร้างreplacementแล้วเรียกว่าoriginal |

Sourceของทุกcell: `dataset_inventory.json` exactpathrecord; bytehash/schema/full-rowduplicate/missing countsอยู่recordนั้น ไม่จำเป็นต้องcopyfullhashมาทุกตาราง

### ทำไมจำนวนแถวต่าง

36,807กับ24,729เป็นpresentpopulationsต่างกัน ไม่มีcompleteproducer/revision/exclusionlistที่พิสูจน์ว่าfileหลังเป็นต้นกำเนิดfileแรก คำอธิบายว่าcleanแล้วจำนวนเพิ่มหรือimageไม่ครบจึงทำให้ต่างเป็นเพียงhypothesisถ้าไม่มีkeyreconciliation [transformation_verification.csv:24729 cleaned→36807 normalized=UNPROVEN; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100–105]

Canonicalnumericpopulation36,807→eligible36,804อธิบายได้แน่: drop3rowsที่ไม่มีnumericentityID/user_folder;profile_row_idยังuniqueทุก36,807rows [dataset_candidate_accounting.json.numeric_entity_mapping/eligibility; src/identity_resolution/workflows/full_candidate.py:50–68]. 2,086,245คือpairrows ไม่ใช่profiles;2,073,842คือmodelscoredpairsหลังแยกexacttier

### Workbook07ตรวจตรงอะไร/ไม่ตรงอะไร

- Sheets01/02มี36,807datarows;03มี204,701;05มี24,729;06มี2,459;featureguideมี17รายการ [dataset_workbook07_evidence.json; workbook_evidence.json]
- Serializedraw/cleanfeature-sourcecellsของsheets01/02ตรงpresentCSVในvaluecomparison และkey/label/featurecellsของ03ตรวจเทียบpresentfeatureCSV รายละเอียดจำนวนcompared/mismatchedcellsใน`dataset_workbook07_evidence.json` ไม่ตีว่าพิสูจน์raw-to-cleantransition
- Builderassertline27–29คาด raw/clean36,807และalignedsource_folder/user_folder/platform/outputProfileName/pictureURL แต่currentreplayพบuser_folderต่าง3rowsและoutputProfileNameต่าง2rows จึง **builderalignmentassertionไม่ผ่านบนinputsปัจจุบัน** แม้workbookแต่ละsheetตรงกับCSVของตัวเอง [transformation_verification.csv; thesis_rebuild/build_dataset_excel.py:25–29]
- Image05semanticcomparisonหลังจัดbooleanserializationแล้วมี406cellmismatches:bio202,bio_clean202,location2. ยังระบุไม่ได้ว่าartifactเปลี่ยนภายหลังหรือExcelencoding/producerrevisionต่าง จึงไม่รับรองexportidenticalทุกvalue [dataset_reconciliation_outputs.json.workbook_image_reconciliation]
- Workbookเก็บmatch_statusA:OK203,401/DUPLICATE_ID251/NO_PROFILE1,049;B:OK204,688/DUPLICATE_ID6/NO_PROFILE7. ใช้uniqueIDlookupไม่เดาduplicateหรือmissingให้เป็นprofile [dataset_audit_outputs.json.workbook_endpoint_mapping_recomputed; builder:33–51]

Cellwisepositioncomparisonข้างต้นเป็นexportdiagnostic ไม่ใช่joiningdifferentprotocolrecords;ไม่มีการนำrawrowsที่identityไม่พิสูจน์มาเติมtraininglabels/predictions ควรตรวจindependentidentityก่อนใช้งานjoinsต่อ

## 2. 21 normalized columns และความหมาย

คำว่า21columnsมีสองschema จึงต้องระบุfilename ไม่ใช้columncountเป็นschemaidentity ตารางนี้เป็นcanonical`normalized_profiles_with_profile_id.csv`ที่ใช้production/V2 [dataset_inventory.json exactrecord; src/identity_resolution/stages/train_base.py:152–167]

| Column | หน้าที่/ข้อจำกัด |
|---|---|
|userName|normalizedaccountname ใช้namefeatures/retrieval;ไม่ใช่uniqueentitykey|
|fullName|displayname ใช้namecomparison;อาจซ้ำหรือหาย|
|bio|biotext ใช้lexical/semantic/stylefeatures|
|location|textlocation;missing≠differentknownlocation|
|externalUrl|original/serializedexternalURL evidence;parseตามbranch|
|pictureURL|imageingestionreference ไม่ใช่pairlabelหรือimageembeddingเอง|
|platform|twitter/googleplus/instagram ใช้cross-platformfilter/platformpaircode|
|user_folder|groundtruthgroupในsnapshot ไม่ใช่modelinputที่ควรให้scorer|
|bio_urls|URLsextractedจากbio;formatต้องparseก่อนsetcomparison|
|bio_url_count|จำนวนURLbio;branchmetadatafeature|
|bio_mentions|mentionsในbio;socialevidenceไม่ใช่socialgraphedgesครบ|
|bio_mentions_count|จำนวนmentions;ไม่ใช่feature17V2|
|location_type|historicalclassificationของlocationfield|
|location_valid|flagตามproducer ไม่รับรองว่าพิกัดจริงโดยอิสระ|
|latitude|parsedcoordinate;storedzeroอาจเป็นmissingfill ไม่ใช่รับรองอยู่latitude0|
|longitude|เช่นเดียวกับlatitude;อย่าใช้0เป็นknownlocationโดยไม่มีmask|
|url_count|externalURLcountตามnormalizationproducer|
|externalUrl_clean|cleaned/squashedURL evidenceสำหรับexacttier|
|external_domain|domain evidenceสำหรับblocking/URLfeatures|
|profile_id|numericentity/groupIDในschemaนี้ หลายprofilesใช้เดียวกันได้|
|profile_row_id|numericuniqueprofile-rowID ใช้canonicalendpointpairkeys|

`nomalized_profiles.csv`21columnsไม่มีprofile_row_id แต่มีoutputProfileName;profile_idและuser_folderไม่ควรสมมติว่าความหมาย/valuesตรงnumericfileโดยไม่มีmapping;ordereduser_foldercomparisonnomalized→normalizedต่าง14,348rows [dataset_inventory.json; transformation_verification.csv]. `merged_profiles.csv`มี22columnsและอีกschema ต้องดูrecordก่อนadapter

### Normalization rulesและverificationไม่ใช่คำบรรยายลอยๆ

| Transformation | Source rule | ผลตรวจ |
|---|---|---|
|currentpreparetext|lowercase,removeemojis,leading@,nonwordpunctuation,collapsewhitespace|cleaned24,729fullName/profile_id/bioตรง;usernameต่าง1 [prepare.py:76–116,149–155; reconciliationchecks]|
|historicalfirstclean|functionsnormalize_text/clean_bio/normalize_location/normalize_url|replayบนblocking36,807:usernameตรง แต่fullname32,087/bio29,950/location9,829/URL9,836rowsต่าง;ไม่พิสูจน์ว่าproducerรุ่นนี้สร้างartifact [original/01_data_clean_first.ipynb:cell15; transformationCSV]|
|laterusername/fullname|clean_username/clean_fullname|raw→nomalizedusernameต่าง1/fullnameต่าง2 [original/01_data_clean_later.ipynb:cells30,35]|
|laterlocation|clean_location_fullทำlocation/type/valid/coordinate|location/type/validต่าง1แต่latitude/longitude36,421rowsต่าง;storedzero36,426ต่อcolumn สนับสนุนmissingfillconventionต่าง ไม่รับรองgeocodecorrectness [later:cell46; reconciliationJSON]|
|laterexternalURL|clean_external_url_field/squash_single_or_list|perfieldchecksในCSV;ไม่ถือว่าข้อความURLsที่แสดงเป็นlistคือscalarURL [later:cells51–52]|
|advancedbio/URL/mention|emoji/ftfy-dependentbiofunctions|NOT_EXECUTEDเมื่อdependenciesไม่พร้อม;ไม่ใช้identityfallbackแทนfunctionจริง [later:cells39,41; dataset_audit_outputs.json]|
|blockingprefixes|str[:3].strip()บนcleanname/fullname|storedname_prefix3ต่าง123/fullname_prefix3ต่าง893;domainruleตรง [original/07_blocking.ipynb:cell5; reconciliationJSON]|
|labeled→featuremetadata|pairIDs/entity_a/labels|orderedmetadatachecksในCSV ไม่inferprobabilityjoinจากrowposition|
|GB17corrected|purelabel-freeformulasจากnumericendpoints|all17features×2,073,842pairsตรงpersistedfloat32values [dataset_v2_feature_verification.json]|
|MiniLMcosine|existingID-indexednormalized384-dimembeddingsdotproduct|legacycosineexactmatch;V2maxabsdifference6.5565e-7และzerooutside-tolerance [candidateaccounting.feature18_replay]|

134recordsoftransformationverificationประกอบsource/value/exportchecks ไม่ใช่134independenttransformations:97PASS,35FAIL,1UNPROVEN,1NOT_EXECUTED [transformation_verification.csv; verification.json]. FAILบางรายการอาจเป็นrevision/NAsemanticsต่าง ไม่กล่าวว่าผู้ทำข้อมูลผิดโดยไม่มีหลักฐาน

## 3. Entity mappingและground truth

Numeric snapshotมีprofile_row_idunique36,807,knownentitygroups15,297,user_folder↔numericprofile_idไม่มีone-to-manyconflictในknownrows;missingfolder/numericID3rowsตรงกัน [dataset_candidate_accounting.json.numeric_entity_mapping]. `profile_id`numericในสายนี้เป็นentity ไม่ควรตรวจว่าuniqueต่อprofile;legacystringIDของblockingfileมีduplicateexcess102และlookupambiguous [dataset_inventory.json]

Positivepairนิยาม: entityเดียวกันและplatformต่างกัน;negativepair:ต่างknownentitiesบนcross-platformpairs สายtrain_baseสร้างpositivesจากnumericprofile_id [train_base.py:170–189] archivedStage8v2ใช้groupbyuser_folderและitertools.combinationsแล้วข้ามsameplatform [stage8_labeling_v2.ipynb:cell4]

HistoricalGTCSV58,500directedpairsไม่มีself/out-of-range/nonunit/asymmetry แต่6directedpairsเชื่อมindexentitiesต่างกัน;indexfolderเทียบcurrentmergedต่าง3rows;cross-platformupperpairs29,246ต่างcanonicaleligible29,243 ขณะที่same-platform4คู่เท่ากัน NPZหายจึงตรวจmatrixbytesไม่สำเร็จ [dataset_candidate_accounting.json.historical_gt_csv]. ไม่ใช้GTCSVเก่าเป็นlabelauthorityใหม่โดยไม่reconcile

Legacyfeaturepairlabelตรวจจากuniqueendpointlookupได้203,367คู่โดยlabel/entity_aตรง;1,334คู่unresolvedเพราะmissing/duplicateID ห้ามเติมnegativeให้คู่เหล่านี้ [dataset_audit_outputs.json.label_verification]. Legacycleaned24,729ไม่มีresolvableendpointsสำหรับfeaturepairsนี้ จึงเป็นinput-contractmismatchที่ต้องระบุ

## 4. Pairs,labelingและblocking

### คู่ฝึกhistorical

Stage8v2สร้างallcross-platformpositivesจากgroupbyuser_folder;randomnegativeเลือกplatformcombo/rowsด้วยseed42แล้วรับต่างuser_folder มีmaxattempts;hardnegativesเลือกชื่อคล้ายจากblockingcandidates แยกจากrandom sampling [archived stage8_labeling_v2.ipynb:cells4,6และhardnegativecellในdataset_notebook_evidence.json]. Storedlabeled204,701มี29,243positive/175,458negative,unorderedduplicateexcess30และno contradictorylabelgroups [dataset_inventory.json]

Mainmultimodaltrain_baseแบ่งentities70/15/15ก่อนสร้างpositive/random/hardnegativeภายในrole;hardbucketsใช้usernameprefix1/2/3และcap120rowsต่อbucket ไม่ใช่fullretrievalnegativepopulation [train_base.py:211–289]. Storedsupervised58,696pairsของmultimodalไม่ใช่204,701หรือ2,086,245 [02_HISTORICAL_EXPERIMENT_MATRIX.md]

### Legacyblocking

ArchivedStage7originalมีexactusername/URLและkeysname_prefix3,fullname_prefix3,url_domain,username_stripped_prefix4,fullname_first4พร้อมblockcaps/graphpruningในsource [original/07_blocking.ipynb:cells3,5,7และremainingcellsในdataset_notebook_evidence.json]. ไม่เหมาว่าทุกstoredcandidateถูกสร้างด้วยcurrentnotebookrevisionเพราะstoredprefixesไม่ตรงบางrows

Legacycandidate873,956มีunresolvedentitypairs3,306;uniquepositivekeysของlabeled29,243เข้าcandidates25,252และไม่เข้า3,991 ค่าintersectioncoverageนี้ไม่ใช่canonicalrow-levelretrievalrecallเพราะstringkeys collapse duplicates [dataset_candidate_accounting.json.legacy_candidates]

### Canonicalfull-candidate/V2

EligibleknownnumericIDs36,804:twitter13,959/googleplus11,889/instagram10,956;exactusernameมีminimumlength3หรือnonemptyexternalURL แล้วblockusername-prefix3/fullname-prefix3/external_domain สร้างcross-platformcanonicalunorderedkeysและdedup;scoredexcludeexact [full_candidate.py:50–68,90–151]

Reconstructionactualkeysตรงpersistedexact/modelscored/workflowไม่มีmissing/extra/duplicatekeys:

- Exact12,403 (TP12,340/FP63),scored2,073,842,total2,086,245
- Cross-platformpositive29,243=covered25,931+missed3,312;all-platform29,247=cross29,243+same4
- possiblecross-platformuniverse449,149,239;retrievalrecall0.8867421263;reduction0.9953551185
- Incrementalexactusername11,133/URL1,270;incrementalblocksusername1,026,466/fullname1,041,315/domain6,061 การนับตามลำดับไม่ใช่独立overlap-freecontributionของแต่ละkey

ทั้งหมดคำนวณด้วย`dataset_candidate_audit.py`และsourcepaths/hashใน`dataset_candidate_accounting.json` ไม่ใช้TOTAL_POSconstantจากR-seriesมาแทน

## 5. 17 original notebook features: สูตรจริงตามsource ไม่ตามชื่อ

อ้าง`thesis_rebuild/00_notebook_history/v2/stage9_features_v2.ipynb` cells4/6/8/10 และworkbook`04_FEATURE_GUIDE!A2:B18` ต้นทางdefaultPROFILES_CSVเป็นcleaned24,729ปัจจุบันซึ่งไม่resolvefeatureendpoints;replayบนblocking36,807เป็นalternativeartifactdiagnostic ไม่ยืนยันfitlineageเดิม

| # | Feature | สูตรจริง / purpose |
|---:|---|---|
|1|username_jaro|RapidFuzz WRatio/100 ของ strippeduserName_clean ไม่ใช่Jaroจริง|
|2|username_token_sort|token_sort_ratio/100 ของusername|
|3|username_levenshtein|RapidFuzz ratio/100 ไม่ใช่1−raweditdistance/maxlen|
|4|username_both_empty|1เมื่อสองstringหลังstripว่าง;missinglookupfallback1|
|5|fullname_jaro|WRatio/100 ของfullName_clean|
|6|fullname_token_sort|token_sort_ratio/100 ของfullname|
|7|fullname_levenshtein|ratio/100 ของfullname|
|8|fullname_both_empty|ทั้งfullnameว่าง;missinglookupfallback1|
|9|bio_jaro|WRatio/100 ของbio_clean|
|10|bio_token_sort|token_sort_ratio/100 ของbio|
|11|bio_levenshtein|ratio/100 ของbio|
|12|bio_both_empty|ทั้งbioว่าง;missinglookupfallback1|
|13|bio_tfidf_cosine|TfidfVectorizer(max_features5000,stop_wordsenglish,min_df2)fitallbiosแล้วcosine pair|
|14|url_exact_match|1เมื่อexternalUrl_cleanสองข้างnonemptyและเท่ากัน|
|15|url_domain_match|1เมื่อurl_domainnonemptyสองข้างและเท่ากัน|
|16|same_platform|1เมื่อplatformเท่ากัน;missinglookup0|
|17|location_sim|WRatio/100 ของlocation_cleanเมื่อทั้งสองnonempty|

string_simคืน0เมื่อstrippedstringข้างหนึ่งว่าง;ถ้าrapidfuzzไม่มีใช้SequenceMatcherสำหรับทุกmethodจึงเปลี่ยนsemanticsตามenvironment มีNApitfall:pd.read_csvdefaultทำNaNแล้ว`str(value or '')`อาจเป็นliteral'nan';duplicateprofilelookupใช้firstrowแต่TF-IDFkey_to_idxdictใช้lastrow คนละendpointchoice [Stage9v2:cells2,4,6]. เปลี่ยนไปpureJaroโดยชื่อcolumnเหมือนเดิมไม่ใช่faithfulhistoricalreproduction

Replay17columnsบนalternativeblockinginputพบmismatchesตามcolumnในCSV:username922แต่ละsim/fullname982/bio1009,emptyflags1055,URL58/59,location989,TF-IDF1;same_platformตรง ไม่ประกาศ17featurematrixreproducibleครบและไม่แก้เก่า [transformation_verification.csv]

## 6. Reconstructed/corrected GB-17 ไม่ใช่original17

CorrectedV2schemaตาม`features.py:12–19`:

| Feature(s) | Computation source |
|---|---|
|username_jaro/fullname_jaro|actualRapidFuzzJaro similarity เมื่อทั้งสองnonempty;otherwise0 [:67–68,92–95]|
|username_lev_sim/fullname_lev_sim|1−Levenshteindistance/maxlength;missing0 [:70–73]|
|username_token_sort/fullname_token_sort|token_sort_ratio/100;missing0 [:75–76]|
|name_sim|maxJaro-Winklerของusername/fullnameสี่crossfieldcomparisonsที่available;allmissing0 [:30–49]|
|bio_jaccard|wordsetintersection/union;emptyunion0 [:85,99]|
|bio_len_ratio|minbiolength/max;bothmissing0 [:86,100]|
|both_have_bio|boolทั้งbioมีค่า [:101]|
|location_jaro|actualJaro;missing0 [:102]|
|location_exact|boolnonemptyและlocationตรง [:103]|
|both_have_location|boolทั้งlocationมีค่า [:104]|
|same_platform|boolnonemptyplatformAและเท่ากับB [:105]|
|username_len_diff|absolute lengthdifference/maxlength;bothmissing0 [:106]|
|fullname_wordcount_diff|absolute wordcountdifference/maxwordcount;bothmissing0 [:107]|
|username_prefix3_match|ทั้งusernameยาว≥3และprefix3ตรง [:108]|

NormalizeคือNFKC/casefold/strip/lstrip@/collapsewhitespaceก่อนcomparison ไม่มีlabel/scorearguments [features.py:22–49]. Independentfullpairreplay17featuresบน2,073,842pairsพบzero mismatch/maxabsdifference0ทั้งหมด [dataset_v2_feature_verification.json; dataset_v2_feature_audit.py] เป็นPASSเฉพาะfeaturevalues/formulaversion ไม่รับรองraw/encoder/splitทั้งpipeline

LegacyR2constructed17ใช้คล้ายschemaนี้แต่`name_sim`จากcacheที่gatepredecessorscore≥.5 ดังนั้นcoefficient/scorerยังรับhiddenmodeldependency; V2correctedซ่อมแล้ว [experiments/code/exp_lib.py:28,93–101; experiments/code/exp_r2_bert_feature.py; experimentmatrix02]

## 7. Feature18 และbranch-onlyfeatures

GB-18=corrected17+`bert_cos` เพียงหนึ่งcolumn [features.py:19]. มีexistingMiniLMembeddingsshape36,807×384และIDindex36,807unique;eligibleทุกendpointมีembedding,3IDsเป็นexcludedprofiles Normsใกล้1 จึงdotproductเป็นcosineหลังnormalization [dataset_candidate_accounting.json.existing_minilm_embeddings]

Legacy`pair_bert_cos.parquet`2,073,842pairs replayจากexistingembeddingIDsตรงexact;V2`bert_cos.parquet`maxabsdiff6.5565e-7อยู่toleranceทุกแถว ต้องระบุencoderrevision/textcomposition/packageversionก่อนgenerationใหม่ การมีcachehashและsemanticvalueเท่ากันไม่provepretrainedmodelrevision [dataset_candidate_accounting.json.feature18_replay; V2R1 PROTOCOL_V2R1.md:85–90]

Branch-onlyfeatureclasses: TF-IDF/SBERTbio,domain/URLJaccard,mentions/hashtags,stylecaps/wordlength/biolen/punctuation,platformpaircode,domain/hashtagcounts,imageavailability/perceptualhash/stats/face/blur/filesizeและcaptioncrosssimilarities [train_base.py:79–164; train_multimodal.py; experiments/code/run_feature_aware_ga_pipeline.py:44–53; experimentmatrix02]. ไม่อยู่corrected17เว้นที่ระบุชื่อร่วมชัด

Historicalmultimodaldeclared23text→37imagestats→41imagecontext;แต่feature-awareexportที่เรียกMULTI41มีcurrentMODEL_FEATURES37และขาดdomain_count_a/b,hashtag_count_a/bจาก41schemadeclaration ต้องใช้actualschemaไม่ใช้worksheetprefixเป็นจำนวนmodelinputs [02_HISTORICAL_EXPERIMENT_MATRIX.md:29–46; experiment_lineage.json]

10-genepolicyweightsของprobability/name/bio/URL/location/social/image/styleไม่ใช่feature18หรือ10additionalGBfeatures;availabilityweightedgroupaggregationมีsourceclassต่าง [run_feature_aware_ga_pipeline.py:34–53,83–131,274–339]

## 8. ข้อสรุปdatasetreadiness

Verified: numericrowIDs/eligibleentitymapping/canonicalpairaccounting,correctedV2-17valueformula,existingMiniLMcosinereplay,granularworkbook/sourceinventoryและlegacylabelsubset ไม่มีข้ออ้างraw-to-resultครบ

Partial/blocked: historicalGTindex/labelscopeconflicts,ambiguouslegacyIDs,rawmissing,cleanedpopulationchainunproven,normalization/export/featuremismatches,advancedbioenvironmentmissing ต้องfreezechosen numeric snapshot/labelauthority/featureversionก่อนPhase2 ไม่ต้องแก้datasetเก่าให้ดูผ่าน [06_PHASE_1_READINESS_GATE.md]

Datasetworkerหยุดด้วยHTTP429หลังสร้างauditoutputsแต่ก่อนเขียนรายงานนี้ Parentจึงอ่านsourceและoutputsแล้วเขียนreconstructionเอง การล้มของworkerไม่ถูกซ่อนหรือแปลงเป็นPASS; independentauditsที่มีผลรันจริงยังตรวจhash/schema/countsได้ด้วยpackageverifier
