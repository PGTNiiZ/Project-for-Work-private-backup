"""Export existing experiment artifacts to row-complete Excel workbooks."""

import argparse
import csv
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import xlsxwriter


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).with_name("experiment_excel")
MAX_DATA_ROWS = 1_048_575


def workbook(name, note):
    OUT.mkdir(exist_ok=True)
    book = xlsxwriter.Workbook(str(OUT / f"{name}.tmp.xlsx"), {
        "constant_memory": True,
        "strings_to_formulas": False,
        "strings_to_urls": False,
    })
    guide = book.add_worksheet("00_READ_ME")
    guide.set_column("A:A", 28)
    guide.set_column("B:B", 105)
    guide.write_row(0, 0, ["Workbook", name])
    guide.write_row(1, 0, ["Meaning", note])
    guide.write_row(2, 0, ["Rule", "All source rows retained; large tables split by source row order. Sheet 00 lists exact source paths."])
    guide.write_row(3, 0, ["Important", "These are historical artifacts from different protocols. Do not merge scores across experiments by row number."])
    return book, guide, []


def cell(sheet, row, col, value):
    if value is None or value is pd.NA or (isinstance(value, float) and pd.isna(value)):
        return
    if isinstance(value, str):
        if len(value) > 32_767:
            raise ValueError(f"Cell exceeds Excel limit: {sheet.name} row {row + 1}")
        sheet.write_string(row, col, value)
    else:
        sheet.write(row, col, value)


def sheet_for(book, name, columns, expected_rows):
    if expected_rows > MAX_DATA_ROWS:
        raise ValueError(f"Split required for {name}: {expected_rows}")
    sheet = book.add_worksheet(name)
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, expected_rows, len(columns) - 1)
    sheet.set_row(0, 34)
    sheet.set_column(0, len(columns) - 1, 19)
    fmt = book.add_format({"bold": True, "bg_color": "#DDEBF7", "text_wrap": True})
    for col, name in enumerate(columns):
        sheet.write(0, col, name, fmt)
    return sheet


def write_rows(sheet, rows, expected):
    count = 0
    for count, values in enumerate(rows, 1):
        for col, value in enumerate(values):
            cell(sheet, count, col, value)
    assert count == expected, (sheet.name, count, expected)


def add_parquet(book, manifest, path, prefix):
    source = ROOT / path
    pf = pq.ParquetFile(source)
    total = pf.metadata.num_rows
    cols = pf.schema.names
    chunk = 0
    row = 0
    sheet = None
    for batch in pf.iter_batches(batch_size=10_000):
        for values in zip(*(column.to_pylist() for column in batch.columns)):
            if sheet is None or row == MAX_DATA_ROWS:
                chunk += 1
                remaining = total - (chunk - 1) * MAX_DATA_ROWS
                row = 0
                sheet = sheet_for(book, f"{prefix}_{chunk}", cols, min(MAX_DATA_ROWS, remaining))
            row += 1
            for col, value in enumerate(values):
                cell(sheet, row, col, value)
    assert total == (chunk - 1) * MAX_DATA_ROWS + row, path
    manifest.append((prefix, path, total, len(cols), chunk))


def add_csv(book, manifest, path, prefix):
    source = ROOT / path
    data = pd.read_csv(source, low_memory=False)
    sheet = sheet_for(book, prefix, list(data.columns), len(data))
    write_rows(sheet, data.itertuples(index=False, name=None), len(data))
    manifest.append((prefix, path, len(data), len(data.columns), 1))


def finish(book, guide, manifest, name):
    guide.write_row(5, 0, ["Sheet prefix", "Source path", "Rows", "Columns", "Sheets"])
    for row, record in enumerate(manifest, 6):
        guide.write_row(row, 0, record)
    book.close()
    (OUT / f"{name}.tmp.xlsx").replace(OUT / f"{name}.xlsx")
    print(f"Created {OUT / (name + '.xlsx')}", flush=True)


