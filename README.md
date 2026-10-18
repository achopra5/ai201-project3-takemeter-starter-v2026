# TakeMeter

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, the
> notebook, the baseline, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> head -5 data/practice_labels.csv     # the shape your labels.csv needs
> ```
>
> Then open `takemeter.ipynb` **in this folder** — in VS Code, or with
> `jupyter notebook` if you prefer. Pick the kernel: the `.venv` inside this
> project. Run section 1, which reports the hardware you'll be training on.
> Everything else waits until you have data.
>
> Nothing to upload, nothing to connect, no accounts and no keys. The notebook
> runs on your machine and writes next to your code.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     Unit 5 asks for the first five sections. Unit 6 adds the five below them.

     Everything is pasted as TEXT. No screenshots, no images.

     ⚠️ The confusion matrix especially. The notebook prints one as a markdown
     table, ready to copy. A screenshot of a matrix earns nothing. Paste the
     table.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 5 — THE BUILD ═══════════════════════ -->

## What This Does

TakeMeter is a text classifier for public **r/LocalLLaMA** submissions. Given the full text of a post, it predicts its primary communicative role: `technical_report`, `help_request`, `discussion`, or `resource_share`. This is **not** a detector of factual truth or general post quality; the labels describe what the author is doing, not whether the post is good. See [exploration.md](exploration.md) for the 38-post community exploration that motivated the taxonomy.

---

## Label Taxonomy

**Annotation unit:** one public text-based r/LocalLLaMA submission, with its title and complete written body. Exclude posts whose useful meaning depends on missing images, an external page with no substantive authored text, or inaccessible content. Ignore subreddit flair when assigning the label.

**Labeling objective:** choose the **primary communicative purpose**, not topic, positivity, factual correctness, word count, or whether a post contains numbers. Each row must have exactly one label from this map.

### `technical_report`

**Definition:** Primarily documents a completed firsthand technical experiment, build, or investigation with concrete configuration/method and observable findings that remain informative without a request for help.

**Example 1:** [Nine models, five coding tasks, one 16GB GPU](https://www.reddit.com/r/LocalLLaMA/comments/1x8qlvw/nine_models_five_coding_tasks_one_16gb_gpu/) — The author describes five coding tasks, nine tested models, a grading procedure, and measured outcomes.

**Example 2:** [You don’t need that expensive of a build for local llms](https://www.reddit.com/r/LocalLLaMA/comments/1x8s73i/you_dont_need_that_expensive_of_a_build_for_local/) — The author reports an actual hardware/software configuration and context-dependent token throughput, rather than requesting a solution.

### `help_request`

**Definition:** Primarily seeks a concrete recommendation or solution for the author's unresolved hardware, software, or usage decision, without a substantive completed report as the main contribution.

**Example 1:** [Buying Strix Halo right now?](https://www.reddit.com/r/LocalLLaMA/comments/1x8za17/buying_strix_halo_right_now/) — The author asks whether a particular used 128 GB computer is worth its asking price.

**Example 2:** [3xrtx8000 48gb... what to do?](https://www.reddit.com/r/LocalLLaMA/comments/1x8st56/3xrtx8000_48gb_what_to_do/) — The author lists purchased GPUs and requests advice on how to use them.

### `discussion`

**Definition:** Primarily offers an opinion, prediction, interpretation, reaction, or open-ended proposal for debate rather than a completed technical report, a concrete personal support request, or a resource introduction.

**Example 1:** [What are the odds Qwen 4 models are going to think less?](https://www.reddit.com/r/LocalLLaMA/comments/1x8uqig/what_are_the_odds_qwen_4_models_are_going_to/) — The author speculates about future reasoning-token behavior while referring to a current model's speed.

**Example 2:** [Anyone feel like reverse-engineering CUDA?](https://www.reddit.com/r/LocalLLaMA/comments/1x4n6sg/anyone_feel_like_reverseengineering_cuda/) — The author floats a speculative community project, not an actionable troubleshooting question.

### `resource_share`

**Definition:** Primarily announces, releases, links, or teaches access to a model, tool, guide, or other resource, with any benchmark claims serving the introduction or tutorial.

**Example 1:** [Agens Volundr 32B v1: we fixed what you flagged in the Preview](https://www.reddit.com/r/LocalLLaMA/comments/1x8yc8d/agens_volundr_32b_v1_we_fixed_what_you_flagged_in/) — The team introduces a new model/engine version, supported by author-reported performance data.

**Example 2:** [10 Things you maybe didn't know you can do with Qwen 3.6 27B right now](https://www.reddit.com/r/LocalLLaMA/comments/1x7sq8e/10_things_you_maybe_didnt_know_you_can_do_with/) — The author offers a multi-part tutorial for newcomers.

### The hardest boundary

**Which two labels:** `technical_report` and `help_request`.

**Real borderline example:** [My 5070 ti/3070 Chimera build](https://www.reddit.com/r/LocalLLaMA/comments/1x8u6eg/my_5070_ti3070_chimera_build/) describes working hardware, model selection, actual throughput, and a remaining configuration question.

**The decision rule I used every time:** If a post describes **a completed firsthand setup or test** with sufficiently specific method/configuration **and an actual outcome useful to another reader independently of the closing question**, label it `technical_report`, even when it asks for optimization suggestions. If the hardware details and symptoms mainly provide context for an **unresolved problem or buying/usage question**, label it `help_request`. The mixed-GPU example is `technical_report` under this rule.

### Rules for other mixed-purpose posts (apply in order)

1. **Release/guide precedence:** If the main contribution is a newly available artifact, linked resource, or instructional walkthrough, use `resource_share`, even if supporting numbers are included. An experiment *comparing* existing artifacts without primarily introducing one is not automatically a release.
2. **Completed-results precedence:** Otherwise, if a substantive firsthand completed investigation and concrete outcome are reported, use `technical_report`; an optional request for optimization does not override the findings.
3. **Actionable-help precedence:** Otherwise, if the author wants a specific solution, buying recommendation, or configuration advice for their situation, use `help_request`.
4. **Discussion fallback:** Otherwise, if the post supplies substantial readable text consisting of interpretation, opinion, prediction, debate, or a proposal, use `discussion`. Do **not** use it as a dumping ground for empty, image-only, or link-only posts; those are excluded from text training.

**Stress test:** Eight **synthetic** posts covering these boundaries, their predicted labels, and justifications are recorded in [taxonomy_stress_test.md](taxonomy_stress_test.md). Synthetic cases help detect gaps in definitions; they do not validate agreement on real posts.

**Status:** Taxonomy drafted and stress-tested before labeling or model training. Revisit definitions if genuine examples expose unresolved ambiguity, and document any change before generating the training split.

---

## The Dataset

<!-- MILESTONE4_STATUS_START -->
**Milestone 4 status: READY.** 0 selected AI proposals await a recorded review decision or attestation.
Selected verified posts: 200, including all 20 unchanged cold annotations. Selected human-reviewed AI labels: 180, of which 180 are covered by offline batch attestation. Individual CLI review events: 0; offline attestation events: 1. No training has been started.

**Curated distribution** (all selected labels review-verified):

- `technical_report`: 36 (18.00%).
- `help_request`: 58 (29.00%).
- `discussion`: 51 (25.50%).
- `resource_share`: 55 (27.50%).

Projected total: 200; projected balance: PASS. Retain all usable non-help posts; select 58 help requests, including 13 cold help requests, using seed 20261018.
Supplemental candidates: 15. Help reserves: 128. Parked unreviewed proposals: 132 (including unselected help and proposed exclusions).
Only selected rows require review for export. Unselected proposals remain in the audit; they are never marked verified or unsuitable just because they were not sampled.
<!-- MILESTONE4_STATUS_END -->

**Source and collection:** The frozen original pool contains 320 r/LocalLLaMA submissions from the [pszemraj/LocalLLaMA-posts archive](https://huggingface.co/datasets/pszemraj/LocalLLaMA-posts). Its collection script was **not rerun**, and the original queue, candidates, proposals, collection manifest, independent notes and exclusions remain unchanged. A separate supplemental search retrieved 11 archive pages (1,100 scan rows) from historical 2023 material, used titles only to locate leads, then read the full text of each selected candidate. This added **15 distinct proposed technical reports**, stored separately in [data/supplemental_candidates.csv](data/supplemental_candidates.csv) and [data/supplemental_proposals.csv](data/supplemental_proposals.csv). Full API response bytes, request URLs, retrieval times, row indices and SHA-256 checksums are retained under [data/supplemental_scans](data/supplemental_scans/). The selected candidates have complete stored title/body text and no API truncation flags. They are real archived submissions, not generated examples, but live Reddit availability/authorship was not independently reauthenticated.

**Retention and help sampling:** Keep **every** usable `technical_report`, `discussion` and `resource_share`; do not impose a quota or cap on these categories. Preserve all 20 original cold rows, including all 13 cold help requests. Sample only the remaining `help_request` posts, using fixed seed **20261018** and ascending SHA-256 of `seed:source_id` as a stable pseudorandom rank. This is independent of post text, review order, perceived difficulty and model performance. Choose the **smallest help count** that produces at least 200 posts and satisfies the exact 15–40% limits for all four classes. If the retained classes require more than 200 posts, increase the total. If no help count works, report the conflict and obtain more genuine examples or finish resolving pending labels; do not drop or relabel non-help posts to force balance.

**Curation and review provenance:** The selected composition is 36 technical reports, 51 discussions, 55 resource shares and 58 help requests (13 cold + 45 sampled), for 200 posts. The reviewer reports completing the 180 selected AI proposals offline with no corrections. Record that approval with `.venv/bin/python scripts/review_labels.py attest-offline --reviewer "Adi" --expected-count 180 --export`, which requires explicit terminal confirmation of the exact source/proposal snapshot. The status block above and audit show whether confirmation has actually been recorded; the user's report alone does not create an event. The other 128 help requests remain reserves, and four parked AI-proposed exclusions remain outside this exact batch and unreviewed. The original three exclusions stay unchanged. The balanced enrichment does not estimate organic subreddit prevalence.

**Preservation and AI assistance:** The original input backup is [data/backups/20261018T223001Z](data/backups/20261018T223001Z/sha256.json). Before updating curation, the prior data and workflow were backed up again in [data/backups/curation-20261018T230224Z](data/backups/curation-20261018T230224Z/sha256.json). All original annotations and acceptance thresholds remain unchanged. Codex previously read each of the 297 undecided original posts and now read each of the 15 added candidates in full. Every new annotation remains `ai_suggested`; none has been marked human-verified by the assistant. Real Reddit posts can themselves contain model-generated text, which does not imply independent human-authored source prose.

**Human review and recalculation:** Run `python3 scripts/review_labels.py review --curated --reviewer "Adi"`; see [REVIEWING.md](REVIEWING.md). The full post appears before the AI suggestion. The resumable queue reviews non-help categories first, then only currently selected help requests. Each actual acceptance, correction, exclusion or reopened decision triggers recalculation of the class counts, feasible total and help sample, and refreshes the saved queue, audit, validation report and status block. Replacements are drawn from the same seeded order. Any human-verified non-help post is retained even if it began as an unselected help proposal. Unselected help proposals remain unchanged in the audit; they are not deleted or relabeled as unsuitable.

**Audit and export:** [data/annotation_audit.csv](data/annotation_audit.csv) retains all 335 sources, original notes, proposed labels, current review decisions and selection reasons. [data/curation_selection.csv](data/curation_selection.csv) records the selected and reserve IDs, seed and ranks; [data/curated_review_queue.csv](data/curated_review_queue.csv) contains only pending intended inclusions. [data/curation_manifest.json](data/curation_manifest.json) fingerprints the supplemental inputs and records the strategy. [data/validation_report.md](data/validation_report.md) distinguishes full-pool, selected projected and selected verified distributions. Export with `python3 scripts/review_labels.py export` only after actual review; it refuses unreviewed selected rows or an infeasible/unbalanced set. It writes exactly `text,label,note` to a single unsplit `labels.csv`, preserving cold notes exactly and using `ai_suggested; human_verified` for individual CLI reviews or `ai_suggested; human_verified_offline` with an attestation ID for reviewer-attested offline approval. Unselected unreviewed help does not block export. Criteria 1–3 and 5 remain unevaluated. No split, baseline or training was run.

**Three difficult real cases (original AI proposals; current review state is in the audit):**

- [Discuss GPU configs | Why do I get 40 tokens / sec on a rtx 3060!?](https://www.reddit.com/r/LocalLLaMA/comments/137x4qg/discuss_gpu_configs_why_do_i_get_40_tokens_sec_on/) — `technical_report` versus `help_request`. Detailed working server configuration, model comparison and generation log remain informative beyond the closing speed question. Review provenance: see the audit and case log.
- [Fatty Alpaca: alpaca-lora-65B GGML, quantised to 4bit and 2bit](https://www.reddit.com/r/LocalLLaMA/comments/12sqo3r/fatty_alpaca_alpacalora65b_ggml_quantised_to_4bit/) — `resource_share` versus `technical_report`. Announces quantized model artifacts; timings and sample outputs support the release. Review provenance: see the audit and case log.
- [Speed difference between 8bit and 4bit](https://www.reddit.com/r/LocalLLaMA/comments/122218d/speed_difference_between_8bit_and_4bit/) — `help_request` versus `technical_report`. Timings and installation changes mainly diagnose an unresolved suspected CUDA/setup problem. Review provenance: see the audit and case log.

More boundary cases and suitability decisions are documented in [data/ambiguous_cases.md](data/ambiguous_cases.md). Synthetic stress-test examples remain outside the real-post dataset.

---

## The Training Run

<!-- Your starting model, your settings, and anything you changed and why. -->

**Base model:**

**Settings:** <!-- epochs, learning rate, batch size, seed -->

**Anything I changed from the defaults, and why:**

**Split sizes:** <!-- train / val / test, and per-label counts in the test
split. If a label had fewer than about 8 in test, say so — it explains a lot
of next unit's variance. -->



---

## How I Used AI

<!-- Two specific moments — what you asked, what came back, what you changed.

     ⚠️ Plus disclosure of any pre-labelling. If you had a model pre-label a
     batch and then read and corrected every one, say that. It's an allowed
     workflow and disclosing it costs you nothing. Not disclosing it is the
     problem. -->

**Moment 1**

- *What I asked for:* AI-assisted labeling of the remaining real posts using the existing primary-purpose taxonomy, preserving independent annotations.
- *What came back:* 297 original individually reasoned proposals and 15 supplemental technical-report proposals, all stored separately with `ai_suggested` provenance and competing interpretations. The four original AI-proposed exclusions remain unreviewed.
- *What I changed:* Review decisions and corrections are recorded in the audit and decision journal as I make them. At preparation, all proposals were pending. The original cold annotations and exclusions were preserved.

**Moment 2**

- *What I asked for:* A resumable human-review workflow and honest validation against the five existing criteria.
- *What came back:* A curated review/export CLI that retains all usable non-help posts, samples help with a recorded seed, recalculates after every decision, and gates export on actual review and balance. The selected 200-post composition passes balance; the audit distinguishes individual CLI reviews from a reviewer-attested offline batch approval, subject to terminal confirmation.
- *What I changed:* The status block and validation report track outstanding review and dataset construction decisions; no model training has been started for this milestone.

**Pre-labelling disclosure:** The first 20 usable posts were labeled independently before AI suggestions. The remaining 297 original decisions and 15 supplemental technical-report labels were proposed by Codex after reading each full stored post; none is an independent or human-verified annotation until actual review. Offline verification, if confirmed, records the reviewer’s completed-review attestation in one event, not an independently observed or individually timestamped CLI review. AI-assisted review does not establish inter-annotator agreement, and the separate staff-taxonomy exercise has not been performed here.

<!-- ═══════════════════════ UNIT 6 — THE TEST ═══════════════════════

     Don't fill these in during unit 5.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Baseline vs. Trained

<!-- Both models on the same posts. `python baseline.py --trained results.json`
     prints this table for you. -->

| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy |  |  |  |
| Macro F1 |  |  |  |
| F1 — `label_one` |  |  |  |
| F1 — `label_two` |  |  |  |

**What I predicted before I looked:**
<!-- Milestone 1 asks you to write this BEFORE seeing the trained numbers. A
     prediction made afterwards isn't one. -->

**What the gap actually means:**
<!-- If the baseline matched your trained model, your fine-tuning added
     nothing — and that is a real finding, not a failure. Say it plainly. -->



---

## Run Log — Before

<!-- Five criteria across three seeds. The notebook's section 6 prints the
     spread table; the Target and Verdict columns are yours. -->

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

### Confusion matrix

<!-- ⚠️ TYPED AS A MARKDOWN TABLE. The notebook prints one ready to paste.
     An image of a matrix earns nothing. -->

| true \ predicted |  |  |  |
|---|---|---|---|
| **** |  |  |  |
| **** |  |  |  |
| **** |  |  |  |

**My biggest off-diagonal number, and what it means:**
<!-- Not "the model made mistakes" — WHICH boundary it didn't learn, and which
     direction. "7 real analysis posts were called hot_take and only 3 went the
     other way" is a direction, not just an error rate. -->



---

## Verdicts and Diagnoses

<!-- MET or MISSED against LAST UNIT's target. The target has to hold across
     all three seeds, not turn up sometimes. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**

<!-- For each miss: the cause, and how you know. The four common causes are:
     too few examples for a label, a boundary you applied inconsistently, a
     genuinely hard label pair, and a task the model can't reach from this
     much data.

     ⚠️ Use your agreement report as evidence. It is the only instrument you
     have that can tell a LABELLING problem from a MODEL problem, and this
     section is graded on whether you used it that way. -->



---

## Agreement Report

<!-- Your rate against the staff set, and every disagreement adjudicated.

     Remember you labelled these 30 under the STAFF taxonomy in
     data/staff_taxonomy.md, not your own — so every argument below is made
     from those definitions and those decision rules. -->

**Agreement rate:** ___ / 30 = ___%

<!-- Nobody grades this number. A 60% who argues every disagreement from the
     stated rules beats a 95% who wrote "staff was right" nine times. Several
     of the 30 were chosen because they're genuinely ambiguous — you should be
     winning some of these. -->

**Disagreements**

<!-- Three lines each: the post, both labels, and who you think is right and
     why — grounded in the staff definitions you were both applying.

     Then sort each into one of three piles:
       (a) the rule covered it and I applied it loosely → a consistency problem
       (b) the rule genuinely doesn't say               → a gap in the definitions
       (c) the rule is ambiguous here and my reading is defensible → argue it.
           This is a legitimate win.

     Pile (a) is the one that matters most for your diagnosis: if you applied a
     written rule two different ways on 30 posts, that is direct evidence about
     what you did across your own 200. -->

**1.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**2.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**What the pattern in my disagreements tells me:**



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Run Log — After

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it didn't, say so. Relabelling that didn't help is a genuinely
     interesting result and earns full credit. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped. -->



**The gap between what I meant my labels to capture and what the model
learned:**
<!-- Two sentences. Your confusion matrix is the evidence. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 5

       [ ] criteria.md has five numbered criteria, each naming a NUMBER
       [ ] Each has a reason underneath tied to your data or taxonomy
       [ ] labels.csv: at least 150 rows, text/label/note, ONE file not split
       [ ] No label above 70%
       [ ] All five unit 5 sections have real content
       [ ] Label Taxonomy includes the decision rule for your hardest boundary
       [ ] The Dataset includes three hard cases
       [ ] results.json and test_split.csv committed (the notebook does this)
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 6

       [ ] Baseline vs. Trained table, with your prediction written beforehand
       [ ] Run Log — Before, five criteria across three seeds
       [ ] Confusion matrix TYPED AS A MARKDOWN TABLE
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, using the agreement report as evidence
       [ ] Agreement Report with every disagreement adjudicated
       [ ] One improvement, with Run Log — After
       [ ] What's Still Broken
       [ ] results_three_seeds_before.json, results_three_seeds_after.json,
           baseline_results.json and
           agreement_results.json committed
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
