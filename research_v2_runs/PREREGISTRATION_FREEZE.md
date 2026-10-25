# Preregistration Freeze — G4

UTC timestamp: 2026-10-25T19:04:57.225751+00:00
Pre-run source commit: a2dce399a36b354ce7464e22f1facf2ffe407508
Protocol SHA-256: 1b6acf5946b2eddacee3fa8affc631386fd9bac8293c9a4fc3505488046d0ed6

EXPLORATORY (LinkSocial, retrospectively exposed). ไม่มีผล validation/test ของรอบนี้ถูกอ่านก่อนสร้าง freeze.
ค่าทุกตัวอยู่ใน protocol.json (cost, k* selection rule, P_target, SESOI, seeds, search spaces/budgets). Freeze นี้ไม่ได้ยืนยัน G5 หรือ power.
Pilot variance ไม่ทำก่อน freeze เพราะทุกผลเป็น exploratory ตั้งแต่ต้น; ไม่ปรับ SESOI ย้อนหลัง.

## Design file hashes
- research_v2_review_workspace/research_v2/design/COMPUTE_AND_COST_PLAN.md: 2875ec33a27e58c326bf9687aa3da730f228651b52fc1e709fe3457ce6769ef1
- research_v2_review_workspace/research_v2/design/EVALUATION_AND_STATISTICS.md: 51f25b5a0e5be1ebd486476ae27ed7fb5e13e7d01e679c77f26575c079ebe605
- research_v2_review_workspace/research_v2/design/EXPERIMENTAL_MASTER_PLAN_TH.md: 5a12880b462239276223df782a56b2efc1c81174be50b198c396067283260a4d
- research_v2_review_workspace/research_v2/design/EXPERIMENT_DEPENDENCY_GRAPH.md: 5f7b0589d2a0c7054e46bdbbc1e92ed315fbcbed498a3da73bd774252514fefc
- research_v2_review_workspace/research_v2/design/HYPOTHESIS_EXPERIMENT_MATRIX.csv: b60af1ea0fa2b0433e4b7d50a90cc2703e21fd6cbc0e6fe088fd6170349591e3
- research_v2_review_workspace/research_v2/design/RESEARCH_GATES.md: 3ac86ecdc79b0c5d79b6b23813294c6b4309be219892fd0a4cdb150a802150ea
- research_v2_review_workspace/research_v2/design/RESEARCH_QUESTIONS_AND_HYPOTHESES.md: 4349b9a43b9c6ef83f9a1a4bc157369b4dcfdc7213e2bf93b7385d37cc83a009
- research_v2_review_workspace/research_v2/design/TRAINING_REQUIREMENTS.md: 28856bb0bba8330a4a1822b4c25a88780457ad6f958cef588524649495f2804a

## Protected inputs
Hash ทั้ง _input_v1, raw input และ historical output inventory อยู่ใน protocol.json; ไม่รวม profile values หรือ identifiers.

