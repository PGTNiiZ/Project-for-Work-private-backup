"""Build the reconciled V2 HYPOTHESIS_EXPERIMENT_MATRIX.csv (single source of truth for IDs and counts)."""
import csv, sys
from pathlib import Path

OUT = Path(sys.argv[1])
COLS = ["exp_id","track","pipeline_stage","name","hypotheses_or_DQ","independent_variable","fixed_controls",
        "baseline_for_comparison","primary_metric","secondary_metrics","training_required","training_type",
        "gpu_required","priority","in_minimum_program","depends_on","motivating_papers","historical_link",
        "reusable_code","v2_id_status","n_variants","n_training_jobs","n_tuning_fits","n_validation_evals",
        "n_test_evals","status"]

M = "MAIN@1e0a2db"
rows = []
def r(**k):
    d = {c: "" for c in COLS}; d.update({k2: str(v) for k2, v in k.items()}); rows.append(d)

# ---------------- D0 diagnostics ----------------
r(exp_id="D0-1",track="D0",pipeline_stage="diagnostic",name="Label provenance audit (LinkSocial origin + dual annotation)",
  hypotheses_or_DQ="DQ0;DQ1",independent_variable="—",fixed_controls="—",baseline_for_comparison="—",
  primary_metric="Cohen kappa; positive error rate",secondary_metrics="label-proxy mechanism documented",
  training_required="No",training_type="—",gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",
  depends_on="G1",motivating_papers="P33;P07;P38",historical_link="user_folder GT; Dataset-LinkSocial gitlink",
  reusable_code=f"{M}:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L167-L186",
  v2_id_status="KEPT (scope extended)",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,
  status="PROPOSED/BLOCKED(G0,G1)")
r(exp_id="D0-2",track="D0",pipeline_stage="diagnostic",name="Dataset profile and datasheet",hypotheses_or_DQ="DQ2",
  independent_variable="—",fixed_controls="—",baseline_for_comparison="—",primary_metric="Missingness and language per attribute",
  secondary_metrics="1:1 vs 1:n ratio",training_required="No",training_type="—",gpu_required="No",priority="ESSENTIAL",
  in_minimum_program="Yes",depends_on="G1",motivating_papers="P33;P01",historical_link="schema stats in REPOSITORY_RESEARCH_INVENTORY §5",
  reusable_code="—",v2_id_status="KEPT",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="PROPOSED/BLOCKED(G1)")
r(exp_id="D0-3",track="D0",pipeline_stage="diagnostic",name="Hidden-positive audit of high-similarity unlabeled pairs",
  hypotheses_or_DQ="DQ1;DQ5",independent_variable="—",fixed_controls="—",baseline_for_comparison="—",
  primary_metric="Estimated hidden-positive rate pi_hidden with CI",secondary_metrics="—",training_required="No",training_type="—",
  gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",depends_on="G1;D0-1",motivating_papers="P27;P07",
  historical_link="exact-tier FP 63 (HIST)",reusable_code="—",v2_id_status="KEPT",n_variants=0,n_training_jobs=0,n_tuning_fits=0,
  n_validation_evals=0,n_test_evals=0,status="PROPOSED/BLOCKED(G1)")
r(exp_id="D0-4",track="D0",pipeline_stage="diagnostic",name="Leakage, duplicate and historical-exposure audit",
  hypotheses_or_DQ="DQ3",independent_variable="—",fixed_controls="—",baseline_for_comparison="—",
  primary_metric="Cross-split identities; leaky features; identities previously used in historical test",
  secondary_metrics="—",training_required="No",training_type="—",gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",
  depends_on="D0-2",motivating_papers="P20;P21",historical_link="md5 test split reused >=15 times; leakage_excluded_features*.txt",
  reusable_code=f"{M}:exp_lib.py#L166-L221 build_nested_entity_split; {M}:train_data/leakage_excluded_features.txt",
  v2_id_status="KEPT (scope extended)",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="PROPOSED/BLOCKED(G1)")
r(exp_id="D0-5",track="D0",pipeline_stage="diagnostic",name="Historical artifact re-analysis (CI on stored predictions; exploratory)",
  hypotheses_or_DQ="DQ7",independent_variable="—",fixed_controls="stored historical predictions only",baseline_for_comparison="—",
  primary_metric="Bootstrap CI of historical deltas (R1 vs R3; GB-18 vs GB-18-GA)",secondary_metrics="—",training_required="No",
  training_type="—",gpu_required="No",priority="OPTIONAL",in_minimum_program="No",depends_on="G1",motivating_papers="P21;P22",
  historical_link="experiments/*probabilities.parquet (HIST)",reusable_code=f"{M}:exp_lib.py#L130-L140 evaluate",
  v2_id_status="NEW",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="PROPOSED/BLOCKED(G1)")

