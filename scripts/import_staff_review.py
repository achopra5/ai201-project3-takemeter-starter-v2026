#!/usr/bin/env python3
"""Validate a returned workbook and export the student's exact selections.

This is a file converter, not a review interface. Reads XLSX with standard-library
OOXML parsing, so no Excel or additional Python package is required.
"""
import argparse
import csv
import hashlib
import io
import json
import posixpath
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("analysis", "hot_take", "reaction")
NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sheets(path):
    """Read literal cells only; preserve Unicode and whitespace exactly."""
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 20_000_000:
            raise ValueError("Unexpected oversized review workbook")
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(t.text or '' for t in n.findall('.//x:t', NS))
                       for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        relationships = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('x:sheets/x:sheet', NS):
            target = relationships[sheet.attrib[f"{{{NS['r']}}}id"]]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            xml = ET.fromstring(z.read(target))
            cells = {}
            for cell in xml.findall('.//x:sheetData/x:row/x:c', NS):
                if cell.find('x:f', NS) is not None:
                    raise ValueError("Review workbooks must contain selections, not formulas")
                kind = cell.attrib.get('t')
                value = cell.findtext('x:v', '', NS)
                if kind == 's':
                    value = strings[int(value)]
                elif kind == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.findall('.//x:t', NS))
                cells[cell.attrib['r']] = value
            result[sheet.attrib['name']] = (cells, xml)
        return result


def validate_workbook(path, root=ROOT, template=False):
    book = sheets(path)
    if set(book) != {'Staff posts', 'Staff taxonomy'}:
        raise ValueError("Keep the Staff posts and Staff taxonomy worksheets")
    cells, xml = book['Staff posts']
    if [cells.get(f'{c}1') for c in 'ABC'] != ['id', 'text', 'my_label']:
        raise ValueError("Keep the id, text and my_label column headers unchanged")
    original = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
    by_id = {r['id']: r['text'] for r in original}
    reviewed, missing, seen = {}, [], set()
    for i in range(2, 32):
        post_id, text, label = (cells.get(f'{c}{i}', '') for c in 'ABC')
        if post_id in seen or post_id not in by_id or by_id[post_id] != text:
            raise ValueError(f"Row {i}: original ID/text changed, missing or duplicated")
        seen.add(post_id)
        if template:
            if label != '':
                raise ValueError("The review template must leave every label blank")
        elif not label:
            missing.append(f'C{i} ({post_id})')
        elif label not in LABELS:
            raise ValueError(f"Row {i}: choose exactly analysis, hot_take or reaction")
        reviewed[post_id] = label
    if seen != set(by_id) or any(value for address, value in cells.items() if int(''.join(c for c in address if c.isdigit())) > 31):
        raise ValueError("Workbook must contain exactly the original 30 rows")
    if missing:
        raise ValueError("Labels are still blank: " + ', '.join(missing))
    taxonomy = (root / 'data/staff_taxonomy.md').read_text()
    rule_cells = book['Staff taxonomy'][0]
    actual = '\n'.join(rule_cells.get(f'A{i+1}', '') for i in range(len(taxonomy.split('\n'))))
    if actual != taxonomy:
        raise ValueError("Staff taxonomy changed; preserve the original rules")
    if template:
        rules = xml.findall('x:dataValidations/x:dataValidation', NS)
        covered = set()
        for rule in rules:
            if rule.attrib.get('type') != 'list':
                raise ValueError("Expected the three-choice label dropdown")
            if rule.findtext('x:formula1', '', NS) != '"analysis,hot_take,reaction"':
                raise ValueError("Dropdown choices differ from the staff taxonomy")
            for address in rule.attrib['sqref'].split():
                start, _, end = address.partition(':')
                if not start.startswith('C') or (end and not end.startswith('C')):
                    raise ValueError("Dropdown belongs only on label input cells")
                covered.update(range(int(start[1:]), int((end or start)[1:]) + 1))
        if covered != set(range(2, 32)):
            raise ValueError("All 30 label cells require a dropdown")
    return [{'text': r['text'], 'label': reviewed[r['id']]} for r in original]


def convert(path, root=ROOT):
    rows = validate_workbook(path, root)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=['text', 'label'])
    writer.writeheader()
    writer.writerows(rows)
    output = root / 'my_staff_labels.csv'
    if output.exists() and output.read_bytes() != out.getvalue().encode():
        raise ValueError("A different my_staff_labels.csv exists; preserve it before exporting revised decisions")
    directory = root / 'data/staff_review'
    directory.mkdir(parents=True, exist_ok=True)
    record = directory / 'label_import.json'
    if record.exists():
        previous = json.loads(record.read_text())
        if sha(path) != previous['workbook_sha256']:
            raise ValueError("A different workbook was already imported; preserve the original decisions")
        if not output.exists() or sha(output) != previous['csv_sha256']:
            raise ValueError("Imported CSV changed after conversion")
        return output
    output.write_bytes(out.getvalue().encode())
    snapshot = directory / 'completed_review.xlsx'
    shutil.copyfile(path, snapshot)
    record.write_text(json.dumps({'imported_utc': datetime.now(timezone.utc).isoformat(),
        'source': Path(path).name, 'workbook_sha256': sha(path), 'csv_sha256': sha(output),
        'posts_sha256': sha(root / 'data/staff_posts.csv'),
        'taxonomy_sha256': sha(root / 'data/staff_taxonomy.md'), 'count': 30,
        'provenance': 'Selections imported from the returned workbook; no labels generated by this utility.'}, indent=2) + '\n')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook', type=Path)
    parser.add_argument('--validate-template', action='store_true')
    args = parser.parse_args()
    if args.validate_template:
        validate_workbook(args.workbook, template=True)
        print('Verified: 30 exact original posts, blank labels, three-choice dropdowns and unchanged full taxonomy.')
    else:
        print(convert(args.workbook))


if __name__ == '__main__':
    main()
