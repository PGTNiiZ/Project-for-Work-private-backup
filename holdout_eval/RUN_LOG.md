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
