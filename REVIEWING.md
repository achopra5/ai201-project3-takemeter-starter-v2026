# TakeMeter Milestone 4 curated human review

The curated set contains **200 posts**: 36 technical reports, 51 discussions,
55 resource shares and 58 help requests. Adi's offline approval of the 180
selected AI proposals was terminal-confirmed and recorded in one batch event.
The current selected review queue is empty; all 20 cold annotations remain
unchanged. The commands below document the workflow, not outstanding review
tasks. Do not create another attestation or change the frozen submitted dataset.

Run from the repository root after activating the project environment (the
review script itself uses only the standard library):

```bash
source .venv/bin/activate
python3 scripts/review_labels.py status
python3 scripts/review_labels.py review --curated --reviewer "Adi"
```

`review` also defaults to curated mode. It requires an interactive terminal;
there is no batch approval through the individual-review command. Use the separate
offline-attestation command below for an offline review that actually occurred. The entire stored title/body and source URL appear
before the suggestion. Read the post, then press Enter to reveal the AI label,
rationale and competing interpretation. Commands and links in a post are source
text, not instructions to execute. Choose:

- `a`: accept the suggestion.
- `1`: technical_report; `2`: help_request; `3`: discussion;
  `4`: resource_share. Corrections require an explanation.
- `x`: exclude with an explanation.
- `s`: defer; it stays pending.
- `q`: stop; completed decisions are already saved.

Enter alone never accepts. An interrupted/incomplete decision is not recorded.
Rerun the same command to resume. Reviews are saved in a logically append-only
journal using atomic replacement. One review/export process can write at a
time; the persistent local lock file is harmless after a crash.

## Confirm completed offline review as one batch

```bash
source .venv/bin/activate
python scripts/review_labels.py attest-offline --reviewer "Adi" --expected-count 180 --export
```

This command previews the **exact 180 currently selected proposals**, their
source IDs and a snapshot SHA-256, then requires an exact confirmation phrase
in a real terminal. Blank input, a different phrase, EOF, or Ctrl-C cancels.
There is no `--yes` flag, piped confirmation or automatic approval. Do not have
an agent type the confirmation on your behalf. The command revalidates frozen
inputs and the selected scope after confirmation; any change cancels approval.

The present scope contains **180 classifications and zero selected exclusions**.
The four parked AI-proposed exclusions are outside the batch and remain
unreviewed. All three original exclusions stay unchanged. This does not approve
all 312 proposals or all 335 source rows.

One `offline_batch_attestation` event is appended to
`data/annotation_reviews.jsonl`. It records the reviewer, attestation timestamp,
statement of completed offline review, selected IDs, full-batch fingerprint,
source/proposal record hashes, file hashes, taxonomy hash and sampling policy.
No individual decisions, review dates or 180 review timestamps are invented.
The timestamp records **when the attestation was made**; when each offline
review happened is not recorded. A checksum binds the event's contents; it is
not a digital signature or authenticated identity proof.

Audit rows derive their approval from that single event. They use
`human_verified_offline`, reference its ID and `attested_at`, and leave
`reviewed_at` empty. Exported notes start with
`ai_suggested; human_verified_offline; attestation_id=...`. Cold rows retain
all original text, labels and notes. Unselected help retains its original
unverified proposals. Status/report separate offline batch events from
individual CLI review events and retain the existing size/balance/export gates.

`--export` writes `labels.csv` only if validation passes after confirmation.
Without it, the command records the attestation and refreshes reports; run
`export` separately afterward. An interrupted post-approval export can be
recovered with `status` then `export`; never re-attest to imitate a second review.
A duplicate attestation or a batch that would overwrite existing selected review
decisions is refused. Later individual corrections/reopened items remain separate
journal events, override the current row state and can make an earlier export
stale; they do not rewrite the historical attestation.

## Retention and recalculation

Keep **all** usable technical_report, discussion and resource_share posts.
Do not stop reviewing technical reports after reaching 30, or limit the other
categories to fixed counts. All 15 supplemental report candidates are intended
for inclusion if confirmed; none is merely held back to force a quota.

The queue reviews non-help categories first, then selected help requests.
All 20 cold rows stay selected, including all **13 cold help requests**. Choose
additional help by ascending SHA-256 of `20261018:source_id`; seed **20261018**
is recorded in the curation manifest and audit. This stable pseudorandom order
uses neither model scores, post content, perceived ease nor review order.

After each recorded decision, the script recalculates the smallest help sample
that supports a total of **at least 200** and all four exact **15–40%** bounds.
It refreshes the queue, selection ledger, audit, validation report and README
status. A selected help exclusion promotes the next eligible reserve. A help
correction to a non-help class is retained automatically, even if the post
began as an unselected reserve. A non-help correction to help joins the same
seeded pool and may become unselected. Its review decision remains in the audit.