# ---------------- T1 ----------------
def t1(i,name,iv,base,prim,sec,train,ttype,gpu,prio,mvp,dep,pap,hist,code,stat,nv,ntr,ntu,nval,ntest,st="PROPOSED"):
    r(exp_id=i,track="T1",pipeline_stage="S1 candidate generation",name=name,hypotheses_or_DQ="H5" if i!="E1-4" else "H5;H3",
      independent_variable=iv,fixed_controls="Normalization; matched candidate budget",baseline_for_comparison=base,
      primary_metric=prim,secondary_metrics=sec,training_required=train,training_type=ttype,gpu_required=gpu,priority=prio,
      in_minimum_program=mvp,depends_on=dep,motivating_papers=pap,historical_link=hist,reusable_code=code,v2_id_status=stat,
      n_variants=nv,n_training_jobs=ntr,n_tuning_fits=ntu,n_validation_evals=nval,n_test_evals=ntest,status=st)
t1("E1-1","Historical B0 replica: exact tier (username/URL) + key blocking (username/fullname prefix3, external domain)","Blocking method","—(is baseline)",
   "PC at native |C_B0|","RR;PQ;latency","No","—","No","ESSENTIAL","Yes","G4","P12;P17","F07 B0 (HIST PC=0.8866)",
   f"{M}:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L118-L179","KEPT (now exactly specified)",1,0,0,1,1)
t1("E1-2","Token blocking + block purging","Blocking method","E1-1","PC@|C_B0|","RR;PQ;latency","No","—","No","CONDITIONAL","No","G4",
   "P12;P10","—","—","KEPT (priority changed)",5,0,0,5,0)
t1("E1-3","TF-IDF char n-gram sparse retrieval top-k","Blocking method; k","E1-1","PC@|C_B0| and PC@k*","RR;PQ;recovery rate;latency",
   "No","fit vocabulary on D_train only","No","ESSENTIAL","Yes","G4","P12;P14","F02 bigram index (REFERENCE_ONLY)",
   f"{M}:bigram_username_and_fullname/bigram_full_pipeline.py#L287-L327 (idea only)","KEPT",5,0,0,5,1)
t1("E1-4","Dense retrieval frozen encoder kNN top-k","Blocking method; encoder; k","Best lexical of E1-1..E1-3","PC@k*",
   "recovery rate;index time;RAM","No","frozen encoder","No (optional)","ESSENTIAL","Yes","G4;D0-2","P13;P14;P15",
   "R6 hash blocking (REFERENCE_ONLY; recovery 4/3,316)",f"{M}:exp_r2_bert_feature.py#L95-L114 encode_profiles","KEPT",10,0,0,10,0)
t1("E1-5","Hybrid sparse+dense (union or RRF) at matched budget","Fusion mode; k","Best lexical of E1-1..E1-3","PC@|C_B0| (primary H5)",
   "recovery of B0-missed positives;latency","No","—","No","ESSENTIAL","Yes","E1-3;E1-4","P13","—","—","KEPT",10,0,0,10,1)
t1("E1-6","Supervised meta-blocking (GSM-style)","Blocking method","E1-5","PC@|C_B0|","RR;training size curve","Yes",
   "classifier for pruning","No","CONDITIONAL","No","E1-5;G3 (run only if best PC < 0.90)","P10;P11","HIST B0 PC 0.8866 < 0.90 suggests trigger",
   "—","KEPT",5,25,0,5,0)

# ---------------- T2 ----------------
r(exp_id="E2-1",track="T2",pipeline_stage="S2 feature representation",name="Per-attribute lexical similarity profile (F-LEX)",
  hypotheses_or_DQ="H1;H2",independent_variable="Similarity function per attribute",fixed_controls="C(B*) from T1",
  baseline_for_comparison="—",primary_metric="Univariate PR-AUC per feature",secondary_metrics="Missing-indicator rates",
  training_required="No",training_type="TF-IDF vocab on D_train only",gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",
  depends_on="E1-5;E1-1",motivating_papers="P17;P02;P03",historical_link="17 hand features of R2 (F09); 41 features of F06",
  reusable_code=f"{M}:exp_r2_bert_feature.py#L53-L61 FEATURE17_COLS; #L146-L265 compute_features17",
  v2_id_status="KEPT",n_variants=1,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=1,n_test_evals=0,status="PROPOSED")
