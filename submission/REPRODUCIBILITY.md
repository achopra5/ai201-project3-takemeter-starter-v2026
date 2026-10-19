# Submission evidence and reproduction

Unit 5 closeout uses completed experiments only. Do not rerun collection,
training, candidate selection or held-out inference. Verifying saved metrics
and hashes is read-only and does not perform a new model evaluation.

## Committed evidence

- [The original notebook](../takemeter.ipynb), [seed-42 results](../results.json),
  [three-seed original results](../results_three_seeds_before.json) and
  [seed-42 test split](../test_split.csv) remain unchanged.
- [The dataset](../labels.csv), [criteria](../criteria.md), annotation journal,
  source/proposal CSVs, curation ledger and audit preserve the original data and
  review provenance. The frozen [annotation manifest](../data/annotation_session.json)
  and [curation manifest](../data/curation_manifest.json) pin their byte hashes.
- Necessary raw supplemental response pages and their retrieval manifests under
  `data/supplemental_scans/` are committed (about 1.8 MB). The validator reconstructs
  the 15 supplemental posts from these exact responses. They are required source
  evidence, not model-training artifacts. Search catalogs are omitted.
- [The validation protocol](../experiments/validation-20261018T234742Z/protocol.json),
  frozen splits, input/token audit, candidate metrics, compact per-run metadata,
  validation predictions, histories and checkpoint-hash records preserve the
  controlled comparison. [runner_used.py](../experiments/validation-20261018T234742Z/runner_used.py)
  archives the exact source used for the completed training fits. Use the current
  maintained scripts for integrity checks, not the source archive as an entry point.
- [The final plan](../experiments/validation-20261018T234742Z/final_evaluation_plan.json),
  [start record](../experiments/validation-20261018T234742Z/final_evaluation_started.json),
  [final results](../experiments/validation-20261018T234742Z/final_test_results.json)
  and three small saved prediction CSVs document the already completed one-time
  evaluation. The plan's status is a historical preparation record; final results
  establish completion. It was not modified after inference.
- [The closeout manifest](closeout_manifest.json) pins 72 original evidence files
  before documentation edits. [Submission validation](validation_report.md)
  checks their bytes and reconciles metrics from existing predictions/confusions.

## Local artifacts preserved, omitted from Git

All paths are relative to the repository root; none of these original files was
removed during closeout.

- `data/backups/20261018T223001Z/`: original pre-AI data snapshot and SHA-256 file.
- `data/backups/curation-20261018T230224Z/` and
  `data/backups/pre-offline-20261018T232227Z/`: redundant workflow preservation copies.
- `experiments/validation-20261018T234742Z/originals/`: original result/data/notebook
  backups, pinned by the committed preservation manifest.
- `experiments/validation-20261018T234742Z/runs/*/epoch-{3,6,8}/`: 21 saved model/tokenizer
  checkpoint directories. The selected artifacts are
  `runs/controlled-len256-seed42/epoch-6/`,
  `runs/controlled-len256-seed7/epoch-6/` and
  `runs/controlled-len256-seed2024/epoch-6/` inside that experiment directory.
  Exact weight/config/tokenizer hashes for those three are in the final plan.
- Verbose `training.log`, `tests.log`, train-prediction CSVs, duplicate per-seed
  final metric JSONs, catalogs, virtual environments and Hugging Face caches.

The manifests remain committed. A clean clone can verify immutable current
original files against the same snapshot hashes without duplicate backups.
The README taxonomy is checked against the original annotation-session hash.
Any local backup that is present is still hash-checked and corruption fails.
No manifest, attestation or input hash was rewritten to accommodate packaging.

Saved weights are intentionally not distributed. A clone can verify saved
metrics, splits, source provenance and checkpoint hash records; it cannot verify
bytes of absent weights. On the original machine, the checker additionally
verifies every existing checkpoint against its saved hash. It reports local
weight availability explicitly. New training would not be a byte-identical
reproduction on every device, and is outside this closeout.

## Safe verification commands

```bash
source .venv/bin/activate
python test.py
python -m unittest discover -s tests -v
python scripts/check_submission.py
python scripts/validation_experiment.py verify --experiment experiments/validation-20261018T234742Z
git diff --check
git status --short
```

`check_submission.py --write-report` refreshes only the submission validation
report. `scripts/review_labels.py status` refreshes derived dataset reports and
the README dataset-status block; it does not approve reviews, export data or run
models. Do not use `export` during closeout: the frozen exported dataset already
matches the recorded reviews. The separate final evaluator has a start marker
and refuses to silently query the test set again.

Original results and criteria existed before closeout in Git commit `b9e0e83`.
The project history also preserves the earlier criteria, collection, cold-label
workflow, completed curation and training configuration commits. No history was
rewritten and the repository was not recreated.

## Remaining course work

The zero-shot baseline and personal/staff taxonomy comparison belong to Unit 6
and are not completed here. Their absent results are explicitly disclosed in
README. The three model criteria fail; balanced data and submission completeness
do not convert those failures into passes. Submit the existing GitHub repository
URL in the Unit 5 course assignment; a Git push does not perform that portal action.
