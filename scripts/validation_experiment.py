#!/usr/bin/env python3
"""Frozen, validation-only DistilBERT experiment. Never evaluates a test split.

Use the project's activated .venv. Artifacts are isolated from notebook results.
"""
import argparse
import csv
import gc
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path
from evidence_integrity import verify_frozen_file

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["technical_report", "help_request", "discussion", "resource_share"]
SEEDS = [42, 7, 2024]
BASE_MODEL = "distilbert-base-uncased"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text())


def split_indices(frame, seed):
    """Exactly the notebook algorithm, including its floating-point val_share."""
    from sklearn.model_selection import train_test_split
    strat = lambda x: x["label"] if x["label"].value_counts().min() >= 2 else None
    rest, test = train_test_split(frame, test_size=.15, random_state=seed, stratify=strat(frame))
    train, val = train_test_split(rest, test_size=.15 / (1 - .15), random_state=seed,
                                stratify=strat(rest))
    return {"train": train.index.tolist(), "validation": val.index.tolist(),
            "test": test.index.tolist()}


def audit_lengths(lengths, limit):
    import numpy as np
    values = np.asarray(lengths)
    return {"posts": len(lengths), "truncated_posts": int((values > limit).sum()),
            "truncated_fraction": float((values > limit).mean()),
            "discarded_tokens": int(np.maximum(values - limit, 0).sum()),
            "retained_token_fraction": float(np.minimum(values, limit).sum() / values.sum()),
            "length_quantiles": {str(q): float(np.quantile(values, q))
                                 for q in (0, .25, .5, .75, .9, .95, 1)}}


def verify(exp):
    protocol = read_json(exp / "protocol.json")
    manifest = read_json(exp / "preservation_manifest.json")
    # README may gain an experiment link; its original is still frozen in backups.
    for name, digest in manifest["sha256"].items():
        backup = exp / "originals" / name
        if backup.exists() and sha(backup) != digest:
            raise ValueError(f"Original backup changed: {name}")
        if not backup.exists() and name != "README.md" and protocol["protected_sha256"].get(name) != digest:
            raise ValueError(f"Missing backup without identical frozen original: {name}")
    # Documentation can evolve, but the README's original taxonomy cannot.
    def taxonomy(path):
        return path.read_text().split("## Label Taxonomy\n", 1)[1].split("## The Dataset\n", 1)[0]
    if "README.md" in manifest["sha256"]:
        original = exp / "originals/README.md"
        expected_taxonomy = (text_sha(taxonomy(original)) if original.exists() else
                             read_json(ROOT / "data/annotation_session.json")["taxonomy_sha256"])
        if text_sha(taxonomy(ROOT / "README.md")) != expected_taxonomy:
            raise ValueError("Original README taxonomy changed")
    for name, digest in protocol["protected_sha256"].items():
        verify_frozen_file(ROOT, name, digest)
    for name, digest in protocol["artifact_sha256"].items():
        if sha(exp / name) != digest:
            raise ValueError(f"Frozen experiment artifact changed: {name}")
    import pandas as pd
    frame = pd.read_csv(ROOT / "labels.csv", keep_default_na=False)
    splits = read_json(exp / "splits.json")
    for seed in SEEDS:
        if split_indices(frame, seed) != splits[str(seed)]:
            raise ValueError(f"Reconstructed split changed for seed {seed}")
    return protocol, frame, splits