r(exp_id="E2-2",track="T2",pipeline_stage="S4 decision policy",name="RETIRED: historical rule replica (merged into E6-1)",
  hypotheses_or_DQ="—",independent_variable="—",fixed_controls="—",baseline_for_comparison="—",primary_metric="—",secondary_metrics="—",
  training_required="No",training_type="—",gpu_required="No",priority="EXCLUDE",in_minimum_program="No",depends_on="—",
  motivating_papers="P16",historical_link="R0 is a threshold on a learned score, not a lexical rule formula",
  reusable_code="—",v2_id_status="RETIRED -> E6-1",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="EXCLUDED")
r(exp_id="E2-3",track="T2",pipeline_stage="S3 classifier",name="Tuned weighted rule (weights on simplex + threshold; same budget as T3)",
  hypotheses_or_DQ="H2",independent_variable="Rule weights/threshold",fixed_controls="F-LEX; C(B*); search budget = 200 configs",
  baseline_for_comparison="—(H2 baseline)",primary_metric="PR-AUC",secondary_metrics="F1;Recall@P_target;learning curve",
  training_required="No",training_type="parameter search on D_train (grouped CV)",gpu_required="No",priority="ESSENTIAL",
  in_minimum_program="Yes",depends_on="E2-1",motivating_papers="P16;P17;P41",historical_link="—",reusable_code="—",
  v2_id_status="KEPT",n_variants=1,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=200,n_test_evals=1,status="PROPOSED")
r(exp_id="E2-4",track="T2",pipeline_stage="S3 classifier",name="Fellegi-Sunter unsupervised EM",hypotheses_or_DQ="H2",
  independent_variable="Probabilistic rule",fixed_controls="F-LEX binarized; C(B*)",baseline_for_comparison="E2-3",
  primary_metric="PR-AUC",secondary_metrics="F1",training_required="No",training_type="unsupervised EM (5 inits)",gpu_required="No",
  priority="OPTIONAL",in_minimum_program="No",depends_on="E2-1",motivating_papers="P16",historical_link="—",reusable_code="—",
  v2_id_status="KEPT",n_variants=1,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=5,n_test_evals=0,status="PROPOSED")

# ---------------- T3 ----------------
r(exp_id="E3-1",track="T3",pipeline_stage="S3 classifier",name="Logistic Regression on F-LEX",hypotheses_or_DQ="H2",
  independent_variable="Learner",fixed_controls="F-LEX; C(B*); 200 configs",baseline_for_comparison="E2-3",primary_metric="PR-AUC",
  secondary_metrics="F1;Brier;ECE;ms/1k pairs;learning curve",training_required="Yes",training_type="supervised",gpu_required="No",
  priority="SUPPORTING",in_minimum_program="No",depends_on="E2-1;G4",motivating_papers="P21;P26",historical_link="F06 logreg (HIST)",
  reusable_code="—",v2_id_status="KEPT (priority changed)",n_variants=1,n_training_jobs=17,n_tuning_fits=800,n_validation_evals=200,n_test_evals=0,status="PROPOSED")
r(exp_id="E3-2",track="T3",pipeline_stage="S3 classifier",name="Gradient Boosted Trees on F-LEX (= E5-1 reference)",
  hypotheses_or_DQ="H2;H1;H3",independent_variable="Learner",fixed_controls="F-LEX; C(B*); 200 configs; 5 seeds",
  baseline_for_comparison="E2-3",primary_metric="PR-AUC",secondary_metrics="F1;Brier;ECE;ms/1k pairs;learning curve",
  training_required="Yes",training_type="supervised",gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",
  depends_on="E2-1;G4",motivating_papers="P10;P21",historical_link="F13 GB-17 (HIST; untuned)",
  reusable_code=f"{M}:run_gb_transformer_experiments.py#L279-L301 train_gb_variant",v2_id_status="KEPT (absorbs E5-1)",
  n_variants=1,n_training_jobs=37,n_tuning_fits=800,n_validation_evals=200,n_test_evals=1,status="PROPOSED")