def multimodal_ga():
    name = "01_multimodal_and_GA"
    book, guide, manifest = workbook(name, "41-feature multimodal input, R1 GA trace, and 10-gene full-candidate decisions")
    add_parquet(book, manifest, "artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/decisioning_features.parquet", "MULTI41_GA_INPUT")
    for file, prefix in [
        ("r1_ga_validation_chromosome_detail.csv", "R1_VALIDATION_TRACE"),
        ("r1_ga_run_input.csv", "R1_GA_INPUT"),
        ("r1_ga_transition_summary.csv", "R1_TRANSITIONS"),
        ("r1_ga_changed_examples.csv", "R1_CHANGED_EXAMPLES"),
    ]:
        add_csv(book, manifest, "experiments/walkthroughs/r1_ga_redecision/data/" + file, prefix)
    add_parquet(book, manifest, "artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet", "GA10_FULL_DECISIONS")
    finish(book, guide, manifest, name)


def ga_full_join():
    name = "01b_GA_full_feature_to_decision"
    book, guide, manifest = workbook(name, "Every model-scored full-candidate GA input row beside its decision output; exact-tier rows on a separate sheet")
    chunk_dir = ROOT / "artifacts/decisioning/feature_aware_ga/full_2m/feature_chunks"
    chunks = sorted(chunk_dir.glob("decisioning_features_*.parquet"))
    source = "artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet"
    decisions = pq.read_table(ROOT / source)
    assert decisions.num_rows == 2_086_245
    exact_rows = 12_403
    exact = decisions.slice(0, exact_rows)
    sheet = sheet_for(book, "EXACT_TIER", exact.column_names, exact_rows)
    row = 0
    for batch in exact.to_batches(max_chunksize=10_000):
        for values in zip(*(column.to_pylist() for column in batch.columns)):
            row += 1
            for col, value in enumerate(values):
                cell(sheet, row, col, value)
    assert row == exact_rows and set(exact["decision_source"].to_pylist()) == {"AUTO_EXACT"}
    manifest.append(("EXACT_TIER", source + " [0:12403]", exact_rows, len(exact.column_names), 1))

    columns = None
    sheet = None
    sheet_row = 0
    total = 0
    written = 0
    part = 0
    for chunk in chunks:
        feature = pq.read_table(chunk)
        output = decisions.slice(exact_rows + total, feature.num_rows)
        assert feature.num_rows == output.num_rows
        assert feature["profile_row_id_a"].equals(output["profile_id_a"])
        assert feature["profile_row_id_b"].equals(output["profile_id_b"])
        assert feature["label"].cast(output["actual"].type).equals(output["actual"])
        if columns is None:
            columns = [*feature.column_names, *("out_" + name for name in output.column_names)]
        out_table = feature
        for column_name in output.column_names:
            out_table = out_table.append_column("out_" + column_name, output[column_name])
        for batch in out_table.to_batches(max_chunksize=10_000):
            for values in zip(*(column.to_pylist() for column in batch.columns)):
                if sheet is None or sheet_row == MAX_DATA_ROWS:
                    part += 1
                    sheet_row = 0
                    remaining = decisions.num_rows - exact_rows - written
                    sheet = sheet_for(book, f"GA_INPUT_OUTPUT_{part}", columns, min(MAX_DATA_ROWS, remaining))
                sheet_row += 1
                written += 1
                for col, value in enumerate(values):
                    cell(sheet, sheet_row, col, value)
        total += feature.num_rows
    assert written == total == decisions.num_rows - exact_rows == 2_073_842
    manifest.append(("GA_INPUT_OUTPUT", str(chunk_dir.relative_to(ROOT)) + " + " + source, total, len(columns), part))
    finish(book, guide, manifest, name)


def icsec_features():
    name = "02_ICSEC_model_inputs"
    book, guide, manifest = workbook(name, "V2/V2R1 frozen model-scored candidate pairs: GB-17 features plus MiniLM cosine")
    source = "experiments/icsec_final/authoritative_run_v2/features/"
    gb = pq.read_table(ROOT / (source + "gb17.parquet"))
    bert = pq.read_table(ROOT / (source + "bert_cos.parquet"))
    assert gb.num_rows == bert.num_rows == 2_073_842
    for key in ("profile_row_id_a", "profile_row_id_b"):
        assert gb[key].equals(bert[key]), key
    columns = [*gb.column_names, "bert_cos"]
    start = 0
    chunk = 0
    while start < gb.num_rows:
        end = min(start + MAX_DATA_ROWS, gb.num_rows)
        chunk += 1
        sheet = sheet_for(book, f"MODEL_FEATURES_{chunk}", columns, end - start)
        combined = gb.slice(start, end - start).append_column("bert_cos", bert["bert_cos"].slice(start, end - start))
        row = 0
        for batch in combined.to_batches(max_chunksize=10_000):
            for values in zip(*(column.to_pylist() for column in batch.columns)):
                row += 1
                for col, value in enumerate(values):
                    cell(sheet, row, col, value)
        assert row == end - start
        start = end
    manifest.append(("MODEL_FEATURES", source + "gb17.parquet + bert_cos.parquet", gb.num_rows, len(columns), chunk))
    add_csv(book, manifest, "data_for_project/normalized_profiles_with_profile_id.csv", "PROFILES_ROW_ID")
    finish(book, guide, manifest, name)


