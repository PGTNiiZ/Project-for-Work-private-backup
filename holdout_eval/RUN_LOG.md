# RUN_LOG — holdout_eval (Research V2 three-tier external evaluation)

Every decision, warning and deviation, in order. Aggregate counts only; never log profile values.

## 2026-10-26 — Researcher decisions received (logged before any code was written)

1. Toolkit copied from `~/Downloads/holdout_eval` to `holdout_eval/` (zip not copied).
   Ignore `holdout_eval/data/`, `holdout_eval/raw/`, `*.csv` under holdout_eval, `holdout_eval/**/out/`, `data/`.
   Toolkit code committed before freeze. `freeze.py` must FAIL (not warn) on a dirty tree.
2. Leakage: scrub explicit other-platform account references from bio and external_url in BOTH
   directions (github.com/<login>, "gh: <login>", "github: <login>", "@<login> on github",
   bsky.app/profile/<handle>, bare <handle>.bsky.social); case-insensitive; zero-width and Unicode
   lookalikes treated as equivalent. Username fields NOT scrubbed. Log aggregate counts per
   pattern per side only. Report secondary stratum: pairs with a scrubbed reference vs without.
3. external_url: primary condition = WITHOUT external_url on both sides, implemented as adapter flag
   `--drop-external-url` (not by editing records.csv). "With external_url" = secondary,
   labelled leakage-ceiling condition only.
4. `evaluate.py --possible-threshold`: report MATCH-only and MATCH+POSSIBLE metrics plus review rate;
   unit test on synthetic data; commit before freeze.
5. Tier 3 `--reuse`: measure from LinkSocial dev data (fraction of gold cross-platform pairs with
   identical normalized usernames; aggregate count only); log code + number here; use as --reuse.
6. Final pipeline: the system whose LinkSocial result the thesis claims, frozen before any holdout
   data exists. (a) V2R1 is default if it repairs V2 and has FINAL_RESULTS; report which has complete
   results. (b) Evaluate all three outer-seed models (101/202/303); primary = mean of three, report each.
   (c) If no model file exists, retrain from frozen config on LinkSocial train only, hash the files.
   (d) Image/unavailable features: report as feature-availability mismatch, evaluate with them missing,
   do NOT retrain a different model. (e) Report conflict with STATUS_TH.md (24 Oct).
7. Thresholds: use frozen values if they exist; else derive from LinkSocial validation predictions only.
   Never tune on holdout.
8. Decision rule (pre-registered): transfer SUPPORTED iff lower bound of 95% bootstrap CI of holdout F1
   >= LinkSocial F1 - delta, LinkSocial F1 measured end-to-end (blocked-out gold = FN). Also report
   holdout-minus-LinkSocial difference with CI. If LinkSocial F1 is at a different level, STOP and tell
   the researcher.

Earlier decisions: Tier 1A target = bluesky, 1200 pairs. Use Research V2 code, not `src/identity_resolution/`.
CLAUDE.md is NOT to be updated in this task.

## Open items at time of writing (researcher placeholders still unfilled)
- 6a: pipeline/version/method (B0–B3, V2 vs V2R1) not filled in.
- 7: MATCH / POSSIBLE_MATCH values, source artifact, and derivation rule (cost-optimal vs val-F1-optimal) not filled in.
- 8: LinkSocial F1 value and delta not filled in.

## Discrepancies
- CLAUDE.md and `src/identity_resolution/` describe the first-generation 17-feature notebook pipeline
  (IdentityMLP, thresholds 0.90/0.70). Not updated in this task, by instruction.
- `docs/STATUS_TH.md` (24 Oct 2026): "main system still uses the original model and thresholds; R3 not
  adopted into main". The holdout evaluates the pipeline selected under 6a, not necessarily the main system.

