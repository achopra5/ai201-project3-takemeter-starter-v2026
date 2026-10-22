"""Unit 6 regressions. Human decisions are simulated only in temporary fixtures."""
import copy
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import import_staff_review as importer
import staff_agreement_workflow as workflow
import check_submission
import unit6_experiment


def fixture(root):
    (root / 'data').mkdir()
    for name in ('staff_posts.csv', 'staff_taxonomy.md'):
        shutil.copyfile(ROOT / 'data' / name, root / 'data' / name)
    shutil.copyfile(ROOT / 'staff_review.xlsx', root / 'staff_review.xlsx')


def edited_workbook(source, target, changes):
    """Patch disposable test XML; never touch the delivered workbook."""
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(target, 'w') as new:
        for info in old.infolist():
            data = old.read(info.filename)
            if info.filename == 'xl/worksheets/sheet1.xml':
                xml = ET.fromstring(data)
                sheet_data = xml.find('x:sheetData', importer.NS)
                for address, value in changes.items():
                    row_number = ''.join(c for c in address if c.isdigit())
                    row = next(r for r in sheet_data if r.attrib['r'] == row_number)
                    cell = next((c for c in row if c.attrib['r'] == address), None)
                    if cell is None:
                        cell = ET.SubElement(row, f"{{{importer.NS['x']}}}c", {'r': address})
                    for child in list(cell):
                        cell.remove(child)
                    cell.attrib['t'] = 'inlineStr'
                    inner = ET.SubElement(cell, f"{{{importer.NS['x']}}}is")
                    ET.SubElement(inner, f"{{{importer.NS['x']}}}t").text = value
                data = ET.tostring(xml)
            new.writestr(info, data)