def icsec_ga():
    name = "03_ICSEC_V2R1_GA"
    book, guide, manifest = workbook(name, "V2R1 seed-specific validation replay input, replayed optimizer trace, chosen policies, and test decisions")
    guide.write_row(4, 0, ["Replay scope", "VAL_REPLAY and SEARCH_REPLAY sheets come from reviewer_revision replay artifacts; they are not a saved original GA call log."])
    v2r1 = "experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/"
    v2 = "experiments/icsec_final/authoritative_run_v2/"
    revision = "experiments/icsec_final/reviewer_revision/"
    policy_rows = []
    for seed in (101, 202, 303):
        prefix = f"S{seed}"
        frozen = v2 + f"scientific_inputs/outer_{seed}/"
        add_parquet(book, manifest, frozen + "development_labels/labels.parquet", f"{prefix}_DEV_LABELS")
        add_parquet(book, manifest, frozen + "sealed_test_labels/labels.parquet", f"{prefix}_TEST_LABELS")
        add_parquet(book, manifest, v2 + f"routing/outer_{seed}/model_scored.parquet", f"{prefix}_ROUTING")
        add_parquet(book, manifest, frozen + "blocking_misses/positive_pairs.parquet", f"{prefix}_BLOCK_MISS")
        base = revision + f"outer_{seed}/"
        add_parquet(book, manifest, base + "validation_replay_input.parquet", f"{prefix}_VAL_REPLAY")
        for method in ("B2", "B3"):
            add_csv(book, manifest, base + f"{method}_anytime.csv", f"{prefix}_{method}_REPLAY")
        p = ROOT / (v2r1 + f"outer_{seed}/policies.json")
        data = json.loads(p.read_text())
        for method, params in data["parameters"].items():
            policy_rows.append((seed, method, *(params + [None] * (4 - len(params))), json.dumps(data["metadata"].get(method, {}), ensure_ascii=False)))
        add_parquet(book, manifest, v2r1 + f"outer_{seed}/sealed_predictions/predictions.parquet", f"{prefix}_FROZEN_PRED")
        for method in ("B0", "B1", "B2", "B3", "GB17_B0"):
            add_parquet(book, manifest, v2r1 + f"outer_{seed}/decisions/{method}_workflow.parquet", f"{prefix}_{method}_TEST")
    cols = ["outer_seed", "policy", "t_match", "t_review", "c_promote", "c_demote", "metadata_json"]
    sh = sheet_for(book, "POLICY_PARAMETERS", cols, len(policy_rows))
    write_rows(sh, policy_rows, len(policy_rows))
    manifest.append(("POLICY_PARAMETERS", "V2R1 scientific_outputs/outer_*/policies.json", len(policy_rows), len(cols), 1))
    for file, prefix in [("selected_vectors.csv", "REV_SELECTED_VECTORS"), ("anytime_checkpoints.csv", "REV_ANYTIME_CHECKS"), ("metrics_per_seed.csv", "REV_METRICS")]:
        add_csv(book, manifest, revision + file, prefix)
    finish(book, guide, manifest, name)