r(exp_id="E3-3",track="T3",pipeline_stage="S3 classifier",name="Random Forest on F-LEX",hypotheses_or_DQ="H2",independent_variable="Learner",
  fixed_controls="As E3-2",baseline_for_comparison="E3-2",primary_metric="PR-AUC",secondary_metrics="F1",training_required="Yes",
  training_type="supervised",gpu_required="No",priority="OPTIONAL",in_minimum_program="No",depends_on="E3-2",motivating_papers="P17",
  historical_link="F06 rf (HIST)",reusable_code="—",v2_id_status="KEPT",n_variants=1,n_training_jobs=25,n_tuning_fits=800,n_validation_evals=200,n_test_evals=0,status="PROPOSED")

# ---------------- T4 ----------------
r(exp_id="E4-1",track="T4",pipeline_stage="S2 feature representation",name="Frozen bi-encoder cosine features per text attribute (F-SEM)",
  hypotheses_or_DQ="H3",independent_variable="Encoder (<=2)",fixed_controls="Encoder revision; serialization",baseline_for_comparison="—",
  primary_metric="Univariate PR-AUC per semantic feature",secondary_metrics="ms/pair;coverage",training_required="No",
  training_type="frozen encoder inference",gpu_required="No (optional)",priority="ESSENTIAL",in_minimum_program="Yes",
  depends_on="E1-5;D0-2",motivating_papers="P15;P14;P08",historical_link="R2 MiniLM cosine on fullName+bio+location (F09)",
  reusable_code=f"{M}:exp_r2_bert_feature.py#L78-L137",v2_id_status="KEPT",n_variants=2,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=2,n_test_evals=0,status="PROPOSED")
r(exp_id="E4-2",track="T4",pipeline_stage="S3 classifier",name="Semantic-only classifier (canonical; former E5-2)",hypotheses_or_DQ="H3",
  independent_variable="Feature set",fixed_controls="Learner (LR & GBDT); C(B*)",baseline_for_comparison="E3-2",primary_metric="PR-AUC",
  secondary_metrics="FN recovered",training_required="Yes",training_type="supervised classifier",gpu_required="No",priority="SUPPORTING",
  in_minimum_program="No",depends_on="E4-1",motivating_papers="P15",historical_link="—",reusable_code="—",
  v2_id_status="KEPT (absorbs E5-2)",n_variants=2,n_training_jobs=30,n_tuning_fits=1600,n_validation_evals=400,n_test_evals=0,status="PROPOSED")
r(exp_id="E4-3",track="T4",pipeline_stage="S2 feature representation",name="Fine-tuned bi-encoder (contrastive)",hypotheses_or_DQ="H3b",
  independent_variable="Representation training",fixed_controls="C(B*); learner",baseline_for_comparison="E4-1 within E5-3",
  primary_metric="PR-AUC",secondary_metrics="GPU-h;ms/pair",training_required="Yes",training_type="fine-tuning",gpu_required="Yes",
  priority="CONDITIONAL",in_minimum_program="No",depends_on="E5-3;T4 inclusion rule",motivating_papers="P15;P14",
  historical_link="R6 GPU plan (PROPOSED_NEVER_EXECUTED)",reusable_code="—",v2_id_status="KEPT",n_variants=1,n_training_jobs=15,
  n_tuning_fits=0,n_validation_evals=3,n_test_evals=0,status="PROPOSED")
r(exp_id="E4-4",track="T4",pipeline_stage="S3 classifier",name="Fine-tuned cross-encoder (Ditto-style)",hypotheses_or_DQ="H3b",
  independent_variable="Representation training",fixed_controls="C(B*); serialization template; 3 seeds",baseline_for_comparison="E5-3",
  primary_metric="PR-AUC",secondary_metrics="GPU-h;ms/pair;stratum results",training_required="Yes",training_type="fine-tuning",
  gpu_required="Yes",priority="CONDITIONAL",in_minimum_program="No",depends_on="E5-3;T4 inclusion rule",motivating_papers="P04;P05;P06",
  historical_link="R6 DistilBERT (frozen; F11)",reusable_code="—",v2_id_status="KEPT",n_variants=1,n_training_jobs=15,n_tuning_fits=0,
  n_validation_evals=3,n_test_evals=0,status="PROPOSED")
r(exp_id="E4-5",track="T4",pipeline_stage="S3 classifier",name="Local LLM zero/few-shot matcher",hypotheses_or_DQ="H3 (exploratory)",
  independent_variable="Matcher type",fixed_controls="Prompt frozen at G4; local model only",baseline_for_comparison="E5-3",
  primary_metric="PR-AUC (on sample)",secondary_metrics="cost per pair",training_required="No",training_type="prompting",gpu_required="Yes",
  priority="OPTIONAL",in_minimum_program="No",depends_on="G1 explicit approval",motivating_papers="P09",historical_link="—",
  reusable_code="—",v2_id_status="KEPT",n_variants=1,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=3,n_test_evals=0,status="PROPOSED/BLOCKED(G1)")

