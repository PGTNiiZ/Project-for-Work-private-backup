# Final Double-Anonymous Audit

## Manuscript audit

| Check | Finding | Status |
|---|---|---|
| Author names | No manuscript author line or author biography | Pass |
| Affiliations | No university, laboratory, employer, or geographic affiliation for authors | Pass |
| Repository URL/usernames | No personal repository URL, username, or local source path in manuscript body | Pass |
| Internal URLs | No internal project URLs in manuscript | Pass |
| Acknowledgements | No acknowledgements section | Pass |
| Data source | LinkSocial source is a third-party public corpus citation, not an author-identifying source | Pass |
| File paths | No local paths or machine identifiers in manuscript | Pass |
| Raw profiles | No names, usernames, biographies, URLs, images, or identifiable examples | Pass |
| Historical artifacts | No author-identifying historical run paths or timestamps cited | Pass |

## Remaining anonymity precautions

- Do not upload `experiments/icsec_final/primary_reproduction/summary.json` or raw decision artifacts as anonymous supplementary material because artifacts include local paths.
- If supplementary material is provided, construct a sanitized archive containing only code, relative paths, hashes, configurations, aggregate tables, and non-identifying error categories.
- Preserve third-party dataset citation because omitting it would impair scholarly attribution; it does not identify the submitting authors.

Verdict: manuscript text is double-anonymous. A separate sanitation step is required before any artifact upload.

## LaTeX/PDF packaging audit

- `paper/ieee/main.tex` contains no author name, affiliation, acknowledgement, personal URL, institutional URL, absolute filesystem path, or raw-profile content.
- `paper/ieee/references.bib` contains author names only within third-party scholarly references, which are required citations and do not identify the submitting authors.
- The compiled PDF has title metadata, subject `Double-anonymous ICSEC 2026 submission`, and PDF author `Anonymous`; it contains no local path, workspace name, or user identifier.
- The manuscript’s only diagram is embedded TikZ source and has no external file path or metadata.
- Final verdict: double-anonymous review package passes, subject to excluding unsanitized supplementary artifacts.
