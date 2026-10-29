# Final Configurations — EXPLORATORY

ค่าทุกตัวและ artifacts ถูกตรึงก่อน --final; ไม่มี test-selected threshold/model/seed.
E7-1 REF ใช้ best lexical blocker + lexical GBDT + validation-F1; BEST-VAL alias ไป configuration ที่มีอยู่ ไม่ evaluate ซ้ำเพื่อนับยอด.
Eight E7-2 cells: B0 vs hybrid × tuned rule vs frozen M* × fixed0.5 vs best validation policy. Rule calibration ใช้ algorithm เดียวกับ M* และ fit บน rule OOF โดยไม่ reselect.
จำนวน final configurations อาจไม่เท่า planned19 เพราะนับ atomic access configurations แยกจาก grouped experiment variants; รายงาน actual จาก access log.

| Config | Experiment | Kind | Blocker | Matcher / families |
|---|---|---|---|---|
| blocking-B0 | E1-1 | blocking | B0 | — /  |
| blocking-sparse | E1-3 | blocking | sparse | — /  |
| blocking-hybrid_rrf | E1-5 | blocking | hybrid_rrf | — /  |
| matcher-rule | E2-3 | matcher | sparse | rule /  |
| matcher-GBDT-lexical | E3-2 | matcher | sparse | GBDT-lexical /  |
| matcher-GBDT-fusion | E5-3 | matcher | sparse | GBDT-fusion /  |
| matcher-GBDT-lexical-single-fullname | E5-5 | matcher | sparse | GBDT-lexical-single-fullname /  |
| policy-E6-1 | E6-1 | policy | sparse | GBDT-fusion / fixed_0.5,historical_R0,historical_stage18 |
| policy-E6-2 | E6-2 | policy | sparse | GBDT-fusion / validation_F1 |
| policy-E6-3 | E6-3 | policy | sparse | GBDT-fusion / closed_cost,Chow |
| policy-E6-4 | E6-4 | policy | sparse | GBDT-fusion / random,scrambled_sobol,TPE |
| policy-E6-5 | E6-5 | policy | sparse | GBDT-fusion / GA |
| policy-E6-6 | E6-6 | policy | sparse | GBDT-fusion / three_way |
| factorial-B0-M0-P0 | E7-2 | factorial | B0 | rule / fixed_0.5 |
| factorial-B0-M0-P1 | E7-2 | factorial | B0 | rule / three_way |
| factorial-B0-M1-P0 | E7-2 | factorial | B0 | GBDT-fusion / fixed_0.5 |
| factorial-B0-M1-P1 | E7-2 | factorial | B0 | GBDT-fusion / three_way |
| factorial-B1-M0-P0 | E7-2 | factorial | hybrid_rrf | rule / fixed_0.5 |
| factorial-B1-M0-P1 | E7-2 | factorial | hybrid_rrf | rule / three_way |
| factorial-B1-M1-P0 | E7-2 | factorial | hybrid_rrf | GBDT-fusion / fixed_0.5 |
| factorial-B1-M1-P1 | E7-2 | factorial | hybrid_rrf | GBDT-fusion / three_way |

