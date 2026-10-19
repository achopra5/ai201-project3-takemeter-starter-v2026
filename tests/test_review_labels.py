"""Exercise provenance/review gates in disposable copies, never the real journal."""
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_labels import LABELS, ROOT, Session, atomic_text, csv_text, read_csv, review, plan_curation, attest_offline, canonical_hash


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="takemeter-review-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        manifest = json.loads((ROOT / "data/annotation_session.json").read_text())
        curation = json.loads((ROOT / "data/curation_manifest.json").read_text())
        files = set(manifest["pinned_files"]) | set(curation["pinned_files"]) | {
            "data/annotation_session.json", "data/curation_manifest.json", "README.md",
            "data/ambiguous_cases.md", "data/supplemental_cases.md"}
        files |= {str(Path(manifest["backup_directory"]) / name) for name in manifest["backup_sha256"]
                  if (ROOT / manifest["backup_directory"] / name).exists()}
        for name in files:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.session = Session(self.root)

    def rewrite_proposals_for_test(self, proposals):
        path = self.root / "data/proposed_annotations.csv"
        atomic_text(path, csv_text(proposals, list(proposals[0])))
        manifest_path = self.root / "data/annotation_session.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["pinned_files"]["data/proposed_annotations.csv"] = hashlib.sha256(path.read_bytes()).hexdigest()
        atomic_text(manifest_path, json.dumps(manifest))

    def accept_all_in_test_copy(self):
        # Review only the curated subset; the reserve stays genuinely pending.
        while self.session.review_queue_numbers():
            number = self.session.review_queue_numbers()[0]
            proposal = self.session.proposals[number]
            self.session.record(number, "exclude" if proposal["proposed_action"] == "exclude" else "accept",
                                proposal["proposed_label"], "TEST FIXTURE ONLY", proposal["rationale"])

    def attest_in_test_copy(self, answer=None):
        snapshot = self.session.offline_snapshot()
        phrase = f"APPROVE OFFLINE 180 {canonical_hash(snapshot)[:12]}"
        with patch("review_labels.sys.stdin.isatty", return_value=True), \
             patch("review_labels.sys.stdout.isatty", return_value=True), patch("builtins.print"), \
             patch("builtins.input", side_effect=answer if callable(answer) else None,
                   return_value=phrase if answer is None or callable(answer) else answer):
            return attest_offline(self.session, "TEST OFFLINE REVIEWER")

    def test_offline_attestation_is_one_event_with_no_invented_reviews(self):
        snapshot = self.session.offline_snapshot()
        self.session = self.attest_in_test_copy()
        lines = self.session.journal.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["event_type"], "offline_batch_attestation")
        self.assertEqual(event["snapshot"], snapshot)
        self.assertEqual(len(event["snapshot"]["selected_source_ids"]), 180)
        self.assertEqual(len(event["snapshot"]["curated_source_ids"]), 200)
        self.assertEqual(event["reviewer"], "TEST OFFLINE REVIEWER")
        self.assertFalse(event["review_time_recorded"])
        self.assertNotIn("reviewed_at", event)
        self.assertTrue(all("reviewed_at" not in m and "attested_at" not in m for m in snapshot["selected_proposals"]))
        resumed = Session(self.root)
        report = resumed.report()
        self.assertTrue(report["ready"])
        self.assertEqual(report["selected_offline_verified"], 180)
        self.assertEqual(report["interactive_review_events"], 0)
        self.assertEqual(report["offline_attestation_events"], 1)
        self.assertEqual(report["pending_reviews"], 0)
        self.assertEqual(report["all_pending_proposals"], 132)
        self.assertEqual(report["offline_attestations"][0]["exclusions"], 0)

    def test_offline_export_and_audit_preserve_cold_and_unselected_rows(self):
        self.session = self.attest_in_test_copy()
        report = self.session.export()
        rows = read_csv(self.root / "labels.csv")
        self.assertEqual(len(rows), 200)
        self.assertTrue(report["labels_csv_matches_current_reviews"])
        self.assertEqual(sum(r["note"].startswith("ai_suggested; human_verified_offline;") for r in rows), 180)
        cold = [{k: r[k] for k in ("text", "label", "note")} for r in self.session.queue if r["label"]]
        self.assertEqual(rows[:20], cold)
        with (self.root / "labels.csv").open(newline="") as stream:
            self.assertEqual(csv.DictReader(stream).fieldnames, ["text", "label", "note"])
        audit = self.session.audit_rows()
        covered = [r for r in audit if r["status"] == "human_verified_offline"]
        self.assertEqual(len(covered), 180)
        self.assertTrue(all(not r["reviewed_at"] and r["review_action"] == "attest_offline" for r in covered))
        self.assertEqual(len({r["attested_at"] for r in covered}), 1)
        self.assertEqual(len({r["attestation_id"] for r in covered}), 1)
        self.assertEqual(sum(r["status"] == "cold" for r in audit), 20)
        self.assertEqual(sum(r["status"] == "excluded_original" for r in audit), 3)
        self.assertTrue(all(r["final_note"] == r["original_note"] for r in audit if r["status"] in ("cold", "excluded_original")))
        outside = [r for r in audit if r["status"] == "ai_suggested"]
        self.assertEqual(len(outside), 132)
        self.assertTrue(all(not r["attestation_id"] and not r["final_label"] for r in outside))
        self.assertEqual(len(read_csv(self.root / "data/curated_review_queue.csv")), 0)
        self.assertIn("approved by offline batch attestation", (self.root / "data/supplemental_cases.md").read_text())
        self.assertNotIn("Review status: pending", (self.root / "data/supplemental_cases.md").read_text())

    def test_offline_confirmation_is_required_and_exact(self):
        for answer in ("", "yes", "APPROVE OFFLINE 180 wrong"):
            with self.subTest(answer=answer), self.assertRaisesRegex(ValueError, "cancelled"):
                self.attest_in_test_copy(answer)
            self.assertFalse(self.session.journal.exists())
        with patch("review_labels.sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(ValueError, "interactive terminal"):
                attest_offline(self.session, "TEST OFFLINE REVIEWER")
        self.assertFalse(self.session.journal.exists())

    def test_offline_interrupted_confirmation_does_not_write(self):
        def interrupt(_):
            raise EOFError
        with self.assertRaises(EOFError):
            self.attest_in_test_copy(interrupt)
        self.assertFalse(self.session.journal.exists())

    def test_offline_count_and_reviewer_must_match(self):
        with self.assertRaisesRegex(ValueError, "scope mismatch"):
            self.session.offline_snapshot(expected_count=179)
        with patch("review_labels.sys.stdin.isatty", return_value=True), \
             patch("review_labels.sys.stdout.isatty", return_value=True):
            with self.assertRaisesRegex(ValueError, "reviewer's name"):
                attest_offline(self.session, " ")
        self.assertFalse(self.session.journal.exists())

    def test_offline_rechecks_frozen_sources_after_confirmation(self):
        phrase = f"APPROVE OFFLINE 180 {canonical_hash(self.session.offline_snapshot())[:12]}"
        def mutate(_):
            path = self.root / "data/annotation_queue.csv"
            path.write_bytes(path.read_bytes() + b"\n")
            return phrase
        with self.assertRaisesRegex(ValueError, "Integrity check"):
            self.attest_in_test_copy(mutate)
        self.assertFalse(self.session.journal.exists())

    def test_offline_rechecks_selection_after_confirmation(self):
        phrase = f"APPROVE OFFLINE 180 {canonical_hash(self.session.offline_snapshot())[:12]}"
        def mutate(_):
            path = self.root / "data/curation_manifest.json"
            policy = json.loads(path.read_text())
            policy["help_seed"] = 7
            path.write_text(json.dumps(policy))
            return phrase
        with self.assertRaisesRegex(ValueError, "scope changed"):
            self.attest_in_test_copy(mutate)
        self.assertFalse(self.session.journal.exists())

    def test_offline_duplicate_and_existing_cli_decisions_are_refused(self):
        self.session = self.attest_in_test_copy()
        original = self.session.journal.read_bytes()
        with self.assertRaisesRegex(ValueError, "wholly unreviewed"):
            self.session.offline_snapshot()
        self.assertEqual(self.session.journal.read_bytes(), original)

    def test_offline_journal_detects_tampered_scope(self):
        self.session = self.attest_in_test_copy()
        event = json.loads(self.session.journal.read_text())
        event["snapshot"]["selected_source_ids"][0] = "wrong-id"
        self.session.journal.write_text(json.dumps(event) + "\n")
        with self.assertRaisesRegex(ValueError, "scope or frozen"):
            Session(self.root)

    def test_offline_cannot_silently_rebind_changed_proposal_files(self):
        self.session = self.attest_in_test_copy()
        path = self.root / "data/proposed_annotations.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        manifest_path = self.root / "data/annotation_session.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["pinned_files"]["data/proposed_annotations.csv"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "scope or frozen"):
            Session(self.root)

    def test_later_cli_correction_is_distinct_from_historical_batch(self):
        self.session = self.attest_in_test_copy()
        self.session.record(24, "correct", "discussion", "TEST CLI REVIEWER", "Test-only correction")
        resumed = Session(self.root)
        self.assertEqual(len(resumed.events), 2)
        self.assertEqual(resumed.report()["selected_offline_verified"], 179)
        self.assertEqual(resumed.report()["interactive_review_events"], 1)
        row = resumed.audit_rows()[23]
        self.assertEqual(row["status"], "human_verified")
        self.assertTrue(row["reviewed_at"])
        self.assertFalse(row["attestation_id"])
        resumed.record(24, "defer", "", "TEST CLI REVIEWER", "Reopened for test")
        self.assertEqual(Session(self.root).report()["pending_reviews"], 1)

    def test_initial_state_does_not_verify_ai(self):
        report = self.session.report()
        self.assertEqual(report["pending_reviews"], 180)
        self.assertEqual(report["human_verified_after_ai"], 0)
        self.assertEqual(report["verified"]["total"], 20)
        self.assertEqual(report["projected"]["total"], 200)
        self.assertEqual(report["projected"]["counts"], dict(technical_report=36, help_request=58, discussion=51, resource_share=55))
        self.assertEqual(report["minimum_additional_examples_at_200"]["technical_report"], 0)
        self.assertTrue(report["source_checks"]["passed"])
        self.assertFalse(report["ready"])
        self.assertFalse(self.session.journal.exists())

    def test_pending_export_is_refused_without_creating_labels(self):
        with self.assertRaisesRegex(ValueError, "180 selected proposals"):
            self.session.export()
        self.assertFalse((self.root / "labels.csv").exists())

    def test_source_and_backup_byte_integrity(self):
        queue = self.root / "data/annotation_queue.csv"
        queue.write_bytes(queue.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Integrity check"):
            Session(self.root)

    def test_clean_clone_without_redundant_backups_uses_identical_frozen_sources(self):
        shutil.rmtree(self.root / "data/backups", ignore_errors=True)
        report = Session(self.root).report()
        self.assertTrue(report["source_checks"]["passed"])
        self.assertEqual(report["cold_annotations"], 20)
        self.assertEqual(report["pending_reviews"], 180)

    def test_present_corrupt_backup_is_never_ignored(self):
        manifest = json.loads((self.root / "data/annotation_session.json").read_text())
        backup = self.root / manifest["backup_directory"] / "annotation_queue.csv"
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes((self.root / "data/annotation_queue.csv").read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Backup changed"):
            Session(self.root)

    def test_taxonomy_change_invalidates_session(self):
        readme = self.root / "README.md"
        readme.write_text(readme.read_text().replace("### `technical_report`", "### Revised report"))
        with self.assertRaisesRegex(ValueError, "Taxonomy changed"):
            Session(self.root)

    def test_proposal_cannot_claim_cold(self):
        proposals = read_csv(self.root / "data/proposed_annotations.csv")
        proposals[0]["note"] = "cold"
        self.rewrite_proposals_for_test(proposals)
        with self.assertRaisesRegex(ValueError, "Invalid AI proposal"):
            Session(self.root)

    def test_proposal_cannot_touch_original_decisions(self):
        proposals = read_csv(self.root / "data/proposed_annotations.csv")
        cold = self.session.queue[1]
        source = self.session.candidates[cold["source_url"]]
        p = proposals[0]
        p.update(queue_row=2, text=cold["text"], source_url=cold["source_url"],
                 source_id=source["source_id"], text_sha256=hashlib.sha256(cold["text"].encode()).hexdigest())
        self.rewrite_proposals_for_test(proposals)
        with self.assertRaisesRegex(ValueError, "overwrite an existing decision"):
            Session(self.root)

    def test_resume_accept_correct_exclude_and_reopen(self):
        self.session.record(24, "accept", "resource_share", "TEST FIXTURE ONLY", "")
        self.session.record(26, "correct", "help_request", "TEST FIXTURE ONLY", "Test-only correction")
        self.session.record(46, "exclude", "", "TEST FIXTURE ONLY", "Missing results")
        resumed = Session(self.root)
        self.assertEqual(len(resumed.decisions), 3)
        self.assertEqual(resumed.report()["pending_reviews"], 180 - resumed.report()["selected_human_verified"])
        self.assertEqual(resumed.report()["human_verified_after_ai"], 2)
        self.assertEqual(resumed.report()["human_exclusions"], 1)
        self.assertTrue(all("ai_suggested; human_verified" in r["note"] for r in resumed.final_rows()[20:]))
        resumed.record(26, "defer", "", "TEST FIXTURE ONLY", "Reopen test")
        again = Session(self.root)
        self.assertNotIn(26, again.decisions)
        self.assertEqual(len(again.events), 4)
        self.assertEqual(again.report()["pending_reviews"], 180 - again.report()["selected_human_verified"])

    def test_invalid_decisions_cannot_be_saved(self):
        for action, label, reason in (("accept", "discussion", ""), ("correct", "invalid", "reason"),
                                     ("correct", "discussion", ""), ("exclude", "", "")):
            with self.subTest(action=action, label=label, reason=reason):
                with self.assertRaises(ValueError):
                    self.session.record(24, action, label, "TEST FIXTURE ONLY", reason)
        self.assertFalse(self.session.journal.exists())

    def test_noninteractive_review_is_refused(self):
        with patch("review_labels.sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(ValueError, "interactive terminal"):
                review(self.session, "TEST FIXTURE ONLY")
        self.assertFalse(self.session.journal.exists())

    def test_interrupted_note_does_not_verify(self):
        with patch("review_labels.sys.stdin.isatty", return_value=True), \
             patch("review_labels.sys.stdout.isatty", return_value=True), \
             patch("builtins.print"), patch("builtins.input", side_effect=["", "a", EOFError]):
            with self.assertRaises(EOFError):
                review(self.session, "TEST FIXTURE ONLY", 24)
        self.assertFalse(self.session.journal.exists())

    def test_export_preserves_cold_exactly_and_meets_balance(self):
        self.accept_all_in_test_copy()
        report = self.session.export()
        with (self.root / "labels.csv").open(newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            self.assertEqual(reader.fieldnames, ["text", "label", "note"])
        original_cold = [{k: r[k] for k in ("text", "label", "note")} for r in self.session.queue if r["label"]]
        self.assertEqual(rows[:20], original_cold)
        self.assertEqual(len(rows), 200)
        self.assertEqual(sum(r["note"].split(";", 1)[0] == "cold" for r in rows), 20)
        self.assertTrue(all(r["label"] in LABELS for r in rows))
        self.assertEqual(report["pending_reviews"], 0)
        self.assertTrue(report["labels_csv_matches_current_reviews"])
        self.assertTrue(report["ready"])
        self.assertEqual(report["all_pending_proposals"], 132)
        self.assertEqual(report["curation"]["cold_help_selected"], 13)
        self.assertIn("READY", (self.root / "README.md").read_text())
        self.assertIn("0 selected AI proposals await", (self.root / "README.md").read_text())
        self.session.record(24, "correct", "discussion", "TEST FIXTURE ONLY", "Test revision")
        self.assertFalse(self.session.report()["labels_csv_matches_current_reviews"])
        self.session.export()
        self.assertEqual(len(list((self.root / "data/backups").glob("labels-*.csv"))), 1)
        Session(self.root)  # README status refresh must not invalidate taxonomy.

    def test_missing_readme_marker_fails_before_export(self):
        self.accept_all_in_test_copy()
        path = self.root / "README.md"
        path.write_text(path.read_text().replace("<!-- MILESTONE4_STATUS_START -->", ""))
        with self.assertRaisesRegex(ValueError, "status block"):
            self.session.export()
        self.assertFalse((self.root / "labels.csv").exists())

    def test_audit_keeps_all_sources_and_distinguishes_pending(self):
        audit = self.session.audit_rows()
        self.assertEqual(len(audit), 335)
        self.assertEqual(audit[0]["original_note"], self.session.queue[0]["note"])
        self.assertEqual(audit[0]["status"], "excluded_original")
        self.assertEqual(audit[1]["final_note"], "cold")
        self.assertEqual(audit[23]["status"], "ai_suggested")
        self.assertEqual(audit[23]["final_label"], "")
        self.assertEqual(audit[23]["final_note"], "")
        self.assertTrue(all(r["source_url"] for r in audit))

    def test_corrupt_journal_fails_closed(self):
        self.session.journal.write_text('{"broken":')
        with self.assertRaisesRegex(ValueError, "Invalid review journal"):
            Session(self.root)

    def test_curated_queue_contains_only_selected_pending_inclusions(self):
        self.session.write_reports()
        rows = read_csv(self.root / "data/curated_review_queue.csv")
        self.assertEqual(len(rows), 180)
        self.assertEqual(sum(r["proposed_label"] == "help_request" for r in rows), 45)
        self.assertTrue(all(r["proposed_action"] == "label" for r in rows))
        self.assertTrue(all(int(r["queue_row"]) in self.session.selection()["selected_rows"] for r in rows))
        first_help = next(i for i, r in enumerate(rows) if r["proposed_label"] == "help_request")
        self.assertTrue(all(r["proposed_label"] == "help_request" for r in rows[first_help:]))
        self.assertTrue(all(n in {int(r["queue_row"]) for r in rows} for n in range(321, 336)))

    def test_help_exclusion_promotes_seeded_reserve_without_changing_labels(self):
        before = self.session.selection()
        helpers = [r for r in self.session.effective_records() if r["effective_label"] == "help_request" and not r["cold"]]
        chosen = next(r for r in helpers if r["queue_row"] in before["selected_rows"])
        self.session.record(chosen["queue_row"], "exclude", "", "TEST FIXTURE ONLY", "Unusable test fixture")
        after = self.session.selection()
        self.assertEqual(len(after["selected_rows"]), 200)
        self.assertEqual(after["help_selected"], 58)
        self.assertNotIn(chosen["queue_row"], after["selected_rows"])
        promoted = set(after["selected_rows"]) - set(before["selected_rows"])
        reserves = sorted((r for r in helpers if r["queue_row"] not in before["selected_rows"]),
                          key=lambda r: hashlib.sha256(f"20261018:{r['source_id']}".encode()).hexdigest())
        self.assertEqual(promoted, {reserves[0]["queue_row"]})

    def test_reserve_corrected_to_non_help_is_always_retained(self):
        before = self.session.selection()
        reserve = next(r for r in self.session.effective_records()
                       if r["effective_label"] == "help_request" and r["queue_row"] not in before["selected_rows"])
        self.session.record(reserve["queue_row"], "correct", "technical_report", "TEST FIXTURE ONLY", "Test correction")
        after = self.session.selection()
        self.assertIn(reserve["queue_row"], after["selected_rows"])
        self.assertEqual(after["retained_non_help_counts"]["technical_report"], 37)
        self.assertEqual(after["help_selected"], 57)
        self.assertEqual(self.session.report()["projected"]["total"], 200)
        self.assertEqual(self.session.proposals[reserve["queue_row"]]["proposed_label"], "help_request")

    def test_all_verified_non_help_retained_even_when_balance_impossible(self):
        for number, proposal in self.session.proposals.items():
            if proposal["proposed_label"] == "technical_report":
                self.session.record(number, "correct", "discussion", "TEST FIXTURE ONLY", "Test-only correction")
        plan = self.session.selection()
        self.assertFalse(plan["feasible"])
        for record in self.session.effective_records():
            if record["effective_label"] in ("technical_report", "discussion", "resource_share"):
                self.assertIn(record["queue_row"], plan["selected_rows"])
        self.assertTrue(all(self.session.proposals[n]["proposed_label"] != "help_request"
                            for n in self.session.review_queue_numbers()))
        with self.assertRaises(ValueError):
            self.session.export()

    def test_supplemental_evidence_tampering_fails(self):
        path = self.root / self.session.curation["supplemental_candidate_file"]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Supplement integrity"):
            Session(self.root)

    def test_non_help_exclusion_increases_required_help(self):
        self.session.record(321, "exclude", "", "TEST FIXTURE ONLY", "Test-only exclusion")
        report = self.session.report()
        self.assertEqual(report["projected"]["counts"]["technical_report"], 35)
        self.assertEqual(report["curation"]["help_selected"], 59)
        self.assertEqual(report["projected"]["total"], 200)
        self.assertTrue(report["curation_checks"]["all_verified_non_help_retained"])

    def test_restored_ai_exclusion_becomes_retained_non_help(self):
        self.session.record(46, "correct", "technical_report", "TEST FIXTURE ONLY", "Restored for test")
        report = self.session.report()
        self.assertIn(46, report["curation"]["selected_rows"])
        self.assertEqual(report["projected"]["counts"]["technical_report"], 37)
        self.assertEqual(report["curation"]["help_selected"], 57)
        self.assertTrue(report["curation_checks"]["all_20_cold_selected"])

    def test_interactive_decision_refreshes_selection_files(self):
        helpers = [r for r in self.session.effective_records() if r["effective_label"] == "help_request"
                   and not r["cold"] and r["queue_row"] in self.session.selection()["selected_rows"]]
        number = helpers[0]["queue_row"]
        with patch("review_labels.sys.stdin.isatty", return_value=True), \
             patch("review_labels.sys.stdout.isatty", return_value=True), patch("builtins.print"), \
             patch("builtins.input", side_effect=["", "x", "Test-only unusable text"]):
            review(self.session, "TEST FIXTURE ONLY", number)
        rows = read_csv(self.root / "data/curated_review_queue.csv")
        self.assertNotIn(str(number), {r["queue_row"] for r in rows})
        report = json.loads((self.root / "data/validation_report.json").read_text())
        self.assertEqual(report["curation"]["help_selected"], 58)
        self.assertEqual(report["projected"]["total"], 200)


class PlanTests(unittest.TestCase):
    def records(self, technical, discussion, resource, help_count=200):
        result = []
        for label, count in (("technical_report", technical), ("discussion", discussion),
                             ("resource_share", resource), ("help_request", help_count)):
            for i in range(count):
                result.append(dict(queue_row=len(result) + 1, source_id=f"{label}-{i}",
                                   effective_label=label, cold=label == "help_request" and i < 13, verified=False))
        return result

    def test_user_example_is_exactly_200_and_64_help(self):
        plan = plan_curation(self.records(30, 51, 55))
        self.assertTrue(plan["feasible"])
        self.assertEqual(plan["help_selected"], 64)
        self.assertEqual(len(plan["selected_rows"]), 200)
        self.assertEqual(plan["cold_help_selected"], 13)

    def test_large_non_help_pool_requires_more_than_200_without_capping(self):
        plan = plan_curation(self.records(60, 100, 100))
        self.assertTrue(plan["feasible"])
        self.assertEqual(plan["retained_non_help_counts"], dict(technical_report=60, discussion=100, resource_share=100))
        self.assertEqual(plan["help_selected"], 46)
        self.assertEqual(len(plan["selected_rows"]), 306)

    def test_29_reports_cannot_support_200(self):
        plan = plan_curation(self.records(29, 51, 55))
        self.assertFalse(plan["feasible"])
        self.assertEqual(plan["retained_non_help_counts"]["discussion"], 51)

    def test_retaining_a_large_class_can_require_a_larger_total(self):
        plan = plan_curation(self.records(40, 90, 40))
        self.assertTrue(plan["feasible"])
        self.assertEqual(len(plan["selected_rows"]), 225)
        self.assertEqual(plan["help_selected"], 55)

    def test_help_shortage_is_reported(self):
        plan = plan_curation(self.records(30, 51, 55, help_count=63))
        self.assertFalse(plan["feasible"])
        self.assertEqual(plan["help_required"], 64)
        self.assertEqual(plan["help_available"], 63)

    def test_seed_is_repeatable_and_independent_of_input_order(self):
        records = self.records(36, 51, 55)
        first = plan_curation(records, seed=20261018)
        self.assertEqual(first, plan_curation(list(reversed(records)), seed=20261018))
        different = plan_curation(records, seed=7)
        self.assertNotEqual(first["selected_rows"], different["selected_rows"])
        cold = {r["queue_row"] for r in records if r["cold"]}
        self.assertTrue(cold <= set(first["selected_rows"]) & set(different["selected_rows"]))

    def test_integer_solver_matches_enumeration(self):
        import random
        rng = random.Random(414)
        for _ in range(100):
            counts = [rng.randrange(10, 110) for _ in range(3)]
            available = rng.randrange(30, 180)
            plan = plan_curation(self.records(*counts, help_count=available))
            valid = []
            for h in range(13, available + 1):
                n = sum(counts) + h
                if n >= 200 and all(15 * n <= 100 * c <= 40 * n for c in counts + [h]):
                    valid.append(h)
            self.assertEqual(plan["feasible"], bool(valid), (counts, available))
            if valid:
                self.assertEqual(plan["help_selected"], min(valid), (counts, available))


if __name__ == "__main__":
    unittest.main()