class StaffSpreadsheetTests(unittest.TestCase):
    def test_delivered_template_exact_texts_empty_labels_dropdowns_and_rules(self):
        rows = importer.validate_workbook(ROOT / 'staff_review.xlsx', template=True)
        self.assertEqual(len(rows), 30)
        self.assertTrue(all(r['label'] == '' for r in rows))

    def test_blank_workbook_cannot_export_partial_or_invented_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            with self.assertRaisesRegex(ValueError, 'still blank'):
                importer.convert(root / 'staff_review.xlsx', root)
            self.assertFalse((root / 'my_staff_labels.csv').exists())

    def test_import_preserves_every_character_and_only_exports_two_columns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            returned = root / 'returned_TEST_ONLY.xlsx'
            edited_workbook(root / 'staff_review.xlsx', returned,
                            {f'C{i}': importer.LABELS[i % 3] for i in range(2,32)})
            output = importer.convert(returned, root)
            with output.open(newline='') as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, ['text', 'label'])
                exported = list(reader)
            originals = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
            self.assertEqual([r['text'] for r in exported], [r['text'] for r in originals])
            self.assertEqual(len(exported), 30)
            self.assertEqual(output, importer.convert(returned, root))

    def test_import_rejects_changed_text_duplicate_ids_and_mixed_taxonomy(self):
        for changes, message in [({'B2': 'Altered original text'}, 'original ID/text'),
                                 ({'A3': 'sp_001'}, 'original ID/text'),
                                 ({'C2': 'technical_report'}, 'choose exactly')]:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'TEST_ONLY.xlsx'
                edited_workbook(ROOT / 'staff_review.xlsx', target, changes)
                with self.assertRaisesRegex(ValueError, message):
                    importer.validate_workbook(target)

    def test_missing_reference_cannot_be_opened_before_human_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            with self.assertRaises(FileNotFoundError) as error:
                workflow.inputs(root)
            self.assertIn('label_import.json', str(error.exception))

    def test_explicit_message_selections_import_without_fabricating_workbook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            posts = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
            source = root / 'TEST_ONLY_selections.csv'
            workflow.write_csv(source, [{'id': p['id'], 'my_label': importer.LABELS[i%3],
                                        'reason': 'TEST FIXTURE ONLY'} for i,p in enumerate(posts)], ['id','my_label','reason'])
            output = importer.convert_id_labels(source, root)
            saved_posts, saved_labels = workflow.label_inputs(root)
            self.assertEqual([r['text'] for r in saved_labels], [p['text'] for p in posts])
            self.assertEqual([r['label'] for r in saved_labels], [importer.LABELS[i%3] for i in range(30)])
            self.assertFalse((root / 'data/staff_review/completed_review.xlsx').exists())
            self.assertFalse((root / 'agreement_results.json').exists())
            record = json.loads((root / 'data/staff_review/label_import.json').read_text())
            self.assertEqual(record['source_kind'], 'user_message_transcription')
            self.assertNotIn('workbook_sha256', record)
            self.assertEqual(importer.convert_id_labels(source, root), output)

    def test_message_selection_import_rejects_partial_duplicate_and_wrong_taxonomy(self):
        for mode in ['partial','duplicate','wrong_taxonomy']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fixture(root)
                posts = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
                rows = [{'id': p['id'], 'my_label': 'analysis'} for p in posts]
                if mode == 'partial': rows.pop()
                elif mode == 'duplicate': rows[-1]['id'] = rows[0]['id']
                else: rows[0]['my_label'] = 'technical_report'
                source = root / 'TEST_ONLY.csv'
                workflow.write_csv(source, rows, ['id','my_label'])
                with self.assertRaises(ValueError):
                    importer.convert_id_labels(source, root)
                self.assertFalse((root / 'my_staff_labels.csv').exists())

    def test_changed_message_evidence_is_rejected_before_reference_is_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            posts = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
            source = root / 'TEST_ONLY.csv'
            workflow.write_csv(source, [{'id': p['id'], 'my_label': 'analysis'} for p in posts], ['id','my_label'])
            importer.convert_id_labels(source, root)
            snapshot = root / 'data/staff_review/submitted_labels.csv'
            snapshot.write_text(snapshot.read_text().replace('analysis','reaction',1))
            with self.assertRaisesRegex(ValueError,'labeling evidence changed'):
                workflow.inputs(root)

    def test_complete_file_workflow_preserves_original_decisions_and_needs_approvals(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root)
            returned = root / 'TEST_ONLY_returned.xlsx'
            edited_workbook(root / 'staff_review.xlsx', returned,
                            {f'C{i}': importer.LABELS[i % 3] for i in range(2,32)})
            output = importer.convert(returned, root)
            frozen = output.read_bytes()
            posts = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
            # Artificial reference fixture, never a claim about staff answers.
            workflow.write_csv(root / 'data/staff_labels.csv', [
                {'id': p['id'], 'label': 'analysis'} for p in posts], ['id','label'])
            result = workflow.prepare(root, reference_source='SYNTHETIC TEST FIXTURE ONLY')
            self.assertEqual(result['compared'], 30)
            self.assertFalse(result['adjudication_complete'])
            review = list(csv.DictReader((root / 'staff_adjudication_review.csv').open(newline='')))
            self.assertTrue(all(not r['human_approved'] and not r['final_label'] for r in review))
            with self.assertRaisesRegex(ValueError, 'valid final label'):
                workflow.import_adjudications(root / 'staff_adjudication_review.csv', root)
            self.assertEqual(output.read_bytes(), frozen)
            for row in review:
                row.update(final_label=row['my_original_label'], pile='c', rule='1',
                           rationale='TEST FIXTURE ONLY', human_approved='yes')
            workflow.write_csv(root / 'returned_adjudications_TEST_ONLY.csv', review, workflow.FIELDS)
            workflow.import_adjudications(root / 'returned_adjudications_TEST_ONLY.csv', root)
            self.assertTrue(json.loads((root / 'agreement_results.json').read_text())['adjudication_complete'])
            self.assertEqual(output.read_bytes(), frozen)

    def test_no_automatic_adjudication_or_approval(self):
        result = {'disagreements': [{'id': 'TEST_ONLY', 'text': 'Synthetic test text', 'mine': 'analysis', 'staff': 'hot_take'}]}
        row = {'id': 'TEST_ONLY', 'text': 'Synthetic test text', 'my_original_label': 'analysis',
               'staff_label': 'hot_take', 'final_label': 'analysis', 'pile': 'c', 'rule': '1',
               'rationale': 'TEST FIXTURE ONLY; not a student decision.', 'proposed_rule': '', 'human_approved': ''}
        with self.assertRaisesRegex(ValueError, 'explicit human_approved'):
            workflow.validate_adjudications([row], result)
        row['human_approved'] = 'yes'
        self.assertEqual(len(workflow.validate_adjudications([row], result)), 1)
        row['final_label'] = 'technical_report'
        with self.assertRaisesRegex(ValueError, 'valid final label'):
            workflow.validate_adjudications([row], result)

    def test_gap_requires_rule_and_original_decisions_cannot_be_rewritten(self):
        result = {'disagreements': [{'id': 'TEST', 'text': 'Synthetic', 'mine': 'analysis', 'staff': 'hot_take'}]}
        row = {'id': 'TEST', 'text': 'Synthetic', 'my_original_label': 'analysis', 'staff_label': 'hot_take',
               'final_label': 'reaction', 'pile': 'b', 'rule': 'gap', 'rationale': 'TEST ONLY', 'proposed_rule': '', 'human_approved': 'yes'}
        with self.assertRaisesRegex(ValueError, 'proposed rule'):
            workflow.validate_adjudications([row], result)
        row['text'] = 'Changed'
        with self.assertRaisesRegex(ValueError, 'evidence was changed'):
            workflow.validate_adjudications([row], result)