def catalog():
    name = "04_source_artifact_catalog"
    book, guide, manifest = workbook(name, "Inventory of all local CSV, Parquet, and JSON artifacts; paths keep experiment versions separate")
    guide.write_row(4, 0, ["Scope", "FILES lists every matching source artifact; data-heavy workbooks 01–03 contain the central row-level inputs and outputs."])
    flow = [
        ("Legacy", "raw profile CSV", "data_for_project/combined_profiles.csv", "07_dataset_raw_to_features.xlsx / 01_RAW_PROFILES"),
        ("Legacy", "cleaned profiles", "data/processed/all_profiles_with_blocking_keys.csv", "07_dataset_raw_to_features.xlsx / 02_CLEAN_PROFILES"),
        ("Legacy", "labeled pair features", "data/processed/feature_matrix.csv", "07_dataset_raw_to_features.xlsx / 03_PAIRS"),
        ("R1 GA", "validation and GA input", "experiments/walkthroughs/r1_ga_redecision/data/", "01_multimodal_and_GA.xlsx / R1_*"),
        ("Multimodal GA", "41 selected features + evidence/score fields", "artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/decisioning_features.parquet", "01_multimodal_and_GA.xlsx / MULTI41_*"),
        ("10-gene GA", "full candidate decisions", "artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet", "01_multimodal_and_GA.xlsx / GA10_*"),
        ("10-gene GA", "full input evidence beside output", "artifacts/decisioning/feature_aware_ga/full_2m/feature_chunks/ + full_2m_pair_decisions.parquet", "01b_GA_full_feature_to_decision.xlsx"),
        ("ICSEC V2R1", "profile row IDs", "data_for_project/normalized_profiles_with_profile_id.csv", "02_ICSEC_model_inputs.xlsx / PROFILES_*"),
        ("ICSEC V2R1", "frozen 17 + MiniLM model inputs", "experiments/icsec_final/authoritative_run_v2/features/", "02_ICSEC_model_inputs.xlsx / MODEL_FEATURES_*"),
        ("ICSEC V2R1", "development labels, routing, blocking misses", "experiments/icsec_final/authoritative_run_v2/scientific_inputs/", "03_ICSEC_V2R1_GA.xlsx / S*_DEV, S*_ROUTING, S*_BLOCK"),
        ("ICSEC V2R1", "validation and optimizer replay", "experiments/icsec_final/reviewer_revision/outer_*/", "03_ICSEC_V2R1_GA.xlsx / S*_VAL_REPLAY, S*_B2/B3_REPLAY"),
        ("ICSEC V2R1", "frozen predictions and policy test decisions", "experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/", "03_ICSEC_V2R1_GA.xlsx / S*_FROZEN, S*_*_TEST"),
        ("R0–R6", "probabilities, optimizer trials, generations", "experiments/r2_probabilities.parquet + experiments/r6_bert_er/ + experiments/automation/", "05_R0_R6_experiment_history.xlsx"),
        ("GA search", "10-gene and GB transformer search history and frozen policies", "artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/ + experiments/automation/gb_transformer_*/", "06_GA_search_parameters.xlsx"),
    ]
    sh = sheet_for(book, "FLOW", ["experiment", "stage", "source", "Excel location"], len(flow))
    write_rows(sh, flow, len(flow))
    manifest.append(("FLOW", "Manual path map verified against local artifacts", len(flow), 4, 1))

    roots = ("data", "data_for_project", "train_data", "artifacts", "experiments")
    paths = sorted(p for root in roots for p in (ROOT / root).rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".parquet", ".json"})
    sh = sheet_for(book, "FILES", ["path", "type", "rows", "columns", "size_MB", "column_names"], len(paths))
    for row, p in enumerate(paths, 1):
        if p.suffix.lower() == ".parquet":
            meta = pq.ParquetFile(p).metadata
            count, cols = meta.num_rows, meta.schema.names
        elif p.suffix.lower() == ".csv":
            with p.open(newline="", encoding="utf-8-sig", errors="replace") as source:
                reader = csv.reader(source)
                cols = next(reader, [])
                count = sum(1 for _ in reader)
        else:
            count, cols = None, []
        values = (str(p.relative_to(ROOT)), p.suffix.lower(), count, len(cols) if cols else None, round(p.stat().st_size / 1024**2, 2), ", ".join(cols))
        for col, value in enumerate(values):
            cell(sh, row, col, value)
    manifest.append(("FILES", "data/, data_for_project/, train_data/, artifacts/, experiments/", len(paths), 6, 1))
    finish(book, guide, manifest, name)


