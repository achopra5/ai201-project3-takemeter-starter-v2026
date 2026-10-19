#!/usr/bin/env python3
"""Explicit, separate final test evaluation of a reviewer-selected frozen plan.

Not called by validation_experiment.py. Does not train or choose configurations.
"""
import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path

from validation_experiment import (LABELS, SEEDS, read_json, save_json, sha,
                                   text_sha, verify, score, write_rows)


def validate_plan(exp):
    protocol, frame, splits = verify(exp)
    plan = read_json(exp / "final_evaluation_plan.json")
    if plan["protocol_sha256"] != sha(exp / "protocol.json"):
        raise ValueError("Experiment protocol changed after final selection")
    if plan["validation_results_sha256"] != sha(exp / "validation_results.json"):
        raise ValueError("Validation results changed after final selection")
    results = read_json(exp / "validation_results.json")
    candidate = next((c for c in results["candidates"] if c["name"] == plan["candidate"]), None)
    if candidate is None or plan["max_length"] != candidate["max_length"]:
        raise ValueError("Plan does not match an evaluated validation candidate")
    if [r["seed"] for r in plan["runs"]] != SEEDS:
        raise ValueError("Final evaluation requires the three original seeds")
    for entry, original in zip(plan["runs"], candidate["seeds"]):
        checkpoint = (exp / entry["checkpoint"]).resolve()
        if not checkpoint.is_relative_to((exp / "runs").resolve()):
            raise ValueError("Checkpoint must belong to this experiment")
        if entry["checkpoint"] != original["checkpoint"] or entry["weights_sha256"] != original["weights_sha256"]:
            raise ValueError("Plan checkpoint differs from validation checkpoint")
        if sha(checkpoint / "model.safetensors") != entry["weights_sha256"]:
            raise ValueError("Selected checkpoint changed")
        files = {p.name: sha(p) for p in checkpoint.iterdir() if p.is_file()}
        if files != entry["checkpoint_files_sha256"]:
            raise ValueError("Selected model configuration or tokenizer changed")
        if entry["test_row_indices"] != splits[str(entry["seed"])]["test"]:
            raise ValueError("Original held-out examples changed")
    return plan, frame


def evaluate(exp, reviewer, confirmed=False):
    if not confirmed or not reviewer.strip():
        raise ValueError("Requires --confirm-final-evaluation and the selecting reviewer's name")
    plan, frame = validate_plan(exp)
    output = exp / "final_test_results.json"
    marker = exp / "final_evaluation_started.json"
    if output.exists() or marker.exists():
        raise ValueError("A final evaluation has already started; refusing repeated test evaluation")
    # Exclusive reservation precedes inference: no rerun can silently query test again.
    with marker.open("x") as stream:
        json.dump({"started_utc": datetime.now(timezone.utc).isoformat(), "reviewer": reviewer,
                   "plan_sha256": sha(exp / "final_evaluation_plan.json")}, stream, indent=2)
    import numpy as np
    import torch
    from datasets import Dataset
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              Trainer, TrainingArguments, set_seed)
    records = []
    for entry in plan["runs"]:
        seed = entry["seed"]
        set_seed(seed)
        checkpoint = exp / entry["checkpoint"]
        tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(checkpoint, local_files_only=True)
        subset = frame.loc[entry["test_row_indices"]]
        encoded = tokenizer(subset.text.tolist(), truncation=True, padding="max_length", max_length=plan["max_length"])
        encoded["labels"] = [LABELS.index(label) for label in subset.label]
        args = TrainingArguments(output_dir=str(exp / "final_trainer"),
                                 per_device_eval_batch_size=16, report_to="none", disable_tqdm=True)
        trainer = Trainer(model=model, args=args)
        prediction = trainer.predict(Dataset.from_dict(encoded))
        predicted = np.argmax(prediction.predictions, axis=-1)
        metrics = score(prediction.label_ids, predicted)
        metrics["loss"] = float(prediction.metrics["test_loss"])
        records.append({"seed": seed, "device": str(args.device), "metrics": metrics,
                        "criterion1_accuracy_ge_070": metrics["accuracy"] >= .70,
                        "criterion2_macro_f1_ge_060": metrics["f1_macro"] >= .60,
                        "criterion3_each_class_f1_ge_040": all(d["f1"] >= .40 for d in metrics["per_label"].values())})
        write_rows(exp / f"final_test_predictions_seed{seed}.csv", [
            {"row_index": idx, "text_sha256": text_sha(frame.loc[idx, "text"]),
             "gold": frame.loc[idx, "label"], "predicted": LABELS[int(y)]}
            for idx, y in zip(entry["test_row_indices"], predicted)])
        save_json(exp / f"final_test_seed{seed}.json", records[-1])
        del trainer, model
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    verify(exp)
    result = {"candidate": plan["candidate"], "reviewer": reviewer,
              "plan_sha256": sha(exp / "final_evaluation_plan.json"),
              "finished_utc": datetime.now(timezone.utc).isoformat(), "seeds": records,
              "mean_accuracy": sum(r["metrics"]["accuracy"] for r in records) / 3,
              "mean_f1_macro": sum(r["metrics"]["f1_macro"] for r in records) / 3,
              "acceptance": {name: all(r[name] for r in records) for name in (
                  "criterion1_accuracy_ge_070", "criterion2_macro_f1_ge_060", "criterion3_each_class_f1_ge_040")},
              "criterion5": "Staff-taxonomy agreement is a separate exercise; not measured here",
              "limitation": "Exploratory follow-up after known original test aggregates; no further tuning on these outcomes"}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Saved separate final evaluation: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--confirm-final-evaluation", action="store_true")
    args = parser.parse_args()
    evaluate(args.experiment.resolve(), args.reviewer, args.confirm_final_evaluation)


if __name__ == "__main__":
    main()
