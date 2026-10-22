#!/usr/bin/env python3
"""Fresh three-epoch fits: only input length changes from the frozen notebook.

Reuses function definitions (not executable cells) from the original notebook.
Never loads an earlier fine-tuned checkpoint or overwrites an original result.
"""
import argparse
import ast
import gc
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from validation_experiment import (ROOT, LABELS, SEEDS, BASE_MODEL, sha, text_sha,
                                   save_json, read_json, split_indices, write_rows)

EXPERIMENT = ROOT / "experiments/unit6-length256-three-epochs"
PROTECTED = ("labels.csv", "criteria.md", "takemeter.ipynb", "results.json",
             "results_three_seeds_before.json", "test_split.csv", "baseline_results.json",
             "label_definitions.txt", "data/staff_posts.csv", "data/staff_taxonomy.md")
FUNCTIONS = {"to_ids", "compute_metrics", "train_model", "evaluate", "confidence_report",
             "confusion_counts", "split_dataset"}


def now():
    return datetime.now(timezone.utc).isoformat()


def notebook_definitions(path):
    nodes = []
    for cell in read_json(path)["cells"]:
        if cell["cell_type"] == "code":
            nodes += [n for n in ast.parse("".join(cell["source"])).body
                      if isinstance(n, ast.FunctionDef) and n.name in FUNCTIONS]
    if {n.name for n in nodes} != FUNCTIONS or len(nodes) != len(FUNCTIONS):
        raise ValueError("Notebook function set changed")
    return ast.Module(body=nodes, type_ignores=[])


def check_recipe(args, seed):
    expected = {"num_train_epochs": 3, "learning_rate": 2e-5,
                "per_device_train_batch_size": 16, "per_device_eval_batch_size": 16,
                "gradient_accumulation_steps": 1, "weight_decay": 0., "warmup_steps": 0,
                "warmup_ratio": 0., "seed": seed, "max_steps": -1,
                "load_best_model_at_end": False, "dataloader_drop_last": False}
    for key, value in expected.items():
        if getattr(args, key) != value:
            raise ValueError(f"Training recipe changed: {key}")
    if args.lr_scheduler_type.value != "linear" or args.optim.value != "adamw_torch_fused":
        raise ValueError("Scheduler or optimizer differs from original installed defaults")


def prepare(exp=EXPERIMENT):
    import pandas as pd
    if (exp / "protocol.json").exists():
        raise ValueError("Protocol already exists; use run to resume completed seeds")
    frame = pd.read_csv(ROOT / "labels.csv", keep_default_na=False)
    splits = {str(s): split_indices(frame, s) for s in SEEDS}
    if len(frame) != 200 or set(frame.label) != set(LABELS):
        raise ValueError("Original dataset expected")
    test = pd.read_csv(ROOT / "test_split.csv", keep_default_na=False)
    if not frame.loc[splits['42']['test']][['text', 'label']].reset_index(drop=True).equals(test[['text', 'label']]):
        raise ValueError("Original seed-42 test split changed")
    protocol = {"created_utc": now(), "base_model": BASE_MODEL, "seeds": SEEDS,
                "label_order": LABELS, "before_max_length": 128, "after_max_length": 256,
                "epochs": 3, "learning_rate": 2e-5, "batch_size": 16,
                "scheduler": "linear", "optimizer_updates_per_seed": 27,
                "initialization": "Fresh pretrained DistilBERT and seeded classification head for each seed",
                "intervention": "Only MAX_LENGTH changes; exact original notebook helper functions and three-epoch horizon",
                "limitation": "Original and previous exploratory test outcomes already known; not a pristine confirmatory test",
                "protected_sha256": {n: sha(ROOT / n) for n in PROTECTED},
                "runner_sha256": sha(Path(__file__)), "splits": splits}
    save_json(exp / "protocol.json", protocol)
    (exp / "runner_used.py").write_bytes(Path(__file__).read_bytes())
    print(f"Prepared fixed single-variable protocol: {exp}", flush=True)


def verify_inputs(exp):
    protocol = read_json(exp / "protocol.json")
    for name, digest in protocol["protected_sha256"].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f"Frozen Unit 6 input changed: {name}")
    if sha(exp / "runner_used.py") != protocol["runner_sha256"]:
        raise ValueError("Archived Unit 6 runner changed")
    return protocol


