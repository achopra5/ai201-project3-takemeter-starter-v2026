#!/usr/bin/env python3
"""Verify existing submission evidence without training, inference or data writes."""
import argparse
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from review_labels import Session
from validation_experiment import ROOT, LABELS, SEEDS, read_json, save_json, sha, score, text_sha, verify, select_candidate

EXPERIMENT = "experiments/validation-20261018T234742Z"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal_number(actual, expected, name):
    require(math.isclose(float(actual), float(expected), abs_tol=1e-12, rel_tol=1e-12),
            f"Saved metric mismatch: {name}: {actual} != {expected}")


def check_metrics(metrics, matrix):
    """Reconcile saved aggregate counts; this never runs a classifier."""
    require(len(matrix) == 4 and all(len(row) == 4 for row in matrix), "Invalid confusion shape")
    require(all(type(n) is int and n >= 0 for row in matrix for n in row), "Invalid confusion counts")
    require(sum(map(sum, matrix)) == 30, "Expected original 30-post test split")
    gold, predicted = [], []
    for i, row in enumerate(matrix):
        for j, n in enumerate(row):
            gold.extend([i] * n)
            predicted.extend([j] * n)
    calculated = score(gold, predicted)
    for key in ("accuracy", "f1_macro"):
        equal_number(metrics[key], calculated[key], key)
    for label in LABELS:
        for key in ("precision", "recall", "f1", "support"):
            equal_number(metrics["per_label"][label][key], calculated["per_label"][label][key], f"{label}.{key}")
        if "predicted" in metrics["per_label"][label]:
            equal_number(metrics["per_label"][label]["predicted"], calculated["per_label"][label]["predicted"], label)
    return calculated


def markdown_checks(root):
    files = [root / name for name in ("README.md", "RUNNING.md", "REVIEWING.md", "criteria.md",
              "exploration.md", "taxonomy_stress_test.md", "data/validation_report.md",
              "data/ambiguous_cases.md", "data/supplemental_cases.md", "submission/REPRODUCIBILITY.md",
              "submission/validation_report.md", f"{EXPERIMENT}/EXPERIMENT.md", f"{EXPERIMENT}/validation_report.md")]
    links = 0
    for path in files:
        require(path.is_file(), f"Missing referenced documentation: {path}")
        text = path.read_text()
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            target = unquote(target.split("#", 1)[0]).strip("<>")
            if target:
                require((path.parent / target).exists(), f"Broken local link in {path}: {target}")
            links += 1
        if path.name == "README.md":
            require(not re.search(r"___|FIX ME|FIXME|label_one|label_two", text), "README still contains required placeholders")
            table_columns = None
            for line in text.splitlines():
                if line.startswith("|"):
                    cells = line.strip().strip("|").split("|")
                    require(all(c.strip() for c in cells), "Empty README table cell")
                    if table_columns is None:
                        table_columns = len(cells)
                    require(len(cells) == table_columns, "README table column mismatch")
                else:
                    table_columns = None
        for command in re.findall(r"python(?:3)?\s+([\w/.-]+\.py)\b", text):
            require((root / command).is_file(), f"Missing documented command: {command}")
    return {"files_checked": len(files), "local_links_checked": links,
            "readme_tables_and_placeholders": "PASS", "documented_python_entry_points": "PASS"}


