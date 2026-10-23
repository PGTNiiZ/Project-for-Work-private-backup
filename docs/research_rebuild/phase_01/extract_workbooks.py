"""Read-only bounded-memory OOXML audit. Data rows never exported."""
from pathlib import Path
import csv
import hashlib
import json
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
N = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
required = ['01_multimodal_and_GA.xlsx', '01b_GA_full_feature_to_decision.xlsx', '02_ICSEC_model_inputs.xlsx', '04_source_artifact_catalog.xlsx', '05_R0_R6_experiment_history.xlsx', '07_dataset_raw_to_features.xlsx']
result = []
for name in required:
    paths = [p for p in [ROOT / 'thesis_rebuild' / name, ROOT / 'thesis_rebuild' / 'experiment_excel' / name] if p.is_file()]
    if not paths:
        result.append({'name': name, 'status': 'MISSING_IN_REPOSITORY'})
    for p in paths:
        h = hashlib.sha256()
        with p.open('rb') as f:
            while block := f.read(1024 * 1024):
                h.update(block)
        entry = {'name': name, 'path': str(p.relative_to(ROOT)), 'sha256': h.hexdigest(), 'status': 'AVAILABLE', 'sheets': []}
        print('READING', name, flush=True)
        with zipfile.ZipFile(p) as z:
            strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                raise RuntimeError('Shared strings require explicit safe adapter; exports expected inline strings')
            relationships = {x.attrib['Id']: x.attrib['Target'] for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
            for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet', N):
                target = relationships[s.attrib['{' + R + '}id']]
                target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
                metadata = (z.getinfo(target).file_size < 250000 and not any(token in s.attrib['name'].upper() for token in ('EXAMPLE', 'PROFILE', 'PAIR', 'INPUT', 'DECISION', 'LABEL')))
                sheet = {'name': s.attrib['name'], 'xml_bytes': z.getinfo(target).file_size, 'cells': [], 'rows': 0, 'serialized_cells': 0, 'formulas': 0, 'export_policy': 'metadata_cells' if metadata else 'header_only_no_personal_rows'}
                first = b''
                tail = b''
                patterns = [re.compile(rb'<row\b'), re.compile(rb'<c\b'), re.compile(rb'<f(?:\s|>)')]
                with z.open(target) as stream:
                    while block := stream.read(4 * 1024 * 1024):
                        data = tail + block
                        for key, pat in zip(['rows', 'serialized_cells', 'formulas'], patterns):
                            sheet[key] += sum(m.end() > len(tail) for m in pat.finditer(data))
                        tail = data[-128:]
                        if metadata:
                            first += block
                        elif b'</row>' not in first:
                            first += block
                if metadata:
                    cells = ET.fromstring(first).findall('.//m:sheetData/m:row/m:c', N)
                else:
                    a = first.index(b'<row')
                    b = first.index(b'</row>', a) + len(b'</row>')
                    cells = ET.fromstring(b'<root xmlns="' + N['m'].encode() + b'">' + first[a:b] + b'</root>').findall('m:row/m:c', N)
                for c in cells:
                    v = c.find('m:v', N)
                    text = v.text if v is not None else None
                    if c.attrib.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in c.findall('.//m:t', N))
                    f = c.find('m:f', N)
                    if text is not None or f is not None:
                        sheet['cells'].append({'cell': c.attrib['r'], 'value': text, 'formula': f.text if f is not None else None})
                entry['sheets'].append(sheet)
                print(sheet['name'], sheet['rows'], sheet['serialized_cells'], flush=True)
        result.append(entry)
        (OUT / 'workbook_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
with (OUT / 'workbook_inventory.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['name', 'path', 'sha256', 'status', 'sheets', 'serialized_cells', 'formulas'])
    w.writeheader()
    for e in result:
        w.writerow({**{k: e.get(k, '') for k in ['name', 'path', 'sha256', 'status']}, 'sheets': len(e.get('sheets', [])), 'serialized_cells': sum(s['serialized_cells'] for s in e.get('sheets', [])), 'formulas': sum(s['formulas'] for s in e.get('sheets', []))})
print('COMPLETE', len(result), flush=True)
