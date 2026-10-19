# DistilBERT validation intervention

**Closeout status:** candidate `controlled-len256-epoch6` was selected and the
separate held-out evaluation completed on 2026-10-19 at 00: 00: 06 UTC. See
[saved final results](final_test_results.json), [the final analysis](../../README.md)
and [submission verification](../../submission/validation_report.md). The protocol
below describes the earlier validation-only selection stage. Its training and
evaluation commands are historical instructions, not closeout tasks. No further
experiments or test evaluations should be run.

This experiment follows the completed original run. The user supplied original mean test accuracy of 43.3% and macro F 1 of approximately 0.298, and reported validation loss still decreasing at epoch 3 for seeds 42, 7 and 2024. Those aggregates motivate investigation; no original test result file was parsed to tune this intervention. Original result bytes were copied and hashed first. The notebook's training/validation table for seed 42 was inspected separately: validation loss 1.368994 → 1.347105 → 1.335875 and validation macro F 1 0.102564 → 0.360185 → 0.360185.

## Frozen inputs and audit

`preservation_manifest.json` identifies the original result files and backups under `originals/`. `protocol.json` freezes the dataset, criteria, notebook, label definitions, split identities, truncation audit and selection rule before candidate training. The original results JSON files are handled as opaque bytes, never used as selection inputs. `test_split.csv` is read only to verify that reconstructed seed-42 test identities/order match. No held-out text is tokenized for the truncation audit, no held-out model predictions are made and no held-out outcomes are scored.

The notebook's exact stratified split algorithm is preserved, including floating-point rounding of `.15 / .85`: **139 train / 31 validation / 30 test** per seed. Altering it to nominal 140/30/30 would change examples. `splits.json` records original zero-based dataset row indices for every partition and seed; `dataset_identities.json` pins their text hashes and labels. Dataset text, taxonomy, acceptance criteria, source posts and annotations remain unchanged.

The truncation audit uses the cached uncased DistilBERT tokenizer with special tokens included and no initial truncation. It records post counts, length quantiles, discarded tokens, retained token fractions and per-class breakdowns on train/validation only. The partitions overlap between seeds and must not be interpreted as 510 distinct posts.

- At 128: train truncates 98/139, 94/139 and 98/139 for seeds 42/7/2024; validation truncates 22/31, 22/31 and 21/31.
- At 256: train truncates 61/139, 65/139 and 62/139; validation truncates 12/31, 11/31 and 14/31.
- Mean partition-level truncated fraction falls from about 69.7% to 42.5%. Retained tokens increase by about 16.9 percentage points. Long posts dominate the total-token denominator: 128 retains only 25–31% of all tokens in each partition; 256 retains about 38–50%. Even 256 loses substantial content.

Technical reports are especially affected: **24/25 training reports and all 6/6 validation reports truncate at 128 in every seed**. This supports testing more context without assuming that truncation alone explains the class failure. The audit JSON retains the same per-class breakdowns at 256 as well.

The data-only rule for including 256 was fixed before candidate predictions: at least 20% of posts truncate at 128 and the mean retained-token fraction improves by at least 10 percentage points at 256. Both conditions pass. This rule is a compute-budget choice for this experiment, not a new acceptance criterion. All full stored texts remain intact; truncation affects model inputs only.

## Controlled comparison

Keep model, learning rate **2e-5**, batch size **16**, split/model seeds **42, 7, 2024**, label mapping, zero weight decay, zero warmup, default AdamW and linear scheduler unchanged. The installed optimizer default is `adamw_torch_fused`, recorded explicitly with package versions in each run's metadata. Training runs locally on Apple MPS using cached weights, with no hosted inference or model download.

With 139 training posts and no dropped batch, there are **9 optimizer updates per epoch** (eight full batches and one of eleven). Three epochs give **27** updates, six give **54**, eight give **72**. Actual global steps are asserted and recorded. The low update budget plus weak train performance can indicate insufficient fitting; decreasing validation loss alone cannot establish that more epochs will improve class decisions.

The comparison has two parts:

1. Three 3-epoch/128-token reference fits reproduce the original setup, including a 27-update linear learning-rate horizon.
2. Six 8-epoch fits cover 128 and 256 tokens with each seed. Candidate checkpoints at epochs **3, 6 and 8** share a 72-update scheduler and the same preceding training trajectory within a fit. This isolates continuing a given run. Epoch 3 of this trajectory is deliberately distinguished from the original 3-epoch reference: its learning rate has not yet decayed to zero.

There are nine fits and seven candidate configurations across three seeds. Checkpoints and training/validation predictions are captured at the candidate epochs; validation loss, accuracy and macro F 1 are logged at every epoch. Training diagnostics are inference-mode predictions over the training partition, distinct from minibatch training loss. Additional diagnostic dataloaders can consume random-state draws, so a plain notebook rerun with only the chosen epoch/length settings need not reproduce these exact checkpoint weights. The saved candidate checkpoints are the intended artifacts for later evaluation.