# ---------------- T5 ----------------
r(exp_id="E5-1",track="T5",pipeline_stage="S3 classifier",name="ALIAS: lexical-only reference = E3-2 (GBDT) / E3-1 (LR) outputs",
  hypotheses_or_DQ="H1;H3",independent_variable="—",fixed_controls="—",baseline_for_comparison="—",primary_metric="(from E3-2)",
  secondary_metrics="—",training_required="No",training_type="reuses E3-1/E3-2 artifacts",gpu_required="No",priority="ESSENTIAL",
  in_minimum_program="Yes (via E3-2)",depends_on="E3-2",motivating_papers="P01;P02",historical_link="R0/R1 representation (HIST)",
  reusable_code="—",v2_id_status="ALIAS -> E3-2/E3-1",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="ALIAS")
r(exp_id="E5-2",track="T5",pipeline_stage="S3 classifier",name="ALIAS: semantic-only = E4-2",hypotheses_or_DQ="H3",independent_variable="—",
  fixed_controls="—",baseline_for_comparison="—",primary_metric="(from E4-2)",secondary_metrics="—",training_required="No",
  training_type="reuses E4-2",gpu_required="No",priority="SUPPORTING",in_minimum_program="No",depends_on="E4-2",motivating_papers="P15",
  historical_link="—",reusable_code="—",v2_id_status="ALIAS -> E4-2",n_variants=0,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=0,n_test_evals=0,status="ALIAS")
r(exp_id="E5-3",track="T5",pipeline_stage="S2 feature representation",name="Lexical + Semantic fusion",hypotheses_or_DQ="H3 (primary)",
  independent_variable="Feature set",fixed_controls="Learner; 200 configs; C(B*); seeds",baseline_for_comparison="E5-1 (=E3-2)",
  primary_metric="PR-AUC",secondary_metrics="FN recovered;FP change;cost ratio ms/pair",training_required="Yes",training_type="supervised",
  gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",depends_on="E3-2;E4-1",motivating_papers="P13;P04",
  historical_link="R2/R3 18-feature; GB-18 (HIST)",reusable_code=f"{M}:run_gb_transformer_experiments.py#L279-L301",
  v2_id_status="KEPT",n_variants=2,n_training_jobs=30,n_tuning_fits=1600,n_validation_evals=400,n_test_evals=1,status="PROPOSED")
r(exp_id="E5-4",track="T5",pipeline_stage="S2 feature representation",name="Leave-one-attribute-group-out ablation (5 groups)",
  hypotheses_or_DQ="H1",independent_variable="Feature set",fixed_controls="Hyperparameters frozen from E5-3",baseline_for_comparison="E5-3",
  primary_metric="Delta PR-AUC per group",secondary_metrics="stratum effects",training_required="Yes",training_type="supervised",
  gpu_required="No",priority="SUPPORTING",in_minimum_program="No",depends_on="E5-3",motivating_papers="P01;P02",
  historical_link="F02 location delta; F15 name-sim ablation (HIST)",reusable_code="—",v2_id_status="KEPT (priority changed)",
  n_variants=5,n_training_jobs=150,n_tuning_fits=0,n_validation_evals=30,n_test_evals=0,status="PROPOSED")
r(exp_id="E5-5",track="T5",pipeline_stage="S2 feature representation",name="Single-attribute-group lexical models (5 groups)",
  hypotheses_or_DQ="H1 (primary)",independent_variable="Feature set",fixed_controls="Hyperparameters frozen from E3-2",
  baseline_for_comparison="E5-1 (=E3-2) vs best single group",primary_metric="PR-AUC",secondary_metrics="Recall@P_target",
  training_required="Yes",training_type="supervised",gpu_required="No",priority="ESSENTIAL",in_minimum_program="Yes",depends_on="E3-2",
  motivating_papers="P02;P03",historical_link="—",reusable_code="—",v2_id_status="KEPT",n_variants=5,n_training_jobs=150,n_tuning_fits=0,
  n_validation_evals=30,n_test_evals=1,status="PROPOSED")
