"""Selection/integrity checks; no training and no held-out model inference."""
import importlib.util
import json
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("validation_experiment", ROOT / "scripts/validation_experiment.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)
import evaluate_validation_selection as final_evaluation
import check_submission


class ValidationExperimentTests(unittest.TestCase):
    def test_splits_match_notebook_and_partition_exactly(self):
        import pandas as pd
        from sklearn.model_selection import train_test_split
        frame = pd.read_csv(ROOT / "labels.csv")
        for seed in experiment.SEEDS:
            actual = experiment.split_indices(frame, seed)
            rest, test = train_test_split(frame, test_size=.15, random_state=seed, stratify=frame.label)
            train, val = train_test_split(rest, test_size=.15 / (1 - .15), random_state=seed, stratify=rest.label)
            self.assertEqual(actual, {"train": list(train.index), "validation": list(val.index), "test": list(test.index)})
            self.assertEqual([len(actual[p]) for p in ("train", "validation", "test")], [139, 31, 30])
            self.assertEqual(set(sum(actual.values(), [])), set(frame.index))
            self.assertEqual(len(sum(actual.values(), [])), len(frame))

    def test_truncation_counts_token_loss_and_exact_boundary(self):
        result = experiment.audit_lengths([10, 128, 129, 400], 128)
        self.assertEqual(result["truncated_posts"], 2)
        self.assertEqual(result["discarded_tokens"], 273)
        self.assertAlmostEqual(result["retained_token_fraction"], 394 / 667)

    def test_macro_f1_includes_unpredicted_classes(self):
        result = experiment.score([0, 1, 2, 3], [1, 1, 1, 1])
        self.assertAlmostEqual(result["f1_macro"], .1)
        self.assertEqual(result["per_label"]["technical_report"]["predicted"], 0)
        self.assertEqual(result["confusion_matrix"], [[0, 1, 0, 0]] * 4)

    def candidate(self, name, f1s, length=128, epoch=3, loss=1):
        return {"name": name, "max_length": length, "epoch": epoch,
                "seeds": [{"validation": {"f1_macro": f1, "loss": loss}} for f1 in f1s]}

    def test_selection_uses_validation_even_with_better_training_or_test_values(self):
        a = self.candidate("a", [.2, .3, .4])
        b = self.candidate("b", [.4, .4, .4])
        a["test_f1"] = 1
        a["train_f1"] = 1
        self.assertEqual(experiment.select_candidate([a, b])["name"], "b")

    def test_selection_tiebreak_is_precommitted_and_order_independent(self):
        a = self.candidate("unstable", [.2, .4, .6])
        b = self.candidate("stable", [.4, .4, .4], length=256)
        c = self.candidate("shorter", [.4, .4, .4])
        for candidates in ([a, b, c], [c, b, a]):
            self.assertEqual(experiment.select_candidate(candidates)["name"], "shorter")

    def test_verify_rejects_changed_originals_and_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            (exp / "originals").mkdir()
            (exp / "originals/results.json").write_text("original")
            experiment.save_json(exp / "preservation_manifest.json", {"sha256": {"results.json": "wrong"}})
            experiment.save_json(exp / "protocol.json", {"protected_sha256": {}, "artifact_sha256": {}})
            with self.assertRaisesRegex(ValueError, "Original backup changed"):
                experiment.verify(exp)

    def test_clean_clone_verifies_frozen_inputs_without_duplicate_original_backups(self):
        source = ROOT / "experiments/validation-20261018T234742Z"
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            for name in ("preservation_manifest.json", "protocol.json", "splits.json",
                         "truncation_audit.json", "token_lengths_train_validation.csv", "dataset_identities.json"):
                shutil.copy2(source / name, exp / name)
            protocol, frame, splits = experiment.verify(exp)
            self.assertEqual(len(frame), 200)
            self.assertEqual(len(splits["42"]["test"]), 30)

    def test_closeout_detects_inconsistent_saved_metrics_without_running_model(self):
        result = {"accuracy": 1., "f1_macro": 1., "per_label": {
            label: {"precision": 1., "recall": 1., "f1": 1., "support": n}
            for label, n in zip(experiment.LABELS, [5, 9, 8, 8])}}
        matrix = [[5, 0, 0, 0], [0, 9, 0, 0], [0, 0, 8, 0], [0, 0, 0, 8]]
        check_submission.check_metrics(result, matrix)
        result["accuracy"] = .5
        with self.assertRaisesRegex(ValueError, "Saved metric mismatch"):
            check_submission.check_metrics(result, matrix)

    def test_final_plan_refuses_unknown_candidate_without_inference(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            experiment.save_json(exp / "validation_results.json", {"candidates": []})
            with patch.object(experiment, "verify", return_value=({}, None, {})):
                with self.assertRaisesRegex(ValueError, "existing validation candidate"):
                    experiment.prepare_final(exp, "made-up")
            self.assertFalse((exp / "final_evaluation_plan.json").exists())

    def test_final_evaluation_requires_explicit_confirmation_before_access(self):
        from unittest.mock import patch
        with patch.object(final_evaluation, "validate_plan") as validate:
            with self.assertRaisesRegex(ValueError, "confirm-final-evaluation"):
                final_evaluation.evaluate(Path("unused"), "Adi")
            validate.assert_not_called()

    def test_final_evaluation_cannot_silently_query_test_twice(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            (exp / "final_evaluation_started.json").write_text("already reserved")
            with patch.object(final_evaluation, "validate_plan", return_value=({}, None)):
                with self.assertRaisesRegex(ValueError, "refusing repeated test evaluation"):
                    final_evaluation.evaluate(exp, "Adi", confirmed=True)

    def test_final_plan_rejects_changed_validation_results_before_loading_model(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            (exp / "protocol.json").write_text("frozen")
            (exp / "validation_results.json").write_text("changed")
            experiment.save_json(exp / "final_evaluation_plan.json", {
                "protocol_sha256": experiment.sha(exp / "protocol.json"),
                "validation_results_sha256": "original-digest"})
            with patch.object(final_evaluation, "verify", return_value=({}, None, {})):
                with self.assertRaisesRegex(ValueError, "Validation results changed"):
                    final_evaluation.validate_plan(exp)

    def test_prepare_final_locks_all_checkpoint_files_and_refuses_reselection(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            exp = Path(temp)
            (exp / "protocol.json").write_text("test protocol")
            records, splits = [], {}
            for seed in experiment.SEEDS:
                checkpoint = exp / "runs" / f"test-seed{seed}"
                checkpoint.mkdir(parents=True)
                (checkpoint / "model.safetensors").write_bytes(b"TEST FIXTURE ONLY")
                (checkpoint / "config.json").write_text("test config")
                records.append({"seed": seed, "checkpoint": str(checkpoint.relative_to(exp)),
                                "weights_sha256": experiment.sha(checkpoint / "model.safetensors")})
                splits[str(seed)] = {"test": [seed]}
            experiment.save_json(exp / "validation_results.json", {"candidates": [
                {"name": "test-candidate", "max_length": 256, "seeds": records}]})
            with patch.object(experiment, "verify", return_value=({}, None, splits)):
                experiment.prepare_final(exp, "test-candidate")
                with self.assertRaisesRegex(ValueError, "already locked"):
                    experiment.prepare_final(exp, "test-candidate")
            plan = experiment.read_json(exp / "final_evaluation_plan.json")
            self.assertEqual(plan["status"], "PREPARED_ONLY; NO TEST EVALUATION")
            self.assertEqual([r["seed"] for r in plan["runs"]], experiment.SEEDS)
            self.assertTrue(all(set(r["checkpoint_files_sha256"]) == {"model.safetensors", "config.json"}
                                for r in plan["runs"]))


if __name__ == "__main__":
    unittest.main()
