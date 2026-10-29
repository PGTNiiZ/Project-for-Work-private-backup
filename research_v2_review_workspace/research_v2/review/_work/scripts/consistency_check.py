"""Definition-of-Done consistency checks for the Research V2 review workspace (read-only on inputs)."""
import csv, hashlib, json, re, sys
from pathlib import Path

W = Path(sys.argv[1])  # research_v2_review_workspace
RV = W / "research_v2"
out = []
def p(*a): out.append(" ".join(str(x) for x in a))
fails = []
def check(cond, msg):
    p(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

def read_csv(path):
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines))

# 1. required review files
req = ["REPOSITORY_RESEARCH_INVENTORY.md","HISTORICAL_EXPERIMENT_AUDIT.md","REPOSITORY_COMPARISON.md","LITERATURE_VS_IMPLEMENTATION.md",
       "LITERATURE_VERIFICATION_REPORT.md","RESEARCH_GAP_VALIDATION.md","HYPOTHESIS_COVERAGE_REVIEW.md","EXPERIMENT_REDUNDANCY_REVIEW.md",
       "TRAINING_DECISION_REPORT.md","METHODOLOGICAL_RISKS.md","BLOCKER_REGISTER.csv","ID_CHANGELOG.md","FINAL_HANDOFF_TH.md"]
for f in req:
    fp = RV / "review" / f
    check(fp.exists() and fp.stat().st_size > 200, f"review/{f} exists and non-empty")

# 2. working copies begin with Changes vs v1
wc = ["literature/PAPER_EVIDENCE_MATRIX.csv","literature/REFERENCES.bib","design/EXPERIMENTAL_MASTER_PLAN_TH.md",
      "design/HYPOTHESIS_EXPERIMENT_MATRIX.csv","design/RESEARCH_QUESTIONS_AND_HYPOTHESES.md","design/TRAINING_REQUIREMENTS.md",
      "design/EXPERIMENT_DEPENDENCY_GRAPH.md","history/HISTORICAL_EXPERIMENT_MAPPING.md","history/REUSABLE_COMPONENTS.md"]
opt = ["literature/LITERATURE_REVIEW_TH.md","literature/RESEARCH_GAPS_TH.md","design/RESEARCH_GATES.md",
       "design/EVALUATION_AND_STATISTICS.md","design/COMPUTE_AND_COST_PLAN.md"]
for f in wc + opt:
    fp = RV / f
    if not fp.exists():
        check(f in opt, f"{f} exists (optional={f in opt})"); continue
    head = "\n".join(fp.read_text(encoding="utf-8").splitlines()[:6])
    check("Changes vs v1" in head, f"{f} begins with 'Changes vs v1'")

# 3. _input_v1 immutable
man = json.loads((RV / "review/_work/input_manifest.json").read_text())
for name, sha in man.items():
    cur = hashlib.sha256((W / "_input_v1" / name).read_bytes()).hexdigest()
    check(cur == sha, f"_input_v1/{name} unchanged")

# 4. CSVs parse; ID consistency
mat = read_csv(RV / "design/HYPOTHESIS_EXPERIMENT_MATRIX.csv")
ids = [r["exp_id"] for r in mat]
check(len(ids) == len(set(ids)), f"matrix IDs unique ({len(ids)} rows)")
for f in ["literature/PAPER_EVIDENCE_MATRIX.csv", "review/BLOCKER_REGISTER.csv"]:
    try:
        rows = read_csv(RV / f); check(len(rows) > 0, f"{f} parses ({len(rows)} rows)")
    except Exception as e:
        check(False, f"{f} parses: {e}")
idre = re.compile(r"\b(D0-\d|E\d{1,2}-\d)\b")
for f in ["design/EXPERIMENTAL_MASTER_PLAN_TH.md", "design/EXPERIMENT_DEPENDENCY_GRAPH.md", "design/TRAINING_REQUIREMENTS.md"]:
    found = set(idre.findall((RV / f).read_text(encoding="utf-8")))
    live = {r["exp_id"] for r in mat if r["status"] not in ("EXCLUDED",)}
    missing = sorted(live - found); extra = sorted(found - set(ids))
    check(not missing, f"{f}: every matrix ID mentioned (missing={missing})")
    check(not extra, f"{f}: no unknown IDs (extra={extra})")

# 5. every hypothesis has an ESSENTIAL experiment with baseline + metric
for h in ["H1","H2","H3","H4","H5"]:
    ok = [r["exp_id"] for r in mat if r["priority"] == "ESSENTIAL" and h in r["hypotheses_or_DQ"]
          and r["baseline_for_comparison"] not in ("", "—") and r["primary_metric"] not in ("", "—")]
    check(bool(ok), f"{h} has ESSENTIAL experiment with baseline+metric: {ok}")

