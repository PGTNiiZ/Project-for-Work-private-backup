# Project Structure

## Repository map

```text
Project-for-Work/
├── README.md                 # entry point and common commands
├── requirements.txt          # shared Python dependencies
├── artifacts/
│   ├── decisioning/          # evaluation JSON and decision-matrix analysis
│   ├── evaluation/           # canonical Stage 5 evaluation outputs
│   └── pair_building/        # pair-construction summaries
├── data/                     # source and processed datasets
├── data_for_project/         # shared project exports
├── docs/
│   ├── plans/                # implementation plans and roadmaps
│   ├── prompts/              # reusable task prompts
│   └── reports/              # findings and human-readable analysis
├── experiments/
│   ├── code/                 # R0–R6 implementations and runners
│   ├── walkthroughs/         # teaching notebooks
│   └── automation/           # recorded experiment runs
├── notebooks/                # canonical lifecycle notebooks
├── src/identity_resolution/  # canonical 7-stage ML architecture
├── presentation/             # slide sources and generated presentation
├── pub_multi/                # publication package
└── tests/                    # automated tests
```

`train_data/` and `image_process/` retain large data/model artifacts at their
historical paths. New Python source belongs only in `src/identity_resolution/`.

## Placement guide

| New item | Location |
|---|---|
| Production stage or workflow | `src/identity_resolution/` |
| R-series implementation or runner | `experiments/code/` |
| Canonical lifecycle notebook | `notebooks/` |
| Reproducible research walkthrough | `experiments/walkthroughs/` |
| Plan or roadmap | `docs/plans/` |
| Research finding or narrative report | `docs/reports/` |
| Reusable prompt | `docs/prompts/` |
| Generated metric/report | `artifacts/<topic>/` |
| Backup or abandoned variant | Git history; do not add another source copy |

## Naming rules

- Use lowercase `snake_case` for new folders and Python files.
- Keep numeric stage prefixes only where they communicate execution order.
- Do not create folders that differ only by letter case.
- Use descriptive output folders instead of `out2`, `final_new`, or `backup_latest`.
- Resolve runtime paths from `Path(__file__)` or the repository root, never from
  an assumed current working directory.

## Root-level rule

The root should contain only repository metadata, dependency/configuration files,
high-level documentation, and major category/domain folders. A new loose script,
notebook, JSON report, or backup at root should be treated as misplaced.