## Frozen artifact SHA-256
- artifacts/model_GBDT-lexical_seed11.pkl: 7371468767b0ab7987d91c24873f71e56c4c3a23103ab23047dc2095ff13b5c5
- artifacts/model_GBDT-lexical_seed23.pkl: 8a5517407e1d40eaa02b64137d30107bd10c19cede55edd20e1a80275eb0d7ea
- artifacts/model_GBDT-lexical_seed42.pkl: 5fcdfe909b2fb6d9feb3e4e70a8aff35f850cded8227567e65fed2bed5aaacfc
- artifacts/model_GBDT-lexical_seed71.pkl: 8dc6d35306bc77fc5035efc59ff15962be5c7a6f77b149d6f07558b7d1639eed
- artifacts/model_GBDT-lexical_seed101.pkl: ebde3fc01f1fbd77e5554c985ee8443c2070c23e451d0ec8c824decf7095cb60
- artifacts/model_GBDT-fusion_seed11.pkl: fb74eee6a61e92f8b7530d5ed6c640654cce7ecdc2009f89951c32ffba9493fe
- artifacts/model_GBDT-fusion_seed23.pkl: 354ad388062fce3888ffe3525e04a7065a478c69f407e7074406e95444a93fab
- artifacts/model_GBDT-fusion_seed42.pkl: 46c06b5ba66a1ae972ae6e980102ed24172ac8e228680754a77c4634737a5ec7
- artifacts/model_GBDT-fusion_seed71.pkl: de7385d19dcd10fa39dca78be9dc4c15c6953403b2ab3102a5e6efd9869bf3aa
- artifacts/model_GBDT-fusion_seed101.pkl: 362a495b19bfe851d74b9bac059792e22bc9a58987a402aa49b1aeb4c8333f66
- artifacts/model_GBDT-lexical-single-fullname_seed11.pkl: 574fd18be1ff3a194894bfade2baffea942cebc15e5a1e4d195d34b2ae15c197
- artifacts/model_GBDT-lexical-single-fullname_seed23.pkl: be909779824646d58171cfeed0290f5d23400d2bccb84f5764812296e92723a9
- artifacts/model_GBDT-lexical-single-fullname_seed42.pkl: 360ccaeca937b08ddec7e020d9f0b6affc6ca2631f7f19a6e4aabce9f287ec89
- artifacts/model_GBDT-lexical-single-fullname_seed71.pkl: 91dae9d7e8b71a968ada3a42608a2e9e296d769c7aaa27ea49e1e976155f39ee
- artifacts/model_GBDT-lexical-single-fullname_seed101.pkl: a3012f7be8c0446f0b934f215a6798e81d6e77825fd7e306e8cbcff789038e9a
- artifacts/rule_weights.npy: 7d455cf2276f0c7f0de14804f84e192496cab7ab15a0cf5d411523cd854165ff
- artifacts/calibrator.pkl: d9e909bcfc76c3dfe68f3f1b9aded4cf4deaf20a72d4037d8fb7d0d70972a58a
- artifacts/rule_calibrator.pkl: 8c061e23df4e8530451d1c4fe61bfbc4c298dd7bd457b21b91369f64cb74eed4
- data_derived/representation/lexical_vectors_cv4.pkl: f82435ed74c3d2e2b60943896bd6878a2b8d04f74d0a77af0d0f10b04c2183f1
- data_derived/representation/retriever_refit.pkl: a4b42bc0f4860cf2a3219520298d92726bd8ef938cba9e8590c78d6abdca5605
- metrics/blocker_selection.json: 9a8a4f2660bef6a276d096b8e992732397a10f2164889b5bfdab1b6a6651045a
- metrics/policy_selection.json: ec5af9eb3da4fd90f3f0e33fd0ad5785df84f8eecad19b231218c6febd85294f
- metrics/single_group_selection.json: c90dc6e412225b23ad3d872a813bc3b7c80ae23cc9b62637053c9db8af8426be
- metrics/model_rule.json: f84bbf3583fc6f5468e9086bf24db53120c5b361659d5fc0481ae0100c225093
- protocol.json: 1b6acf5946b2eddacee3fa8affc631386fd9bac8293c9a4fc3505488046d0ed6
- manifests/split_summary.json: 816826d7912b892ec2dabd547f66fc3826b69f2391d4cdc45638445e66510a37
- manifests/TIER2_FIXED_PLAN.json: 7b766bcc3e858ef2d29e73a8ba0b928ede63d1a974fab44a810776bcc83347b0
- tier2_run.py: e3e1b1dc38c66744d9c2c27bee6125451c51635c1ff8c7a6699767f0d3988e11
- final_run.py: dd193ef35303ceed6851a79ba0620ea59fa46007963871ce620cf53e17854f08
- decision_run.py: 02ba1717114dac761bd25c29f6f816b5b1a0ea8e774db52205a7662312483dcd
- training.py: a634b13c129212925e2400cc9fcd1ca80e90563da0e7cee669185b034a0eaa9b
- statistics_run.py: 2aadf0b75fa0753d8d6f3925ce5c107c38e1985087fcaca8959412cf9a81fb33
- work/representation/rep.py: 60f0260a573a554353e9a4778e7baeebe760f40addabe10fd69f3e1ec591d55b
- work/statistics/analysis_tools.py: 6fbc815762f5f7cfa76e11bbd704cd4cb7c7576c73718a819b12119f2364b67c
- metrics/model_GBDT-lexical.json: 18afb007b7b2ce5872bb9c5a53acfdbfca2885b057ad872e646ac471f78be695
- metrics/model_GBDT-fusion.json: a92a396d8573b0a595217a4353496e08c9d14475a2d49227649c604098775d3e
- metrics/model_GBDT-lexical-single-fullname.json: 6ab19de7b27a97b9709a1d8c2dd42291dc3740dc513e8d951091af7671251cac
