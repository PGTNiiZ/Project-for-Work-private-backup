"""Export the historical raw → cleaned → pair-feature snapshot for inspection."""

from pathlib import Path

import pandas as pd
import xlsxwriter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).with_name("07_dataset_raw_to_features.xlsx")

RAW = ROOT / "data_for_project/combined_profiles.csv"
CLEAN = ROOT / "data/processed/all_profiles_with_blocking_keys.csv"
PAIRS = ROOT / "data/processed/feature_matrix.csv"
IMAGE_PROFILES = ROOT / "data/final/profiles_with_images.csv"
IMAGE_FEATURES = ROOT / "data/final/image_features_complete.csv"

raw = pd.read_csv(RAW, low_memory=False)
raw.columns = [name.strip().strip('"') for name in raw.columns]
clean = pd.read_csv(CLEAN, low_memory=False)
pairs = pd.read_csv(PAIRS, low_memory=False)
image_profiles = pd.read_csv(IMAGE_PROFILES, low_memory=False)
image_features = pd.read_csv(IMAGE_FEATURES, low_memory=False)

# These files preserve row order, but profile_id alone is not unique. Verify
# the row alignment before using the original values beside cleaned values.
assert len(raw) == len(clean) == 36_807
for column in ("source_folder", "user_folder", "platform", "outputProfileName", "pictureURL"):
    assert raw[column].fillna("").astype(str).equals(clean[column].fillna("").astype(str)), column
assert len(pairs) == 204_701
assert not pairs[["profile_id_a", "profile_id_b"]].isna().any().any()

id_counts = clean["profile_id"].value_counts(dropna=True)
unique = clean.loc[clean["profile_id"].map(id_counts).eq(1)].copy()
unique["source_row"] = unique.index + 2  # Excel/CSV row, including header.
lookup = unique.set_index("profile_id")

feature_columns = list(pairs.columns[4:])
assert len(feature_columns) == 17
raw_fields = ["platform", "user_folder", "userName", "fullName", "bio", "externalUrl", "location", "pictureURL"]
clean_fields = ["userName_clean", "fullName_clean", "bio_clean", "location_clean", "externalUrl_clean"]
side_fields = ["source_row", *raw_fields, *clean_fields]

def side(profile_id):
    count = id_counts.get(profile_id, 0)
    if count == 0:
        return ["NO_PROFILE", *([None] * len(side_fields))]
    if count > 1:
        return ["DUPLICATE_ID", *([None] * len(side_fields))]
    profile = lookup.loc[profile_id]
    return ["OK", *(profile[field] for field in side_fields)]


workbook = xlsxwriter.Workbook(str(OUTPUT.with_suffix(".tmp.xlsx")), {
    "constant_memory": True,
    "strings_to_formulas": False,
    "strings_to_urls": False,
})
header = workbook.add_format({"bold": True, "bg_color": "#DDEBF7", "text_wrap": True, "valign": "top"})
title = workbook.add_format({"bold": True, "font_size": 16})
note = workbook.add_format({"text_wrap": True, "valign": "top"})

def write_cell(sheet, row, col, value):
    if pd.isna(value):
        return
    if isinstance(value, str):
        if len(value) > 32_767:
            raise ValueError(f"Excel cell limit exceeded at {sheet.name}!{row + 1}:{col + 1}")
        sheet.write_string(row, col, value)
    elif isinstance(value, bool):
        sheet.write_boolean(row, col, value)
    elif isinstance(value, (int, float)):
        sheet.write_number(row, col, value)
    else:
        sheet.write_string(row, col, str(value))


def table(name, columns, rows, count):
    sheet = workbook.add_worksheet(name)
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, count, len(columns) - 1)
    sheet.set_default_row(18)
    sheet.set_row(0, 34)
    sheet.set_column(0, len(columns) - 1, 20)
    for col, column in enumerate(columns):
        sheet.write(0, col, column, header)
    for row_no, values in enumerate(rows, 1):
        for col, value in enumerate(values):
            write_cell(sheet, row_no, col, value)
    return sheet


