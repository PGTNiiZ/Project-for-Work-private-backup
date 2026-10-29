"""Close actual outputs without retraining or reopening sealed test resources."""
from pathlib import Path
import csv
import datetime as dt
import json
import shutil
import subprocess
import sys
import numpy as np
from integrity import sha256
from runtime import ROOT as R,TREE,commit_files
from verify_run import verify,scan_public_outputs,raw_git_baseline
from write_reports import write_all,table


def main():
    initial=R/'manifests/verification.json'
    if initial.exists() and not (R/'manifests/verification_initial.json').exists():
        shutil.copy2(initial,R/'manifests/verification_initial.json')
        shutil.copy2(R/'reports/consistency_check.txt',R/'reports/consistency_check_initial.txt')
    tests=subprocess.run([sys.executable,'-m','pytest',str(R/'tests'),str(R/'work/representation/test_rep.py'),str(R/'work/statistics/test_analysis_tools.py'),'-q'],text=True,capture_output=True)
    (R/'reports/synthetic_test_output.txt').write_text(tests.stdout+tests.stderr)
    if tests.returncode:raise RuntimeError('synthetic regression suite failed; inspect retained output')
    commit_files([*R.glob('*.py'),*R.joinpath('tests').glob('*.py'),R/'DEVIATIONS.md',R/'ENVIRONMENT.md'],'Record closing verification implementation and disclosed execution deviations')
    write_all()
    secondary=json.loads((R/'metrics/secondary_analyses.json').read_text())
    extra='\n## Univariate development diagnostics — EXPLORATORY\n\nใช้ candidate population ของสี่ development folds; เป็น feature diagnostics ไม่ใช่ supervised test model comparison.\n\n'
    for source in ['metrics/E2-1--univariate-OOF-lexical.json','metrics/E4-1--univariate-semantic.json']:
        data=json.loads((R/source).read_text())
        extra+=table(['Feature','Candidate AP','n pairs'],[[r['feature'],f"{r['candidate_AP']:.4f}",data['n_pairs']] for r in data['features']])+'\nSource: '+source+'\n'
    extra+='\n## Robustness strata — EXPLORATORY, descriptive\n\nStrata อาจทับซ้อนกัน; denominator คือ candidate rows และ positives ภายในแต่ละ stratum ไม่เปรียบ AP ระหว่าง strata เป็น causal gain.\n\n'+table(['Stratum','n pairs','Positive pairs','Candidate AP'],[[r['stratum']+'='+str(r['value']),r['n_pairs'],r['positive_pairs'],f"{r['candidate_AP']:.4f}"] for r in secondary['strata']])
    extra+='\n## Mechanical error taxonomy — EXPLORATORY\n\nเป็น flags/counts จาก frozen predictions ไม่ใช่ adjudicated semantic causes; ไม่รวม flags ซ้ำเป็น total ใหม่.\n\n'+table(['Operating-point index',*secondary['taxonomy'][0].keys()],[[i+1,*row.values()] for i,row in enumerate(secondary['taxonomy'])])+'\nSource: metrics/secondary_analyses.json\n'
    with (R/'reports/THESIS_TABLES_TH.md').open('a') as f:f.write(extra)
    caveat='\n## ขอบเขต protocol compliance ที่ยังต้อง review\n\nTechnical checks ไม่เท่ากับ full strict-v4 compliance. G4 ตรึง k* selection rule แทน numeric k ล่วงหน้า; primary AP ใช้ frozen ensemble aggregation ส่วน table ใช้ seed mean. Supporting summaries คำนวณ validation-only operating-point diagnostics หลัง final แต่ไม่ได้ใช้เปลี่ยน primary system หรือประเมิน thresholds เหล่านั้นบน test. จึงรับรอง no primary retuning ไม่ใช่ zero diagnostic selection ทั้ง session; validation counter นับ ledger-accounted held-fold/objective events ไม่รวมทุก supplemental threshold/metric call. LR และ semantic-only มี development evidence แต่ไม่มี standalone final-test configuration; ไม่เปิดเพิ่มหลัง unblinding.\n\nBranch ยังมี inherited concurrent commit c68c9d20 ซึ่งเปลี่ยน16pathsนอก runs; owned commitsตรวจแยกและไม่ rewrite งานอื่น. ก่อนเผยแพร่ต้อง review branch scope. File-output PII scan ไม่ลบ metadata incident ใน terminal. รายละเอียด DEVIATIONS.md.\n'
    for name in ['THREATS_TO_VALIDITY_TH.md','EXECUTION_HANDOFF_TH.md']:
        with(R/'reports'/name).open('a') as f:f.write(caveat)
    with(R/'BLOCKER_REGISTER.csv').open('a') as f:
        w=csv.writer(f)
        w.writerow(['CONCURRENT-SCOPE','inherited concurrent commit','UNKNOWN','c68c9d20 contains16 outside paths; owned writes scoped separately','review release diff; do not rewrite unrelated history','researcher'])
        w.writerow(['STRICT-PROTOCOL','literal-v4 compliance','UNKNOWN','numeric-k freeze, AP aggregation and post-final supporting diagnostics disclosed','researcher review deviations before publication; no extra test selection','researcher'])
    arrays=np.load(R/'data_derived/final/matcher-GBDT-lexical.npz')
    candidate_n=len(arrays['y']);positive_n=int(arrays['y'].sum());gt_n=len(arrays['gt_pairs'])
    captions=f'''# Figure captions — EXPLORATORY (LinkSocial, retrospectively exposed)

ทุกภาพมี source vector PDF/SVG และ PNG preview; ไม่มี profile values.

1. pr_curves: locked within-fold natural candidate population, n={candidate_n}, positives={positive_n}; precision denominatorคือ automatic predicted positivesตามscore cutoff และ recall denominatorคือ candidate positives ไม่รวม blocking misses. แสดง raw fixed seed-ensemble probabilities ไม่ใช่ mean-of-seed AP.
2. pc_candidate_curve: development folds4folds; xเป็นผลรวมunique candidate pairsภายในfold ไม่รวมcross-fold pairs. PC denominatorเป็นผลรวมcanonical cross-platform positivesภายในfold. Curvesใช้frozen k grid; primary matched-budget pointอยู่ในTHESIS_TABLES_TH.md ไม่อนุมานจากinterpolation.
3. cost_sensitivity: full cross-platform universeของlocked fold; positivesทั้งหมด={gt_n}. Policiesยังfreezeที่primary scenario ไม่retuneในแต่ละcost scenario; ratiosทั้ง4เป็นASSUMPTION และ REVIEW utilityสมมติperfectreview ไม่ใช่financial ROI.
4. calibration_reliability: locked candidate population n={candidate_n},15 equal-mass bins; จุดแสดง mean probabilityและobserved positive fractionต่อbin. เส้นเชื่อมเป็นvisual interpolation ไม่ใช่หลักฐานว่ามีข้อมูลทุกprobability interval.

Sources: metrics/final_summary.json, metrics/secondary_analyses.json, metrics/blocking_development.json. Primary evidenceและuncertainty: reports/RESULTS_SUMMARY_TH.md. การดูภาพไม่เปลี่ยนfrozen configurations.
'''
    (R/'figures/CAPTIONS_TH.md').write_text(captions)
    first=verify()
    if first['FAIL']:raise RuntimeError('closing consistency checks failed; inspect report')
    with (R/'reports/EXECUTION_HANDOFF_TH.md').open('a') as f:
        f.write('\n## Executed verification output\n\nSynthetic tests:\n\n'+tests.stdout+'\n'+(R/'reports/consistency_check.txt').read_text()+'\nPASS ในรายการนี้มีขอบเขตตามแต่ละcheck; ไม่ใช่ ethics verification, fresh confirmatory evidence หรือการรับรอง strict protocol ทั้งหมด.\n')
    final=verify()
    if final['FAIL']:raise RuntimeError('final consistency check failed')
    excluded={'cache','.venv','__pycache__','.pytest_cache','git_execution'}
    manifest={}
    for path in sorted(R.rglob('*')):
        rel=path.relative_to(R)
        if not path.is_file() or any(p in excluded for p in rel.parts) or path.name=='PROVENANCE_SHA256.json':continue
        if path.is_symlink():continue
        manifest[str(rel)]=sha256(path)
    (R/'PROVENANCE_SHA256.json').write_text(json.dumps({'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'classification':'EXPLORATORY (LinkSocial, retrospectively exposed)','files':manifest,'excludes':'self, environment/cache/bytecode/isolated Git tree; private derived/model files are hashed not committed'},indent=2)+'\n')
    public=[*R.glob('*.py'),*R.glob('*.md'),*R.glob('*.lock'),R/'.gitignore',R/'protocol.json',R/'BLOCKER_REGISTER.csv',R/'PROVENANCE_SHA256.json',*R.joinpath('tests').glob('*.py')]
    for folder in ['reports','figures','manifests','metrics','configs','ledger']:
        public.extend(p for p in (R/folder).rglob('*') if p.is_file())
    commit=commit_files(public,'Close exploratory research results, vector figures and verified provenance manifest')
    mismatches=sum(sha256(R/path)!=digest for path,digest in manifest.items())
    pii=scan_public_outputs(write=False)
    raw=raw_git_baseline(json.loads((R/'protocol.json').read_text()))
    status=subprocess.check_output(['git','status','--porcelain'],cwd=TREE,text=True)
    if mismatches or pii['unclassified_hits'] or raw['mismatches'] or status.strip():raise RuntimeError('read-only postcommit verification failed; no results overwritten')
    print(json.dumps({'final_commit':commit,'manifest_files':len(manifest),'manifest_mismatches':mismatches,'raw_files_checked':raw['files_checked'],'raw_mismatches':raw['mismatches'],'pii_unclassified':pii['unclassified_hits'],'technical_PASS':final['PASS'],'technical_FAIL':final['FAIL'],'isolated_tree_clean':not status.strip(),'classification':'EXPLORATORY; strict protocol deviations disclosed'},indent=2))

if __name__=='__main__':main()