## Config hashes
- configs/D0-1.yaml: 183a1a00ca089bb5502b8f3ac5dc558fcf60f78dd929b631ffaa072de33e5c24
- configs/D0-2.yaml: 2c747bb04046b8c246c631651574fc74cb1e78d4d9b6a7c677d9556fda1ff0d4
- configs/D0-3.yaml: c4d96f80ae7489a353a0cf5de92c3114764c3a7b97155c71ded84fad24bf6c74
- configs/D0-4.yaml: 18a5480b5f9ebf9023c2ced6b70cfa7ee775eb481ddbc33d34b888958a667673
- configs/D0-5.yaml: b42c4643993374c37b9de303eb36550022c1133702b77bf5b3378b8b13cb1c02
- configs/E1-1.yaml: 8a4fc74ea2b0a184332c9237086397bcb71569cff3447260dc2a86d1a94ce322
- configs/E1-2.yaml: 2fd141a72dbd1c92262be3adc2f98addd7dce855f15b4cb600ca78496cdf7cf2
- configs/E1-3.yaml: 8653f73a2c42e0aae5bc79de4e834839765e8e2b4e3d96bbe12ffbbfeaa86229
- configs/E1-4.yaml: fb6ba1eadcf2dccc2c6515c99c1825418eb6cf85883a76a7fb387915903b2a71
- configs/E1-5.yaml: 1913cc55d41782060d4e6c8b9c6928bd12e2d6550a880e11f0ae22a2ecf35b13
- configs/E1-6.yaml: 1dc024c062d6c955518af56111b0f3b30d45734e72586b0c31e6fa09d3dea800
- configs/E10-1.yaml: 645529651ee39feeddcde7d18bda2c70a7878de087ae1f99ca3d9460631c5532
- configs/E2-1.yaml: 39be2de4d878f0da67a594edf0a4962d5fb890c1fea67cba2f8ab4ae9b06c8cd
- configs/E2-3.yaml: 3b68c2bee9e2021137536b06b2354bcf9787024080b253557b565da9c0aed9a3
- configs/E2-4.yaml: d1273f1a7b8841bd85eabf9162977173f468dff8170134483c682b26b2201f4f
- configs/E3-1.yaml: d53db6354728a6a72792f4e4842fb9ef5f2c1f0177307727fb6d7e7f0517c02e
- configs/E3-2.yaml: cb02c0f0e121fc39dc0210a5ceb9ad29510c6c7f2aa2bdcba1ee42cbd698628b
- configs/E3-3.yaml: f64800893cd5a2d952d7dd061b6a963448faec81cc9e5b14a85d62625d8b347e
- configs/E4-1.yaml: 7bb862aa87f19c287325a39260ff28b0e0283911a61de8641e8fc196094e678d
- configs/E4-2.yaml: de0282de33195f776f250a222fc71268f22e12f6ae7ecc24f73119bbac7638eb
- configs/E4-3.yaml: c42e2c339ea4ac574efee48502641643efe73dfea0744617271fa79001ae7f56
- configs/E4-4.yaml: d737089adff436131a1de0a01ab226bfae506c8eb1d4ad0db10e7de37ba59b63
- configs/E4-5.yaml: 15af374bf43b721dc1ec294398916bf5d7c05fedf223d24e8607215fef69611e
- configs/E5-3.yaml: 603e80347b3def925cd1a218804767667c43f822dfb90f2a6a6ddb4cac5877aa
- configs/E5-4.yaml: adcd29f8537453578090ad4c4e895213871b63dd063592cdb8ee8bbab53c5c96
- configs/E5-5.yaml: b8bf0bec61dcce9f66c1567d3051b4cc310e7a1b870a8677e5bf665d09f7d5db
- configs/E5-6.yaml: 3cbe6993c0330864943cbacc76584651afe472f3aa3816f305352152e002d137
- configs/E6-1.yaml: c1e0c03e1b3b323b42485d137f8f5bda54a65258a6d28b035b6377db085e6112
- configs/E6-2.yaml: d52f3aa9af26ea739490a4fc0095307f7da1f63454eba28a3c2bf2652a686137
- configs/E6-3.yaml: 50432ff98a783e3900e311c521fc0b15a65d5a8ebe0466c9602d9db7384f4d40
- configs/E6-4.yaml: d2a753de51ad5220c42414dd6cf229e6aa980476109f257849063de48c67f2e6
- configs/E6-5.yaml: 112dacc2d82e1673bf6f8a0d07d92a6126c226e4f32f82a05d2a39f4922c75b5
- configs/E6-6.yaml: fac202d3214dbdf25e3bbe8aa85259c754c415a7672d48c49b4bd07b9266f03a
- configs/E6-7.yaml: 5b5ef079b3da596c74ddfc3c2afeeac9fa83c50e077b2d875735c22815769112
- configs/E6-8.yaml: 511cf5be7a1dc3dcd52d197f3941952f103841ab49e247099d5b2c264ff6b3bb
- configs/E7-1.yaml: 997e870a31a91875c940f414aafadf7ade4e0d3ce3028436debf5f12cd748f09
- configs/E7-2.yaml: 00d1504c4f197afa68f034f8ea059c18bbfd36ec643bbe6b278a5c241bdb5c94
- configs/E7-3.yaml: 5c1513791b4cccfd7e13c0a74a5442ea870cf70dfec65741eec969d3056ec88b
- configs/E7-4.yaml: a1c416b2b00c946ef963ec5bca7d050415a8663561e13f6ac95924600eb37048
- configs/E7-5.yaml: 664d91cf8e482499b01e365c318b3df50e46f76661ce13c2ceb2c23de53cd2cf
- configs/E7-6.yaml: bae069c835106ac8e2afcd5ffd8ded2c5df148b789de8bd4f318e901e270560d
- configs/E7-7.yaml: b51e9118b615e373e01ef957326a6e0603e5d38c4c1189f656c5da41570e3b11
- configs/E8-1.yaml: 7affe5912207ca3def750d1f44599dfec500307c4e79019a7f43015cd03d9926
- configs/E8-2.yaml: 4d01a68bcbfa910b65a1c95fcaf9673d0291d5055ee1805b10940aa51a3e39f2
- configs/E8-3.yaml: 27f84a1bd0e43dc7abf56b88f0b6acb20793960f5517df0c037e675fb7863b6e
- configs/E9-1.yaml: 0acc4dad5e30f3d7296e64a948c90a0a8509e7d50b811bdf2407e52cb7246b7e
