# Human Editing Guide: ICSEC 2026 Editable Manuscript

This directory is an authoring workspace. The frozen submission files remain in `paper/ieee/` and are not overwritten by the editable files.

The DOCX is a clean authoring copy, not an authoritative IEEE-formatted submission file. No official IEEE conference Word template was found locally, so no template was imitated or fabricated.

## A. SAFE TO EDIT FREELY

You may freely revise:

- Title wording (while retaining technical scope and not adding unsupported claims).
- Grammar, clarity, transitions, and section introductions.
- Motivation and background explanation.
- Agentic CRM application context. Keep it framed as context; do not claim CRM deployment or business impact.
- Discussion prose and conclusion wording, provided the reported evidence and limitations remain unchanged.
- Figure placeholder wording and non-technical caption phrasing.

Marked locations:

- Markdown: `[SAFE TO REWORD]` or `<!-- SAFE TO REWORD ... -->`
- LaTeX: `% SAFE TO REWORD ...`

## B. EDIT CAREFULLY

Revise only while preserving the evidence boundary:

- Research gap and novelty framing: do not claim GA, three-way linkage, MiniLM, calibrated probabilities, or generic entity resolution as new.
- Contribution statements: retain the study's empirical and protocol-oriented positioning.
- Interpretation of results: state that the GA changes FP/FN/REVIEW trade-offs; it is not uniformly better in every error dimension.
- MiniLM discussion: repeated outer-split fixed-threshold evidence is mixed.
- Limitations and threats to validity: retain the one-corpus scope, illustrative utility, offline REVIEW, candidate-generation ceiling, and source-provenance limitations.
- Citations: verify metadata and claims before changing or adding references.

## C. DO NOT CHANGE WITHOUT RE-RUNNING / VERIFYING

Do not alter these without corresponding experimental evidence and updates to the frozen research package:

- F1, precision, recall, FP, FN, REVIEW, utility, confidence intervals, or per-split results.
- Candidate-pair counts, positive-pair counts, blocking misses, space reduction, or retrieval recall.
- Dataset profile/entity counts and platform composition.
- Entity-disjoint split role counts, split seeds, or dropped cross-role pair count.
- Model settings, MiniLM representation, calibration method, fixed thresholds, GA genome, GA seeds, population, generations, elites, crossover, mutation, or objective coefficients.
- Research questions, experimentally supported conclusions, and citation metadata.

These locations are marked:

- Markdown: `<!-- VERIFIED ... -->`
- LaTeX: `% VERIFIED ... -->` (LaTeX comments use `%`; the trailing marker is explanatory only.)

## Editing workflow

1. For easiest prose and tables editing, use `manuscript_editable.md`.
2. For the authoritative IEEE layout, edit `main_editable.tex` and its sibling `references.bib`.
3. The editable LaTeX source contains all figures as TikZ code and all tables as normal `tabular` environments.
4. Keep `\bibliography{references}` and edit `paper/editable/references.bib` when changing verified bibliography entries.
5. Do not overwrite `paper/ieee/main.tex` or `paper/ieee/main.pdf` unless you intentionally replace the frozen submission version after review.

## Regenerate an IEEE PDF after LaTeX edits

From the project root:

```sh
cd paper/editable
tectonic --keep-logs --keep-intermediates main_editable.tex
tectonic --keep-logs --keep-intermediates main_editable.tex
```

The second run resolves the bibliography and references. The output is `paper/editable/main_editable.pdf`.

Before treating it as a final submission PDF:

1. Confirm the page count and IEEE two-column layout.
2. Check that no citations are unresolved.
3. Inspect tables and the two-column pipeline figure for clipping.
4. Perform a double-anonymous check of title metadata, author block, acknowledgements, URLs, and file paths.
5. Reconcile every modified claim against experiment output or verified literature.

## Recommended role of each file

| File | Purpose |
|---|---|
| `manuscript_editable.md` | Easiest manual prose and Markdown-table editing. |
| `main_editable.tex` | IEEE-formatted source used to build an editable review PDF. |
| `references.bib` | Editable verified bibliography for the LaTeX authoring copy. |
| `manuscript_editable.docx` | Word-friendly authoring copy with editable text and tables; not IEEE-authoritative. |