## 2026-10-26 — Work done (pipeline-independent)
- Toolkit copied; `.gitignore` extended (holdout_eval/data, raw, **/out, **/*.csv, **/*.jsonl, progress.json, /data/).
  Note: `.gitignore` already contained `!**/*.csv` and `!**/*.md`; the new ignore lines were appended after
  them so they take precedence. Verified with `git check-ignore`.
- `common/freeze.py`: now exits non-zero when the repo is dirty or git status cannot be read (no bypass flag).
  Also records `possible_threshold`, `reference_f1`, `delta` in the manifest.
- `common/evaluate.py`: `--possible-threshold` (or manifest) adds `match_plus_possible` (point, CI, review rate);
  `--strata` splits results by scrubbed/unscrubbed; `decision` block (CI lower bound vs reference_f1 - delta,
  plus holdout-minus-reference with CI) when the manifest carries reference_f1 and delta.
  Unit tests: `tests/test_evaluate.py` (synthetic data, 3 tests).
- `common/scrub.py` + `tier1/collect_github_social.py`: bidirectional scrubbing of bio/external_url,
  case-insensitive, zero-width and lookalike folding; usernames untouched. Writes aggregate-only
  `scrub_counts.json` and `strata.csv` (entity_id, flag). Unit tests: `tests/test_scrub.py` (4 tests).
  Offline smoke test with one synthetic raw record passed. Self-references on the same platform
  (e.g. "GH: <login>" inside the GitHub bio) are intentionally not scrubbed: only references to the OTHER platform.
- Tests run with the project venv (`.venv/bin/python`; Homebrew python3.11 has no pandas). `requests` is
  not installed in `.venv`; needed before running the collector.
