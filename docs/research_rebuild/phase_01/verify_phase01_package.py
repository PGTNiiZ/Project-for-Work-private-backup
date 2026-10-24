"""Read-only source verification and isolated audit package validation."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REQUIRED = ['00_START_HERE_TH.md', '01_DATASET_AND_FEATURE_LINEAGE.md', '02_HISTORICAL_EXPERIMENT_MATRIX.md', '03_MODEL_AND_GA_EXPLANATION_TH.md', '04_RESULT_COMPARISON_TH.md', '05_DATA_AND_EXPERIMENT_LIMITATIONS.md', '06_PHASE_1_READINESS_GATE.md']

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()

for name in REQUIRED:
    assert (OUT / name).is_file() and (OUT / name).stat().st_size > 1000, name
for p in OUT.glob('*.py'):
    ast.parse(p.read_text(), filename=str(p))
for p in OUT.glob('*.json'):
    json.loads(p.read_text())

inventory = json.loads((OUT / 'dataset_inventory.json').read_text())
source_count = 0
for row in inventory:
    if row.get('exists') and row.get('sha256'):
        assert digest(ROOT / row['path']) == row['sha256'], row['path']
        source_count += 1
metrics = json.loads((OUT / 'verified_metrics.json').read_text())
for path, item in metrics['source_hashes'].items():
    assert digest(ROOT / path) == item['sha256'], path
assert all(c['pass'] for c in metrics['checks'])
assert all(c['agrees'] for c in metrics['summary_comparisons'])
assert len(metrics['metrics']) == metrics['metric_rows'] == 221
lineage = json.loads((OUT / 'experiment_lineage.json').read_text())
assert len(lineage['experiments']) == lineage['row_count'] == 1077
lineage_source_count = 0
for item in lineage['source_artifacts']:
    if item.get('exists') and item.get('sha256'):
        assert digest(ROOT / item['path']) == item['sha256'], item['path']
        lineage_source_count += 1
links = json.loads((OUT / 'lineage_metric_evidence_links.json').read_text())
assert len(links) == 48
metric_index = {(r['family'], str(r['partition']), r['method'], r['scope']): r for r in metrics['metrics']}
for link in links:
    target = metric_index[(link['family'], link['partition'], link['method'], link['scope'])]
    assert target['artifact'] == link['granular_artifact'] and target['status'] == link['numeric_evidence_status']
for row in lineage['experiments']:
    assert all(k in row for k in ['experiment_id', 'dataset', 'split', 'candidate_population', 'features', 'model', 'calibration', 'policy', 'metrics', 'results', 'source', 'status'])
books = json.loads((OUT / 'workbook_evidence.json').read_text())
assert len(books) == 6 and all(e['status'] == 'AVAILABLE' for e in books)
for book in books:
    assert digest(ROOT / book['path']) == book['sha256']
    for s in book['sheets']:
        if s['export_policy'] == 'header_only_no_personal_rows':
            assert all(re.fullmatch(r'[A-Z]+1', c['cell']) for c in s['cells'])
with (OUT / 'transformation_verification.csv').open(encoding='utf-8-sig') as f:
    transforms = list(csv.DictReader(f))
for name, key in [('dataset_inventory.csv', 'inventory'), ('verified_metrics.csv', 'metrics'), ('experiment_lineage.csv', 'lineage')]:
    with (OUT / name).open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == {'inventory': len(inventory), 'metrics': 221, 'lineage': 1077}[key]
accounting = json.loads((OUT / 'dataset_candidate_accounting.json').read_text())['canonical_candidate_accounting']
assert all(accounting['invariants'].values())
assert accounting['exact'] + accounting['scored'] == accounting['workflow']
assert accounting['covered_positive'] + accounting['missed_positive'] == accounting['cross_platform_positives']
# No raw field values should have been exported by the read-only workbook reader.
privacy_scan = []
for book in books:
    for sheet in book['sheets']:
        for c in sheet['cells']:
            value = str(c.get('value') or '')
            if re.search(r'https?://(?:twitter|instagram|plus\.google)\.', value, re.I):
                privacy_scan.append({'book': book['name'], 'sheet': sheet['name'], 'cell': c['cell']})
assert not privacy_scan, 'personal platform URL found in workbook export'
result = {'required_markdown_files': len(REQUIRED), 'all_required_files_present': True,
          'dataset_inventory_records': len(inventory), 'dataset_source_hashes_verified': source_count,
          'lineage_records': lineage['row_count'], 'lineage_source_hashes_verified': lineage_source_count,
          'lineage_metric_evidence_links_verified': len(links), 'metric_records': metrics['metric_rows'],
          'metric_checks_passed': len(metrics['checks']), 'summary_comparisons_agreed': len(metrics['summary_comparisons']),
          'metric_source_hashes_verified': len(metrics['source_hashes']), 'required_workbooks_available_and_hashed': len(books),
          'workbook_sheets_scanned': sum(len(e['sheets']) for e in books),
          'transformation_checks': len(transforms), 'transformation_status_counts': dict(Counter(r['status'] for r in transforms)),
          'candidate_accounting_invariants_pass': True, 'audit_script_syntax_pass': True,
          'workbook_header_only_policy_pass': True, 'platform_personal_url_scan_hits': 0,
          'privacy_scope': 'No full automated semantic PII certification; report outputs reviewed as aggregate/code/schema metadata.',
          'scientific_status': 'PHASE_1_PARTIAL_PHASE_2_BLOCKED',
          'git_branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()}
(OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
manifest = {str(p.relative_to(OUT)): digest(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS.json' and '__pycache__' not in p.parts}
(OUT / 'SHA256SUMS.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
assert all(digest(OUT / path) == h for path, h in manifest.items())
print(json.dumps(result | {'final_deliverable_hashes_verified': len(manifest)}, ensure_ascii=False, indent=2))