def prepare(exp):
    import pandas as pd
    from transformers import AutoTokenizer
    if (exp / "protocol.json").exists():
        raise ValueError("Protocol already exists; will not rewrite it after viewing results")
    manifest = read_json(exp / "preservation_manifest.json")
    for name, digest in manifest["sha256"].items():
        if sha(ROOT / name) != digest or sha(exp / "originals" / name) != digest:
            raise ValueError(f"Preserved input changed before preparation: {name}")
    frame = pd.read_csv(ROOT / "labels.csv", keep_default_na=False)
    if len(frame) != 200 or not set(frame.label) == set(LABELS) or frame.text.duplicated().any():
        raise ValueError("Unexpected original dataset")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
    splits = {str(seed): split_indices(frame, seed) for seed in SEEDS}
    # Identity check only: no model predictions and no held-out outcome file parsed.
    original_test = pd.read_csv(ROOT / "test_split.csv", keep_default_na=False)
    test42 = frame.loc[splits["42"]["test"]].reset_index(drop=True)
    if not test42[["text", "label"]].equals(original_test[["text", "label"]]):
        raise ValueError("Seed 42 test identities/order do not match original test_split.csv")
    audit, token_rows = {}, []
    for seed in SEEDS:
        audit[str(seed)] = {}
        for part in ("train", "validation"):
            subset = frame.loc[splits[str(seed)][part]]
            lengths = [len(tokenizer(t, truncation=False, verbose=False)["input_ids"])
                       for t in subset.text]
            audit[str(seed)][part] = {
                str(limit): {"overall": audit_lengths(lengths, limit),
                             "per_class": {label: audit_lengths(
                                 [n for n, y in zip(lengths, subset.label) if y == label], limit)
                                 for label in LABELS}}
                for limit in (128, 256)}
            token_rows.extend({"seed": seed, "partition": part, "row_index": int(idx),
                               "text_sha256": text_sha(frame.loc[idx, "text"]),
                               "label": frame.loc[idx, "label"], "tokens_with_special": n}
                              for idx, n in zip(subset.index, lengths))
    # Rule fixed before any candidate predictions: use 256 if >=20% truncate at 128
    # and 256 saves >=10 percentage points of tokens, averaged over train/val seeds.
    groups = [audit[str(s)][p] for s in SEEDS for p in ("train", "validation")]
    trunc128 = sum(g["128"]["overall"]["truncated_fraction"] for g in groups) / len(groups)
    saved = sum(g["256"]["overall"]["retained_token_fraction"] -
                g["128"]["overall"]["retained_token_fraction"] for g in groups) / len(groups)
    lengths = [128, 256] if trunc128 >= .20 and saved >= .10 else [128]
    save_json(exp / "splits.json", splits)
    save_json(exp / "truncation_audit.json", audit)
    write_rows(exp / "token_lengths_train_validation.csv", token_rows)
    identities = [{"row_index": int(i), "text_sha256": text_sha(r.text), "label": r.label}
                  for i, r in frame.iterrows()]
    save_json(exp / "dataset_identities.json", identities)
    files = ["splits.json", "truncation_audit.json", "token_lengths_train_validation.csv",
             "dataset_identities.json"]
    protected = {n: d for n, d in manifest["sha256"].items() if n != "README.md"}
    for name in ("data/annotation_session.json", "data/curation_manifest.json",
                 "data/review_decisions.jsonl", "taxonomy_stress_test.md"):
        if (ROOT / name).exists():
            protected[name] = sha(ROOT / name)
    protocol = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Validation-only selection. No test predictions, metrics or test truncation.",
        "base_model": BASE_MODEL, "seeds": SEEDS, "label_order": LABELS,
        "learning_rate": 2e-5, "batch_size": 16, "weight_decay": 0,
        "gradient_accumulation_steps": 1, "drop_last": False, "warmup_steps": 0,
        "optimizer": "adamw_torch_fused (notebook installed default)",
        "scheduler": "linear; original reference horizon=27, controlled horizon=72",
        "max_lengths": lengths, "candidate_epochs": [3, 6, 8],
        "length_rule": {"trunc128_min_fraction": .20, "retention_gain_min": .10,
                        "observed_mean_trunc128": trunc128, "observed_mean_retention_gain": saved},
        "design": "3-epoch original reference at128 plus shared 8-epoch trajectory per length/seed. "
                  "Compare checkpoints3/6/8 within each trajectory to control scheduler history. "
                  "Reference3 uses the original shorter scheduler, so duration alone is not isolated against it.",
        "selection": "Maximize mean validation macro F1 over seeds; ties (rounded12 decimals) "
                     "use minimum seed macro F1, then lower mean validation loss, shorter input, "
                     "fewer epochs, then candidate name. Original reference is also eligible.",
        "protected_sha256": protected, "artifact_sha256": {n: sha(exp / n) for n in files},
        "test42_identity_match": True, "split_sizes": {str(s): {k: len(v) for k, v in splits[str(s)].items()}
                                                      for s in SEEDS}}
    save_json(exp / "protocol.json", protocol)
    print(json.dumps({"max_lengths": lengths, "length_rule": protocol["length_rule"],
                      "split_sizes": protocol["split_sizes"]}, indent=2))


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def score(gold, predicted):
    from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
    ids = list(range(len(LABELS)))
    p, r, f, support = precision_recall_fscore_support(gold, predicted, labels=ids, zero_division=0)
    return {"accuracy": float(accuracy_score(gold, predicted)), "f1_macro": float(f.mean()),
            "per_label": {label: {"precision": float(p[i]), "recall": float(r[i]),
                                  "f1": float(f[i]), "support": int(support[i]),
                                  "predicted": int(sum(int(x) == i for x in predicted))}
                          for i, label in enumerate(LABELS)},
            "confusion_matrix": confusion_matrix(gold, predicted, labels=ids).tolist()}


