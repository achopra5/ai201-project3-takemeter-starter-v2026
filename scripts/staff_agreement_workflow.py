#!/usr/bin/env python3
"""Prepare file-based staff comparison and validate returned adjudication decisions.

For the agent after the student returns the workbook/reference files. There is
no interactive review mode, prediction, suggested label or automatic approval.
"""
import argparse
import csv
import io
import json
from pathlib import Path

from import_staff_review import ROOT, LABELS, sha
from validation_experiment import save_json

PILES = {'a': 'The rule covered it; I applied it loosely',
         'b': 'A taxonomy gap: the rule does not settle it',
         'c': 'Two defensible readings; my original reading holds up'}
FIELDS = ['id', 'text', 'my_original_label', 'staff_label', 'final_label', 'pile',
          'rule', 'rationale', 'proposed_rule', 'human_approved']


def write_csv(path, rows, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(out.getvalue().encode())


def inputs(root):
    record = json.loads((root / 'data/staff_review/label_import.json').read_text())
    for name, key in [('my_staff_labels.csv', 'csv_sha256'), ('data/staff_posts.csv', 'posts_sha256'),
                      ('data/staff_taxonomy.md', 'taxonomy_sha256'),
                      ('data/staff_review/completed_review.xlsx', 'workbook_sha256')]:
        if sha(root / name) != record[key]:
            raise ValueError(f'Independent labeling evidence changed: {name}')
    posts = list(csv.DictReader((root / 'data/staff_posts.csv').open(newline='')))
    mine = list(csv.DictReader((root / 'my_staff_labels.csv').open(newline='')))
    if len(mine) != 30 or [r['text'] for r in mine] != [r['text'] for r in posts]:
        raise ValueError('Exactly 30 unchanged human-labeled texts are required')
    if any(r['label'] not in LABELS for r in mine):
        raise ValueError('Missing or invalid independent label')
    # Only after validating complete independent labels do we read staff answers.
    staff_rows = list(csv.DictReader((root / 'data/staff_labels.csv').open(newline='', encoding='utf-8-sig')))
    staff = {}
    texts = {p['id']: p['text'] for p in posts}
    for row in staff_rows:
        label = row.get('label', row.get('staff_label', ''))
        if row.get('id') in staff or label not in LABELS:
            raise ValueError('Duplicate staff ID or invalid reference label')
        if 'text' in row and row['text'] != texts.get(row.get('id')):
            raise ValueError('Reference text differs from the original staff post')
        staff[row.get('id')] = label
    if set(staff) != {r['id'] for r in posts}:
        raise ValueError('The authentic reference must cover all 30 staff post IDs exactly')
    return posts, mine, staff


def prepare(root=ROOT, reference_source=''):
    if not reference_source.strip():
        raise ValueError('Record where the student obtained the authentic TF reference file')
    posts, mine, staff = inputs(root)
    differences = [{**post, 'mine': human['label'], 'staff': staff[post['id']]}
                   for post, human in zip(posts, mine) if human['label'] != staff[post['id']]]
    result = {'compared': 30, 'agreed': 30-len(differences), 'agreement_rate': (30-len(differences))/30,
              'disagreements': differences, 'staff_posts_not_in_mine': 0,
              'mine_sha256': sha(root / 'my_staff_labels.csv'),
              'staff_sha256': sha(root / 'data/staff_labels.csv'),
              'taxonomy_sha256': sha(root / 'data/staff_taxonomy.md'),
              'reference_source': reference_source.strip(),
              'reference_authentication': 'Student-supplied TF provenance, not independently authenticated by the utility',
              'adjudication_complete': not differences, 'adjudications_approved': 0,
              'criterion5': 'PASS' if 30-len(differences) >= 23 else 'FAIL'}
    target = root / 'agreement_results.json'
    if target.exists():
        raise ValueError('Comparison already saved; preserve original results before changing inputs')
    save_json(target, result)
    if differences:
        write_csv(root / 'staff_adjudication_review.csv', [
            {**{k: '' for k in FIELDS}, 'id': d['id'], 'text': d['text'],
             'my_original_label': d['mine'], 'staff_label': d['staff']} for d in differences], FIELDS)
    render_report(root, result, [])
    return result


def validate_adjudications(rows, result):
    expected = {d['id']: d for d in result['disagreements']}
    decisions = {}
    for row in rows:
        post_id = row.get('id')
        if post_id not in expected or post_id in decisions:
            raise ValueError('Adjudication IDs must cover each disagreement exactly once')
        original = expected[post_id]
        if (row.get('text'), row.get('my_original_label'), row.get('staff_label')) != (original['text'], original['mine'], original['staff']):
            raise ValueError('Original disagreement evidence was changed')
        if row.get('final_label') not in LABELS or row.get('pile') not in PILES or row.get('rule') not in ('1', '2', '3', '4', 'gap'):
            raise ValueError('Choose a valid final label, pile and taxonomy rule')
        if not row.get('rationale', '').strip() or row.get('human_approved') != 'yes':
            raise ValueError('Each final adjudication needs personal reasoning and explicit human_approved=yes')
        if row['pile'] == 'b' and not row.get('proposed_rule', '').strip():
            raise ValueError('A taxonomy gap requires a proposed rule')
        if row['pile'] == 'a' and row['final_label'] != original['staff']:
            raise ValueError('Pile a means the original rule supports staff')
        if row['pile'] == 'c' and row['final_label'] != original['mine']:
            raise ValueError('Pile c means the original human reading holds up')
        decisions[post_id] = row
    if set(decisions) != set(expected):
        raise ValueError('Every disagreement must have a final human-approved decision')
    return list(decisions.values())


def render_report(root, result, decisions):
    lines = ['# Staff agreement and adjudication', '',
             f"Original agreement: {result['agreed']}/30 ({result['agreement_rate']:.1%}). Criterion 5: **{result['criterion5']}**.", '',
             f"Human-approved adjudications: {len(decisions)}/{len(result['disagreements'])}.", '',
             'Agreement always uses the original independent labels, before adjudication. Staff labels are a second opinion, not an unquestionable answer key.', '',
             'The running-forum staff taxonomy is independent of the four-category r/LocalLLaMA taxonomy. There is no direct mapping between their label pairs; this does not measure consistency on the 200 TakeMeter posts.', '']
    by_id = {r['id']: r for r in decisions}
    for row in result['disagreements']:
        lines += [f"## {row['id']}", '', row['text'], '', f"Original human label: `{row['mine']}`. Staff: `{row['staff']}`.", '']
        d = by_id.get(row['id'])
        if d:
            lines += [f"Final human-approved label: `{d['final_label']}`. Pile {d['pile']}: {PILES[d['pile']]}. Rule: {d['rule']}.", '', d['rationale'], '']
            if d.get('proposed_rule'):
                lines += ['Proposed rule: ' + d['proposed_rule'], '']
        else:
            lines += ['Awaiting the student’s reasoning and explicit approval in the review file.', '']
    (root / 'staff_agreement_report.md').write_text('\n'.join(lines))


def import_adjudications(path, root=ROOT):
    inputs(root)
    result = json.loads((root / 'agreement_results.json').read_text())
    if sha(root / 'my_staff_labels.csv') != result['mine_sha256'] or sha(root / 'data/staff_labels.csv') != result['staff_sha256']:
        raise ValueError('Original comparison evidence changed')
    rows = list(csv.DictReader(Path(path).open(newline='', encoding='utf-8-sig')))
    decisions = validate_adjudications(rows, result)
    target = root / 'data/staff_review/approved_adjudications.json'
    if target.exists():
        raise ValueError('Approved decisions already saved; preserve them before importing revisions')
    save_json(target, {'review_file_sha256': sha(path), 'decisions': decisions,
                      'provenance': 'Imported explicit approvals from the student-returned review file'})
    result.update(adjudication_complete=True, adjudications_approved=len(decisions), adjudication_sha256=sha(target))
    save_json(root / 'agreement_results.json', result)
    render_report(root, result, decisions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'import-adjudications'])
    parser.add_argument('--reference-source', default='')
    parser.add_argument('--review-file', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(reference_source=args.reference_source)
    elif args.review_file:
        import_adjudications(args.review_file)
    else:
        parser.error('A returned review file is required')


if __name__ == '__main__':
    main()
