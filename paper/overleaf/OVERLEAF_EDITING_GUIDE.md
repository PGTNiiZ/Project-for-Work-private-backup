# Overleaf Editing Guide

## A. SAFE TO EDIT FREELY

- Title wording.
- Abstract wording while preserving every marked number and scope limitation.
- Motivation, background, transitions, and section openings.
- Agentic CRM explanation, only as application context.
- Discussion prose and conclusion prose, provided their evidence meaning remains unchanged.

Search `main.tex` for `% SAFE TO REWORD` markers.

## B. EDIT CAREFULLY

- Research gap and contribution statements: do not describe GA, three-way linkage, MiniLM, or generic entity resolution as new.
- Agentic CRM framing: do not claim system deployment, agent evaluation, commercial impact, or user outcomes.
- Interpretation of the GA: it changes FP/FN/REVIEW operating trade-offs and is not better in every error dimension.
- MiniLM discussion: fixed-threshold repeated-split evidence is mixed.
- Limitations, provenance wording, and threats to validity.

## C. DO NOT CHANGE WITHOUT NEW EVIDENCE

- Experimental results: F1, precision, recall, FP, FN, REVIEW, utility, confidence intervals, and per-split values.
- Dataset/candidate statistics: profile count, possible and candidate pairs, positive pairs, blocking misses, space reduction, and retrieval recall.
- Split roles/counts, seeds, model parameters, calibration method, fixed thresholds, GA settings, or utility coefficients.
- Verified citations and bibliographic metadata.

Search `main.tex` for `% VERIFIED` markers before editing evidence-sensitive text.

## Upload to Overleaf

1. Compress the contents of `paper/overleaf/` as a ZIP; do not zip the parent directory itself.
2. In Overleaf, select **New Project** → **Upload Project**.
3. Upload the ZIP.
4. Set `main.tex` as the Main document if Overleaf does not detect it automatically.
5. Recompile with the default pdfLaTeX/BibTeX workflow.
6. Verify the PDF remains 4–6 pages including figure, tables, and references.
7. Check unresolved citations, table/figure readability, and double-anonymous metadata before submission.

## Build locally

From this directory:

```sh
tectonic --keep-logs --keep-intermediates main.tex
tectonic --keep-logs --keep-intermediates main.tex
```

The second run resolves citations and bibliography. The output is `main.pdf`.