r(exp_id="E5-6",track="T5",pipeline_stage="S2 feature representation",name="Missingness-aware fusion",hypotheses_or_DQ="H1 (exploratory)",
  independent_variable="Missing handling",fixed_controls="As E5-3",baseline_for_comparison="E5-3",primary_metric="PR-AUC in high-missing strata",
  secondary_metrics="—",training_required="Yes",training_type="supervised",gpu_required="No",priority="OPTIONAL",in_minimum_program="No",
  depends_on="E5-3;D0-2",motivating_papers="P01",historical_link="location missing 65% (schema)",reusable_code="—",v2_id_status="KEPT",
  n_variants=2,n_training_jobs=50,n_tuning_fits=0,n_validation_evals=10,n_test_evals=0,status="PROPOSED")

# ---------------- T6 ----------------
def t6(i,name,hyp,iv,base,prim,sec,ttype,prio,mvp,dep,pap,hist,code,stat,nv,nval,ntest):
    r(exp_id=i,track="T6",pipeline_stage="S4 decision policy",name=name,hypotheses_or_DQ=hyp,independent_variable=iv,
      fixed_controls="Frozen calibrated M* OOF scores on development folds; frozen cost model",baseline_for_comparison=base,primary_metric=prim,
      secondary_metrics=sec,training_required="No",training_type=ttype,gpu_required="No",priority=prio,in_minimum_program=mvp,
      depends_on=dep,motivating_papers=pap,historical_link=hist,reusable_code=code,v2_id_status=stat,n_variants=nv,n_training_jobs=0,
      n_tuning_fits=0,n_validation_evals=nval,n_test_evals=ntest,status="PROPOSED")
t6("E6-7","Probability calibration (Platt vs isotonic) on D_cal","H4 (precondition)","Calibration method","Uncalibrated","ECE;Brier",
   "reliability diagram","calibration fit (1-2 params)","ESSENTIAL","Yes","E5-3;E3-2","P26","isotonic in F06/F09/F13",
   f"{M}:run_gb_transformer_experiments.py#L279-L301","KEPT",2,2,0)
t6("E6-1","Fixed/historical policies: t=0.5; R0 (0.98/0.95); stage18 manual 4-gene rule","H4a;historical bridge","Policy",
   "—(reference)","Expected cost per pair","False merges/1k;F1","—","SUPPORTING","No","E6-7","P18",
   "R0 production rule; manual_stage18 [0.98,0.95,0.90,0.70]",f"{M}:exp_r1_ga_redecision.py#L18 STAGE18_MANUAL; #L75-L84 decide_code",
   "KEPT (absorbs E2-2)",3,3,1)
t6("E6-2","Validation-F1-optimal threshold","H4b (baseline)","Policy","E6-1","Expected cost per pair","F1;false merges/1k",
   "threshold sweep (99 values)","ESSENTIAL","Yes","E6-7","P18","threshold=argmax val F1 in F06",
   f"{M}:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L388-L393 choose_threshold","KEPT",1,99,1)
t6("E6-3","Closed-form cost-optimal threshold t*=c_FP/(c_FP+c_FN) (+4 cost scenarios)","H4a (primary);H4b (baseline)","Policy",
   "E6-1","Expected cost per pair","false merges/1k","analytic","ESSENTIAL","Yes","E6-7","P24;P25","Chow risk rule of reviewer revision (HIST U 1879.0)","BACKUP@903246c:experiments/code/reviewer_revision.py (chow_decide)","KEPT",4,4,1)
t6("E6-4","Non-GA search (random, scrambled Sobol, TPE) on the same policy space and budget","H4b (baseline)","Optimizer",
   "E6-3","Expected cost per pair","seed SD","policy search 3 optimizers x 10 seeds x 2,048 evals","ESSENTIAL","Yes","E6-7","P21;P24;P41;P42","ICSEC v2 B1/B2 unscrambled Sobol 12,000 calls (HIST)","BACKUP@903246c:experiments/icsec_final/authoritative_run_v2/policies.py (b1_search/b2_sobol_search)",
   "KEPT (Sobol added; budget 2,048)",3,61440,1)
t6("E6-5","Genetic algorithm on historical 4-gene policy space, budget-matched (replicates R1/R3 and ICSEC-v2 B3 under V2 protocol)",
   "H4b (primary)","Optimizer","Best of E6-2/E6-3/E6-4","Expected cost per pair","seed SD;false merges/1k",
   "policy search 10 seeds x 2,048 evals","ESSENTIAL","Yes","E6-4","P24;P39;P40","R1/R3/R5 GA (HIST; ARTIFACT_CONSISTENT)",
   f"{M}:exp_r1_ga_redecision.py#L75-L156 decide_code/clip/run_ga","KEPT (policy space + budget specified)",1,20480,1)
