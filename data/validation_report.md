# TakeMeter Milestone 4 curated validation

**READY** — 0 selected proposals await recorded verification.

Collection: 320 frozen originals + 15 supplemental candidates. 335 locally archive-matched posts; 335 unique IDs and 335 unique normalized texts.
Source integrity: PASS. Original source files and backups retain pinned byte hashes. Supplemental text is also reconstructed from checksummed raw API evidence, with no truncated cells.
Missing text rows: 0; invalid verified labels: 0. Every proposal is checked against the four taxonomy labels and must have ai_suggested provenance.
Preserved cold annotations: 20; original exclusions: 3.
Human-reviewed AI labels across the pool: 180; selected: 180; human exclusions: 0. Unselected help is a reserve, not a suitability exclusion.
Selected labels verified by offline attestation: 180. Offline batch events: 1; individual CLI review events: 0. Offline approval records the reviewer's assertion; its one timestamp is the attestation time, not the unrecorded time each post was reviewed.
All pending proposals: 132; parked outside curated review: 132. Proposed exclusions: 4 (not claimed human-confirmed).
Documented competing-label cases: 156; detailed cases remain in ambiguous_cases.md.

## Selection policy and feasibility

Keep every usable technical_report, discussion and resource_share, using current human decisions when available. Pending non-help proposals are provisionally retained and must be reviewed. Keep all 20 cold rows, including all 13 cold help requests.
Help random seed: 20261018. Rank remaining help candidates by SHA-256(decimal seed + ':' + source_id), ascending. This stable pseudorandom order never uses post text, model scores, perceived difficulty or review order.
Integer constraints permit 58–94 help requests. Selected: 58; available: 186; reserves: 128.
Plan feasible: True. Minimum feasible help sample
Retention checks: all 20 cold rows selected = True; all 13 cold help selected = True; all usable non-help retained = True; all verified non-help retained = True.
Recompute the minimum feasible help count after every correction, exclusion or reopened decision. Never force exactly 200: retaining a large non-help class can require a larger balanced total. If bounds conflict, report the shortage and keep all non-help posts; help review and final export are blocked until feasible.

## Selected verified labels only

Total: 200. Balance: PASS.

- `technical_report`: 36 (18.00%).
- `help_request`: 58 (29.00%).
- `discussion`: 51 (25.50%).
- `resource_share`: 55 (27.50%).

At this denominator, each class needs 30–80 examples.

## Projected curated dataset

Total: 200. Balance: PASS.

- `technical_report`: 36 (18.00%).
- `help_request`: 58 (29.00%).
- `discussion`: 51 (25.50%).
- `resource_share`: 55 (27.50%).

At this denominator, each class needs 30–80 examples.

## Entire usable pool, before help sampling

Total: 328. Balance: FAIL.

- `technical_report`: 36 (10.98%).
- `help_request`: 186 (56.71%).
- `discussion`: 51 (15.55%).
- `resource_share`: 55 (16.77%).

At this denominator, each class needs 50–131 examples.

## Review and export gates

- Review the current curated queue (non-help categories first, then selected help). Only intended inclusions and necessary replacements need review. Deferred rows remain pending.
- A corrected reserve help request becomes retained automatically if the reviewer assigns a non-help label. A selected help correction or exclusion automatically changes the required help sample and promotes reserves by the same seeded rank.
- Existing proposed exclusions stay parked, explicitly unreviewed. Revisit any source with --row if desired; restored usable non-help posts are retained automatically.
- Export requires every selected AI label to have an actual human decision, at least 200 selected unique posts, all four shares within 15–40%, source integrity and unchanged cold annotations. Unselected unreviewed help never blocks export.
- Individual CLI reviews retain ai_suggested; human_verified provenance. Offline-attested labels use ai_suggested; human_verified_offline and reference a single batch event. Neither is an independent second annotation. Only the original 20 rows are cold.
- labels.csv matches current selected verified rows: True. It remains absent before successful export; re-export after changing reviewed decisions.

## Provenance and limits

- Archive and Reddit IDs/URLs checked locally against original candidates; live Reddit availability and authorship not independently reauthenticated.
- Stored source dates: ['2023-04-01T04:30:41', '2023-09-13T22:35:20']; missing timestamps: 49. Original URLs and IDs are retained even when timestamps are absent.
- Original posts are historical spring-2023 submissions. Supplemental reports were deliberately retrieved from later 2023 archive pages. This enrichment and help downsampling change prevalence; the result does not represent organic subreddit traffic.
- Full raw scan pages include retrieval leads that were not registered as supplemental candidates. Only the selected full-text candidates enter the annotation pool. Retrieval terms and titles are not a labeling rule.
- Unique IDs/texts do not rule out related experiments or same-author leakage. Inspect related threads before eventual splitting; no split or training has started.
- Real submissions may quote or disclose model-authored text (e.g. original rows 137 and 242); this is not a claim that all source prose is independently human-written.

## Five precommitted criteria

- Criterion 1: not evaluated: training deferred.
- Criterion 2: not evaluated: training deferred.
- Criterion 3: not evaluated: training deferred.
- Criterion 4: met.
- Criterion 5: not evaluated: separate personal staff-taxonomy exercise.

## Offline attestation records

- offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8: reviewer Adi; attested at 2026-10-18T23:31:08.660993+00:00; 180 exact proposals (180 classifications, 0 exclusions); snapshot SHA-256 9cfc140cc2f30228a55d3fbca9a7060729ba25c5a0452ca672b191d422f6a4c3.

Numeric targets in criteria.md remain unchanged. No training, model evaluation or staff-answer comparison was performed.