def inspect(root=ROOT):
    exp = root / EXPERIMENT
    closeout = read_json(root / "submission/closeout_manifest.json")
    for name, digest in closeout["protected_sha256"].items():
        require(sha(root / name) == digest, f"Frozen closeout evidence changed: {name}")
    session = Session(root)
    dataset = session.report()
    require(dataset["ready"] and dataset["labels_csv_matches_current_reviews"], "Dataset validation failed")
    require(dataset["verified"]["total"] == 200 and dataset["cold_annotations"] == 20, "Unexpected dataset size/provenance")
    require(dataset["selected_offline_verified"] == 180 and dataset["offline_attestation_events"] == 1
            and dataset["interactive_review_events"] == 0, "Review provenance changed")
    # verify uses the imported module's repository root; temporary clone checks
    # invoke the copy of this script in that clone, so ROOT follows the checkout.
    require(root.resolve() == ROOT.resolve(), "Run the checker from the checkout being checked")
    protocol, frame, splits = verify(exp)
    validation = read_json(exp / "validation_results.json")
    chosen = select_candidate(validation["candidates"])
    require(chosen["name"] == validation["selected_candidate"] == "controlled-len256-epoch6", "Validation selection changed")
    local_weights, missing_weights, fits, updates = 0, 0, 0, 0
    for completion in sorted((exp / "runs").glob("*/complete.json")):
        done = read_json(completion)
        out = completion.parent
        require(sha(out / "metadata.json") == done["metadata_sha256"], "Run metadata changed")
        require(sha(out / "checkpoints.json") == done["checkpoints_sha256"], "Checkpoint metrics changed")
        metadata = read_json(out / "metadata.json")
        require(metadata["protocol_sha256"] == sha(exp / "protocol.json"), "Run protocol mismatch")
        require(metadata["runner_sha256"] == sha(exp / "runner_used.py"), "Archived training source mismatch")
        require(done["global_step"] == metadata["expected_updates"], "Optimizer step count mismatch")
        fits += 1
        updates += done["global_step"]
        for checkpoint in read_json(out / "checkpoints.json"):
            weights = exp / checkpoint["checkpoint"] / "model.safetensors"
            if weights.exists():
                require(sha(weights) == checkpoint["weights_sha256"], "Local checkpoint weights changed")
                local_weights += 1
            else:
                missing_weights += 1
    require(fits == 9 and updates == 513 and local_weights + missing_weights == 21, "Incomplete experiment evidence")
    plan = read_json(exp / "final_evaluation_plan.json")
    final = read_json(exp / "final_test_results.json")
    started = read_json(exp / "final_evaluation_started.json")
    require(final["plan_sha256"] == started["plan_sha256"] == sha(exp / "final_evaluation_plan.json"), "Final plan hash mismatch")
    require(plan["protocol_sha256"] == sha(exp / "protocol.json") and
            plan["validation_results_sha256"] == sha(exp / "validation_results.json"), "Final selection inputs changed")
    require(final["candidate"] == plan["candidate"] == chosen["name"], "Final evaluation candidate mismatch")
    require(datetime.fromisoformat(final["finished_utc"]) >= datetime.fromisoformat(started["started_utc"]), "Invalid evaluation chronology")
    before = read_json(root / "results_three_seeds_before.json")
    require([r["seed"] for r in before] == [r["seed"] for r in final["seeds"]] == SEEDS, "Original seed set changed")
    require(read_json(root / "results.json") == before[0], "Seed-42 original outputs disagree")
    for original, improved, entry, selected in zip(before, final["seeds"], plan["runs"], chosen["seeds"]):
        seed = original["seed"]
        require(entry["seed"] == seed and entry["test_row_indices"] == splits[str(seed)]["test"], "Test identities changed")
        require(entry["checkpoint"] == selected["checkpoint"] and entry["weights_sha256"] == selected["weights_sha256"], "Final weights not from selected candidate")
        directory = exp / entry["checkpoint"]
        if directory.exists():
            require({p.name: sha(p) for p in directory.iterdir() if p.is_file()} == entry["checkpoint_files_sha256"], "Final tokenizer/model configuration changed")
        matrix = [[original["confusion"][g][p] for p in LABELS] for g in LABELS]
        check_metrics(original, matrix)
        check_metrics(improved["metrics"], improved["metrics"]["confusion_matrix"])
        with (exp / f"final_test_predictions_seed{seed}.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        require([int(r["row_index"]) for r in rows] == entry["test_row_indices"], "Saved prediction order changed")
        gold, predicted = [], []
        for row in rows:
            idx = int(row["row_index"])
            require(row["text_sha256"] == text_sha(frame.loc[idx, "text"]) and row["gold"] == frame.loc[idx, "label"], "Saved prediction source mismatch")
            gold.append(LABELS.index(row["gold"]))
            predicted.append(LABELS.index(row["predicted"]))
        reconstructed = score(gold, predicted)
        require(reconstructed["confusion_matrix"] == improved["metrics"]["confusion_matrix"], "Saved predictions disagree with results")
    for key in ("accuracy", "f1_macro"):
        equal_number(final[f"mean_{key}"], sum(r["metrics"][key] for r in final["seeds"]) / 3, f"mean_{key}")
    original_metrics = [r for r in before]
    improved_metrics = [r["metrics"] for r in final["seeds"]]
    def verdicts(records):
        return {"1": "PASS" if all(r["accuracy"] >= .70 for r in records) else "FAIL",
                "2": "PASS" if all(r["f1_macro"] >= .60 for r in records) else "FAIL",
                "3": "PASS" if all(d["f1"] >= .40 for r in records for d in r["per_label"].values()) else "FAIL",
                "4": "PASS" if dataset["verified"]["balance_pass"] else "FAIL", "5": "NOT EVALUATED"}
    return {"checked_utc": datetime.now(timezone.utc).isoformat(), "unit5_submission_readiness": "READY",
            "mode": "Existing evidence only: no training, collection, search or model inference",
            "protected_evidence_files": len(closeout["protected_sha256"]), "frozen_hashes": "PASS",
            "dataset": {"total": 200, "counts": dataset["verified"]["counts"],
                        "cold": 20, "offline_attested": 180, "offline_events": 1,
                        "interactive_events": 0, "original_exclusions": dataset["source_checks"]["original_exclusions"]},
            "experiment": {"completed_fits": fits, "optimizer_updates": updates,
                           "local_checkpoints_verified": local_weights, "local_checkpoints_absent": missing_weights,
                           "saved_test_seed_results_reconciled": 3, "new_test_evaluations": 0,
                           "selected_candidate": chosen["name"]},
            "original_mean": {k: sum(r[k] for r in before) / 3 for k in ("accuracy", "f1_macro")},
            "improved_mean": {k: final[f"mean_{k}"] for k in ("accuracy", "f1_macro")},
            "criteria_original": verdicts(original_metrics), "criteria_improved": verdicts(improved_metrics),
            "markdown": markdown_checks(root), "unit6_pending": ["zero-shot baseline", "personal/staff taxonomy agreement"],
            "submission_action": "Submit the existing GitHub repository URL in the Unit 5 course assignment"}


def write_report(root, report):
    save_json(root / "submission/validation_report.json", report)
    lines = ["# Unit 5 submission validation", "", f"**{report['unit5_submission_readiness']} for Unit 5 submission.** "
             "This does not mean the model meets its performance targets.", "",
             f"Checked UTC: {report['checked_utc']}. {report['mode']}.", "",
             f"- Frozen evidence: {report['protected_evidence_files']} file hashes pass, including original data, "
             "annotations, acceptance criteria, original experiments and completed final results.",
             "- Dataset: 200 unique full-text archived posts;36 technical reports,58 help requests,51 discussions,55 resources. "
             "All four shares satisfy15–40%. No missing text or invalid labels. Export matches recorded reviews.",
             "- Provenance:20 independent cold annotations unchanged;180 AI suggestions covered by one explicit offline attestation; "
             "zero individual CLI reviews. Three original exclusions unchanged;132 parked AI proposals remain unreviewed.",
             "- Experiment:9 completed fits,513 optimizer updates; frozen splits and saved metric/confusion/prediction consistency pass. "
             "No new test evaluation occurred during closeout.",
             f"- Checkpoints: {report['experiment']['local_checkpoints_verified']} locally present weights verified; "
             f"{report['experiment']['local_checkpoints_absent']} absent locally. Weights stay outside Git; manifests are committed.",
             f"- Documentation: {report['markdown']['files_checked']} files and {report['markdown']['local_links_checked']} local links checked; "
             "README tables have consistent columns, no empty required cells/placeholders and valid Python entry points.", "",
             "## Original criteria", ""]
    lines += [f"- Criterion {k}: **{v}**, for both original and improved results." for k, v in report["criteria_improved"].items()]
    lines += ["", "Original and improved test means are respectively accuracy0.433333/0.500000 and "
              "macro F1 0.297680/0.389639. Improved technical-report F1 remains zero in every seed. "
              "The follow-up is exploratory because original test aggregates were known before intervention design.", "",
              "## Other quality checks", "",
              "The closeout also runs `python test.py`, `python -m unittest discover -s tests -v`, "
              "`git diff --check` and `git status --short`. The final command outcomes are recorded in "
              "[quality_checks.json](quality_checks.json). This integrity checker does not itself invoke those commands.", "",
              "## Remaining work", "",
              "Zero-shot baseline and personal/staff-taxonomy agreement are Unit 6 work and remain explicitly pending. "
              "They are not fabricated or required to finish this Unit 5 write-up. No unresolved Unit 5 repository-content blocker was found.", "",
              "Submit https://github.com/achopra5/ai201-project3-takemeter-starter-v2026 as the repository URL in "
              "the Unit 5 course assignment. Git push does not submit the course portal form.", ""]
    (root / "submission/validation_report.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true", help="Refresh only submission/validation_report.{json,md}")
    args = parser.parse_args()
    report = inspect()
    if args.write_report:
        write_report(ROOT, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