def run_fit(exp, protocol, frame, splits, seed, length, epochs, kind):
    import numpy as np
    import torch
    import transformers
    import datasets
    from datasets import Dataset
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification, Trainer,
                              TrainerCallback, TrainingArguments, set_seed)
    run_id = f"{kind}-len{length}-seed{seed}"
    out = exp / "runs" / run_id
    if (out / "complete.json").exists():
        print(f"Already complete: {run_id}", flush=True)
        return
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"Incomplete run {run_id}; preserve/move it before a fresh deterministic retry")
    out.mkdir(parents=True, exist_ok=True)
    set_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=4, id2label=dict(enumerate(LABELS)),
        label2id={label: i for i, label in enumerate(LABELS)}, local_files_only=True)
    def make_dataset(part):
        subset = frame.loc[splits[str(seed)][part]]
        encoded = tokenizer(subset.text.tolist(), truncation=True, padding="max_length", max_length=length)
        encoded["labels"] = [LABELS.index(x.strip()) for x in subset.label]
        return Dataset.from_dict(encoded)
    train_ds, val_ds = make_dataset("train"), make_dataset("validation")
    expected_per_epoch = math.ceil(len(train_ds) / 16)
    args = TrainingArguments(
        output_dir=str(out / "trainer"), num_train_epochs=epochs, learning_rate=2e-5,
        per_device_train_batch_size=16, per_device_eval_batch_size=16,
        eval_strategy="epoch", save_strategy="no", logging_steps=10, seed=seed,
        report_to="none", disable_tqdm=True)
    metadata = {"run_id": run_id, "kind": kind, "seed": seed, "max_length": length,
                "epochs_planned": epochs, "updates_per_epoch": expected_per_epoch,
                "expected_updates": expected_per_epoch * epochs, "device": str(args.device),
                "torch": torch.__version__, "transformers": transformers.__version__,
                "datasets": datasets.__version__, "python": platform.python_version(),
                "model_commit": getattr(model.config, "_commit_hash", None),
                "training_args": args.to_dict(), "protocol_sha256": sha(exp / "protocol.json"),
                "runner_sha256": sha(Path(__file__)),
                "started_utc": datetime.now(timezone.utc).isoformat()}
    save_json(out / "metadata.json", metadata)
    checkpoints = [3] if kind == "reference" else [3, 6, 8]
    class Capture(TrainerCallback):
        def __init__(self):
            self.trainer = None
            self.records = []

        def on_evaluate(self, args, state, control, metrics=None, **kwargs):
            # Auxiliary predict() calls must not recursively enter this callback.
            epoch = int(round(state.epoch))
            if epoch not in checkpoints:
                return
            checkpoint = out / f"epoch-{epoch}"
            checkpoint.mkdir(exist_ok=True)
            model.save_pretrained(checkpoint)
            tokenizer.save_pretrained(checkpoint)
            record = {"epoch": epoch, "global_step": state.global_step,
                      "learning_rate": float(self.trainer.lr_scheduler.get_last_lr()[0])}
            for part, dataset in (("train", train_ds), ("validation", val_ds)):
                prediction = self.trainer.predict(dataset, metric_key_prefix=part)
                logits = prediction.predictions
                probs = torch.softmax(torch.tensor(logits), dim=-1).numpy()
                predicted = np.argmax(logits, axis=-1)
                record[part] = score(prediction.label_ids, predicted)
                record[part]["loss"] = float(prediction.metrics[f"{part}_loss"])
                rows = []
                for j, idx in enumerate(splits[str(seed)][part]):
                    rows.append({"row_index": idx, "text_sha256": text_sha(frame.loc[idx, "text"]),
                                 "gold": frame.loc[idx, "label"], "predicted": LABELS[predicted[j]],
                                 **{f"p_{label}": float(probs[j, i]) for i, label in enumerate(LABELS)}})
                write_rows(out / f"{part}_predictions_epoch{epoch}.csv", rows)
            record["checkpoint"] = str(checkpoint.relative_to(exp))
            record["weights_sha256"] = sha(checkpoint / "model.safetensors")
            self.records.append(record)
            save_json(out / "checkpoints.json", self.records)
            print(f"CHECKPOINT {run_id} epoch={epoch} steps={state.global_step} "
                  f"trainF1={record['train']['f1_macro']:.4f} "
                  f"valF1={record['validation']['f1_macro']:.4f}", flush=True)

    capture = Capture()
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds,
                      compute_metrics=lambda p: {k: v for k, v in score(p.label_ids, np.argmax(p.predictions, axis=-1)).items()
                                                 if k in ("accuracy", "f1_macro")},
                      callbacks=[capture])
    capture.trainer = trainer
    print(f"START {run_id}: {epochs}epochs, {args.device}, {expected_per_epoch * epochs}updates", flush=True)
    trainer.train()
    if trainer.state.global_step != expected_per_epoch * epochs:
        raise ValueError("Unexpected optimizer-step count")
    save_json(out / "history.json", trainer.state.log_history)
    save_json(out / "complete.json", {"global_step": trainer.state.global_step,
                                      "finished_utc": datetime.now(timezone.utc).isoformat(),
                                      "metadata_sha256": sha(out / "metadata.json"),
                                      "checkpoints_sha256": sha(out / "checkpoints.json")})
    verify(exp)
    del trainer, model, train_ds, val_ds, capture
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()


