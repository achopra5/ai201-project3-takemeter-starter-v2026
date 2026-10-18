#!/usr/bin/env python3
"""Label the first 20 TakeMeter candidates independently, without AI suggestions.

Run from project root:
    python scripts/label_cold.py

This reads data/annotation_queue.csv and updates ONLY its label and note columns.
The post text and source information are preserved byte-for-byte as CSV values.
Your answers are autosaved after every labeled post; rerunning resumes the task.
"""

import csv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUEUE = PROJECT_ROOT / "data" / "annotation_queue.csv"
LABELS = {
    "1": ("technical_report", "Completed firsthand technical work with useful observed results."),
    "2": ("help_request", "Primarily seeks a concrete answer for an unresolved personal task."),
    "3": ("discussion", "Primarily expresses opinions, predictions, reactions, or debate."),
    "4": ("resource_share", "Primarily announces a resource, new artifact, or how-to guide."),
}
RESERVED = 20


def load_queue():
    if not QUEUE.is_file():
        raise SystemExit(
            f"Missing {QUEUE}. Run python scripts/collect_candidates.py first."
        )
    with QUEUE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if not fieldnames or not {"text", "label", "note"}.issubset(fieldnames):
            raise SystemExit("Expected CSV columns: text, label, note.")
        rows = list(reader)
    if len(rows) < RESERVED:
        raise SystemExit(f"Only {len(rows)} rows; expected at least {RESERVED}.")
    return fieldnames, rows


def save_queue(fieldnames, rows):
    # Atomic replacement prevents a partial CSV if execution is interrupted.
    temp = QUEUE.with_name(QUEUE.name + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, QUEUE)


def print_rules():
    print("\nLabel by PRIMARY PURPOSE (not subreddit flair or whether it has numbers).")
    print("If a completed, informative test also asks for advice, prefer technical_report.")
    print("If details only support an unresolved troubleshooting question, prefer help_request.")
    print("If introducing a new tool/model/tutorial, prefer resource_share.")
    print("Otherwise, substantial opinion/prediction/debate is discussion.")
    for k, (name, desc) in LABELS.items():
        print(f"  {k}: {name} — {desc}")
    print("Commands: 1/2/3/4 = label; s = skip for now; q = save and quit; ? = repeat rules.")


def main():
    fieldnames, rows = load_queue()
    print("\nTakeMeter — independent annotation of the first 20 real posts")
    print("Do these yourself, without AI pre-labeling. Keep ambiguous-case notes.")
    print_rules()
    for index, row in enumerate(rows[:RESERVED], start=1):
        if row.get("label", "").strip() in {v[0] for v in LABELS.values()}:
            continue
        print("\n" + "=" * 72)
        print(f"POST {index} OF {RESERVED}")
        print("Source:", row.get("source_url", "(not recorded)"))
        print("-" * 72)
        print(row.get("text", ""))
        print("-" * 72)
        while True:
            try:
                choice = input(f"Post {index} — choose 1/2/3/4, s, q or ?: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nStopped. Previous labels were already saved.")
                return
            if choice == "?":
                print_rules()
                continue
            if choice == "q":
                print("Stopped. Previous labels were already saved.")
                return
            if choice == "s":
                print("Skipped — this row remains unlabeled.")
                break
            if choice not in LABELS:
                print("Please enter 1, 2, 3, 4, s, q, or ?.")
                continue
            label = LABELS[choice][0]
            try:
                note = input("Optional ambiguity note (press Enter if clear): ").strip()
            except (KeyboardInterrupt, EOFError):
                note = ""
            row["label"] = label
            row["note"] = "cold" + (f"; {note}" if note else "")
            save_queue(fieldnames, rows)
            print(f"Saved post {index} as {label}.")
            break

    done = sum(row.get("label", "").strip() in {v[0] for v in LABELS.values()}
               and row.get("note", "").startswith("cold")
               for row in rows[:RESERVED])
    print(f"\nIndependent labels completed: {done}/{RESERVED}.")
    if done == RESERVED:
        print("Milestone 4 cold subset complete. Do not overwrite these decisions.")
        print("Next: review and label additional real posts before exporting labels.csv.")
    else:
        print("Rerun this script to label skipped posts.")


if __name__ == "__main__":
    main()