t6("E6-6","Three-way match/review/non-match policy","H4c","Policy structure","Best two-way policy",
   "Expected cost incl. review","review rate;coverage","policy search 10 seeds x 2,048 evals","SUPPORTING","No","E6-3;E6-4",
   "P25;P16;P28","REVIEW band of R0/stage18 (HIST)","—","KEPT (priority changed)",1,20480,1)
t6("E6-8","One-to-one assignment constraint","H4 (exploratory)","Post-processing","Best policy without constraint",
   "Expected cost","false merges/1k","assignment","CONDITIONAL","No","E6-6;D0-2 (1:1 confirmed)","P16",
   "schema: 4/15,297 entities with >1 account per platform","—","KEPT",1,1,0)

# ---------------- T7 ----------------
def t7(i,name,hyp,iv,base,prim,sec,prio,mvp,dep,pap,hist,nval,ntest,code="—"):
    r(exp_id=i,track="T7",pipeline_stage="end-to-end",name=name,hypotheses_or_DQ=hyp,independent_variable=iv,
      fixed_controls="Frozen components; locked test opened once",baseline_for_comparison=base,primary_metric=prim,secondary_metrics=sec,
      training_required="No",training_type="—",gpu_required="No",priority=prio,in_minimum_program=mvp,depends_on=dep,
      motivating_papers=pap,historical_link=hist,reusable_code=code,v2_id_status="KEPT",n_variants=0,n_training_jobs=0,
      n_tuning_fits=0,n_validation_evals=nval,n_test_evals=ntest,status="PROPOSED")
t7("E7-1","End-to-end evaluation of REF and BEST-VAL on locked test","H1-H5","Configuration","REF configuration",
   "End-to-end Recall@P_target and expected cost","F1;PR-AUC(all positives)","ESSENTIAL","Yes","T1-T6;G5","P07;P18",
   "R0-R6 end-to-end harness (HIST)",2,2,f"{M}:exp_lib.py#L107-L140 split_constants/evaluate")
t7("E7-2","2x2x2 factorial stage attribution (Blocker x Matcher x Policy)","H2;H4;H5","Blocker x Matcher x Policy",
   "Cell (B0; rule; fixed)","Main effects on end-to-end expected cost","interaction terms","ESSENTIAL","Yes","E7-1","P07;P22",
   "R0-R3 nominal 2x2 (confounded; HIST)",8,6)
t7("E7-3","Robustness strata and perturbations","H3a;DQ4","Stratum / perturbation","Unperturbed","Per-stratum PR-AUC and cost",
   "CI width","SUPPORTING","No","E7-1","P08","—",0,0)
t7("E7-4","Class-prior sensitivity","All","Prior","Natural prior","Precision and cost at priors","PR curves","SUPPORTING","No",
   "E7-1","P07;P23;P18","—",0,0)
t7("E7-5","Compute and inference cost","DQ6","Stage","—","ms per 1k pairs per stage","RAM/VRAM;train time;index time",
   "SUPPORTING","No","T1-T6","P14","R6 CPU 6.3 s/step (HIST)",0,0)
t7("E7-6","Label-uncertainty sensitivity","DQ5","Label assumption","Unlabeled-as-negative","Precision range across assumptions",
   "cost range","SUPPORTING","No","D0-3;E7-1","P27","—",0,0)
t7("E7-7","Error analysis taxonomy","DQ4","—","—","FN/FP counts by taxonomy class","—","SUPPORTING","No","E7-1","P08;P07",
   "fn_top/fp_top (HIST; PRIVACY)",1,0)

# ---------------- T8-T10 ----------------
r(exp_id="E8-1",track="T8",pipeline_stage="S2 feature representation",name="Keyed Bloom-encoded similarity vs plaintext",
  hypotheses_or_DQ="T8 extension",independent_variable="Encoding (L)",fixed_controls="Frozen learner and policy",
  baseline_for_comparison="E5-1 plaintext",primary_metric="Delta PR-AUC",secondary_metrics="—",training_required="Yes",
  training_type="retrain classifier on encoded features",gpu_required="No",priority="OPTIONAL",in_minimum_program="No",
  depends_on="G1;GX-T8 threat model",motivating_papers="P29;P32",historical_link="R4 (HIST; fixed public salt)",
  reusable_code=f"{M}:exp_r4_bloom_privacy.py#L75-L133 (REIMPLEMENT with keyed HMAC)",v2_id_status="KEPT",n_variants=4,
  n_training_jobs=100,n_tuning_fits=0,n_validation_evals=4,n_test_evals=0,status="PROPOSED/BLOCKED")