guide = workbook.add_worksheet("00_READ_ME")
guide.set_column("A:A", 25)
guide.set_column("B:B", 100)
guide.write("A1", "Raw → Clean → Features", title)
guide_rows = [
    ("วิธีใช้", "เปิดชีต 03_PAIRS แล้วกรอง label, match_status_a/b หรือค่า feature; ทุกแถวของ feature_matrix อยู่ในชีตนี้"),
    ("01_RAW_PROFILES", "36,807 โปรไฟล์จาก combined_profiles.csv; ข้อความก่อน normalize; source_row ใช้เทียบกับชีต 02"),
    ("02_CLEAN_PROFILES", "36,807 โปรไฟล์จาก all_profiles_with_blocking_keys.csv; แถวเดียวกันกับชีต 01"),
    ("03_PAIRS", "204,701 คู่: ID/label → raw A/B → clean A/B → 17 features; แถวเดิมจาก feature_matrix.csv"),
    ("04_FEATURE_GUIDE", "คำอธิบาย 17 features และคอลัมน์สถานะการเชื่อมข้อมูล"),
    ("05_IMAGE_PROFILES", "24,729 โปรไฟล์จาก profiles_with_images.csv; เป็นอีก snapshot ไม่ใช้ profile_id เดียวกับ 03_PAIRS"),
    ("06_IMAGE_FEATURES", "2,459 แถวจาก image_features_complete.csv; เป็น feature ระดับภาพ ไม่ใช่ feature เปรียบเทียบคู่"),
    ("OK", "profile_id เชื่อมกับ cleaned profile ได้เพียงหนึ่งแถว"),
    ("NO_PROFILE", "ไม่พบ profile_id ใน snapshot โปรไฟล์นี้; raw/clean ฝั่งนั้นเว้นว่าง"),
    ("DUPLICATE_ID", "profile_id พบหลายแถว; เว้น raw/clean ว่างเพื่อไม่จับคู่ผิด"),
    ("ข้อจำกัด", "Raw JSON ต้นทางเดิมไม่มีใน workspace; 01_RAW_PROFILES เป็น CSV ที่ใกล้ข้อมูลดิบที่สุดที่มีอยู่"),
    ("ข้อจำกัด", "17 features ใน 03_PAIRS เป็น Stage 9 v2 snapshot; ไม่ใช่ selected 41 features ของ multimodal main run"),
]
for row_no, (label, description) in enumerate(guide_rows, 2):
    guide.write(row_no, 0, label, header)
    guide.write(row_no, 1, description, note)
    guide.set_row(row_no, 32)

table("01_RAW_PROFILES", ["source_row", *raw.columns],
      ((i + 2, *values) for i, values in enumerate(raw.itertuples(index=False, name=None))), len(raw))
table("02_CLEAN_PROFILES", ["source_row", *clean.columns],
      ((i + 2, *values) for i, values in enumerate(clean.itertuples(index=False, name=None))), len(clean))

pair_columns = ["feature_row", "profile_id_a", "profile_id_b", "entity_id_a", "label"]
for suffix in ("a", "b"):
    pair_columns += [f"match_status_{suffix}", *(f"{field}_{suffix}" for field in side_fields)]
pair_columns += feature_columns

def pair_rows():
    for i, values in enumerate(pairs.itertuples(index=False, name=None), 2):
        a, b, entity, label, *features = values
        yield [i, a, b, entity, label, *side(a), *side(b), *features]

table("03_PAIRS", pair_columns, pair_rows(), len(pairs))

feature_help = {
    "username_jaro": "ความคล้ายของ userName_clean A/B (คะแนนสูง = คล้าย)",
    "username_token_sort": "ความคล้ายของ userName_clean เมื่อเรียง token",
    "username_levenshtein": "ความคล้ายของ userName_clean ตามวิธี string ratio ใน Stage 9 v2",
    "username_both_empty": "1 เมื่อชื่อบัญชีที่ clean แล้วว่างทั้งสองฝั่ง",
    "fullname_jaro": "ความคล้ายของ fullName_clean A/B",
    "fullname_token_sort": "ความคล้ายของ fullName_clean เมื่อเรียง token",
    "fullname_levenshtein": "ความคล้ายของ fullName_clean ตามวิธี string ratio ใน Stage 9 v2",
    "fullname_both_empty": "1 เมื่อชื่อแสดงที่ clean แล้วว่างทั้งสองฝั่ง",
    "bio_jaro": "ความคล้ายของ bio_clean A/B",
    "bio_token_sort": "ความคล้ายของ bio_clean เมื่อเรียง token",
    "bio_levenshtein": "ความคล้ายของ bio_clean ตามวิธี string ratio ใน Stage 9 v2",
    "bio_both_empty": "1 เมื่อ bio ที่ clean แล้วว่างทั้งสองฝั่ง",
    "bio_tfidf_cosine": "cosine similarity ระหว่าง bio ใน TF-IDF space",
    "url_exact_match": "1 เมื่อ URL ตรงกันตามกฎ Stage 9 v2",
    "url_domain_match": "1 เมื่อโดเมน URL ตรงกันตามกฎ Stage 9 v2",
    "same_platform": "1 เมื่อโปรไฟล์สองฝั่งมาจากแพลตฟอร์มเดียวกัน",
    "location_sim": "ความคล้ายของ location_clean A/B",
}
assert set(feature_help) == set(feature_columns)
table("04_FEATURE_GUIDE", ["column", "meaning"],
      ((column, feature_help[column]) for column in feature_columns), len(feature_columns))
table("05_IMAGE_PROFILES", list(image_profiles.columns),
      image_profiles.itertuples(index=False, name=None), len(image_profiles))
table("06_IMAGE_FEATURES", list(image_features.columns),
      image_features.itertuples(index=False, name=None), len(image_features))

workbook.close()
OUTPUT.with_suffix(".tmp.xlsx").replace(OUTPUT)
print(f"Created {OUTPUT} ({OUTPUT.stat().st_size / 1024**2:.1f} MB)")
