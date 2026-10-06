# Project-for-Work

Machine-learning system for matching social profiles across platforms and
resolving them into CRM customer entities.

## Start here

- ภาพรวมการทำงานและการทดลองภาษาไทย: [`docs/GETTING_STARTED_TH.md`](docs/GETTING_STARTED_TH.md)
- Canonical code และ dependency architecture: [`docs/ARCHITECTURE_TH.md`](docs/ARCHITECTURE_TH.md)
- Project layout and file-placement rules: [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md)
- Experiment plans: [`docs/plans/`](docs/plans/)
- Research findings: [`docs/reports/`](docs/reports/)
- R-series experiment code: [`experiments/code/`](experiments/code/)
- Reproducible Stage 5 evaluation: [`notebooks/05_evaluate.ipynb`](notebooks/05_evaluate.ipynb)
- Generated metrics and decision analysis: [`artifacts/`](artifacts/)
- Cleanup details: [`docs/CLEANUP_REPORT_TH.md`](docs/CLEANUP_REPORT_TH.md)

## Top-level layout

| Folder | Purpose |
|---|---|
| `src/identity_resolution/` | Canonical production code: core rules and application workflows |
| `data/`, `data_for_project/` | Source, normalized, and shared project datasets |
| `train_data/`, `image_process/` | Data/model artifacts retained at stable paths; not canonical source |
| `experiments/` | R-series code, preserved walkthrough notebooks, cached features, and experiment runs |
| `artifacts/` | Generated reports and analysis tables, separated from source code |
| `docs/` | Plans, reports, prompts, and structure guidance |
| `presentation/`, `pub_multi/` | Presentation and publication deliverables |
| `notebooks/` | Canonical notebooks aligned with the ML lifecycle |
| `tests/` | Automated checks |

## Common commands

Run these from the repository root:

```bash
python3.11 -m pip install -e .
python3.11 -m pytest
identity-ml --help
identity-ml predict --help
identity-ml resolve --help
python3.11 -m experiments.code.run_ga_experiments --experiment r1 --seeds 7 42 123 999 2025
```

## Placement rules

- Keep the root limited to repository metadata, dependency files, and this README.
- Put all canonical production logic in `src/identity_resolution/`.
- Put reusable R-series implementation code in `experiments/code/`.
- Put generated JSON/CSV reports in `artifacts/<topic>/`, not beside source code.
- Put plans, findings, and reusable prompts in their matching `docs/` category.
- Put old copies and backups in `archive/`; do not create case-variant folders such
  as both `Train-Data/` and `train_data/`.