def run(exp=EXPERIMENT):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import numpy as np
    import pandas as pd
    import torch
    import transformers
    from datasets import Dataset
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification, Trainer,
                              TrainingArguments, set_seed)
    protocol = verify_inputs(exp)
    if sha(Path(__file__)) != protocol["runner_sha256"]:
        raise ValueError("Use the exact prepared runner")
    if (ROOT / "results_three_seeds_after.json").exists():
        raise ValueError("After results already exist; refusing another evaluation")
    frame = pd.read_csv(ROOT / "labels.csv", keep_default_na=False)
    results = []
    for seed in SEEDS:
        out = exp / "runs" / f"seed{seed}"
        if (out / "complete.json").exists():
            done = read_json(out / "complete.json")
            for name, digest in done["sha256"].items():
                if sha(out / name) != digest:
                    raise ValueError(f"Completed run changed: {name}")
            results.append(read_json(out / "result.json"))
            continue
        if out.exists():
            raise ValueError(f"Incomplete run must be preserved and investigated: {out}")
        out.mkdir(parents=True)
        save_json(out / "started.json", {"started_utc": now(), "seed": seed,
                  "protocol_sha256": sha(exp / "protocol.json")})
        def training_args(**kw):
            kw["output_dir"] = str(out / "trainer")
            args = TrainingArguments(**kw)
            check_recipe(args, seed)
            return args
        namespace = dict(np=np, pd=pd, torch=torch, Dataset=Dataset,
                         accuracy_score=accuracy_score, f1_score=f1_score,
                         precision_recall_fscore_support=precision_recall_fscore_support,
                         train_test_split=train_test_split, AutoTokenizer=AutoTokenizer,
                         AutoModelForSequenceClassification=AutoModelForSequenceClassification,
                         Trainer=Trainer, TrainingArguments=training_args, set_seed=set_seed,
                         MAX_LENGTH=256)
        exec(compile(notebook_definitions(ROOT / "takemeter.ipynb"), "original-notebook-helpers", "exec"), namespace)
        tr, va, te = namespace["split_dataset"](frame, seed)
        if split_indices(frame, seed) != protocol["splits"][str(seed)]:
            raise ValueError("Split indices changed")
        print(f"START fresh seed={seed}, length=256, epochs=3, sizes={len(tr)}/{len(va)}/{len(te)}", flush=True)
        trainer, tokenizer = namespace["train_model"](tr, va, LABELS, seed, 3, 2e-5, 16, BASE_MODEL, quiet=True)
        if trainer.state.global_step != 27 or trainer.lr_scheduler.get_last_lr()[0] != 0:
            raise ValueError("Expected completed 27-update, three-epoch linear schedule")
        captured = []
        original_predict = trainer.predict
        def capture_predict(*args, **kwargs):
            output = original_predict(*args, **kwargs)
            captured.append(output)
            return output
        trainer.predict = capture_predict
        result = namespace["evaluate"](trainer, tokenizer, te, LABELS, seed=seed)
        trainer.predict = original_predict
        prediction = captured.pop()
        if captured:
            raise ValueError("Expected exactly one held-out prediction call")
        result.update(device=str(trainer.args.device), device_name="Apple Silicon GPU (MPS)" if trainer.args.device.type == "mps" else str(trainer.args.device),
                      torch_version=torch.__version__, max_length=256)
        predicted = np.argmax(prediction.predictions, axis=-1)
        counts = namespace["confusion_counts"](prediction.label_ids, predicted, LABELS)
        if counts != result["confusion"]:
            raise ValueError("Deterministic evaluation capture mismatch")
        write_rows(out / "test_predictions.csv", [
            {"row_index": idx, "text_sha256": text_sha(frame.loc[idx, 'text']),
             "gold": frame.loc[idx, 'label'], "predicted": LABELS[int(p)]}
            for idx, p in zip(protocol["splits"][str(seed)]["test"], predicted)])
        checkpoint = out / "epoch-3"
        trainer.save_model(str(checkpoint))
        tokenizer.save_pretrained(checkpoint)
        save_json(out / "result.json", result)
        save_json(out / "history.json", trainer.state.log_history)
        save_json(out / "metadata.json", {"seed": seed, "max_length": 256, "epochs": 3,
                  "global_step": trainer.state.global_step, "learning_rate_final": trainer.lr_scheduler.get_last_lr()[0],
                  "training_args": trainer.args.to_dict(), "python": platform.python_version(),
                  "torch": torch.__version__, "transformers": transformers.__version__,
                  "model_commit": getattr(trainer.model.config, "_commit_hash", None),
                  "checkpoint_files_sha256": {p.name: sha(p) for p in checkpoint.iterdir() if p.is_file()},
                  "protocol_sha256": sha(exp / "protocol.json")})
        save_json(out / "complete.json", {"finished_utc": now(), "sha256": {
            n: sha(out / n) for n in ("started.json", "metadata.json", "result.json", "history.json", "test_predictions.csv")}})
        results.append(result)
        print(f"DONE seed={seed}: accuracy={result['accuracy']:.6f}, macro F1={result['f1_macro']:.6f}", flush=True)
        del namespace, trainer, tokenizer, prediction, original_predict, capture_predict
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    verify_inputs(exp)
    save_json(ROOT / "results_three_seeds_after.json", results)
    save_json(exp / "complete.json", {"finished_utc": now(), "protocol_sha256": sha(exp / "protocol.json"),
              "after_sha256": sha(ROOT / "results_three_seeds_after.json"),
              "completed_seeds": SEEDS, "optimizer_updates": 81})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    args = parser.parse_args()
    (prepare if args.command == "prepare" else run)()


if __name__ == "__main__":
    main()
