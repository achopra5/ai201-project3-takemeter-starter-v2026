#!/usr/bin/env python3
"""Collect 20 independent TakeMeter annotations, skipping unsuitable posts.

Run from the project root:
    python scripts/label_cold.py

Reads data/annotation_queue.csv. Preserves the post text and source columns,
and updates only label and note. Every choice is atomically autosaved.
The first 20 *usable* labeled posts count; skipped posts do not count.
Never replace or regenerate annotation_queue.csv after labeling has begun.
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
TARGET = 20
VALID_LABELS = {label for label, _ in LABELS.values()}


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
    if len(rows) < TARGET:
        raise SystemExit(f"Only {len(rows)} candidates; expected at least {TARGET}.")
    return fieldnames, rows


def save_queue(fieldnames, rows):
    """Save the whole queue atomically so interruptions do not corrupt it."""
    temp = QUEUE.with_name(QUEUE.name + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, QUEUE)


def is_cold(row):
    return (
        row.get("label", "").strip() in VALID_LABELS
        and row.get("note", "").split(";", 1)[0].strip() == "cold"
    )


def is_excluded(row):
    return row.get("note", "").startswith("excluded:")


def print_rules():
    print("\nChoose a single label based on the post's PRIMARY PURPOSE.")
    print("Do not use subreddit flair as a label.")
    print("A completed report with a closing advice request can be technical_report.")
    print("A problem statement with numbers used only as context can be help_request.")
    print("A release or tutorial primarily introducing a resource is resource_share.")
    for key, (name, desc) in LABELS.items():
        print(f"  {key}: {name} — {desc}")
    print("  s: exclude unsuitable text post (missing image/link content, etc.)")
    print("  q: save and quit; ?: show rules again")


def summary(rows):
    n_cold = sum(is_cold(row) for row in rows)
    n_excluded = sum(is_excluded(row) for row in rows)
    print(f"\nCold labeled: {n_cold}/{TARGET}; excluded: {n_excluded}.")
    if n_cold >= TARGET:
        print("Independent annotation complete. Preserve these original choices.")
    else:
        print("Run this script again to continue from saved progress.")


def main():
    fields, rows = load_queue()
    print("\nTakeMeter — first 20 independent classifications")
    print("You must choose the labels yourself without AI pre-labeling.")
    print("Skipped posts do not count toward your 20 labels.")
    print_rules()

    done = sum(is_cold(row) for row in rows)
    for index, row in enumerate(rows, start=1):
        if done >= TARGET:
            break
        if is_cold(row) or is_excluded(row):
            continue
        if row.get("label", "").strip():
            # Never relabel a pre-annotated row as a fresh independent decision.
            continue
        print("\n" + "=" * 72)
        print(f"CANDIDATE {index}/{len(rows)} — cold labels {done}/{TARGET}")
        print("Source:", row.get("source_url", "(not recorded)"))
        print("-" * 72)
        print(row.get("text", ""))
        print("-" * 72)

        while True:
            try:
                choice = input("Choose 1/2/3/4, s, q or ?: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nStopped; previous decisions are already saved.")
                summary(rows)
                return
            if choice == "?":
                print_rules()
                continue
            if choice == "q":
                print("Stopped; previous decisions are already saved.")
                summary(rows)
                return
            if choice == "s":
                try:
                    reason = input("Why exclude? [insufficient readable text]: ").strip()
                except (KeyboardInterrupt, EOFError):
                    reason = ""
                row["label"] = ""
                row["note"] = "excluded: " + (reason or "insufficient readable text")
                save_queue(fields, rows)
                print(f"Excluded candidate {index}; it will not count as a cold label.")
                break
            if choice not in LABELS:
                print("Enter 1, 2, 3, 4, s, q, or ?.")
                continue
            try:
                note = input("Optional ambiguity note (Enter if none): ").strip()
            except (KeyboardInterrupt, EOFError):
                note = ""
            label = LABELS[choice][0]
            row["label"] = label
            row["note"] = "cold" + (f"; {note}" if note else "")
            save_queue(fields, rows)
            done += 1
            print(f"Saved label '{label}' — cold progress {done}/{TARGET}.")
            break
    summary(rows)


if __name__ == "__main__":
    main()