Selection uses **mean validation macro F 1 across the same three seeds**, with precommitted tie-breaks: minimum seed macro F 1, lower mean validation loss, shorter inputs, fewer epochs, then candidate name. Only the seven specified configurations are eligible. Other logged epochs are diagnostic and cannot become an unplanned winning checkpoint. The original reference remains eligible if longer fits do not improve validation F 1.

## Commands and artifacts

From the repository root:

```bash
source .venv/bin/activate
python scripts/validation_experiment.py verify --experiment experiments/validation-20261018T 234742Z
python scripts/validation_experiment.py run --experiment experiments/validation-20261018T 234742Z
python scripts/validation_experiment.py report --experiment experiments/validation-20261018T 234742Z
python -m unittest discover -s tests -v
```

`run` skips completed fits and refuses to silently overwrite an interrupted fit. Preserve/move an interrupted run directory before retrying that fit from its seed; this is restart-by-fit, not optimizer-state resume. Never run the notebook's result-writing cells for this experiment: they overwrite the original files and evaluate test sets.

`validation_results.json` contains all candidates, per-seed class metrics and confusion matrices, train diagnostics, steps and checkpoint hashes. `validation_report.md` gives the validation recommendation. `runs/*/history.json` contains curves; `runs/*/{train,validation}_predictions_epoch*.csv` retains row/text hashes, gold labels, predictions and probabilities. `runs/*/metadata.json` records device, installed versions, base-model commit and training arguments. Large model checkpoints are local and ignored by Git; keep them until final evaluation.

All nine fits completed, totaling **513 optimizer updates** across 57 training epochs. `learning_curves.csv` collects the 57 validation checkpoints for inspection; candidate selection still uses only the precommitted seven configurations. `runner_used.py` archives the exact training-runner source whose SHA-256 is recorded in run metadata. The maintained script subsequently gained report and final-plan integrity checks; this did not retrain any model.

The validation rule recommends **controlled-len 256-epoch 6**: mean macro F 1 **0.4484** and accuracy **0.5376**, versus **0.3469** and **0.4731** in the original-schedule reference. It is the epoch-6 checkpoint of the 72-update schedule, with learning rate `5e-6` at update 54; do not substitute a fresh 54-update schedule. Seed F 1 values are 0.3890, 0.4222, 0.5341. The third seed contributes the largest gain. Mean train F 1 is 0.7081, while two seeds still predict no validation technical reports. Epoch 8 lowers mean validation loss further but reduces mean macro F 1 to 0.4382. These findings support a modest validation recommendation and leave serious class/generalization weaknesses.

To select this recommendation later without evaluating test yet:

```bash
python scripts/validation_experiment.py prepare-final \
  --experiment experiments/validation-20261018T 234742Z \
  --candidate controlled-len 256-epoch 6
```

After the reviewer selects a configuration, `prepare-final --candidate <exact-name>` locks its three checkpoint hashes and original test-row identities in a separate `final_evaluation_plan.json`. It does **not** evaluate any test examples. A later explicitly authorized evaluation must load those weights without retraining, score each original test split once, write a new `final_test_results.json` without overwriting any earlier result, and evaluate unchanged criteria 1–3 separately for every seed. Criteria 4 and 5 retain their original meanings; staff-taxonomy agreement is not measured by this experiment.

The separate evaluator is implemented in `scripts/evaluate_validation_selection.py`. After selection and plan preparation, its explicit command is:

```bash
python scripts/evaluate_validation_selection.py \
  --experiment experiments/validation-20261018T 234742Z \
  --reviewer "Adi" --confirm-final-evaluation
```

**Do not run this command during validation selection.** It verifies plan, validation-result, checkpoint and source hashes before reserving a one-time test evaluation. An existing final result or start marker blocks another evaluation. A crash preserves its marker and any per-seed results for inspection; automatic retry is intentionally refused. All output stays in this experiment directory, separate from the original results and test-split files.

## Limits

Validation has only 31 posts per seed and 6–9 per class. One validation prediction changes accuracy by 3.23 percentage points. Seeds reuse overlapping posts rather than provide independent datasets; a post held out for one seed can be training data for another, as in the original protocol. Candidate selection adds validation optimism. The original test results were already known before this follow-up; the eventual comparison is exploratory and cannot be called a fresh confirmatory evaluation. Longer inputs double the padded token budget, alter dropout tensor shapes and cost more compute. Technical reports remain relatively sparse. Neither falling loss nor a validation win guarantees meeting the precommitted held-out thresholds or deployment readiness.

AI assistance implemented this protocol, audits, experiment runner, tests and analysis under the user's requested intervention. It did not relabel examples, create posts, change taxonomy/criteria or treat validation as held-out test evidence.