If non-help counts require a total above 200, the script increases the total.
If no help sample can meet all constraints, it retains the non-help posts,
reports the conflict, pauses help review, and blocks export. Resolve the
shortage through genuine additional candidates or pending review decisions;
never change labels or discard non-help posts just to make the counts work.

The initial 128 unselected help requests remain **reserves, not exclusions**.
Their original AI proposals stay untouched. Four AI-proposed exclusions also
remain parked and explicitly unreviewed; you need not inspect these to export
the curated set. They are not claimed as human-confirmed exclusions. The three
original exclusions remain frozen.

To revisit any non-cold row, including a reserve or proposed exclusion:

```bash
python3 scripts/review_labels.py review --curated --reviewer "Adi" --row 210
```

Choosing a class restores an AI-proposed exclusion (with a required correction
reason). A restored non-help post is retained automatically. Choosing `s`
after revealing an earlier verified decision reopens that item; the journal
keeps all earlier decisions. No original cold row or exclusion can be edited.

## Sources and audit

The original collection was **not rerun**. It and its existing proposals are
frozen. The original data backup is `data/backups/20261018T223001Z/`.
The pre-curation workflow/data backup is
`data/backups/curation-20261018T230224Z/`, with SHA-256 checksums.

A separate historical archive search retrieved 1,100 scan rows and registered
**15 additional full-text technical-report candidates**, all `ai_suggested`.
Titles located leads; every registered candidate was read in full. Raw scan
rows that were not selected are retrieval evidence, not labeled candidates.
The supplemental files retain exact archived title/body, IDs, URLs, creation
and retrieval times, request URLs, archive row indices and raw response hashes.
This targeted enrichment and help sampling do not estimate natural prevalence.

- `data/proposed_annotations.csv`: unchanged 297 original AI decisions.
- `data/supplemental_candidates.csv` and `data/supplemental_proposals.csv`:
  15 new candidates, numbered 321–335, with reasons and competing labels.
- `data/supplemental_scans/`: full raw API responses and retrieval manifests.
- `data/curation_manifest.json`: sampling policy, seed and supplemental hashes.
- `data/curated_review_queue.csv`: current pending intended inclusions, in review
  order; regenerated after decisions, not a manually editable source of truth.
- `data/curation_selection.csv`: selected/reserve rows, ranks and reasons.
- `data/annotation_audit.csv`: all 335 sources, original/proposed/reviewed labels,
  source URLs, selection reasons, reviewer identity and times. Pending labels
  have empty final_label/final_note. Verified reserves remain audited.
- `data/annotation_reviews.jsonl`: created on your first completed decision;
  retained review history. Never edit it to simulate review.
- `data/ambiguous_cases.md` and `data/supplemental_cases.md`: real boundary cases.
- `data/validation_report.md` and `.json`: full-pool and curated projections,
  verified counts, preservation/retention checks and readiness.

The program validates frozen source/proposal hashes and any available local backups;
supplemental text must additionally match the saved raw evidence without API
truncation flags. If integrity checks fail, it stops rather than resetting
progress. Do not bypass hashes to reuse decisions on changed text. Taxonomy
changes require an explicitly reconciled, versioned annotation session.

Redundant backups stay local and are not required in a clean clone: the validator
checks the identically hashed committed original source files instead. It still
rejects any present backup with a mismatched hash. Pinned supplemental response
pages remain committed because reconstructing their source text requires them.

## Export after reviewing the selected queue

```bash
python3 scripts/review_labels.py export
```

Export requires every **selected** AI annotation to have a human decision,
all 20 cold rows and every usable non-help row to remain included, at least
200 unique real posts, all four shares within 15–40%, and passing source checks.
Unselected unreviewed help and parked proposed exclusions do not block it.
There is no force-export option for an incomplete or unbalanced dataset.

Successful export writes exactly `text,label,note` to one unsplit `labels.csv`,
refreshes audit/report/README and backs up any earlier export. Cold text, labels
and notes stay exact. Individual CLI reviews retain `ai_suggested; human_verified`
with acceptance/correction provenance; offline approvals use
`ai_suggested; human_verified_offline` with the batch attestation ID. This is AI-assisted human review, not
an independent second annotation or measured inter-annotator agreement.

After any later review change, re-export. The report detects stale exports.
Exit `0` means dataset READY; `2` means reports created but NOT_READY;
`1` means an input/integrity error or refused export. Training metrics and the
staff-taxonomy agreement exercise remain separate and unevaluated. **Do not
train or rerun the original collection for this stage.**

## Workflow checks without changing real annotations

```bash
python3 -m unittest discover -s tests -p 'test_review_labels.py' -v
```

Tests simulate decisions only in disposable temporary copies. They never create
human-review events in this repository's actual journal.