# 6. every paper linked or excluded
pm = read_csv(RV / "literature/PAPER_EVIDENCE_MATRIX.csv")
for r in pm:
    linked = (r.get("experiments_motivated","").strip() not in ("", "—", "NONE")) or r.get("verification_status","") == "EXCLUDED"
    check(linked, f"{r['paper_id']} linked to experiment/gap or excluded")
mot = set()
for r in mat: mot |= set(re.findall(r"P\d\d", r["motivating_papers"]))
known = {r["paper_id"] for r in pm}
check(mot <= known, f"matrix motivating_papers all exist in paper matrix (unknown={sorted(mot-known)})")

# counts
num = ["n_variants","n_training_jobs","n_tuning_fits","n_validation_evals","n_test_evals"]
def tot(sel):
    sub = [r for r in mat if sel(r)]
    d = {k: sum(int(r[k]) for r in sub) for k in num}
    d["policy_objective_evals"] = sum(int(r["n_validation_evals"]) for r in sub if r["pipeline_stage"].startswith("S4"))
    d["model_rule_validation_evals"] = d["n_validation_evals"] - d["policy_objective_evals"]
    d["distinct"] = sum(1 for r in sub if r["status"] not in ("ALIAS","EXCLUDED"))
    d["diagnostics"] = sum(1 for r in sub if r["track"] == "D0" and r["status"] not in ("ALIAS","EXCLUDED"))
    return d
for name, sel in [("MVP", lambda r: r["priority"] == "ESSENTIAL"),
                  ("MVP+SUPPORTING", lambda r: r["priority"] in ("ESSENTIAL","SUPPORTING")),
                  ("ALL", lambda r: r["priority"] != "EXCLUDE")]:
    p("COUNTS", name, json.dumps(tot(sel), ensure_ascii=False))
p("GPU training jobs", sum(int(r["n_training_jobs"]) for r in mat if r["gpu_required"].startswith("Yes")))

# 7. privacy regex scan of outputs (excluding _work raw/_deps/source dumps and repos)
pat = {"url": re.compile(r"https?://[^\s)\]>|]+"), "handle": re.compile(r"(?<![\w.])@[A-Za-z0-9_]{3,}"),
       "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")}
hits = {}
for fp in RV.rglob("*"):
    if not fp.is_file() or "_work" in fp.parts: continue
    if fp.suffix not in (".md", ".csv", ".bib", ".json", ".txt"): continue
    t = fp.read_text(encoding="utf-8", errors="ignore")
    for k, rgx in pat.items():
        for m in rgx.findall(t):
            hits.setdefault((k, m), set()).add(str(fp.relative_to(RV)))
p(f"PRIVACY SCAN: {len(hits)} distinct hits (review each)")
for (k, m), fs in sorted(hits.items()):
    p("  HIT", k, m, "->", ",".join(sorted(fs))[:160])

# 8. NO-GO preserved
for f in ["review/FINAL_HANDOFF_TH.md", "design/RESEARCH_GATES.md", "design/EXPERIMENTAL_MASTER_PLAN_TH.md"]:
    t = (RV / f).read_text(encoding="utf-8")
    check("NO-GO" in t, f"{f} preserves NO-GO")

# 9. numbers without ASSUMPTION in compute plan
cp = (RV / "design/COMPUTE_AND_COST_PLAN.md").read_text(encoding="utf-8").splitlines()
bad = [l for l in cp if re.search(r"(CPU-ชม|GPU-ชม|นาที|ชั่วโมง)", l) and "ASSUMPTION" not in l and "|" in l and not l.startswith("| รหัส")]
p(f"COMPUTE lines with time estimates lacking inline ASSUMPTION tag: {len(bad)} (doc-level banner applies)")

# 10. K1-K6 status in handoff
ho = (RV / "review/FINAL_HANDOFF_TH.md").read_text(encoding="utf-8")
for k in ["K1","K2","K3","K4","K5","K6"]:
    check(re.search(rf"{k}\b.*(RESOLVED|PARTIALLY|BLOCKED)", ho) is not None, f"{k} status present in handoff")
# K3: no '500 config' left in design docs
for fp in (RV / "design").glob("*.md"):
    t = fp.read_text(encoding="utf-8")
    check(not re.search(r"\b500\s*(configs|configurations|config)\b", t), f"{fp.name}: no '500 configs'")

p(f"SUMMARY: {len(fails)} FAIL")
(RV / "review/_work/consistency_check.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[-40:]))