class Unit6IntegrityTests(unittest.TestCase):
    def test_notebook_is_extracted_as_functions_without_executing_cells(self):
        import ast
        tree = unit6_experiment.notebook_definitions(ROOT / 'takemeter.ipynb')
        self.assertTrue(all(isinstance(n, ast.FunctionDef) for n in tree.body))
        self.assertEqual({n.name for n in tree.body}, unit6_experiment.FUNCTIONS)

    def test_rejects_wrong_scheduler_horizon_before_training(self):
        from types import SimpleNamespace
        args = SimpleNamespace(num_train_epochs=8)
        with self.assertRaisesRegex(ValueError, 'num_train_epochs'):
            unit6_experiment.check_recipe(args, 42)

    def test_original_hashes_are_preserved_and_only_definition_evolution_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'submission').mkdir()
            (root / 'submission/unit6_manifest.json').write_text(json.dumps({'unit5_evolution': {'labels.csv': {}}}))
            with self.assertRaisesRegex(ValueError, 'Unsupported frozen-evidence exception'):
                check_submission.verify_historical_closeout(root, {'protected_sha256': {}})

    def test_changed_historical_definition_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'submission/unit5_originals').mkdir(parents=True)
            (root / 'submission/unit5_originals/label_definitions.txt').write_text('tampered')
            (root / 'label_definitions.txt').write_text('new definitions')
            transition = {'historical_sha256': 'original-digest', 'original_snapshot': 'submission/unit5_originals/label_definitions.txt',
                          'unit6_sha256': 'new-digest'}
            (root / 'submission/unit6_manifest.json').write_text(json.dumps({'unit5_evolution': {'label_definitions.txt': transition}}))
            with self.assertRaisesRegex(ValueError, 'Historical Unit 5 snapshot changed'):
                check_submission.verify_historical_closeout(root, {'protected_sha256': {'label_definitions.txt': 'original-digest'}})

    def test_baseline_and_all_training_use_original_four_labels(self):
        baseline = json.loads((ROOT / 'baseline_results.json').read_text())
        self.assertEqual(set(baseline['scores']['per_label']), set(unit6_experiment.LABELS))
        for name in ('results_three_seeds_before.json', 'results_three_seeds_after.json'):
            for result in json.loads((ROOT / name).read_text()):
                self.assertEqual(set(result['per_label']), set(unit6_experiment.LABELS))
                self.assertEqual(set(result['confusion']), set(unit6_experiment.LABELS))
        self.assertTrue(set(importer.LABELS).isdisjoint(unit6_experiment.LABELS))


if __name__ == '__main__':
    unittest.main()