def r_history():
    name = "05_R0_R6_experiment_history"
    book, guide, manifest = workbook(name, "R-series probability artifacts and R1/R3 optimizer histories; each run retains its own source identity")
    add_csv(book, manifest, "experiments/r0_r5_summary_tidy.csv", "R0_R5_SUMMARY")
    add_csv(book, manifest, "experiments/automation/r0_r3_report_20260809/r0_r3_experimental_matrix.csv", "R0_R3_MATRIX")
    for path, prefix in [
        ("experiments/r2_probabilities.parquet", "R2_PROB"),
        ("experiments/r6_bert_er/r6_probabilities.parquet", "R6_PROB"),
        ("experiments/r6_bert_er/new_candidate_pairs.parquet", "R6_NEW_CANDIDATES"),
    ]:
        add_parquet(book, manifest, path, prefix)
    runs = sorted(p for p in (ROOT / "experiments/automation").iterdir() if p.is_dir() and p.name.startswith(("r1_", "r3_")))
    for index, run in enumerate(runs, 1):
        code = f"RUN{index:02d}"
        for filename, suffix in (("generations.csv", "GENERATIONS"), ("trials.csv", "TRIALS"), ("training_history.csv", "TRAINING"), ("r2_probabilities.parquet", "R2_PROB")):
            path = run / filename
            if path.exists():
                relative = str(path.relative_to(ROOT))
                if path.suffix == ".parquet":
                    add_parquet(book, manifest, relative, f"{code}_{suffix}")
                else:
                    add_csv(book, manifest, relative, f"{code}_{suffix}")
    finish(book, guide, manifest, name)


def ga_search_details():
    name = "06_GA_search_parameters"
    book, guide, manifest = workbook(name, "GA search inputs, trials, generation histories, and frozen policy parameters for 10-gene and transformer runs")
    full = "artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/"
    for filename, prefix in [
        ("full_2m_validation_trials.csv", "GA10_VALID_TRIALS"),
        ("full_2m_metrics_by_split.csv", "GA10_SPLIT_METRICS"),
        ("full_2m_feature_coverage.csv", "GA10_COVERAGE"),
    ]:
        add_csv(book, manifest, full + filename, prefix)
    for index, run in enumerate(sorted((ROOT / "experiments/automation").glob("gb_transformer_*")), 1):
        if not run.is_dir():
            continue
        for filename, suffix in (("trials.csv", "TRIALS"), ("ga_generations.csv", "GENERATIONS")):
            path = run / filename
            if path.exists():
                add_csv(book, manifest, str(path.relative_to(ROOT)), f"GBT{index:02d}_{suffix}")

    history = json.loads((ROOT / (full + "full_2m_generation_history.json")).read_text())
    rows = []
    for policy, seeds in history.items():
        for seed, generations in seeds.items():
            for generation in generations:
                rows.append((policy, seed, generation.get("generation"), generation.get("validation_cost"), generation.get("validation_precision"), generation.get("validation_recall"), json.dumps(generation.get("genome")), json.dumps(generation.get("weights"), ensure_ascii=False), json.dumps(generation.get("thresholds"))))
    cols = ["policy", "seed", "generation", "validation_cost", "validation_precision", "validation_recall", "genome_json", "weights_json", "thresholds_json"]
    sh = sheet_for(book, "GA10_GENERATIONS", cols, len(rows))
    write_rows(sh, rows, len(rows))
    manifest.append(("GA10_GENERATIONS", full + "full_2m_generation_history.json", len(rows), len(cols), 1))

    facts = []
    def flatten(source, key, value):
        if isinstance(value, dict):
            for child, item in value.items():
                flatten(source, f"{key}.{child}" if key else str(child), item)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                flatten(source, f"{key}[{index}]", item)
        else:
            facts.append((source, key, value))

    json_paths = [
        full + "full_2m_frozen_policies_before_test.json",
        full + "full_2m_result.json",
        "artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/weighted_ga_history.json",
        "artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/selector_generation_history.json",
    ]
    for path in json_paths:
        flatten(path, "", json.loads((ROOT / path).read_text()))
    sh = sheet_for(book, "GA_JSON_FACTS", ["source", "field", "value"], len(facts))
    write_rows(sh, facts, len(facts))
    manifest.append(("GA_JSON_FACTS", " + ".join(json_paths), len(facts), 3, 1))
    finish(book, guide, manifest, name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("part", choices=("multimodal_ga", "ga_full_join", "icsec_features", "icsec_ga", "catalog", "r_history", "ga_search_details"))
    part = parser.parse_args().part
    globals()[part]()


if __name__ == "__main__":
    main()