- Working tree is not clean: untracked `research_v2_review_workspace/` pre-dates this task. freeze.py will
  refuse until it is committed or ignored (researcher's call).

## 2026-10-26 — Pipeline search findings (blocks Step 1 adapter and Step 2)
- ICSEC `experiments/icsec_final/authoritative_run_v2*` = GB-17 / GB-18 (17 handcrafted + bert_cos),
  seeds 101/202/303, model pkl + calibrator pkl exist under `authoritative_run_v2r1/scientific_outputs/outer_*/models/`.
  This is NOT a 41-feature pipeline and has no image features.
- The 41-feature pipeline is `pub_multi/` docs: main run `image_context_r075_h20_s42` (Gradient Boosting, seed 42,
  random_neg_ratio 0.75, hard_neg_ratio 2.0, val-F1 threshold 0.35, test F1 0.934 at pair level,
  production decision tiers 0.98 / 0.95). 18 of its 41 features are image-based (3 availability + 11 statistics + 4 caption context).
- Its code (`train_data/stage9_features_pipeline_chunked.py`, `stage7_13_multimodal_suite/run_multimodal_suite.py`,
  `stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py`) exists only in the `~/research-*` worktrees,
  not in this checkout. Its run directory (`train_data/stage7_13_multimodal_suite/runs/image_context_r075_h20_s42/`
  with models, feature_list.txt) was not found in this checkout; recorded paths point to a Windows `D:\` machine.
- Rule 6b (three outer seeds 101/202/303) belongs to the ICSEC GB-17/18 pipeline, not the 41-feature one
  (single seed 42). The two cannot both be "the system". Awaiting researcher decision.

## 2026-10-26 (session d9) — Final researcher decisions received; logged BEFORE writing code

Decisions are final. Values given as rules are resolved from artifacts (path + commit cited below).
Session d9 continues from commit c68c9d20 (session 8a: items 1–4 pipeline-independent work). Items already
done there are not redone; deltas are listed.

D1 COPY — done in c68c9d20. Delta: an accidental re-copy by session d9 at 02:08 overwrote three committed files
   (common/evaluate.py, common/freeze.py, tier1/collect_github_social.py) with the zip originals; restored from
   HEAD with `git checkout --` before any further edit (no committed content lost).
D2 LEAKAGE — patterns as specified, both directions, bio + external_url, case-insensitive, zero-width/lookalike
   folding, usernames untouched, aggregate counts per pattern per side only, scrubbed vs not-scrubbed stratum
   reported as secondary. Already implemented (common/scrub.py). Delta: add STOP check (c) to the collector.
D3 EXTERNAL_URL — PRIMARY = external_url dropped on both sides via adapter flag --drop-external-url
   (gold labels were built from the GitHub social link). "With URL" = secondary, labelled LEAKAGE CEILING.
D4 POSSIBLE_MATCH — evaluate.py --possible-threshold, MATCH-only, MATCH+POSSIBLE, review rate, synthetic test
   (done in c68c9d20). Delta: frozen V2R1 policies give per-pair decisions (B2/B3 use a name_sim band), so
   evaluate.py also accepts a `decision` column (MATCH/REVIEW/NO_MATCH) from the adapter.
D5 --reuse — measured from LinkSocial dev data (aggregate), not 0.3.
D6 PIPELINE — V2R1 if complete, else V2; evaluate every method with complete artifacts; PRIMARY = method the
   results/paper designate as proposed (else best LinkSocial VALIDATION mean; never test); all 3 outer seeds,
   primary = mean of 3, also per seed; retrain only if model files missing; missing features → evaluate with
   them missing + report mismatch, never swap models.
D7 THRESHOLDS — frozen MATCH/POSSIBLE values from the chosen pipeline's artifacts if they exist; else derive
   from LinkSocial VALIDATION only (MATCH = max validation F1 end-to-end; POSSIBLE = lowest threshold with
   validation precision >= 0.50). Record in freeze manifest. Never tune on holdout.
D8 DECISION RULE (pre-registered today) — LinkSocial F1 = end-to-end F1 (blocked-out gold = FN, as evaluate.py)
   of the primary method, mean of 3 seeds; delta = 0.05; SUPPORTED iff lower 95% bootstrap CI bound of holdout F1
   >= LinkSocial F1 - 0.05; always report holdout-minus-LinkSocial difference with CI; report regardless of outcome.
STOP only if (a) no usable config to retrain from, (b) LinkSocial end-to-end F1 unobtainable, (c) scrub removes
   > 20% of holdout pairs' bio content.

## 2026-10-26 (session d9) — Resolved values (Step 1). 10-line summary

1. Pipeline = `experiments/icsec_final/authoritative_run_v2r1` (complete: 3 seeds × GB-17/GB-18 model+calibrator, policies, sealed predictions, decisions; SHA256SUMS OK) [repo @ c68c9d20; PROTOCOL_V2R1.md "Versioning"].
2. V2R1 exists because it is the integrity-repaired rerun of V2 (sealed-label guard, pre-label prediction freeze); "if it passes, it is the ONLY numerical source for the paper" [authoritative_run_v2r1/PROTOCOL_V2R1.md L5-L8]. STATUS_TH.md says the MAIN system still uses the original model/thresholds and never mentions V2/V2R1 [docs/STATUS_TH.md, 50d95e9] → holdout tests the paper's system, not the deployed one.
3. Primary method = GB-18 + B3 (genetic three-way policy), designated by the paper title/abstract [paper/reviewer_revision/main.tex L9, L16]; all of GB17_B0, B0, B1, B2, B3 evaluated (all complete).
4. Seeds 101/202/303 (existing models; no retraining needed); primary = mean of 3, each seed reported.
5. Thresholds = frozen per-seed policies [authoritative_run_v2r1/scientific_outputs/outer_*/policies.json]; e.g. B3: t_match 0.9329/0.9990/0.9125, t_review 0.5000/0.5287/0.5263 (seeds 101/202/303). Rule-7 derivation not needed.
6. LinkSocial F1 (decision rule) = 0.861031 = mean B3 end-to-end F1 with blocked-out gold AND positive REVIEW as FN — identical definition to evaluate.py MATCH-only; recomputed from V2R1 decisions, equals paper Table L183 (0.8610). FINAL_RESULTS' decision-conditional F1 0.8903 (REVIEW excluded) reported as SECONDARY sensitivity only. See rationale below.
7. delta = 0.05 → SUPPORTED iff lower 95% CI of holdout mean B3 F1 ≥ 0.811031 (PRIMARY condition, external_url dropped).
8. --reuse = 0.3829 (dev-only identical-normalized-username share; seeds 0.385233/0.381570/0.381912) [tools/measure_reuse.py].
9. Adapter `adapter/run_v2r1.py` reproduces stored V2R1 seed-101 B3 probabilities exactly (max |Δp| = 0.0) and decisions 100% on 2,000 LinkSocial pairs.
10. No STOP condition hit: (a) models exist; (b) LinkSocial end-to-end F1 obtained; (c) checked at collection time (collector exits before writing records.csv if > 20% of bio characters are removed).

### Details and rationale
- Reference-F1 choice (rule 8): FINAL_RESULTS.md (v2) reports decision-conditional F1, which counts blocked-out gold as FN but EXCLUDES
  positive REVIEW from the denominator. evaluate.py MATCH-only counts positive REVIEW as FN. To compare like with like as rule 8 requires
  ("the same as evaluate.py"), the reference is the automatic end-to-end F1 (F_auto) of the same pipeline, recomputed from the stored
  V2R1 test decisions (per seed 0.855616 / 0.853237 / 0.874240). The stricter F_dec-based outcome is always reported alongside
  (`decision_sensitivity_f_dec`, threshold 0.840293). Recomputation of all methods: GB17_B0 0.829952, B0 0.841952, B1 0.866722,
  B2 0.861105, B3 0.861031 (F_auto); F_dec 0.849436 / 0.850965 / 0.891037 / 0.890149 / 0.890293 — all match paper/FINAL_RESULTS.
- MATCH = t_match and POSSIBLE_MATCH = t_review of each frozen policy. For B2/B3 the REVIEW/POSSIBLE region also depends on the
  name_sim band (c_promote/c_demote), so the adapter emits the frozen per-pair decision and evaluate.py/aggregate.py read it
  (MATCH-only = MATCH; MATCH+POSSIBLE = MATCH or REVIEW; review rate = REVIEW share of candidates).
- Exact tier (username exact ≥3 chars, external-URL exact) = automatic MATCH, as in V2R1 [final_runner.py L248, L270].
- PRIMARY drops external_url both sides inside the adapter (records.csv untouched) → URL exact tier and external_domain blocking key
  are inactive; LEAKAGE CEILING keeps them (URL cleaning approximates LinkSocial's externalUrl_clean: lower, strip scheme/www/trailing "/").
- Feature-availability mismatch (reported, models not swapped): Bluesky has no location field; no image features in GB-18;
  Bluesky usernames are full handles and are not altered.
- Leakage scrub (session 8a, common/scrub.py) also removes the bare Bluesky handle and <login>.github.io from bios/URLs — slightly broader
  than the listed patterns, still "explicit references to the other platform's account"; kept.
- STOP (c) operationalised as: removed bio characters / total bio characters (both sides, all pairs) > 0.20. Share of pairs with any bio
  scrubbed is also logged (`pairs_with_bio_scrubbed_fraction`).
- Bootstrap for the 3-seed mean: 1,000 resamples of left (GitHub) entities, same resample applied to every seed; LinkSocial reference fixed.
- Freeze is run from a dedicated clean `git worktree` of the toolkit commit, because the main working tree holds another session's
  untracked `research_v2_runs/*` work and the untracked `research_v2_review_workspace/`; neither was committed, ignored or modified.
- `requests` must be installed in `.venv` before running the collector; GITHUB_TOKEN required; collector header reminds to check ToS/ethics.
