# Confirmatory Evidence Options — Strategy Memo

สถานะปัจจุบัน NO-GO. ข้อเสนอนี้ไม่อนุญาตให้เก็บข้อมูล ดาวน์โหลดdataset หรือเริ่มtraining. รอบนี้อ่านเฉพาะpublisher/arXivpapersและGitHubREADME/license/API metadata ไม่ดาวน์โหลดdataset,embeddingsหรือweights. เอกสารpaperที่อ่านเก็บในreview/_work/เพื่อtraceability ไม่ใช่data acquisition.

## ทำไมrandomsplitใหม่ไม่เพียงพอ

V2พบtest30%ของR-seriesถูกใช้≥15ครั้งและlaterICSECมีrepeatedpartitions/reviewerrevisions. ชื่อSEALED_TESTหรือhashsplitใหม่ไม่ทำให้historicaldataกลับเป็นpristineholdout. ไม่มีเอกสารรับรองว่ามีLinkSocialidentitysubsetที่ไม่เคยมีอิทธิพลต่อการออกแบบ. ดังนั้นG5ยังBLOCKEDสำหรับstrongconfirmatoryclaimบนข้อมูลเดิม;“ไม่เคยเห็นผลของsplitใหม่นี้”ไม่เท่ากับ“ไม่เคยใช้ข้อมูลเหล่านี้พัฒนา”. [V2R:METHODOLOGICAL_RISKS.md#R-15] [V2R:FINAL_HANDOFF_TH.md#Q14]

Thesisเพิ่มความชัดว่าsampledneural,classical,multimodalและproductionreportเป็นหลายgeneration ไม่ได้เพิ่มindependentholdoutให้V2. ข้อจำกัดนี้ไม่ทำให้ผลhistoricalไร้ค่า แต่กำหนดระดับข้อสรุปเป็นexploratory/developmentevidence. [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F05] [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F06]

## ทางเลือกเปรียบเทียบ

| Option | ทำอะไร / evidence requirements | ข้อดี | ความเสี่ยง / ข้อจำกัด | Decision |
|---|---|---|---|---|
| (a) ExternalpublicUILholdout | freezefeatureintersection/models/policies/contrastsก่อนlabelaccess;verifydata-use,platforms,labelconstructionและoverlapกับLinkSocial;หากต้องadaptให้แยกexternaldevelopmentจากuntouchedholdout | ทดสอบcross-domaingeneralizationได้โดยไม่เก็บใหม่ | public≠licensed;หลายชุดมีแต่graph/embeddingหรือself-linklabels;ไม่รองรับprofileH1/H3หรือimageT9ครบ;sizeเล็ก/attributeheterogeneity | CONDITIONAL;ยังไม่พบชุดที่ครบrights+schema+independenceพร้อมใช้ทันที |
| (b) Newconsented/out-of-timecollection | protocolและethicsก่อนcollection;participants/collectionperiodที่ไม่ทับhistorical;independentidentityverificationไม่ใช้matchingfeaturesเป็นlabelproxy;retention/accesscontrol | เหมาะที่สุดสำหรับcurrentplatform/targetpopulationและbusinessrelevance | เวลา/งบ/consent/ToS;newtimepointของpersonเดิมไม่ใช่entity-disjointโดยอัตโนมัติ;อาจต้องnewtraining | CONDITIONALfutureconfirmatoryprogram;cost/timeUNKNOWNไม่แต่งestimate |
| (c) LinkSocialทั้งหมดเป็นexploratory | ระบุretrospectiveexposureทุกclaim;maincontributionเป็นrealisticprotocol/populationmapping/fairbaselines/negativefindings;predeclareก่อนrerunใด ๆ หลังG0/G1 | ไม่อ้างunseenconfirmationที่ไม่มี;ใช้historicalengineeringevidenceได้ตรงไปตรงมา | จำกัดcausalgeneralizationและdeploymentclaim;protocolimplementationไม่เท่ากับscientificresult;ยังต้องG0/G1แม้exploratory | RECOMMENDEDตอนนี้;ไม่ใช่scientificGO |

## Candidate public datasets — ตรวจว่ามีจริงแต่ไม่ดาวน์โหลด

ตัวเลขในตารางเป็นpaper/READMEreportedcounts ไม่ใช่rowcountsที่วัดจากdatasetfiles. Licenseของcodeไม่ใช่consent/สิทธิ์เผยแพร่profileโดยอัตโนมัติ. BibliographicIDsP54/P55เป็นreport-localเพิ่มจากv2P01–P49โดยไม่แก้bibliographyหรือdesignรอบนี้.

| Candidate | Sizeตามแหล่งต้นทาง | Platforms / schema | Labelconstruction | Licence / existence | Transferdecision |
|---|---|---|---|---|---|
| MAUILWeibo–Douban(WD) [P54] | Weibo9,714users/117,218relations;Douban9,526users/120,245relations;1,397matchedpairs (paperTable2,p18) | Weibo/Douban;profileattributesและfollower/followeegraph;Chinese | DoubanhomepageประกาศWeiboaccountเป็นprealignedpairs;subgraphคัดdegreeและcommunityก่อนexperiment (paperpp16–18/README) | authorrepoChenBaiyang/MAUILมีจริง;MITLICENSEระบุSoftware;scopeสำหรับrawdataset/collectionrightsยังUNKNOWN ต้องขอคำยืนยัน | candidateที่ใกล้profileUILที่สุด;CONDITIONALpendingrights/schema/overlap/label-proxychecks;selflinksทำให้URLfeatureเสี่ยงวนหาlabel;ไม่ใช่ภาพT9ทันที |
| MAUILDBLP17–19 [P54] | DBLP17 9,086users/51,700relations;DBLP19 9,325users/47,775relations;2,832matchedpairs (Table2,p18) | bibliographycoauthornetworks;ไม่ใช่socialprofilecross-platformsettingเดียวกับTwitter/Instagram/Google+ | uniqueDBLPauthorkeyเป็นalignmenttruth;pruneego/communitygraph | repoเดียวกันMITSoftware;datasetlicencescopeต้องแยกยืนยัน;paper/READMEเรียกDBLP17–19แต่บรรยายbackup2017-12-1/2018-12-1—วันที่ยังขัดชื่อ | EXCLUDEเป็นprimaryconfirmatoryUILholdout;ใช้SUPPORTINGnetwork/temporaltransferได้ถ้าrightsผ่าน ไม่ตอบH1–H5ครบ |
| Twitter–Foursquare /IONEbenchmark [P55] | Twitter5,220users/164,919relations;Foursquare5,315users/76,972relations;1,609anchorlinks (IJCAI2016Table1,p1777/PDF4) | socialnetworkgraph;profileattributesครบตามV2หรือไม่UNKNOWN | ground-truthanchorsจากFoursquareprofilesตามpaper;เป็นself-declaredlinksไม่ใช่independentmanualadjudication | originalpaperมีจริง;publicKDD-HIEPT/DeepLinkimplementationREADMEอ้างชุดนี้ แต่ระบุไม่ให้rawdataทั้งหมดเพราะprivacy;GitHublicense=null/license404 | BLOCKEDสำหรับprofilefeatureconfirmation;embedding-onlydataไม่พอH1/H3และT9;ต้องoriginaldata-usepermissionและavailableprofilesก่อน |
| Dataset-LinkSocial [P38] — negativecontrolในการเลือกholdout | upstreamREADMEInstagram10,958/Twitter13,961/Google+11,892;7,729three-platformusers;ไม่เท่ากับprocessed36,807โดยตรง | corpusต้นทางเดียวกับproject | upstreamconstruction/adjudicationไม่ระบุในREADME;fulltextยังไม่ได้แก้G0 | repoมีจริง;license=null/license404 | EXCLUDEเป็นindependentexternalholdout;การดาวน์โหลดcopyใหม่ไม่ทำให้เป็นข้อมูลอิสระ |

### Verification sources

[P54] BaiyangChenและXiaoliangChen, “MAUIL: Multilevel attribute embedding for semisupervised user identity linkage”, InformationSciences593:527–545,2022,DOI10.1016/j.ins.2022.02.023. ตรวจCrossrefmetadataและauthorpreprintarXiv:2012.00936v2,pp16–18/Table2. วิธีalignmentเป็นmultilevelattributeembedding+RCCA ไม่ใช่downstreamGApolicy. แหล่ง:
  https://arxiv.org/abs/2012.00936v2
  https://doi.org/10.1016/j.ins.2022.02.023
  https://github.com/ChenBaiyang/MAUIL
  https://api.github.com/repos/ChenBaiyang/MAUIL/license

[P55] LiLiu,WilliamK.Cheung,XinLi,LejianLiao,“AligningUsersAcrossSocialNetworksUsingNetworkEmbedding”,IJCAI2016;officialPDFTable1/§4,p1777. ไม่เดาDOIที่ไม่ได้ยืนยัน. แหล่ง:
  https://www.ijcai.org/Proceedings/16/Papers/254.pdf
  https://github.com/KDD-HIEPT/DeepLink
  https://api.github.com/repos/KDD-HIEPT/DeepLink/license

[P38] upstreamREADMEเป็นหลักฐานexistence/schema/counts ไม่ใช่สิทธิ์ใช้ข้อมูล:
  https://github.com/vishalshar/Dataset-LinkSocial
  https://api.github.com/repos/vishalshar/Dataset-LinkSocial/license

SnapshotคำตอบAPIอยู่ `_work/v3_web_metadata.json`;CrossrefและarXivqueryอยู่ `_work/v3_MAUIL_crossref.txt`, `_work/v3_MAUIL_arxiv.txt`;อ่านTable2จากpaperPDFเท่านั้นไม่เปิดdatasetarchive. DOI/URLทั้งหมดเป็นpaper/repositorysources ไม่ใช่social-profileURLs.

## ข้อเสนอสุดท้ายและเงื่อนไขเปลี่ยนทางเลือก

เลือก(c)อย่างเปิดเผยสำหรับขอบเขตปัจจุบัน เพราะไม่ต้องอ้างสิทธิ์เข้าถึงหรือความเป็นอิสระที่ยังไม่มี. ในเอกสารควรใช้คำว่า“exploratoryretrospectiveprofile-linkagestudywithanexplicitrealistic-evaluationprotocol”ไม่ใช่“confirmedgeneralization”หรือ“production-readyAgenticCRM”. หากต้องการconfirmatoryresultจริง ให้พัฒนา(b)แบบconsented/out-of-timeเป็นเป้าหมายระยะถัดไป;ถ้างบ/เวลาไม่พอให้สำรวจ(a)MAUILWDก่อน แต่ต้องผ่านdataset-specificG0/G1และตรวจschema/labelproxy/identityoverlapแบบnon-identifyingก่อนประกาศเป็นholdout. ไม่อนุมานว่าคนละplatformทำให้ไม่มีpersonoverlap. [P54][P55][P38] [V2R:FINAL_HANDOFF_TH.md#Q14]

MVP21/217/19อาจยังเป็นexploratoryplanningbudgetเดิมหลังgatesผ่าน แต่ผลไม่ใช่confirmatoryเพียงเพราะมีpre-registrationภายหลังการดูhistoricalresults. ถ้าเพิ่มexternaldatasetหรือnewcollection จำนวนfits/testevaluationsต้องfreezeใหม่ตามavailability ไม่ใส่ตัวเลขประมาณเป็นmeasurement. Leadconversionvalidationต้องมีoutcomesแยกและไม่อยู่ในholdoutUILโดยอัตโนมัติ. [V2R:FINAL_HANDOFF_TH.md#Q7] [V2R:METHODOLOGICAL_RISKS.md#R-15]