r(exp_id="E8-2",track="T8",pipeline_stage="S4 decision policy",name="Bloom-encoded + best T6 policy",hypotheses_or_DQ="T8 extension",
  independent_variable="Policy",fixed_controls="As E8-1",baseline_for_comparison="E8-1",primary_metric="Expected cost",secondary_metrics="—",
  training_required="No",training_type="policy search",gpu_required="No",priority="OPTIONAL",in_minimum_program="No",depends_on="E8-1",
  motivating_papers="P29",historical_link="R5 (HIST)",reusable_code="—",v2_id_status="KEPT",n_variants=4,n_training_jobs=0,n_tuning_fits=0,
  n_validation_evals=4,n_test_evals=0,status="PROPOSED/BLOCKED")
r(exp_id="E8-3",track="T8",pipeline_stage="S2 feature representation",name="Privacy attack evaluation on encodings",
  hypotheses_or_DQ="T8 extension (mandatory if T8)",independent_variable="Attack type",fixed_controls="Threat model frozen",
  baseline_for_comparison="—",primary_metric="Re-identification rate",secondary_metrics="—",training_required="No",training_type="—",
  gpu_required="No",priority="OPTIONAL",in_minimum_program="No",depends_on="E8-1;ethics approval",motivating_papers="P30;P31;P35",
  historical_link="none (R4/R5 had no attack)",reusable_code="—",v2_id_status="KEPT",n_variants=2,n_training_jobs=0,n_tuning_fits=0,
  n_validation_evals=0,n_test_evals=0,status="PROPOSED/BLOCKED")
r(exp_id="E9-1",track="T9",pipeline_stage="S2 feature representation",name="Profile image similarity feature",hypotheses_or_DQ="T9 extension",
  independent_variable="Feature set",fixed_controls="As E5-3",baseline_for_comparison="E5-3",primary_metric="Delta PR-AUC",secondary_metrics="coverage",
  training_required="Yes",training_type="supervised (+ frozen image encoder)",gpu_required="Optional",priority="CONDITIONAL",
  in_minimum_program="No",depends_on="G1;GX-T9 image rights;coverage>=50%",motivating_papers="P07",
  historical_link="F04 image features (Twitter-only coverage; HIST)",reusable_code="BACKUP:src/identity_resolution/imaging/*",
  v2_id_status="KEPT",n_variants=1,n_training_jobs=25,n_tuning_fits=0,n_validation_evals=1,n_test_evals=0,status="PROPOSED/BLOCKED")
r(exp_id="E10-1",track="T10",pipeline_stage="S5 entity-level resolution",name="Entity-level clustering from pairwise decisions",
  hypotheses_or_DQ="T10 extension",independent_variable="Clustering method",fixed_controls="Frozen pairwise model",
  baseline_for_comparison="Connected components",primary_metric="B-cubed F1",secondary_metrics="transitivity violations",
  training_required="No",training_type="—",gpu_required="No",priority="CONDITIONAL",in_minimum_program="No",
  depends_on="D0-2 (1:n present >5%)",motivating_papers="P16;P28",historical_link="F07 CRM union-find merge (HIST)",
  reusable_code=f"{M}:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L250-L272 (union-find)",
  v2_id_status="KEPT",n_variants=2,n_training_jobs=0,n_tuning_fits=0,n_validation_evals=2,n_test_evals=0,status="PROPOSED/BLOCKED")

HEADER = ("# Changes vs v1: E2-2 RETIRED->E6-1; E5-1 ALIAS->E3-2/E3-1; E5-2 ALIAS->E4-2; D0-5 NEW; priority labels ESSENTIAL/SUPPORTING/CONDITIONAL/OPTIONAL/EXCLUDE; "
          "policy budget 2,048 + scrambled Sobol in E6-4; new columns pipeline_stage, priority, reusable_code, v2_id_status, n_* counts; "
          "evidence and rationale in review/ID_CHANGELOG.md. Parse with csv after skipping lines starting with '#'.\n")
with OUT.open("w", newline="", encoding="utf-8") as fh:
    fh.write(HEADER)
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
print(f"wrote {len(rows)} rows -> {OUT}")
