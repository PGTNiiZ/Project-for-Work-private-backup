# Figure captions — EXPLORATORY (LinkSocial, retrospectively exposed)

ทุกภาพมี source vector PDF/SVG และ PNG preview; ไม่มี profile values.

1. pr_curves: locked within-fold natural candidate population, n=87702, positives=5410; precision denominatorคือ automatic predicted positivesตามscore cutoff และ recall denominatorคือ candidate positives ไม่รวม blocking misses. แสดง raw fixed seed-ensemble probabilities ไม่ใช่ mean-of-seed AP.
2. pc_candidate_curve: development folds4folds; xเป็นผลรวมunique candidate pairsภายในfold ไม่รวมcross-fold pairs. PC denominatorเป็นผลรวมcanonical cross-platform positivesภายในfold. Curvesใช้frozen k grid; primary matched-budget pointอยู่ในTHESIS_TABLES_TH.md ไม่อนุมานจากinterpolation.
3. cost_sensitivity: full cross-platform universeของlocked fold; positivesทั้งหมด=5852. Policiesยังfreezeที่primary scenario ไม่retuneในแต่ละcost scenario; ratiosทั้ง4เป็นASSUMPTION และ REVIEW utilityสมมติperfectreview ไม่ใช่financial ROI.
4. calibration_reliability: locked candidate population n=87702,15 equal-mass bins; จุดแสดง mean probabilityและobserved positive fractionต่อbin. เส้นเชื่อมเป็นvisual interpolation ไม่ใช่หลักฐานว่ามีข้อมูลทุกprobability interval.

Sources: metrics/final_summary.json, metrics/secondary_analyses.json, metrics/blocking_development.json. Primary evidenceและuncertainty: reports/RESULTS_SUMMARY_TH.md. การดูภาพไม่เปลี่ยนfrozen configurations.
