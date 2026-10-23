# Final Paper V2 validation report

## Authority and build

Numerical authority: `experiments/icsec_final/authoritative_run_v2/final_evidence.json` and `FINAL_RESULTS.md` only. Historical V1 artifacts were excluded.

Source: `paper/overleaf_v2/main.tex`
PDF: `paper/overleaf_v2/main.pdf`
Submission PDF: `paper/final_submission/ICSEC2026_anonymous_submission.pdf`
Compiler: Tectonic 0.17.0 using IEEEtran conference class.

## Format

The final manuscript is 5 pages, within the requested 4--6 page range. It uses `\documentclass[conference]{IEEEtran}` without margin, font, or spacing overrides. Compilation completed with resolved bibliography and no overfull boxes. Remaining warnings are underfull line/page boxes and do not indicate clipping.

Both vector figures were rendered and visually inspected. The system figure communicates profiles through candidate generation, pair features, gradient boosting, calibration, and three-way decisions. The leakage-safe figure shows four roles, zero entity overlap, the sealed boundary, freeze, and final label reveal. Tables and figure labels are readable.

## Numerical and claim audit

All manuscript metrics trace to the frozen V2 aggregate and per-seed artifacts. The manuscript distinguishes exact-tier, model-scored, blocking-miss, and workflow scope; states the 88.6742% retrieval ceiling; reports zero pre-final label reads; and preserves the 12,000/12,000 B2/B3 budget. It reports the semantic-feature negative result and concludes that GA-specific benefit is not supported.

No V1 metric or V1 evidence path appears in the manuscript. Lead scoring, CRM agents, conversion, and business outcomes are explicitly described as unevaluated rather than claimed.

## References

All 15 bibliography entries are cited, and all citation keys resolve. Metadata and relevance were checked against the existing literature audit and publisher/DOI records. The bibliography covers cross-platform linkage, record linkage, blocking, semantic entity matching, calibration, reject/three-way decisions, human-in-the-loop ER, evolutionary optimization, and evaluation. No citation is used to validate experimental numbers.

## Anonymity and PDF checks

The author block is `Anonymous Submission`. PDF metadata is title plus Author=`Anonymous`, Subject=`Anonymous conference submission`, and Creator=`Tectonic`. Extracted PDF text contains no local path, username, company, repository URL, acknowledgement, affiliation, or raw profile information. Bibliographic author names are citations, not identity leakage. All detected PDF fonts are embedded.

## Tests and evidence closure

Full repository test suite: 84 passed in 11.48 seconds.
Authoritative V2 root SHA256 manifest: 161 entries, zero mismatches.
Independent metrics: PASS.
B2/B3 fairness: PASS.
Test-label isolation: PASS.

PAPER V2: PASS
REFERENCES: PASS
ANONYMITY: PASS
IEEE FORMAT: PASS
SUBMISSION STATUS: READY
