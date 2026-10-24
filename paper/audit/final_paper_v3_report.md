# Final Paper V3 validation report

## Scope and authority

- Manuscript: `paper/overleaf_v3/main.tex`
- PDF: `paper/overleaf_v3/main.pdf`
- Numerical authority for final scientific claims: `experiments/icsec_final/authoritative_run_v2/final_evidence.json` and `FINAL_RESULTS.md`
- Historical model-family screen: `train_data/stage7_8_rebuilt_experiment_tuned/best_run.json`; used only as explicitly labeled development motivation because its 22-feature configuration, sampling, and split protocol are not directly comparable with authoritative V2.
- Paper V2 and historical `authoritative_run/` were not edited by this task.

## Research story

The manuscript preserves both requested pillars:

1. empirical multi-feature model development leading to a Gradient Boosting pair scorer; and
2. genetic optimization of a three-way MATCH/REVIEW/NO_MATCH policy under a declared scenario-based remediation-effort objective.

The transition is explicit: calibrated model evidence under fixed thresholds exposes false-merge, missed-merge, and review trade-offs; validation-only policy optimization then chooses an operating point. The manuscript does not claim that GA trains the scorer or that GA outperforms equal-budget Sobol.

## Evidence and claims

The authoritative aggregate table matches V2 values for GB-17+B0, GB-18+B0, GB-18+B1, GB-18+B2, and GB-18+B3. Programmatic recomputation of manuscript differences produced:

- GB-18+B0 minus GB-17+B0 objective: 12.2333 (reported as 12.2 worse);
- B0 minus B1 objective: 499.6333 (reported as 499.6 reduction);
- B0 minus B1 FN: 613.6667;
- B1 minus B0 FP: 27.3333;
- B1 minus B0 REVIEW: 593.6667;
- B1 minus B2 objective: 4.5333;
- B2 minus B3 objective: 1.8000;
- B3 minus B2 F1: 0.000143845.

Candidate scope is stated with the cross-platform denominator: 36,804 eligible profiles; 449,149,239 possible cross-platform pairs; 29,243 cross-platform positives; 12,403 exact-tier pairs; 2,073,842 model-scored pairs; 2,086,245 workflow candidates; 25,931 covered positives; 3,312 blocking misses; 88.6742% retrieval recall; and 99.5355% candidate-space reduction.

The objective is described as a scenario-based remediation-effort proxy. The 20/10/1-minute and 33.33/16.67/1.67-THB values are explicitly declared project assumptions, not measured production observations or company losses. Agentic CRM is application motivation only; no CRM platform, lead scoring, customer conversion, personalization, human review, or downstream agent outcome is claimed as evaluated.

## Figures

- `figures/system_pipeline.pdf`: compact three-block vector diagram for evidence/model development, observed operational problem, and decision optimization.
- `figures/evaluation_protocol.pdf`: TRAIN/CALIBRATION/POLICY_VALIDATION/SEALED_TEST roles, physical label boundary, freeze, final label reveal, zero entity overlap, and zero pre-final test-label reads.
- `figures/controlled_results.pdf`: authoritative mean workflow F1 and objective with sample-SD error bars for the controlled feature and policy stages.

All five final PDF pages were rendered and visually inspected. No clipping, overlap, or figure-after-references defect remains. Figure 3 was redesigned as a one-column stacked vector chart to avoid label collisions. The final page contains only the continuation of references and unused whitespace; no filler or formatting override was introduced.

## IEEE build and anonymity

- Compiler: Tectonic with `IEEEtran` conference class.
- Length: 5 pages, including figures and references.
- Build: successful; bibliography resolved; no overfull boxes or undefined citations/references. One cosmetic underfull hbox remains.
- Citation closure: 13 cited keys, 13 bibliography entries, zero missing keys, zero uncited entries.
- Metadata: Author=`Anonymous`; Subject=`Anonymous conference submission`.
- Extracted PDF text contains no local paths, workspace/user name, acknowledgement, email address, raw profile content, or identifying repository path.
- PDF font audit: 11 font resources; all embedded.

## SHA-256

- `main.tex`: `c0adc33734c3717d40100f160005678526bc40d8c933462ff1187061c817bffa`
- `references.bib`: `d212783b94a317498216eecc294e38c46c7a4d91660ce8156929f9a849b35cc4`
- `figures/system_pipeline.pdf`: `3ae67d8c23a54b0887a84b9b05bfc4ebcbeab71aeeff17ee9f2d8b309f3b53f3`
- `figures/evaluation_protocol.pdf`: `1ec8ea92884800308813714b3afa85fb6a0487460f905006e1e74e71b25c7a6e`
- `figures/controlled_results.pdf`: `e180dc7724049a01fc78462bdaa1f743bb62936b0d93a7ab0b27657d6d5e905a`
- `main.pdf`: `c4a094d1492dffdc9c7fa46c1c1110fe1ebb1170aa4cf0f1846a0db16086a9f9`

These hashes were recomputed after the final leading-zero and bibliography corrections.

## Remaining warnings

- The corpus reuse license, redistribution permission, consent, collection/Terms-of-Service evidence, and ethics documentation remain unresolved. Release should be restricted to code, configuration, hashes, and aggregate results pending clarification.
- The study has one historical corpus and three outer partitions; it does not establish external generalization.
- The historical model-family screen is motivation, not authoritative V2 test evidence.
- The final Paper V3 PDF is format-ready but still requires the conference's external PDF compliance service and administrative submission checks.

PAPER V3: PASS
REFERENCES: PASS
ANONYMITY: PASS
IEEE FORMAT: PASS
SCIENTIFIC CLAIM BOUNDARY: PASS
