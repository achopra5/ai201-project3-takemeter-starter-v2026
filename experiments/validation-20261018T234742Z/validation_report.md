# Validation-only experiment results

This is the historical validation-selection report. The candidate was subsequently
selected and evaluated once; see [the existing final results](final_test_results.json)
and [the current submission analysis](../../README.md). No further evaluation is pending.

Recommended candidate: **controlled-len256-epoch6**.

All figures below are validation results. No held-out test predictions or outcomes were queried.

- reference-len128-epoch3: mean macro F1 0.3469; accuracy 0.4731; loss 1.3073. Seed F1: 42: 0.3602, 7: 0.3556, 2024: 0.3249.
- controlled-len128-epoch3: mean macro F1 0.3691; accuracy 0.4946; loss 1.2280. Seed F1: 42: 0.3825, 7: 0.3485, 2024: 0.3763.
- controlled-len128-epoch6: mean macro F1 0.3478; accuracy 0.4624; loss 1.1028. Seed F1: 42: 0.3311, 7: 0.3556, 2024: 0.3567.
- controlled-len128-epoch8: mean macro F1 0.3568; accuracy 0.4731; loss 1.0836. Seed F1: 42: 0.3453, 7: 0.3429, 2024: 0.3822.
- controlled-len256-epoch3: mean macro F1 0.3644; accuracy 0.4946; loss 1.2203. Seed F1: 42: 0.4459, 7: 0.3357, 2024: 0.3116.
- controlled-len256-epoch6: mean macro F1 0.4484; accuracy 0.5376; loss 1.0880. Seed F1: 42: 0.3890, 7: 0.4222, 2024: 0.5341.
- controlled-len256-epoch8: mean macro F1 0.4382; accuracy 0.5269; loss 1.0636. Seed F1: 42: 0.3655, 7: 0.4222, 2024: 0.5268.

## Findings

The selected checkpoint improves mean validation macro F1 by 0.1015 and accuracy by 6.45 percentage points against the original-schedule reference. These are validation comparisons, not test gains.

Reference mean training macro F1 is 0.3829; selected mean training macro F1 is 0.7081, compared with validation 0.4484. More fitting helps, but the larger train/validation gap shows substantial generalization limits.

Original reference validation technical-report prediction counts are 42: 0, 7: 0, 2024: 0. Inspect the per-class diagnostics below: a mean gain can coexist with an ignored class in some seeds. Do not declare the precommitted held-out criteria satisfied from these results.

At 128 tokens, controlled epoch-3/6/8 mean macro F1 is 0.3691/0.3478/0.3568. At 256 tokens, controlled epoch-3/6/8 mean macro F1 is 0.3644/0.4484/0.4382. Compare F1 as well as loss; decreasing loss alone was not used for selection.

The recommendation uses the **saved epoch-6 checkpoint of the 8-epoch schedule**, at 54 updates (learning rate 5e-06). A fresh run with a shorter scheduler is a different intervention. Keep the saved weights for the separate final evaluation.

## Recommended candidate diagnostics

- Seed 42: 54 updates; train macro F1 0.7113, validation macro F1 0.3890.
  - technical_report: F1 0.0000, recall 0.0000, 6 gold / 0 predicted.
  - help_request: F1 0.4000, recall 0.4444, 9 gold / 11 predicted.
  - discussion: F1 0.4286, recall 0.3750, 8 gold / 6 predicted.
  - resource_share: F1 0.7273, recall 1.0000, 8 gold / 14 predicted.
- Seed 7: 54 updates; train macro F1 0.6136, validation macro F1 0.4222.
  - technical_report: F1 0.0000, recall 0.0000, 6 gold / 0 predicted.
  - help_request: F1 0.6667, recall 1.0000, 9 gold / 18 predicted.
  - discussion: F1 0.2222, recall 0.1250, 8 gold / 1 predicted.
  - resource_share: F1 0.8000, recall 1.0000, 8 gold / 12 predicted.
- Seed 2024: 54 updates; train macro F1 0.7994, validation macro F1 0.5341.
  - technical_report: F1 0.5000, recall 0.3333, 6 gold / 2 predicted.
  - help_request: F1 0.5000, recall 0.5556, 9 gold / 11 predicted.
  - discussion: F1 0.5000, recall 0.3750, 8 gold / 4 predicted.
  - resource_share: F1 0.6364, recall 0.8750, 8 gold / 14 predicted.

## Interpretation and limits

Each seed has 139 training, 31 validation and 30 test posts. One validation decision is 3.23 percentage points. Per-class validation supports are only 6–9. Seeds are overlapping resamples of the same 200 posts, not independent replications. A post held out in one seed may train another seed; this preserves the inherited protocol.

The original 3-epoch linear scheduler performs 27 updates and reaches zero learning rate. The controlled 8-epoch trajectory performs 72 updates; its epochs 3/6/8 share the same training history (27/54/72 updates). Its epoch-3 checkpoint is not the original 3-epoch scheduler. The reference reproduces original hyperparameters; GPU nondeterminism can prevent bitwise metric reproduction.

Validation selection among several candidates can overfit this small validation pool. Longer inputs also change compute and dropout tensor shapes. No acceptance criterion is evaluated or revised here. The original test aggregate was already known before this intervention; a later test comparison is an exploratory follow-up, not a new pristine confirmatory study. Do not infer deployment readiness from validation improvement.

Per-seed epoch histories, per-class metrics/confusion matrices and full train/validation prediction probabilities are saved under runs/. Checkpoints are local ignored artifacts. Originals remain backed up and hash-checked.

The selected [final plan](final_evaluation_plan.json) and completed final results
already exist. The plan's `PREPARED_ONLY` status describes the immutable plan at
creation, not the current evaluation state. Do not recreate the plan or rerun
training/evaluation for submission closeout.