def select_candidate(candidates):
    def rank(c):
        vals = [r["validation"]["f1_macro"] for r in c["seeds"]]
        return (-round(sum(vals) / len(vals), 12), -round(min(vals), 12),
                sum(r["validation"]["loss"] for r in c["seeds"]) / len(vals),
                c["max_length"], c["epoch"], c["name"])
    return min(candidates, key=rank)


def report(exp):
    protocol, frame, splits = verify(exp)
    candidates = []
    for kind, lengths, epochs in (("reference", [128], [3]),
                                  ("controlled", protocol["max_lengths"], [3, 6, 8])):
        for length in lengths:
            runs = []
            for seed in SEEDS:
                out = exp / "runs" / f"{kind}-len{length}-seed{seed}"
                if not (out / "complete.json").exists():
                    raise ValueError(f"Run not complete: {out.name}")
                completion = read_json(out / "complete.json")
                if completion["checkpoints_sha256"] != sha(out / "checkpoints.json"):
                    raise ValueError("Checkpoint metrics changed after completion")
                if completion["metadata_sha256"] != sha(out / "metadata.json"):
                    raise ValueError("Run metadata changed after completion")
                runs.append(read_json(out / "checkpoints.json"))
            for epoch in epochs:
                records = [{"seed": seed, **next(r for r in run if r["epoch"] == epoch)}
                           for seed, run in zip(SEEDS, runs)]
                candidates.append({"name": f"{kind}-len{length}-epoch{epoch}", "kind": kind,
                                   "max_length": length, "epoch": epoch, "seeds": records,
                                   "mean_validation_f1_macro": sum(r["validation"]["f1_macro"] for r in records) / 3,
                                   "mean_validation_accuracy": sum(r["validation"]["accuracy"] for r in records) / 3,
                                   "mean_validation_loss": sum(r["validation"]["loss"] for r in records) / 3})
    selected = select_candidate(candidates)
    result = {"status": "VALIDATION_RECOMMENDATION_ONLY; final test evaluation pending human selection",
              "selection_rule": protocol["selection"], "protocol_sha256": sha(exp / "protocol.json"),
              "selected_candidate": selected["name"], "candidates": candidates,
              "test_evaluations_performed": 0}
    save_json(exp / "validation_results.json", result)
    lines = ["# Validation-only experiment results", "", result["status"], "",
             f"Recommended candidate: **{selected['name']}**.", "",
             "All figures below are validation results. No held-out test predictions or outcomes were queried.", ""]
    for c in candidates:
        f1s = ", ".join(f"{r['seed']}: {r['validation']['f1_macro']:.4f}" for r in c["seeds"])
        lines.append(f"- {c['name']}: mean macro F1 {c['mean_validation_f1_macro']:.4f}; "
                     f"accuracy {c['mean_validation_accuracy']:.4f}; loss {c['mean_validation_loss']:.4f}. "
                     f"Seed F1: {f1s}.")
    reference = candidates[0]
    train_mean = lambda c: sum(r["train"]["f1_macro"] for r in c["seeds"]) / len(c["seeds"])
    series = []
    for length in protocol["max_lengths"]:
        scores = [next(c for c in candidates if c["kind"] == "controlled" and
                       c["max_length"] == length and c["epoch"] == epoch)["mean_validation_f1_macro"]
                  for epoch in (3, 6, 8)]
        series.append(f"At {length} tokens, controlled epoch-3/6/8 mean macro F1 is " +
                      "/".join(f"{f:.4f}" for f in scores) + ".")
    reference_technical = ", ".join(
        f"{r['seed']}: {r['validation']['per_label']['technical_report']['predicted']}" for r in reference["seeds"])
    lines += ["", "## Findings", "",
              f"The selected checkpoint improves mean validation macro F1 by "
              f"{selected['mean_validation_f1_macro'] - reference['mean_validation_f1_macro']:.4f} "
              f"and accuracy by {100 * (selected['mean_validation_accuracy'] - reference['mean_validation_accuracy']):.2f} "
              "percentage points against the original-schedule reference. These are validation comparisons, not test gains.", "",
              f"Reference mean training macro F1 is {train_mean(reference):.4f}; selected mean training macro F1 "
              f"is {train_mean(selected):.4f}, compared with validation {selected['mean_validation_f1_macro']:.4f}. "
              "More fitting helps, but the larger train/validation gap shows substantial generalization limits.", "",
              f"Original reference validation technical-report prediction counts are {reference_technical}. "
              "Inspect the per-class diagnostics below: a mean gain can coexist with an ignored class in some seeds. "
              "Do not declare the precommitted held-out criteria satisfied from these results.", "",
              " ".join(series) + " Compare F1 as well as loss; decreasing loss alone was not used for selection.", "",
              f"The recommendation uses the **saved epoch-{selected['epoch']} checkpoint of the "
              f"{8 if selected['kind'] == 'controlled' else 3}-epoch schedule**, "
              f"at {selected['seeds'][0]['global_step']} updates "
              f"(learning rate {selected['seeds'][0]['learning_rate']:.6g}). "
              "A fresh run with a shorter scheduler is a different intervention. "
              "Keep the saved weights for the separate final evaluation."]
    lines += ["", "## Recommended candidate diagnostics", ""]
    for r in selected["seeds"]:
        lines.append(f"- Seed {r['seed']}: {r['global_step']} updates; "
                     f"train macro F1 {r['train']['f1_macro']:.4f}, validation macro F1 {r['validation']['f1_macro']:.4f}.")
        for label in LABELS:
            d = r["validation"]["per_label"][label]
            lines.append(f"  - {label}: F1 {d['f1']:.4f}, recall {d['recall']:.4f}, "
                         f"{d['support']} gold / {d['predicted']} predicted.")
    lines += ["", "## Interpretation and limits", "",
              "Each seed has 139 training, 31 validation and 30 test posts. One validation decision is 3.23 percentage points. "
              "Per-class validation supports are only 6–9. Seeds are overlapping resamples of the same 200 posts, "
              "not independent replications. A post held out in one seed may train another seed; this preserves the inherited protocol.", "",
              "The original 3-epoch linear scheduler performs 27 updates and reaches zero learning rate. "
              "The controlled 8-epoch trajectory performs 72 updates; its epochs 3/6/8 share the same training history "
              "(27/54/72 updates). Its epoch-3 checkpoint is not the original 3-epoch scheduler. "
              "The reference reproduces original hyperparameters; GPU nondeterminism can prevent bitwise metric reproduction.", "",
              "Validation selection among several candidates can overfit this small validation pool. "
              "Longer inputs also change compute and dropout tensor shapes. No acceptance criterion is evaluated or revised here. "
              "The original test aggregate was already known before this intervention; a later test comparison is an exploratory "
              "follow-up, not a new pristine confirmatory study. Do not infer deployment readiness from validation improvement.", "",
              "Per-seed epoch histories, per-class metrics/confusion matrices and full train/validation prediction probabilities "
              "are saved under runs/. Checkpoints are local ignored artifacts. Originals remain backed up and hash-checked.", "",
              "After the reviewer selects a candidate, prepare a separate final-evaluation plan with "
              "`python scripts/validation_experiment.py prepare-final --experiment <directory> --candidate <name>`. "
              "This command locks checkpoint hashes and test identities; it does not run inference."]
    (exp / "validation_report.md").write_text("\n".join(lines) + "\n")
    curves = []
    for path in sorted((exp / "runs").glob("*/history.json")):
        metadata = read_json(path.parent / "metadata.json")
        for item in read_json(path):
            if "eval_loss" in item:
                curves.append({"run_id": metadata["run_id"], "seed": metadata["seed"],
                               "max_length": metadata["max_length"], "epoch": item["epoch"],
                               "optimizer_step": item["step"], "validation_loss": item["eval_loss"],
                               "validation_accuracy": item["eval_accuracy"],
                               "validation_f1_macro": item["eval_f1_macro"]})
    write_rows(exp / "learning_curves.csv", curves)
    print(json.dumps({"selected_candidate": selected["name"],
                      "mean_validation_f1_macro": selected["mean_validation_f1_macro"],
                      "mean_validation_accuracy": selected["mean_validation_accuracy"],
                      "test_evaluations_performed": 0}, indent=2))


