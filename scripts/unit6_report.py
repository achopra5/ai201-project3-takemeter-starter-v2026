#!/usr/bin/env python3
"""Refresh only the Unit 6 README blocks from saved, verified result files."""
import json
from pathlib import Path
from statistics import mean
import sys

from validation_experiment import ROOT, LABELS, SEEDS
sys.path.insert(0, str(ROOT))
from baseline import markdown_table

EXP = ROOT / 'experiments/unit6-length256-three-epochs'


def table(headers, rows):
    return ['| ' + ' | '.join(map(str, headers)) + ' |',
            '|' + '|'.join(['---'] * len(headers)) + '|'] + [
            '| ' + ' | '.join(map(str, row)) + ' |' for row in rows]


def experiment_section():
    before = json.loads((ROOT / 'results_three_seeds_before.json').read_text())
    after = json.loads((ROOT / 'results_three_seeds_after.json').read_text())
    staff_path = ROOT / 'agreement_results.json'
    staff = json.loads(staff_path.read_text()) if staff_path.exists() else None
    staff_verdict = staff['criterion5'] + ' (shared)' if staff else 'NOT EVALUATED'
    staff_diagnosis = (f"{staff['agreed']}/30 exact matches ({staff['agreement_rate']:.1%}); measured once under the separate staff taxonomy, not per model configuration."
                       if staff else 'Requires original student selections and the authentic TF reference; no personal decisions are fabricated.')
    lines = ['## Unit 6 Single-Variable Experiment: 128 to 256 Tokens', '',
             '**Completed: three fresh fits, three epochs each.** This is the required single-variable experiment. '
             'It is separate from the earlier exploratory eight-epoch-scheduler experiment. '
             'Only maximum input length changes from 128 to 256. Learning rate remains 2e-5, both batch sizes 16, '
             'epochs 3, seeds 42/7/2024, and the dataset, label mapping and split algorithm remain unchanged. '
             'The linear scheduler has exactly 27 optimizer updates per seed and ends at zero learning rate. '
             'No earlier checkpoint was used for initialization or as a substitute result.', '',
             '[After results](results_three_seeds_after.json), [fixed protocol](experiments/unit6-length256-three-epochs/protocol.json), '
             '[runner](scripts/unit6_experiment.py) and compact per-seed metadata, histories and test predictions under '
             '`experiments/unit6-length256-three-epochs/runs/` record the actual execution. '
             'The runner compiles only function definitions from the unchanged original notebook. '
             'Weights remain local and ignored. GPU nondeterminism and the longer dropout tensors limit exact numerical reproducibility.', '',
             '### Before and after on matching test splits', '']
    rows = [[b['seed'], f"{b['accuracy']:.6f}", f"{a['accuracy']:.6f}", f"{a['accuracy']-b['accuracy']:+.6f}",
             f"{b['f1_macro']:.6f}", f"{a['f1_macro']:.6f}", f"{a['f1_macro']-b['f1_macro']:+.6f}"] for b, a in zip(before, after)]
    rows.append(['Mean', f"{mean(r['accuracy'] for r in before):.6f}", f"{mean(r['accuracy'] for r in after):.6f}",
                 f"{mean(a['accuracy']-b['accuracy'] for b,a in zip(before,after)):+.6f}",
                 f"{mean(r['f1_macro'] for r in before):.6f}", f"{mean(r['f1_macro'] for r in after):.6f}",
                 f"{mean(a['f1_macro']-b['f1_macro'] for b,a in zip(before,after)):+.6f}"])
    lines += table(['Seed', 'Before accuracy', 'After accuracy', 'Accuracy difference', 'Before macro F1', 'After macro F1', 'F1 difference'], rows)
    lines += ['', '### Per-class F1 before and after', '']
    lines += table(['Seed', 'Label', 'Test support', 'Before F1', 'After F1', 'Difference'], [
        [b['seed'], f'`{label}`', a['per_label'][label]['support'], f"{b['per_label'][label]['f1']:.6f}",
         f"{a['per_label'][label]['f1']:.6f}", f"{a['per_label'][label]['f1']-b['per_label'][label]['f1']:+.6f}"]
        for b,a in zip(before, after) for label in LABELS])
    lines += ['', '### Actual three-seed run log', '',
              'Original runs use 128 tokens and three epochs on MPS with PyTorch 2.14.1; their saved results remain unchanged. '
              'Each seed uses 139 train / 31 validation / 30 test posts. In label order '
              '`technical_report`, `help_request`, `discussion`, `resource_share`, the supports are '
              '25/40/35/39 in training, 6/9/8/8 in validation and 5/9/8/8 in test. '
              'The original notebook output preserves the original execution; no original run timestamps have been invented. '
              'The following timestamps and measured training runtimes belong to the new 256-token fits.', '']
    runs = []
    for seed in SEEDS:
        out = EXP / 'runs' / f'seed{seed}'
        meta, started, done, history = [json.loads((out / name).read_text()) for name in ('metadata.json', 'started.json', 'complete.json', 'history.json')]
        runtime = next(r['train_runtime'] for r in history if 'train_runtime' in r)
        runs.append([seed, meta['training_args'].get('use_cpu') and 'cpu' or next(r['device'] for r in after if r['seed']==seed),
                     meta['global_step'], f'{runtime:.2f}', started['started_utc'], done['finished_utc']])
    lines += table(['Seed', 'Device', 'Updates', 'Training seconds', 'Started UTC', 'Completed UTC'], runs)
    lines += ['', '### After confusion matrices', '',
              'Rows are original human labels; columns are predictions, in the original four-label order. '
              'Every matrix sums to 30. The original matrices are preserved in **Original confusion matrices** above.', '']
    for r in after:
        lines += [f"#### 256 tokens, three epochs, seed {r['seed']}", '']
        lines += table(['Gold / predicted'] + [f'`{l}`' for l in LABELS], [
            [f'`{g}`'] + [r['confusion'][g][p] for p in LABELS] for g in LABELS])
        lines += ['']
    accuracy_spread = max(r['accuracy'] for r in after)-min(r['accuracy'] for r in after)
    f1_spread = max(r['f1_macro'] for r in after)-min(r['f1_macro'] for r in after)
    lines += ['### Result, diagnosis and remaining failure', '',
              f"**The proposed improvement did not improve these measurements.** Mean accuracy falls from {mean(r['accuracy'] for r in before):.4f} "
              f"to {mean(r['accuracy'] for r in after):.4f}; mean macro F1 falls from {mean(r['f1_macro'] for r in before):.4f} "
              f"to {mean(r['f1_macro'] for r in after):.4f}. Seeds 42 and 7 have unchanged accuracy, while seed 2024 loses two correct posts. "
              'Macro F1 falls at every seed. More available context by itself was insufficient under the original short training schedule.', '',
              f"After accuracy spans {min(r['accuracy'] for r in after):.4f}–{max(r['accuracy'] for r in after):.4f} "
              f"(spread {accuracy_spread:.4f}); macro F1 spans {min(r['f1_macro'] for r in after):.4f}–{max(r['f1_macro'] for r in after):.4f} "
              f"(spread {f1_spread:.4f}). These overlapping splits are sensitivity checks on one small dataset, not independent replications. "
              'One test decision changes accuracy by 3.33 percentage points; each report-recall step is 20 percentage points.', '',
              'Technical-report F1 remains zero for every seed, with zero report predictions in all three new runs. '
              'In seed 42, five discussions become help requests while zero help requests become discussions. '
              'In seed 7, five help requests and five discussions become resource shares; the reverse cells are one and zero. '
              'The directional pattern supports a failure to distinguish primary purpose. It does not establish that the human labels are wrong. '
              'The baseline’s report F1 of 0.50 on seed 42, versus zero for both trained versions, shows that aggregate accuracy gains conceal a lost category.', '',
              'The pre-existing token audit shows truncation was substantial, but this controlled result rejects the claim that doubling context alone solves it. '
              'Sparse report examples (25 in training), only 27 updates, mixed-purpose text and the small archive sample remain plausible explanations. '
              'They have not been experimentally separated here. The earlier schedule-and-length exploration cannot establish a length-only gain.', '',
              'Original test outcomes and earlier exploratory outcomes were already known. This is an honest exploratory follow-up with a fixed requested intervention; '
              'no post-result seed selection, threshold changes, relabeling or additional tuning was performed. '
              'Retain the original trained setup for the comparison; these results do not justify replacing it with the longer input model.', '',
              '### Original acceptance-criteria verdicts for the required experiment', '']
    lines += table(['Criterion', 'Original target', 'Before', 'After', 'Diagnosis'], [
        [1, 'Accuracy ≥ 0.70 for every seed', 'FAIL', 'FAIL', 'Best before and after accuracy is 0.533333; all three seeds fall short.'],
        [2, 'Macro F1 ≥ 0.60 for every seed', 'FAIL', 'FAIL', 'Best after macro F1 is 0.344322; all three seeds fall short.'],
        [3, 'Every class F1 ≥ 0.40 for every seed', 'FAIL', 'FAIL', 'Technical-report F1 is zero at every seed; discussions also remain weak.'],
        [4, 'Each full-dataset class share 15–40%', 'PASS', 'PASS', 'Dataset unchanged: 36/58/51/55 posts out of 200. Balance does not imply reliable classification.'],
        [5, 'Independent staff-taxonomy agreement ≥ 23/30', staff_verdict, staff_verdict, staff_diagnosis]])
    lines += ['', 'Criterion 5 concerns `analysis`, `hot_take`, `reaction` under the staff rules. '
              'All model metrics above concern only `technical_report`, `help_request`, `discussion`, `resource_share`. '
              'There is no justified direct confusion-pair mapping across the two independent tasks. '
              'Any later staff disagreement can motivate reflection about rule application, but cannot prove inconsistency on the TakeMeter dataset.', '']
    return '\n'.join(lines)


def main():
    path = ROOT / 'README.md'
    text = path.read_text()
    start, end = '<!-- UNIT6_LENGTH_EXPERIMENT_START -->', '<!-- UNIT6_LENGTH_EXPERIMENT_END -->'
    block = start + '\n' + experiment_section() + '\n' + end + '\n\n'
    if start in text:
        a, rest = text.split(start, 1)
        _, b = rest.split(end, 1)
        text = a + block.rstrip() + b
    else:
        text = text.replace('## Agreement Report — Unit 6 Pending', block + '## Agreement Report — Unit 6 Pending')
    base = json.loads((ROOT / 'baseline_results.json').read_text())
    trained = json.loads((ROOT / 'results.json').read_text())
    marker_a, marker_b = '<!-- UNIT6_BASELINE_TABLE_START -->', '<!-- UNIT6_BASELINE_TABLE_END -->'
    base_block = marker_a + '\n' + markdown_table(base['scores'], LABELS, trained) + '\n' + marker_b
    if marker_a not in text:
        text = text.replace('**Prediction provenance:**', base_block + '\n\n**Prediction provenance:**')
    path.write_text(text)


if __name__ == '__main__':
    main()
