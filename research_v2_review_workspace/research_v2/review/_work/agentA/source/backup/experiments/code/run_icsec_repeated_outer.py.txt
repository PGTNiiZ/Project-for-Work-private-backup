"""Repeated outer entity-disjoint GB-17/GB-18/GB-18-GA evaluation."""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
import numpy as np
import pandas as pd
from experiments.code import exp_r1_ga_redecision as ga
from experiments.code import run_gb_transformer_experiments as base
from experiments.code.exp_lib import BLOCKING_MISSED, PROFILES, build_nested_entity_split, entity_keys_by_profile

OUTER_TEST_PCT=30

def outer_role(key: str, seed: int) -> str:
    h=int(hashlib.md5(f"icsec-outer-v1:{seed}:{key}".encode()).hexdigest(),16)%100
    return "test" if h<OUTER_TEST_PCT else "val"

def constants(assigned:pd.DataFrame, seed:int)->dict[str,dict[str,int]]:
    keys=entity_keys_by_profile()
    bm=pd.read_csv(BLOCKING_MISSED,keep_default_na=False)
    bm["role"]=bm.user_folder_a.astype(str).map(lambda x: outer_role(x,seed))
    out={}
    for role in ("model_train","model_calibration","ga_validation","test"):
        exact=assigned[(assigned.decision_source=="AUTO_EXACT")&(assigned.experiment_split==role)]
        scored=assigned[(assigned.decision_source!="AUTO_EXACT")&(assigned.experiment_split==role)]
        # Blocking misses are only in the outer test; development constants do not affect GA ordering.
        missed=int((bm.role=="test").sum()) if role=="test" else 0
        out[role]={"tp_exact":int((exact.actual==1).sum()),"fp_exact":int((exact.actual==0).sum()),"fn_blocking":missed,"total_pos":int((scored.actual==1).sum())+int((exact.actual==1).sum())+missed,"n_scored":int(len(scored))}
    return out

def run_one(root:Path, outer_seed:int)->list[dict]:
    d=root/f"outer_{outer_seed}"
    d.mkdir(parents=True,exist_ok=False); (d/"model").mkdir()
    base.set_seed(42)
    cache=pd.read_parquet("experiments/scored_pairs_enriched.parquet")
    keys=entity_keys_by_profile()
    a=cache.profile_id_a.map(keys); b=cache.profile_id_b.map(keys)
    cache=cache.copy(); cache["split"]=np.where(a.map(lambda x:outer_role(str(x),outer_seed))==b.map(lambda x:outer_role(str(x),outer_seed)),a.map(lambda x:outer_role(str(x),outer_seed)),"drop")
    assigned,manifest=build_nested_entity_split(cache,seed=outer_seed)
    feat17=pd.read_parquet("experiments/pair_features17.parquet"); bert=pd.read_parquet("experiments/pair_bert_cos.parquet")
    work=base.validate_inputs(cache,feat17,bert,assigned)
    const=constants(assigned,outer_seed)
    p17,m17=base.train_gb_variant("GB-17",base.FEATURE17_COLS.copy(),work,assigned,d,42)
    p18,m18=base.train_gb_variant("GB-18",base.FEATURE17_COLS+["bert_cos"],work,assigned,d,42)
    p18f=pd.read_parquet(d/"gb18_probabilities.parquet")
    trials,generations,selection=base.run_ga_trials(work,assigned,p18f,const,[7,42,123,999,2025],d)
    test=work[work.experiment_split=="test"].copy(); mask=work.experiment_split.to_numpy()=="test"
    y=base.labels_for(assigned,test[base.KEY_COLS],"test",allow_test=True)
    genome=np.array([selection["selected_genome"][k] for k in ("t_m","t_r","c_promote","c_demote")])
    decs={"GB-17":base.manual_decision(p17[mask]),"GB-18":base.manual_decision(p18f.loc[mask,"probability_gb18"].to_numpy()),"GB-18-GA":ga.decide_code(p18f.loc[mask,"probability_gb18"].to_numpy(),test.name_sim.to_numpy(),genome)}
    rows=[]
    for method,dec in decs.items():
        metric=base.metric_with_cost(dec,y,const["test"],base.GA_WEIGHTS)
        rows.append({"outer_seed":outer_seed,"method":method,**metric,"candidate_recall":1-const["test"]["fn_blocking"]/max(const["test"]["total_pos"],1),"blocking_missed":const["test"]["fn_blocking"]})
    pd.DataFrame(rows).to_csv(d/"test_results.csv",index=False)
    pd.DataFrame(trials).to_csv(d/"ga_trials.csv",index=False);pd.DataFrame(generations).to_csv(d/"ga_generations.csv",index=False)
    manifest.update({"outer_seed":outer_seed,"outer_assignment":"MD5(icsec-outer-v1:seed:entity_key) < 30 => test","entity_overlap_check":manifest["entity_overlap_check"],"test_labels_accessed_before_final_evaluation":False,"selected_ga_test_evaluations":1,"constants":const})
    (d/"split_manifest.json").write_text(json.dumps(manifest,indent=2));(d/"selected_policy.json").write_text(json.dumps(selection,indent=2))
    return rows

def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path("experiments/icsec_final/repeated_outer"));p.add_argument("--seeds",nargs="+",type=int,default=[101,202,303]);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for seed in a.seeds: rows.extend(run_one(a.output,seed))
 all=pd.DataFrame(rows);all.to_csv(a.output/"all_results.csv",index=False)
 summary=all.groupby("method")[["precision","recall","F1","FP","FN","REVIEW","cost","candidate_recall","blocking_missed"]].agg(["mean","std"]).reset_index();summary.to_csv(a.output/"summary.csv",index=False)
 (a.output/"protocol.json").write_text(json.dumps({"outer_seeds":a.seeds,"outer_test_pct":OUTER_TEST_PCT,"note":"Each outer test is selected before fitting/calibration/GA selection; metrics include outer-specific exact/blocking constants."},indent=2))
if __name__=="__main__":main()