def prepare_final(exp, candidate):
    protocol, frame, splits = verify(exp)
    results = read_json(exp / "validation_results.json")
    chosen = next((c for c in results["candidates"] if c["name"] == candidate), None)
    if not chosen:
        raise ValueError("Choose an existing validation candidate")
    target = exp / "final_evaluation_plan.json"
    if target.exists():
        raise ValueError("Final plan already locked; will not silently switch candidates")
    records = []
    for r in chosen["seeds"]:
        weights = exp / r["checkpoint"] / "model.safetensors"
        if sha(weights) != r["weights_sha256"]:
            raise ValueError("Selected weights changed")
        records.append({"seed": r["seed"], "checkpoint": r["checkpoint"],
                        "weights_sha256": r["weights_sha256"],
                        "checkpoint_files_sha256": {p.name: sha(p) for p in sorted(weights.parent.iterdir()) if p.is_file()},
                        "test_row_indices": splits[str(r["seed"])]["test"]})
    save_json(target, {"created_utc": datetime.now(timezone.utc).isoformat(),
                       "candidate": chosen["name"], "max_length": chosen["max_length"],
                       "protocol_sha256": sha(exp / "protocol.json"),
                       "validation_results_sha256": sha(exp / "validation_results.json"),
                       "runs": records, "status": "PREPARED_ONLY; NO TEST EVALUATION",
                       "future_output": "final_test_results.json (exclusive creation; never original files)",
                       "evaluation_policy": "One evaluation per seed, four-label accuracy/macro and per-class F1/confusion; "
                       "compare every seed against unchanged criteria1–3, preserve failures. No further tuning on test outcomes."})
    print(f"Prepared only: {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run", "report", "verify", "prepare-final"])
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--candidate")
    args = parser.parse_args()
    exp = args.experiment.resolve()
    if args.command == "prepare":
        prepare(exp)
    elif args.command == "verify":
        verify(exp)
        print("Frozen files and split identities verified; no test outcomes accessed")
    elif args.command == "report":
        report(exp)
    elif args.command == "prepare-final":
        prepare_final(exp, args.candidate)
    else:
        protocol, frame, splits = verify(exp)
        for seed in SEEDS:
            run_fit(exp, protocol, frame, splits, seed, 128, 3, "reference")
        for length in protocol["max_lengths"]:
            for seed in SEEDS:
                run_fit(exp, protocol, frame, splits, seed, length, 8, "controlled")
        report(exp)


if __name__ == "__main__":
    main()
