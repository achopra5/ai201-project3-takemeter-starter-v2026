#!/usr/bin/env python3
"""Read-only Unit 6 integrity/metric validation; never trains or calls a model."""
import argparse
import csv
import json
from pathlib import Path

from check_submission import check_metrics, equal_number, require, verify_historical_closeout, markdown_checks
from import_staff_review import validate_workbook
from validation_experiment import ROOT, LABELS, SEEDS, sha, text_sha, split_indices, score, save_json


def inspect(root=ROOT):
    manifest = json.loads((root / 'submission/unit6_manifest.json').read_text())
    verify_historical_closeout(root, json.loads((root / 'submission/closeout_manifest.json').read_text()))
    for name, digest in manifest['artifact_sha256'].items():
        require(sha(root / name) == digest, f'Unit 6 saved evidence changed: {name}')
    import pandas as pd
    frame = pd.read_csv(root / 'labels.csv', keep_default_na=False)
    baseline = json.loads((root / 'baseline_results.json').read_text())
    held = list(csv.DictReader((root / 'test_split.csv').open(newline='')))
    predictions = baseline['predictions']
    require(baseline['held_out'] and baseline['used_definitions'] and baseline['n'] == len(predictions) == 30, 'Incomplete baseline')
    require(all(a['text'] == b['text'] and a['gold'] == b['label'] for a,b in zip(predictions,held)), 'Baseline not on the saved test split')
    require(all(p['predicted'] in LABELS and p['gold'] in LABELS for p in predictions), 'Mixed baseline taxonomy')
    gold = [LABELS.index(p['gold']) for p in predictions]
    predicted = [LABELS.index(p['predicted']) for p in predictions]
    reconstructed = score(gold, predicted)
    check_metrics(baseline['scores'], reconstructed['confusion_matrix'])
    require(baseline['scores']['n'] == 30, 'Baseline support mismatch')
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location('baseline_check', root / 'baseline.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    definitions = module.load_definitions(root / 'label_definitions.txt')
    require(set(definitions) == set(LABELS), 'Baseline definitions must match the TakeMeter taxonomy')
    require(all(d in (root / 'README.md').read_text() for d in definitions.values()), 'Baseline definitions differ from original taxonomy')
    before = json.loads((root / 'results_three_seeds_before.json').read_text())
    after = json.loads((root / 'results_three_seeds_after.json').read_text())
    exp = root / 'experiments/unit6-length256-three-epochs'
    protocol = json.loads((exp / 'protocol.json').read_text())
    require(protocol['epochs'] == 3 and protocol['before_max_length'] == 128 and protocol['after_max_length'] == 256, 'Not the requested intervention')
    require(protocol['seeds'] == SEEDS and protocol['label_order'] == LABELS, 'Seeds or original labels changed')
    require(sha(exp / 'runner_used.py') == protocol['runner_sha256'], 'Archived runner changed')
    for name, digest in protocol['protected_sha256'].items():
        require(sha(root / name) == digest, f'Frozen experiment input changed: {name}')
    require([r['seed'] for r in after] == [r['seed'] for r in before] == SEEDS, 'Incomplete seed set')
    for old, new in zip(before, after):
        seed = new['seed']
        out = exp / 'runs' / f'seed{seed}'
        done, meta = [json.loads((out / n).read_text()) for n in ('complete.json', 'metadata.json')]
        for name, digest in done['sha256'].items():
            require(sha(out / name) == digest, f'Completed seed evidence changed: {name}')
        require(new == json.loads((out / 'result.json').read_text()), 'After results do not match completed runs')
        require(old['max_length'] == 128 and new['max_length'] == meta['max_length'] == 256, 'Length intervention mismatch')
        args = meta['training_args']
        require(args['num_train_epochs'] == meta['epochs'] == 3 and meta['global_step'] == 27 and meta['learning_rate_final'] == 0, 'Wrong schedule horizon')
        expected = {'learning_rate': 2e-5, 'per_device_train_batch_size': 16, 'per_device_eval_batch_size': 16,
                    'seed': seed, 'lr_scheduler_type': 'linear', 'optim': 'adamw_torch_fused',
                    'warmup_steps': 0, 'warmup_ratio': 0, 'gradient_accumulation_steps': 1,
                    'weight_decay': 0, 'load_best_model_at_end': False, 'max_steps': -1}
        require(all(args[k] == v for k,v in expected.items()), 'Training variable changed beyond input length')
        original_args = json.loads((root / f'experiments/validation-20261018T234742Z/runs/reference-len128-seed{seed}/metadata.json').read_text())['training_args']
        nontraining = {'output_dir', 'logging_dir'}
        require({k:v for k,v in args.items() if k not in nontraining} == {k:v for k,v in original_args.items() if k not in nontraining}, 'Full TrainingArguments differ from original three-epoch reference')
        require(protocol['splits'][str(seed)] == split_indices(frame, seed), 'Test split changed')
        rows = list(csv.DictReader((out / 'test_predictions.csv').open(newline='')))
        require([int(r['row_index']) for r in rows] == protocol['splits'][str(seed)]['test'], 'Prediction identities/order changed')
        for row in rows:
            idx = int(row['row_index'])
            require(row['gold'] == frame.loc[idx,'label'] and row['text_sha256'] == text_sha(frame.loc[idx,'text']), 'Saved prediction text/gold mismatch')
        matrix = [[new['confusion'][g][p] for p in LABELS] for g in LABELS]
        check_metrics(new, matrix)
        actual = score([LABELS.index(r['gold']) for r in rows], [LABELS.index(r['predicted']) for r in rows])
        require(actual['confusion_matrix'] == matrix, 'After predictions and metrics disagree')
        history = json.loads((out / 'history.json').read_text())
        require([h['epoch'] for h in history if 'eval_loss' in h] == [1., 2., 3.], 'Three-epoch execution history missing')
        require(meta['protocol_sha256'] == sha(exp / 'protocol.json'), 'Run protocol mismatch')
        checkpoint = out / 'epoch-3'
        if checkpoint.exists():
            require({p.name: sha(p) for p in checkpoint.iterdir() if p.is_file()} == meta['checkpoint_files_sha256'], 'Local after checkpoint changed')
    completion = json.loads((exp / 'complete.json').read_text())
    require(completion['optimizer_updates'] == 81 and completion['after_sha256'] == sha(root / 'results_three_seeds_after.json'), 'Final after artifact changed')
    validate_workbook(root / 'staff_review.xlsx', root=root, template=True)
    pending = ['Return independently completed staff_review.xlsx', 'Obtain authentic staff labels from TF', 'Adjudicate each disagreement and approve final decisions']
    staff_status = 'PENDING PERSONAL LABELS AND AUTHENTIC REFERENCE'
    if (root / 'agreement_results.json').exists():
        from staff_agreement_workflow import inputs, validate_adjudications
        posts, mine, reference = inputs(root)
        agreement = json.loads((root / 'agreement_results.json').read_text())
        expected_differences = [{**p, 'mine': r['label'], 'staff': reference[p['id']]}
                                for p,r in zip(posts,mine) if r['label'] != reference[p['id']]]
        require(agreement['disagreements'] == expected_differences, 'Staff disagreement evidence mismatch')
        require(agreement['mine_sha256'] == sha(root / 'my_staff_labels.csv') and
                agreement['staff_sha256'] == sha(root / 'data/staff_labels.csv'), 'Staff comparison source hashes changed')
        expected = sum(r['label'] == reference[p['id']] for p,r in zip(posts,mine))
        require(agreement['agreed'] == expected and agreement['compared'] == 30, 'Staff agreement count mismatch')
        equal_number(agreement['agreement_rate'], expected/30, 'Staff agreement rate')
        require(agreement['criterion5'] == ('PASS' if expected >= 23 else 'FAIL'), 'Staff criterion verdict mismatch')
        if agreement.get('adjudication_complete'):
            approved_path = root / 'data/staff_review/approved_adjudications.json'
            if agreement['disagreements']:
                require(sha(approved_path) == agreement['adjudication_sha256'], 'Human adjudication evidence changed')
                validate_adjudications(json.loads(approved_path.read_text())['decisions'], agreement)
            staff_status, pending = 'COMPLETE; NOT SUBMITTED TO COURSE PORTAL', []
        else:
            staff_status, pending = 'AGREEMENT MEASURED; HUMAN ADJUDICATION PENDING', [pending[-1]]
    return {'automated_work': 'VERIFIED', 'staff_exercise': staff_status, 'course_portal_submitted': False,
            'baseline_accuracy': baseline['scores']['accuracy'], 'baseline_macro_f1': baseline['scores']['f1_macro'],
            'original_mean': {k: sum(r[k] for r in before)/3 for k in ('accuracy','f1_macro')},
            'length_only_after_mean': {k: sum(r[k] for r in after)/3 for k in ('accuracy','f1_macro')},
            'new_completed_fits': 3, 'new_optimizer_updates': 81,
            'historical_unit5_hashes': 'Preserved; original starter definitions retained in the documented snapshot',
            'baseline_per_class_metrics': 'Recomputed from saved predictions',
            'after_metrics': 'Recomputed from saved predictions; identical test identities',
            'staff_template': '30 exact texts; all labels blank; all dropdowns verified; full taxonomy preserved',
            'pending_human_work': pending, 'markdown': markdown_checks(root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()
    result = inspect()
    if args.write_report:
        save_json(ROOT / 'submission/unit6_validation_report.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
