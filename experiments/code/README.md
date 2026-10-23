# R-series experiment code

Shared code and R0–R6 runners live here; generated experiment outputs remain one
level up in `experiments/`.

Run modules from the repository root, for example:

```bash
python -m experiments.code.run_ga_experiments --experiment r1 --seeds 7 42 123 999 2025
python -m experiments.code.run_gb_transformer_experiments
python -m experiments.code.run_one_stage_weighted_ga_experiment
```

`run_one_stage_weighted_ga_experiment` ทดสอบ policy v2 แบบ 10 genes
`[t_match, t_review, eight policy weights]` บน validation เท่านั้น ค่าเริ่มต้นรัน 10 seeds,
population 128 และ 100 generations พร้อม score-only/legacy-name baselines, bootstrap CI,
coverage และ platform-pair slices โดยไม่เปิด held-out test.
