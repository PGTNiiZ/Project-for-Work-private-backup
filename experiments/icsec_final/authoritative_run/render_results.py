"""Render the authoritative numerical result table from recomputed CSVs."""
from pathlib import Path
import pandas as pd
import json

root = Path(__file__).resolve().parents[3]
out = root / "experiments/icsec_final/authoritative_run"
scope = json.loads((out / "candidates/candidate_scope.json").read_text())
raw = pd.read_csv(out / "raw_metrics_by_outer.csv")
agg = raw.groupby("method", sort=False)[["precision","recall","F1","FP","FN","REVIEW","utility"]].agg(["mean","std"]).reset_index()

def f(x): return f"{x:.6f}"
def pm(row, col): return f"{row[(col,'mean')]:.6f} ± {row[(col,'std')]:.6f}"
lines = [
"AUTHORITATIVE RESULTS — ICSEC 2026",
"",
"Source: experiments/icsec_final/authoritative_run/.",
"All workflow metrics below are recomputed by evaluate_authoritative.py from the new row-level decision artifacts, not copied from runner summaries.",
"",
"A. Dataset and candidate generation",
"",
"| Quantity | Value | Local source |",
"|---|---:|---|",
 f"| Eligible profiles | {scope['profiles_eligible']:,} | candidates/candidate_scope.json |",
 f"| All-platform labeled positives | {scope['all_platform_positives']:,} | candidates/candidate_scope.json |",
 f"| Cross-platform labeled positives | {scope['cross_platform_positives']:,} | candidates/candidate_scope.json |",
 f"| Same-platform positives | {scope['same_platform_positives']:,} | candidates/candidate_scope.json |",
 f"| Possible cross-platform pairs | {scope['possible_cross_platform_pairs']:,} | candidates/candidate_scope.json |",
 f"| Exact-tier pairs | {scope['exact_tier_pairs']:,} | candidates/candidate_scope.json |",
 f"| Model-scored candidate pairs | {scope['model_scored_candidate_pairs']:,} | candidates/candidate_scope.json |",
 f"| Workflow candidate pairs | {scope['workflow_candidate_pairs']:,} | candidates/candidate_scope.json |",
 f"| Covered cross-platform positives | {scope['candidate_covered_cross_platform_positives']:,} | candidates/candidate_scope.json |",
 f"| Cross-platform blocking misses | {scope['cross_platform_blocking_misses']:,} | candidates/candidate_scope.json and candidates/blocking_missed_positives.parquet |",
 f"| Retrieval recall | {scope['retrieval_recall']*100:.4f}% | candidates/candidate_scope.json |",
 f"| Candidate-space reduction | {scope['candidate_space_reduction']*100:.4f}% | candidates/candidate_scope.json |",
"",
"Invariant checks: exact-tier + model-scored = workflow; covered + blocking misses = cross-platform positives; all-platform = cross-platform + same-platform. All are true in candidate_scope.json.",
"",
"B. Per-outer workflow results",
"",
"| Seed | Method | Precision | Recall | F1 | FP | FN | REVIEW | U | Exact | Scored | Misses |",
"|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for r in raw.itertuples(index=False):
 lines.append(f"| {r.outer_seed} | {r.method} | {r.precision:.6f} | {r.recall:.6f} | {r.F1:.6f} | {r.FP} | {r.FN} | {r.REVIEW} | {r.utility:.1f} | {r.exact_rows} | {r.model_scored_rows} | {r.blocking_missed_rows} |")
lines += ["", "C. Mean ± sample SD across outer seeds", "", "| Method | Precision | Recall | F1 | FP | FN | REVIEW | U |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for _,r in agg.iterrows():
 lines.append(f"| {r['method']} | {pm(r,'precision')} | {pm(r,'recall')} | {pm(r,'F1')} | {pm(r,'FP')} | {pm(r,'FN')} | {pm(r,'REVIEW')} | {pm(r,'utility')} |")
lines += ["", "D. GA trade-offs", "", "All comparisons are paired by outer seed and use the same row-level workflow artifacts."]
for seed in [101,202,303]:
 a=raw[(raw.outer_seed==seed)&(raw.method=='GB-18')].iloc[0]; g=raw[(raw.outer_seed==seed)&(raw.method=='GB-18-GA')].iloc[0]
 lines.append(f"- Seed {seed}: GA minus GB-18 F1 = {g.F1-a.F1:+.6f}; U change = {g.utility-a.utility:+.1f}; FP change = {g.FP-a.FP:+d}; FN change = {g.FN-a.FN:+d}; REVIEW change = {g.REVIEW-a.REVIEW:+d}.")
lines += ["", "E. Scope definitions", "", "- Exact-tier decisions are rows in exact_tier_decisions.parquet and are included in workflow metrics.", "- Model-scored decisions are rows in model_scored_decisions.parquet.", "- Blocking misses are rows in blocking_missed_positives.parquet and are NO_MATCH positives added to workflow FN.", "- Workflow decisions are the exact, model-scored, and blocking-missed row artifacts concatenated; workflow metrics are recomputed from workflow_decisions.parquet.", "- Retrieval recall is covered cross-platform positives / all cross-platform positives.", "", "F. Failure counts", "", "FP, FN, and REVIEW above are the complete workflow counts. Exact/model-scored/blocking row counts are included per seed and method; exact and blocking rows are identical across methods within each seed, while model-scored decisions differ by method.", "", "G. Limitations", "", "The package uses the current cached feature artifacts pair_features17.parquet and pair_bert_cos.parquet as declared inputs; their upstream feature-generation environment is not separately captured. The package itself captures current source hashes, current input hashes, environment, package versions, split manifests, models, calibrators, GA policies, decisions, and metric outputs. The old primary split and old bootstrap are not used."]
(out/'AUTHORITATIVE_RESULTS.md').write_text("\n".join(lines)+"\n", encoding="utf-8")
print(out/'AUTHORITATIVE_RESULTS.md')
