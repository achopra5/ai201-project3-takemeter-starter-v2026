#!/usr/bin/env python3
"""Review TakeMeter proposals locally; never train or collect data.

python3 scripts/review_labels.py status
python3 scripts/review_labels.py review --reviewer YOUR_NAME
python3 scripts/review_labels.py attest-offline --reviewer YOUR_NAME --export
python3 scripts/review_labels.py export

CLI reviews record individual decisions. Offline approval records one explicitly
confirmed batch attestation, not invented per-post reviews. Frozen inputs,
proposals, and the append-only review journal remain separate.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

LABELS = ("technical_report", "help_request", "discussion", "resource_share")
ROOT = Path(__file__).resolve().parent.parent


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def csv_text(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def safe_display(text):
    # Reddit text is data, including pasted commands and terminal escape codes.
    return "".join(c if c in "\n\t" or unicodedata.category(c) not in ("Cc", "Cf")
                   else f"\\u{ord(c):04x}" for c in text)


def ceil_div(a, b):
    return -(-a // b)


def plan_curation(records, seed=20261018, minimum_total=200):
    """Minimize help count, retaining every non-help record and every cold row.

    Records use current human labels when available, otherwise pending proposals.
    Solve integer 15–40% constraints, not rounded display percentages. Infeasible
    plans retain all non-help rows and disclose the conflict; never cap a class.
    """
    retained = [r for r in records if r["effective_label"] in LABELS and r["effective_label"] != "help_request"]
    helps = [r for r in records if r["effective_label"] == "help_request"]
    cold_help = [r for r in helps if r["cold"]]
    counts = Counter(r["effective_label"] for r in retained)
    m = len(retained)
    non_help_counts = [counts[label] for label in LABELS if label != "help_request"]
    lower = max(len(cold_help), minimum_total - m, ceil_div(15 * m, 85),
                *(ceil_div(100 * count, 40) - m for count in non_help_counts))
    upper = min(len(helps), 40 * m // 60, *(100 * count // 15 - m for count in non_help_counts))
    feasible = lower <= upper
    requested = min(len(helps), max(len(cold_help), lower))
    rank = lambda r: (digest(f"{seed}:{r['source_id']}"), r["source_id"])
    reserves = sorted((r for r in helps if not r["cold"]), key=rank)
    chosen_help = cold_help + reserves[:max(0, requested - len(cold_help))]
    chosen = {r["queue_row"] for r in retained + chosen_help}
    return dict(selected_rows=sorted(chosen), feasible=feasible,
                help_required=lower, help_upper_bound=upper, help_selected=len(chosen_help),
                help_available=len(helps), help_reserve=len(helps) - len(chosen_help),
                cold_help_selected=len(cold_help), seed=seed, minimum_total=minimum_total,
                retained_non_help_counts={label: counts[label] for label in LABELS if label != "help_request"},
                reason="Minimum feasible help sample" if feasible else
                "No help sample can meet size/balance while retaining all non-help posts. Review pending non-help labels or collect the deficient class; do not discard or relabel non-help posts.")


class Session:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.data = self.root / "data"
        self.manifest = json.loads((self.data / "annotation_session.json").read_text())
        for name, expected in self.manifest["pinned_files"].items():
            path = self.root / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Integrity check failed for {name}; restore the snapshot before review.")
        taxonomy = (self.root / "README.md").read_text().split("## Label Taxonomy\n", 1)[1].split("## The Dataset\n", 1)[0]
        if digest(taxonomy) != self.manifest["taxonomy_sha256"]:
            raise ValueError("Taxonomy changed since proposals; reconcile the annotation session before review.")
        backup = self.root / self.manifest["backup_directory"]
        for name, expected in self.manifest["backup_sha256"].items():
            if hashlib.sha256((backup / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Backup changed: {name}")
        self.queue = read_csv(self.data / "annotation_queue.csv")
        candidates = read_csv(self.data / "candidate_posts.csv")
        self.original_pool_size = len(self.queue)
        self.curation = json.loads((self.data / "curation_manifest.json").read_text())
        if (self.curation["original_pool_size"] != self.original_pool_size
                or set(self.curation["retain_labels"]) != set(LABELS) - {"help_request"}
                or self.curation["minimum_total"] < 200):
            raise ValueError("Invalid retention policy or original pool size")
        for name, expected in self.curation["pinned_files"].items():
            if hashlib.sha256((self.root / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Supplement integrity check failed for {name}")
        supplemental = read_csv(self.root / self.curation["supplemental_candidate_file"])
        self.queue.extend(dict(text=r["text"], label="", note="supplemental_pending", source_url=r["source_url"])
                          for r in supplemental)
        candidates.extend(supplemental)
        self.candidates = {r["source_url"]: r for r in candidates}
        if len(self.candidates) != len(candidates):
            raise ValueError("Duplicate candidate source URLs")
        self.proposals = {}
        self.proposal_hashes = {}
        proposal_files = [self.data / "proposed_annotations.csv", self.root / self.curation["supplemental_proposal_file"]]
        all_proposals = []
        for path in proposal_files:
            proposals = read_csv(path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            all_proposals.extend(proposals)
            self.proposal_hashes.update({int(p["queue_row"]): sha for p in proposals})
        for proposal in all_proposals:
            number = int(proposal["queue_row"])
            if number in self.proposals or not 1 <= number <= len(self.queue):
                raise ValueError("Duplicate or out-of-range proposal")
            row = self.queue[number - 1]
            source = self.candidates.get(row["source_url"], {})
            if (proposal["text"] != row["text"] or proposal["source_url"] != row["source_url"]
                    or proposal["text_sha256"] != digest(row["text"])
                    or proposal["source_id"] != source.get("source_id")):
                raise ValueError(f"Proposal text/source mismatch at row {number}")
            if row["label"] or row["note"].startswith("excluded:"):
                raise ValueError("Proposal would overwrite an existing decision")
            if (proposal["note"] != "ai_suggested" or not proposal["rationale"].strip()
                    or proposal["proposed_action"] not in ("label", "exclude")
                    or (proposal["proposed_action"] == "label" and proposal["proposed_label"] not in LABELS)
                    or (proposal["proposed_action"] == "exclude" and proposal["proposed_label"])
                    or proposal["alternative_label"] not in ("", *LABELS)):
                raise ValueError(f"Invalid AI proposal at row {number}")
            self.proposals[number] = proposal
        # Independently reconstruct each supplemental title/body from saved raw
        # archive evidence; a self-consistent CSV alone is not enough provenance.
        raw_cache = {}
        for source in supplemental:
            name = source["raw_file"]
            if name not in raw_cache:
                raw_cache[name] = {str(w["row_idx"]): w for w in json.loads((self.root / name).read_text())["rows"]}
            wrapper = raw_cache[name][source["archive_row_idx"]]
            raw = wrapper["row"]
            expected_url = "https://www.reddit.com" + raw["permalink"]
            if (wrapper.get("truncated_cells") or raw["id"] != source["source_id"]
                    or raw["title"] + "\n\n" + raw["selftext"] != source["text"]
                    or source["source_url"] != expected_url
                    or hashlib.sha256((self.root / name).read_bytes()).hexdigest() != source["raw_sha256"]):
                raise ValueError("Supplement does not match full archived evidence")
        expected = {i for i, r in enumerate(self.queue, 1)
                    if not r["label"] and not r["note"].startswith("excluded:")}
        if set(self.proposals) != expected:
            raise ValueError("Proposals do not cover exactly the previously undecided rows")
        self.journal = self.data / "annotation_reviews.jsonl"
        self.events = []
        self.decisions = {}
        self.attestations = {}
        if self.journal.exists():
            for line_number, line in enumerate(self.journal.read_text().splitlines(), 1):
                try:
                    event = json.loads(line)
                    self.validate_event(event)
                except (ValueError, KeyError, TypeError) as exc:
                    raise ValueError(f"Invalid review journal line {line_number}: {exc}") from exc
                self.events.append(event)
                self.apply_event(event)

    def offline_snapshot(self, expected_count=180):
        """Bind the complete selected AI batch, its 20 cold companions and inputs.

        This describes approval scope; it contains no per-post review events or
        dates. Parked help and AI exclusions are deliberately outside the scope.
        """
        plan = self.selection()
        numbers = [n for n in plan["selected_rows"] if n in self.proposals]
        if not plan["feasible"] or len(numbers) != expected_count or expected_count <= 0:
            raise ValueError(f"Offline scope mismatch: expected {expected_count} selected proposals, found {len(numbers)}; plan feasible={plan['feasible']}.")
        if any(n in self.decisions for n in numbers):
            raise ValueError("Offline batch must be wholly unreviewed; existing reviews/attestations cannot be overwritten or duplicated.")
        files = set(self.manifest["pinned_files"]) | set(self.curation["pinned_files"]) | {
            "data/annotation_session.json", "data/curation_manifest.json"}
        members = []
        for n in numbers:
            p = self.proposals[n]
            source = self.candidates[p["source_url"]]
            members.append(dict(queue_row=n, source_id=p["source_id"], source_url=p["source_url"],
                                text_sha256=p["text_sha256"], source_record_sha256=canonical_hash(source),
                                proposal_file_sha256=self.proposal_hashes[n], proposal_record_sha256=canonical_hash(p),
                                proposed_action=p["proposed_action"], proposed_label=p["proposed_label"]))
        return dict(expected_count=expected_count, selected_proposals=members,
                    selected_source_ids=[m["source_id"] for m in members],
                    curated_source_ids=[self.candidates[self.queue[n - 1]["source_url"]]["source_id"] for n in plan["selected_rows"]],
                    bound_file_sha256={name: hashlib.sha256((self.root / name).read_bytes()).hexdigest() for name in sorted(files)},
                    taxonomy_sha256=self.manifest["taxonomy_sha256"], help_seed=self.curation["help_seed"])

    def apply_event(self, event):
        if event.get("event_type") == "offline_batch_attestation":
            self.attestations[event["attestation_id"]] = event
            # Derive an in-memory lookup from the ONE batch record. These are
            # references to that record, never individual review journal events.
            for member in event["snapshot"]["selected_proposals"]:
                n = member["queue_row"]
                self.decisions[n] = dict(action="accept" if member["proposed_action"] == "label" else "exclude",
                                         label=member["proposed_label"], reviewer=event["reviewer"],
                                         review_method="offline_batch_attestation", attestation_id=event["attestation_id"],
                                         attested_at=event["attested_at"], reason="")
        elif event["action"] == "defer":
            self.decisions.pop(event["queue_row"], None)
        else:
            self.decisions[event["queue_row"]] = event

    def validate_attestation(self, event):
        if event["version"] != 1 or not event["reviewer"].strip():
            raise ValueError("Invalid offline attestation version/reviewer")
        timestamp = datetime.fromisoformat(event["attested_at"])
        if timestamp.utcoffset() is None:
            raise ValueError("Attestation timestamp must include its timezone")
        if event["confirmation_method"] != "explicit_terminal_phrase" or event["review_time_recorded"] is not False:
            raise ValueError("Offline attestation must distinguish confirmation time from unrecorded review times")
        snapshot = event["snapshot"]
        if snapshot != self.offline_snapshot(snapshot["expected_count"]):
            raise ValueError("Offline attestation scope or frozen source/proposal hashes changed")
        if event["snapshot_sha256"] != canonical_hash(snapshot):
            raise ValueError("Offline snapshot checksum mismatch")
        unsigned = {k: v for k, v in event.items() if k != "attestation_id"}
        if event["attestation_id"] != "offline-" + canonical_hash(unsigned):
            raise ValueError("Offline attestation checksum mismatch")

    def validate_event(self, event):
        if event.get("event_type") == "offline_batch_attestation":
            self.validate_attestation(event)
            return
        if event.get("event_type") not in (None, "interactive_review"):
            raise ValueError("Unknown review event type")
        proposal = self.proposals[event["queue_row"]]
        if (event["text_sha256"] != proposal["text_sha256"]
                or event["source_id"] != proposal["source_id"]
                or event["proposal_sha256"] != self.proposal_hashes[event["queue_row"]]):
            raise ValueError("Review belongs to different source text or proposals")
        if not event["reviewer"].strip() or not event["reviewed_at"].strip():
            raise ValueError("Reviewer identity and timestamp required")
        datetime.fromisoformat(event["reviewed_at"])
        action, label = event["action"], event["label"]
        if action not in ("accept", "correct", "exclude", "defer"):
            raise ValueError("Unknown review action")
        if action == "accept" and (proposal["proposed_action"] != "label" or label != proposal["proposed_label"]):
            raise ValueError("Acceptance must match the proposed label")
        if action in ("accept", "correct") and label not in LABELS:
            raise ValueError("Invalid reviewed label")
        if action in ("exclude", "defer") and label:
            raise ValueError("Excluded/deferred decisions cannot have labels")
        if action in ("correct", "exclude") and not event["reason"].strip():
            raise ValueError("Corrections and exclusions require an explanation")

    def record(self, number, action, label, reviewer, reason):
        proposal = self.proposals[number]
        event = dict(event_type="interactive_review", queue_row=number, source_id=proposal["source_id"],
                     text_sha256=proposal["text_sha256"],
                     proposal_sha256=self.proposal_hashes[number],
                     action=action, label=label, reviewer=reviewer,
                     reviewed_at=datetime.now(timezone.utc).isoformat(), reason=reason)
        self.append_event(event)

    def append_event(self, event):
        self.validate_event(event)
        # Logically append-only, atomically replaced to survive interrupted writes.
        # The CLI's exclusive lock prevents simultaneous writers losing events.
        previous = self.journal.read_text(encoding="utf-8") if self.journal.exists() else ""
        atomic_text(self.journal, previous + json.dumps(event, ensure_ascii=False) + "\n")
        self.events.append(event)
        self.apply_event(event)

    def decision_note(self, event):
        if event.get("review_method") == "offline_batch_attestation":
            return "ai_suggested; human_verified_offline; attestation_id=" + event["attestation_id"]
        return (f"ai_suggested; human_verified; {event['action']}"
                + ("; " + event["reason"] if event["reason"] else ""))

    def effective_records(self):
        records = []
        for number, row in enumerate(self.queue, 1):
            p, e = self.proposals.get(number, {}), self.decisions.get(number, {})
            label = row["label"] or (e.get("label", "") if e else p.get("proposed_label", ""))
            records.append(dict(queue_row=number, source_id=self.candidates[row["source_url"]]["source_id"],
                                effective_label=label, cold=bool(row["label"]),
                                verified=bool(row["label"] or e)))
        return records

    def selection(self):
        return plan_curation(self.effective_records(), self.curation["help_seed"], self.curation["minimum_total"])

    def review_queue_numbers(self):
        plan = self.selection()
        by_number = {r["queue_row"]: r for r in self.effective_records()}
        # Review all non-help categories first so the help budget is based on
        # their reviewed labels. Park help reviews if the constraints conflict.
        order = {"technical_report": 0, "discussion": 1, "resource_share": 2, "help_request": 3}
        pending = [n for n in plan["selected_rows"] if n in self.proposals and n not in self.decisions
                   and (plan["feasible"] or by_number[n]["effective_label"] != "help_request")]
        return sorted(pending, key=lambda n: (order[by_number[n]["effective_label"]],
                      digest(f"{self.curation['help_seed']}:{by_number[n]['source_id']}") if by_number[n]["effective_label"] == "help_request" else f"{n:08d}"))

    def labeled_rows(self, projected=False, curated=True):
        result = []
        selected = set(self.selection()["selected_rows"]) if curated else set(range(1, len(self.queue) + 1))
        for i, row in enumerate(self.queue, 1):
            if i not in selected:
                continue
            if row["label"]:
                result.append({key: row[key] for key in ("text", "label", "note")})
            elif i in self.decisions and self.decisions[i]["action"] != "exclude":
                event = self.decisions[i]
                note = self.decision_note(event)
                result.append(dict(text=row["text"], label=event["label"], note=note))
            elif projected and i not in self.decisions and self.proposals.get(i, {}).get("proposed_label"):
                result.append(dict(text=row["text"], label=self.proposals[i]["proposed_label"], note="ai_suggested"))
        return result

    def final_rows(self):
        return self.labeled_rows()

    def projected_rows(self):
        return self.labeled_rows(projected=True)

    def audit_rows(self):
        result = []
        selected = set(self.selection()["selected_rows"])
        records = {r["queue_row"]: r for r in self.effective_records()}
        for number, row in enumerate(self.queue, 1):
            source = self.candidates[row["source_url"]]
            p, e = self.proposals.get(number, {}), self.decisions.get(number, {})
            status = ("cold" if row["label"] else "excluded_original" if row["note"].startswith("excluded:")
                      else "human_excluded" if e.get("action") == "exclude"
                      else "human_verified_offline" if e.get("review_method") == "offline_batch_attestation"
                      else "human_verified" if e else "ai_suggested")
            final_label = row["label"] or (e.get("label", "") if e else "")
            final_note = row["note"] if row["label"] or status == "excluded_original" else ""
            if e:
                final_note = (("excluded: " + (e["reason"] or p["rationale"]) + "; ") if status == "human_excluded" else "") + self.decision_note(e)
            effective = records[number]["effective_label"]
            selection_reason = ("cold_preserved" if row["label"] else "human_excluded" if status == "human_excluded"
                                else "original_exclusion" if status == "excluded_original"
                                else "ai_proposed_exclusion_unreviewed" if not effective
                                else "retained_non_help" if effective != "help_request"
                                else "seeded_help_sample" if number in selected else "help_reserve_not_excluded")
            result.append(dict(queue_row=number, source_id=source["source_id"], source_url=row["source_url"],
                               pool="original" if number <= self.original_pool_size else "supplemental",
                               curation_selected=number in selected, selection_reason=selection_reason,
                               help_seed=self.curation["help_seed"],
                               help_random_rank=digest(f"{self.curation['help_seed']}:{source['source_id']}") if effective == "help_request" else "",
                               archive_row_idx=source.get("archive_row_idx", ""), raw_file=source.get("raw_file", ""),
                               retrieval_url=source.get("retrieval_url", ""), retrieved_utc=source.get("retrieved_utc", ""),
                               created_utc=source["created_utc"], source_dataset=source["source_dataset"],
                               text_sha256=digest(row["text"]), text=row["text"],
                               original_label=row["label"], original_note=row["note"], status=status,
                               proposed_action=p.get("proposed_action", ""), proposed_label=p.get("proposed_label", ""),
                               proposal_note=p.get("note", ""), rationale=p.get("rationale", ""),
                               alternative_label=p.get("alternative_label", ""), final_label=final_label, final_note=final_note,
                               review_action="attest_offline" if e.get("review_method") == "offline_batch_attestation" else e.get("action", ""),
                               review_method=e.get("review_method", "interactive_cli" if e else ""),
                               attestation_id=e.get("attestation_id", ""), attested_at=e.get("attested_at", ""),
                               reviewer=e.get("reviewer", ""),
                               reviewed_at=e.get("reviewed_at", ""), review_reason=e.get("reason", "")))
        return result

    def report(self):
        verified, projected = self.final_rows(), self.projected_rows()
        plan = self.selection()
        def distribution(rows):
            counts = Counter(r["label"] for r in rows)
            n = len(rows)
            return dict(total=n, counts={label: counts[label] for label in LABELS},
                        shares={label: counts[label] / n if n else 0 for label in LABELS},
                        balance_pass=bool(n) and all(15 * n <= 100 * counts[label] <= 40 * n for label in LABELS),
                        minimum_required=ceil_div(15 * n, 100), maximum_allowed=40 * n // 100)
        source_errors = []
        for row in self.queue:
            source = self.candidates.get(row["source_url"], {})
            match = re.fullmatch(r"https://www\.reddit\.com/r/LocalLLaMA/comments/([a-z0-9]+)/[^\s]*", row["source_url"])
            if (not match or match[1] != source.get("source_id") or row["text"] != source.get("text")
                    or source.get("source_dataset") != "pszemraj/LocalLLaMA-posts"):
                source_errors.append(row["source_url"])
        ids = [r["source_id"] for r in self.candidates.values()]
        normalized = [re.sub(r"\s+", " ", r["text"]).strip().casefold() for r in self.queue]
        text_errors = [i for i, r in enumerate(self.queue, 1)
                       if not r["text"].strip() or "\n\n" not in r["text"]
                       or not r["text"].split("\n\n", 1)[1].strip()]
        invalid_labels = [r["label"] for r in verified if r["label"] not in LABELS]
        cold = [r for r in self.queue if r["label"] and r["note"].split(";", 1)[0] == "cold"]
        cold_ok = len(cold) == 20 and all(r["label"] in LABELS for r in cold)
        pending = sum(n in self.proposals and n not in self.decisions for n in plan["selected_rows"])
        all_pending = len(self.proposals) - len(self.decisions)
        selected = set(plan["selected_rows"])
        records = self.effective_records()
        cold_selected = all(r["queue_row"] in selected for r in records if r["cold"])
        non_help_retained = all(r["queue_row"] in selected for r in records
                                if r["effective_label"] in LABELS and r["effective_label"] != "help_request")
        verified_non_help_retained = all(r["queue_row"] in selected for r in records
                                         if r["verified"] and r["effective_label"] in LABELS
                                         and r["effective_label"] != "help_request")
        source_pass = (not source_errors and not text_errors and len(ids) == len(set(ids)) == len(self.queue)
                       and len(normalized) == len(set(normalized)))
        dates = sorted(s["created_utc"] for s in self.candidates.values() if s["created_utc"])
        report = dict(status="NOT_READY", ready=False, source_checks=dict(
            passed=source_pass, queue_and_backups_unchanged=True, archive_matches=len(self.queue) - len(source_errors),
            source_errors=source_errors, missing_text_rows=text_errors, unique_source_ids=len(set(ids)),
            unique_normalized_texts=len(set(normalized)), invalid_labels=invalid_labels,
            cold_annotations_preserved=cold_ok,
            original_exclusions=sum(r["note"].startswith("excluded:") for r in self.queue)),
            source_date_range=[dates[0], dates[-1]] if dates else [],
            missing_source_dates=len(self.queue) - len(dates),
            cold_annotations=len(cold), ai_proposals=len(self.proposals), pending_reviews=pending,
            all_pending_proposals=all_pending, parked_proposals=all_pending - pending,
            original_pool_size=self.original_pool_size, supplemental_candidates=len(self.queue) - self.original_pool_size,
            curation=plan, review_queue_rows=self.review_queue_numbers(),
            curation_checks=dict(all_20_cold_selected=cold_selected,
                                 all_13_cold_help_selected=plan["cold_help_selected"] == 13,
                                 all_usable_non_help_retained=non_help_retained,
                                 all_verified_non_help_retained=verified_non_help_retained,
                                 selected_ai_labels_all_reviewed=pending == 0),
            selected_human_verified=sum(n in self.decisions and self.decisions[n]["action"] != "exclude" for n in plan["selected_rows"]),
            selected_offline_verified=sum(n in self.decisions and self.decisions[n]["action"] != "exclude"
                                         and self.decisions[n].get("review_method") == "offline_batch_attestation" for n in plan["selected_rows"]),
            interactive_review_events=sum(e.get("event_type") != "offline_batch_attestation" for e in self.events),
            offline_attestation_events=len(self.attestations),
            offline_attestations=[dict(attestation_id=e["attestation_id"], reviewer=e["reviewer"], attested_at=e["attested_at"],
                                       scope_count=e["snapshot"]["expected_count"], snapshot_sha256=e["snapshot_sha256"],
                                       classifications=sum(m["proposed_action"] == "label" for m in e["snapshot"]["selected_proposals"]),
                                       exclusions=sum(m["proposed_action"] == "exclude" for m in e["snapshot"]["selected_proposals"]))
                                  for e in self.attestations.values()],
            human_verified_after_ai=sum(e["action"] != "exclude" for e in self.decisions.values()),
            human_exclusions=sum(e["action"] == "exclude" for e in self.decisions.values()),
            proposed_exclusions=sum(p["proposed_action"] == "exclude" for p in self.proposals.values()),
            documented_boundary_cases=sum(bool(p["alternative_label"]) for p in self.proposals.values()),
            projected=distribution(projected), verified=distribution(verified),
            pool_projected=distribution(self.labeled_rows(projected=True, curated=False)),
            pool_verified=distribution(self.labeled_rows(curated=False)),
            minimum_additional_examples_at_200={label: max(0, 30 - distribution(projected)["counts"][label]) for label in LABELS},
            provenance_limit="Archive and Reddit IDs/URLs checked locally against original candidates; live Reddit availability and authorship not independently reauthenticated.",
            criteria={"1": "not evaluated: training deferred", "2": "not evaluated: training deferred",
                      "3": "not evaluated: training deferred", "4": "pending recorded review/attestation" if pending else "met" if distribution(verified)["balance_pass"] else "missed",
                      "5": "not evaluated: separate personal staff-taxonomy exercise"})
        report["ready"] = (source_pass and cold_ok and cold_selected and non_help_retained
                           and verified_non_help_retained and plan["cold_help_selected"] == 13
                           and not invalid_labels and pending == 0 and plan["feasible"]
                           and len(verified) >= 200 and report["verified"]["balance_pass"]
                           and report["documented_boundary_cases"] >= 3)
        report["status"] = "READY" if report["ready"] else "NOT_READY"
        labels_path = self.root / "labels.csv"
        report["labels_csv_matches_current_reviews"] = (labels_path.exists() and read_csv(labels_path) == verified)
        return report

    def write_reports(self):
        report = self.report()
        audit = self.audit_rows()
        atomic_text(self.data / "annotation_audit.csv", csv_text(audit, list(audit[0])))
        audit_by_row = {int(row["queue_row"]): row for row in audit}
        for filename in ("ambiguous_cases.md", "supplemental_cases.md"):
            path = self.data / filename
            if not path.exists():
                continue
            text = path.read_text()
            def update_case(match):
                block, number = match[0], int(match[1])
                row = audit_by_row[number]
                if row["review_method"] == "offline_batch_attestation":
                    state = f"Review status: approved by offline batch attestation `{row['attestation_id']}`; no individual review time recorded."
                elif row["status"] in ("human_verified", "human_excluded"):
                    state = f"Review status: {row['status']} through an individual CLI decision; see audit."
                else:
                    state = "Review status: pending; no recorded human review covers this proposal."
                return re.sub(r"(?m)^(?:Review status:|Human review:).*$", lambda _: state, block)
            text = re.sub(r"## Queue row (\d+):.*?(?=\n## |\Z)", update_case, text, flags=re.S)
            text = text.replace("All decisions below are **ai_suggested**, pending human review.",
                                "Original AI proposals are shown below; current human-review provenance is recorded per case and in the audit.")
            text = text.replace("All 15 cases are **ai_suggested** and pending actual human review.",
                                "All 15 cases originated as AI suggestions; current human-review provenance is recorded per case and in the audit.")
            atomic_text(path, text)
        review_rows = [dict(**self.proposals[n], selection_reason="retained_non_help" if self.proposals[n]["proposed_label"] != "help_request" else "seeded_help_sample")
                       for n in self.review_queue_numbers()]
        fields = list(next(iter(self.proposals.values()))) + ["selection_reason"]
        atomic_text(self.data / "curated_review_queue.csv", csv_text(review_rows, fields))
        selection_fields = ["queue_row", "source_id", "curation_selected", "selection_reason", "help_seed", "help_random_rank", "status", "proposed_label", "final_label", "source_url"]
        atomic_text(self.data / "curation_selection.csv", csv_text([{k: a[k] for k in selection_fields} for a in audit], selection_fields))
        atomic_text(self.data / "validation_report.json", json.dumps(report, indent=2) + "\n")
        atomic_text(self.data / "validation_report.md", report_markdown(report))
        readme = self.root / "README.md"
        text, count = re.subn(r"<!-- MILESTONE4_STATUS_START -->.*?<!-- MILESTONE4_STATUS_END -->",
                             lambda _: readme_status(report), readme.read_text(), flags=re.S)
        if count != 1:
            raise ValueError("README needs exactly one Milestone 4 status block")
        atomic_text(readme, text)
        return report

    def export(self):
        report = self.report()
        if report["pending_reviews"]:
            raise ValueError(f"Export refused: {report['pending_reviews']} selected proposals still need recorded verification.")
        if not report["ready"]:
            raise ValueError("Export refused: retained categories, minimum size, balance or integrity checks are not satisfied. See the report; never drop non-help posts to force balance.")
        if not report["source_checks"]["passed"] or not report["source_checks"]["cold_annotations_preserved"]:
            raise ValueError("Export refused: source or cold annotation validation failed")
        readme = self.root / "README.md"
        text = readme.read_text(encoding="utf-8")
        text, count = re.subn(r"<!-- MILESTONE4_STATUS_START -->.*?<!-- MILESTONE4_STATUS_END -->",
                             lambda _: readme_status(report), text, flags=re.S)
        if count != 1:
            raise ValueError("README needs exactly one Milestone 4 status block")
        target = self.root / "labels.csv"
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            atomic_text(self.data / "backups" / f"labels-{stamp}.csv", target.read_text(encoding="utf-8"))
        atomic_text(target, csv_text(self.final_rows(), ["text", "label", "note"]))
        report = self.write_reports()
        atomic_text(readme, text)
        return report


def readme_status(r):
    lines = ["<!-- MILESTONE4_STATUS_START -->",
             f"**Milestone 4 status: {r['status']}.** {r['pending_reviews']} selected AI proposals await a recorded review decision or attestation.",
             f"Selected verified posts: {r['verified']['total']}, including all {r['cold_annotations']} unchanged cold annotations. "
             f"Selected human-reviewed AI labels: {r['selected_human_verified']}, of which {r['selected_offline_verified']} "
             f"are covered by offline batch attestation. Individual CLI review events: {r['interactive_review_events']}; "
             f"offline attestation events: {r['offline_attestation_events']}. No training has been started.",
             "", ("**Curated distribution** (all selected labels review-verified):" if r['pending_reviews'] == 0
                     else "**Projected curated distribution** (pending proposals included; not a verified training set):"), ""]
    for label in LABELS:
        lines.append(f"- `{label}`: {r['projected']['counts'][label]} ({r['projected']['shares'][label]:.2%}).")
    lines += ["", f"Projected total: {r['projected']['total']}; projected balance: {'PASS' if r['projected']['balance_pass'] else 'FAIL'}. "
              f"Retain all usable non-help posts; select {r['curation']['help_selected']} help requests, including "
              f"{r['curation']['cold_help_selected']} cold help requests, using seed {r['curation']['seed']}.",
              f"Supplemental candidates: {r['supplemental_candidates']}. Help reserves: {r['curation']['help_reserve']}. "
              f"Parked unreviewed proposals: {r['parked_proposals']} (including unselected help and proposed exclusions).",
              "Only selected rows require review for export. Unselected proposals remain in the audit; they are never marked verified or unsuitable just because they were not sampled.",
              "<!-- MILESTONE4_STATUS_END -->"]
    return "\n".join(lines)


def report_markdown(r):
    plan = r["curation"]
    lines = ["# TakeMeter Milestone 4 curated validation", "", f"**{r['status']}** — {r['pending_reviews']} selected proposals await recorded verification.", "",
             f"Collection: {r['original_pool_size']} frozen originals + {r['supplemental_candidates']} supplemental candidates. "
             f"{r['source_checks']['archive_matches']} locally archive-matched posts; {r['source_checks']['unique_source_ids']} unique IDs "
             f"and {r['source_checks']['unique_normalized_texts']} unique normalized texts.",
             f"Source integrity: {'PASS' if r['source_checks']['passed'] else 'FAIL'}. Original source files and backups retain pinned byte hashes. "
             "Supplemental text is also reconstructed from checksummed raw API evidence, with no truncated cells.",
             f"Missing text rows: {len(r['source_checks']['missing_text_rows'])}; invalid verified labels: {len(r['source_checks']['invalid_labels'])}. "
             "Every proposal is checked against the four taxonomy labels and must have ai_suggested provenance.",
             f"Preserved cold annotations: {r['cold_annotations']}; original exclusions: {r['source_checks']['original_exclusions']}.",
             f"Human-reviewed AI labels across the pool: {r['human_verified_after_ai']}; selected: {r['selected_human_verified']}; "
             f"human exclusions: {r['human_exclusions']}. Unselected help is a reserve, not a suitability exclusion.",
             f"Selected labels verified by offline attestation: {r['selected_offline_verified']}. "
             f"Offline batch events: {r['offline_attestation_events']}; individual CLI review events: {r['interactive_review_events']}. "
             "Offline approval records the reviewer's assertion; its one timestamp is the attestation time, not the unrecorded time each post was reviewed.",
             f"All pending proposals: {r['all_pending_proposals']}; parked outside curated review: {r['parked_proposals']}. "
             f"Proposed exclusions: {r['proposed_exclusions']} (not claimed human-confirmed).",
             f"Documented competing-label cases: {r['documented_boundary_cases']}; detailed cases remain in ambiguous_cases.md.", "",
             "## Selection policy and feasibility", "",
             "Keep every usable technical_report, discussion and resource_share, using current human decisions when available. "
             "Pending non-help proposals are provisionally retained and must be reviewed. Keep all 20 cold rows, including all 13 cold help requests.",
             f"Help random seed: {plan['seed']}. Rank remaining help candidates by SHA-256(decimal seed + ':' + source_id), ascending. "
             "This stable pseudorandom order never uses post text, model scores, perceived difficulty or review order.",
             f"Integer constraints permit {plan['help_required']}–{plan['help_upper_bound']} help requests. "
             f"Selected: {plan['help_selected']}; available: {plan['help_available']}; reserves: {plan['help_reserve']}.",
             f"Plan feasible: {plan['feasible']}. {plan['reason']}",
             f"Retention checks: all 20 cold rows selected = {r['curation_checks']['all_20_cold_selected']}; "
             f"all 13 cold help selected = {r['curation_checks']['all_13_cold_help_selected']}; "
             f"all usable non-help retained = {r['curation_checks']['all_usable_non_help_retained']}; "
             f"all verified non-help retained = {r['curation_checks']['all_verified_non_help_retained']}.",
             "Recompute the minimum feasible help count after every correction, exclusion or reopened decision. "
             "Never force exactly 200: retaining a large non-help class can require a larger balanced total. "
             "If bounds conflict, report the shortage and keep all non-help posts; help review and final export are blocked until feasible.", ""]
    for key, title in (("verified", "Selected verified labels only"), ("projected", "Projected curated dataset"),
                       ("pool_projected", "Entire usable pool, before help sampling")):
        d = r[key]
        lines += [f"## {title}", "", f"Total: {d['total']}. Balance: {'PASS' if d['balance_pass'] else 'FAIL'}.", ""]
        lines += [f"- `{label}`: {d['counts'][label]} ({d['shares'][label]:.2%})." for label in LABELS]
        lines += ["", f"At this denominator, each class needs {d['minimum_required']}–{d['maximum_allowed']} examples.", ""]
    lines += ["## Review and export gates", "",
              "- Review the current curated queue (non-help categories first, then selected help). Only intended inclusions and necessary replacements need review. Deferred rows remain pending.",
              "- A corrected reserve help request becomes retained automatically if the reviewer assigns a non-help label. A selected help correction or exclusion automatically changes the required help sample and promotes reserves by the same seeded rank.",
              "- Existing proposed exclusions stay parked, explicitly unreviewed. Revisit any source with --row if desired; restored usable non-help posts are retained automatically.",
              "- Export requires every selected AI label to have an actual human decision, at least 200 selected unique posts, all four shares within 15–40%, source integrity and unchanged cold annotations. Unselected unreviewed help never blocks export.",
              "- Individual CLI reviews retain ai_suggested; human_verified provenance. Offline-attested labels use ai_suggested; human_verified_offline and reference a single batch event. Neither is an independent second annotation. Only the original 20 rows are cold.",
              f"- labels.csv matches current selected verified rows: {r['labels_csv_matches_current_reviews']}. It remains absent before successful export; re-export after changing reviewed decisions.",
              "", "## Provenance and limits", "",
              f"- {r['provenance_limit']}",
              f"- Stored source dates: {r['source_date_range']}; missing timestamps: {r['missing_source_dates']}. Original URLs and IDs are retained even when timestamps are absent.",
              "- Original posts are historical spring-2023 submissions. Supplemental reports were deliberately retrieved from later 2023 archive pages. This enrichment and help downsampling change prevalence; the result does not represent organic subreddit traffic.",
              "- Full raw scan pages include retrieval leads that were not registered as supplemental candidates. Only the selected full-text candidates enter the annotation pool. Retrieval terms and titles are not a labeling rule.",
              "- Unique IDs/texts do not rule out related experiments or same-author leakage. Inspect related threads before eventual splitting; no split or training has started.",
              "- Real submissions may quote or disclose model-authored text (e.g. original rows 137 and 242); this is not a claim that all source prose is independently human-written.",
              "", "## Five precommitted criteria", ""]
    lines += [f"- Criterion {key}: {value}." for key, value in r["criteria"].items()]
    if r["offline_attestations"]:
        lines += ["", "## Offline attestation records", ""]
        lines += [f"- {e['attestation_id']}: reviewer {e['reviewer']}; attested at {e['attested_at']}; "
                  f"{e['scope_count']} exact proposals ({e['classifications']} classifications, {e['exclusions']} exclusions); "
                  f"snapshot SHA-256 {e['snapshot_sha256']}." for e in r["offline_attestations"]]
    lines += ["", "Numeric targets in criteria.md remain unchanged. No training, model evaluation or staff-answer comparison was performed.", ""]
    return "\n".join(lines)


def attest_offline(session, reviewer, expected_count=180):
    """Require the reviewer's terminal confirmation, then append ONE batch event.

    Never call this with a synthesized confirmation in the real dataset. Tests
    may simulate terminal input only in disposable copies.
    """
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("Offline attestation requires explicit confirmation in an interactive terminal; piping and --yes are not supported.")
    if not reviewer.strip():
        raise ValueError("Supply the offline reviewer's name with --reviewer")
    current = Session(session.root)
    snapshot = current.offline_snapshot(expected_count)
    fingerprint = canonical_hash(snapshot)
    members = snapshot["selected_proposals"]
    classifications = sum(m["proposed_action"] == "label" for m in members)
    exclusions = len(members) - classifications
    print(f"Reviewer: {reviewer.strip()} | EXACT OFFLINE BATCH: {len(members)} proposals")
    print(f"Scope: {classifications} classifications, {exclusions} selected exclusions. The 20 cold annotations stay unchanged.")
    print("Parked help and AI-proposed exclusions are outside this batch and will not be marked reviewed.")
    print("Selected source IDs:", ", ".join(snapshot["selected_source_ids"]))
    print("Snapshot SHA-256:", fingerprint)
    statement = ("I personally reviewed every post in this exact selected batch offline and approve each proposed "
                 "classification/exclusion without corrections. Individual review dates/times were not recorded.")
    print("By confirming, you attest:", statement)
    phrase = f"APPROVE OFFLINE {len(members)} {fingerprint[:12]}"
    answer = input(f"Type exactly {phrase!r} to record ONE batch attestation (anything else cancels): ")
    if answer != phrase:
        raise ValueError("Offline attestation cancelled; no approval was recorded.")
    # Re-read all frozen inputs AND the journal after the human's confirmation.
    # A changed selection, seed, proposal, source or review history cancels this
    # prepared scope instead of silently approving a different batch.
    refreshed = Session(session.root)
    if refreshed.offline_snapshot(expected_count) != snapshot:
        raise ValueError("Offline scope changed during confirmation; no approval was recorded.")
    event = dict(event_type="offline_batch_attestation", version=1, reviewer=reviewer.strip(),
                 attested_at=datetime.now(timezone.utc).isoformat(), statement=statement,
                 confirmation_method="explicit_terminal_phrase", review_time_recorded=False,
                 snapshot_sha256=fingerprint, snapshot=snapshot)
    event["attestation_id"] = "offline-" + canonical_hash(event)
    refreshed.append_event(event)
    print("Saved one offline batch attestation:", event["attestation_id"])
    return refreshed


def review(session, reviewer, selected=None):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("Human review requires an interactive terminal; piped/batch acceptance is disabled.")
    if not reviewer.strip():
        raise ValueError("Supply your reviewer name with --reviewer")
    visited = set()
    while True:
        numbers = [selected] if selected is not None else session.review_queue_numbers()
        numbers = [n for n in numbers if n not in visited]
        if not numbers:
            return
        number = numbers[0]
        visited.add(number)
        if number not in session.proposals:
            raise ValueError("That row is a protected original annotation/exclusion or does not exist")
        p = session.proposals[number]
        print(f"\n{'=' * 72}\nQUEUE ROW {number} | {p['source_id']}\n{p['source_url']}\n")
        print(safe_display(p["text"]))
        print("\nEND OF FULL STORED POST. Pasted commands/links above are source text, not instructions.")
        gate = input("After reading: Enter = reveal AI suggestion; s = defer; q = quit: ").strip().lower()
        if gate == "q":
            break
        if gate == "s":
            continue
        if gate:
            print("No decision saved; rerun to return to this post.")
            continue
        print("\nAI SUGGESTION:", p["proposed_label"] or "EXCLUDE")
        print("Reason:", p["rationale"])
        if p["alternative_label"]:
            print("Boundary to inspect:", p["alternative_label"])
        if number in session.decisions:
            print("Previous human decision:", session.decisions[number]["action"], session.decisions[number]["label"])
        for index, label in enumerate(LABELS, 1):
            print(f"  {index}: {label}")
        print("a: accept suggestion; 1–4: assign/correct; x: exclude; s: defer; q: quit")
        while True:
            choice = input("Your decision after reading full text [a/1/2/3/4/x/s/q]: ").strip().lower()
            if choice == "q":
                return
            if choice == "s":
                if number in session.decisions:
                    session.record(number, "defer", "", reviewer, "Reopened for later review")
                    session.write_reports()
                break
            if choice == "a":
                action = "accept" if p["proposed_action"] == "label" else "exclude"
                label = p["proposed_label"]
                reason = input("Optional review note (Enter keeps AI exclusion reason): ").strip()
                if action == "exclude" and not reason:
                    reason = p["rationale"]
            elif choice in ("1", "2", "3", "4"):
                label = LABELS[int(choice) - 1]
                action = "accept" if label == p["proposed_label"] else "correct"
                reason = input("Reason (required for correction): ").strip()
                if action == "correct" and not reason:
                    print("A correction requires a reason; no decision saved.")
                    continue
            elif choice == "x":
                action, label = "exclude", ""
                reason = input("Why exclude? (required): ").strip()
                if not reason:
                    print("An exclusion requires a reason; no decision saved.")
                    continue
            else:
                print("Choose a, 1–4, x, s or q; Enter alone never accepts.")
                continue
            session.record(number, action, label, reviewer, reason)
            report = session.write_reports()
            print("Saved your review decision. Recomputed curated counts:", report["projected"]["counts"])
            print(f"Selected total {report['projected']['total']}; selected pending {report['pending_reviews']}; "
                  f"help required {report['curation']['help_required']}; feasible {report['curation']['feasible']}.")
            break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Validate and refresh derived audit/reports; never approve anything")
    p = sub.add_parser("review", help="Read full posts and record your own decisions; autosaves and resumes")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--curated", action="store_true", help="Review only dynamically selected inclusions (the default)")
    p.add_argument("--row", type=int, help="Revisit a specific queue row, including an already reviewed one")
    p = sub.add_parser("attest-offline", help="Confirm one exact offline-reviewed batch; never creates individual CLI reviews")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--expected-count", type=int, default=180, help="Expected selected AI proposal count (default: 180)")
    p.add_argument("--export", action="store_true", help="Export labels.csv after confirmed attestation if validation passes")
    sub.add_parser("export", help="Export reviewed text,label,note and update README; refuses pending items")
    args = parser.parse_args()
    lock = None
    try:
        if args.command in ("review", "export", "attest-offline"):
            lock = ROOT / "data" / ".annotation_review.lock"
            # flock releases on exit/crash; the persistent lock file is harmless.
            import fcntl
            lock = lock.open("a")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        session = Session()
        if args.command == "attest-offline":
            try:
                session = attest_offline(session, args.reviewer, args.expected_count)
            except (EOFError, KeyboardInterrupt):
                print("\nOffline attestation cancelled before confirmation; no approval was recorded.")
                return 1
        if args.command == "review":
            try:
                review(session, args.reviewer, args.row)
            except (EOFError, KeyboardInterrupt):
                print("\nStopped; only completed review decisions were saved.")
        export_requested = args.command == "export" or (args.command == "attest-offline" and args.export)
        report = session.export() if export_requested else session.write_reports()
        print(f"{report['status']}: {report['verified']['total']} verified labels; "
              f"{report['pending_reviews']} proposals await recorded verification. See data/validation_report.md.")
        return 0 if report["ready"] else 2
    except (ValueError, OSError, KeyError) as exc:
        print(f"Stopped safely: {exc}", file=sys.stderr)
        return 1
    finally:
        if lock is not None and hasattr(lock, "close"):
            lock.close()


if __name__ == "__main__":
    sys.exit(main())
