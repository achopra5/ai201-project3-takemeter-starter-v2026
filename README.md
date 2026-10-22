# TakeMeter

**Unit 5 submission: READY.** The dataset, taxonomy, five precommitted criteria, original training outputs and write-up are complete. The model misses its performance targets; readiness here means an accurate, reproducible submission, not deployment readiness. Existing exploratory follow-up results are included without further experimentation.

**Unit 6 automated evaluation: complete; personal staff selections saved; TF reference pending.** The baseline and fresh three-epoch length-only experiment are saved below. The student's 30 selections supplied in chat are recorded in [my_staff_labels.csv](my_staff_labels.csv), with the original post text unchanged. The blank [review workbook](staff_review.xlsx) remains available as the original template. Unit 6 has not been submitted to the course portal.

**Repository:** [achopra 5/ai 201-project 3-takemeter-starter-v 2026](https://github.com/achopra5/ai201-project3-takemeter-starter-v2026).

[Setup and course requirements](RUNNING.md) · [Five original criteria](criteria.md) · [Dataset validation](data/validation_report.md) · [Submission checks](submission/validation_report.md) · [Reproducibility and local artifacts](submission/REPRODUCIBILITY.md).

## What This Does

TakeMeter classifies public **r/LocalLLaMA** text submissions by their primary communicative purpose: `technical_report`, `help_request`, `discussion` or `resource_share`. It describes what an author is doing, not whether a post is true or high quality. The [38-post exploration](exploration.md) motivated the taxonomy. A post about model performance can be a completed experiment, an unresolved support request, an opinion or a release; subject keywords alone do not distinguish those purposes.

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
Selected verified posts: 200, including all 20 unchanged cold annotations. Selected human-reviewed AI labels: 180, of which 180 are covered by offline batch attestation. Individual CLI review events: 0; offline attestation events: 1. This block reports dataset review only; model outcomes appear below.

**Curated distribution** (all selected labels review-verified):

- `technical_report`: 36 (18.00%).
- `help_request`: 58 (29.00%).
- `discussion`: 51 (25.50%).
- `resource_share`: 55 (27.50%).

Projected total: 200; projected balance: PASS. Retain all usable non-help posts; select 58 help requests, including 13 cold help requests, using seed 20261018.
Supplemental candidates: 15. Help reserves: 128. Parked unreviewed proposals: 132 (including unselected help and proposed exclusions).
Only selected rows require review for export. Unselected proposals remain in the audit; they are never marked verified or unsuitable just because they were not sampled.
<!-- MILESTONE4_STATUS_END -->

### Sources, sampling and provenance

[labels.csv](labels.csv) contains **200 real archived r/LocalLLaMA submissions**, with exactly `text,label,note`, complete stored title/body text, no empty rows and no exact/normalized text duplicates. The class counts are **36 technical reports (18%), 58 help requests (29%), 51 discussions (25.5%) and 55 resource shares (27.5%)**. Synthetic taxonomy stress tests and staff/practice posts are excluded.

The original frozen collection has 320 candidates from the [pszemraj/LocalLLaMA-posts archive](https://huggingface.co/datasets/pszemraj/LocalLLaMA-posts), collected with seed 20261018. Its collection script was not rerun. A separate targeted search of 11 historical archive pages (1,100 scan rows) added **15 technical-report candidates**, each read in full before its AI proposal. [Collection provenance](data/supplemental_collection.manifest.json), [supplemental candidates](data/supplemental_candidates.csv) and pinned raw response pages preserve full text, URLs, IDs, retrieval times, archive row indices and hashes. Locally matched archive records establish source provenance; live Reddit availability and authorship were not independently reauthenticated. Some real posts quote or disclose model-authored prose.

The curation strategy retained **every usable technical report, discussion and resource share**, with no artificial category caps. All 20 independent cold rows were retained. Help requests alone were sampled to meet the precommitted 15–40% bounds and minimum 200 posts: all **13 cold help requests** plus **45 additional help requests**, ranked by ascending SHA-256 of `20261018:source_id`. This reproducible order does not use post text, model scores or perceived difficulty. The [selection audit](data/curation_selection.csv) retains selected and reserve IDs/ranks. The other **128 help requests** remain reserves. Three original exclusions remain unchanged; four AI-proposed exclusions remain parked and **unreviewed**, outside the selected batch.

The source pool is 335 posts, not 335 verified training examples. Enriching technical reports and downsampling help changes class prevalence; the final dataset does not estimate organic subreddit traffic. Stored sources are historical 2023 material, 49 pool timestamps are missing, and unique text/IDs do not rule out same-author or related-thread leakage. Full text is preserved in the dataset even when the model truncates its input.

### Human review and annotation evidence

The **first 20 usable posts were independently labeled**, retain their original text, labels and `note=cold`, and are not AI-generated labels. **180 selected AI suggestions were manually reviewed offline by Adi and approved without corrections through one explicit terminal-confirmed batch attestation**, recorded at `2026-10-18T23:31:08.660993+00:00` in [the review journal](data/annotation_reviews.jsonl).

Attestation ID: `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`. Snapshot SHA-256: `9cfc140cc2f30228a55d3fbca9a7060729ba25c5a0452ca672b191d422f6a4c3`.

Their notes retain `ai_suggested; human_verified_offline` and the attestation ID. There are **zero individual CLI review events**, no invented per-post review timestamps and no independent second annotation. The single timestamp records attestation, not when each post was read. [The annotation audit](data/annotation_audit.csv) retains all 335 source URLs, IDs, original annotations, proposals, review provenance and selection reasons. [REVIEWING.md](REVIEWING.md) documents the resumable workflow; no review remains for the selected dataset.

### Three difficult actual examples

All three examples below are in the exported dataset and covered by the same offline attestation; the rationales originated as AI suggestions.

1. [Discuss GPU configs | Why do I get 40 tokens / sec on a rtx 3060!?](https://www.reddit.com/r/LocalLLaMA/comments/137x4qg/discuss_gpu_configs_why_do_i_get_40_tokens_sec_on/) — **technical_report**, competing with `help_request`. The author supplies a completed server setup, 7B/13B speed comparison and a generation log (41.23 tokens/s). Those findings remain useful beyond the closing request to explain the speed difference, so completed-results precedence applies.
2. [Fatty Alpaca: alpaca-lora-65B GGML, quantised to 4bit and 2bit](https://www.reddit.com/r/LocalLLaMA/comments/12sqo3r/fatty_alpaca_alpacalora65b_ggml_quantised_to_4bit/) — **resource_share**, competing with `technical_report`. The main contribution is newly available quantized model artifacts, their download locations and requirements. Timings and sample outputs support the release, so release precedence applies.
3. [My first chat with llama-7b about catching mice was fun!](https://www.reddit.com/r/LocalLLaMA/comments/1254n2v/my_first_chat_with_llama7b_about_catching_mice/) — **discussion**, competing with `technical_report`. The post shares an amusing conversational failure. A launch command and crash message do not make its primary purpose a substantive completed technical investigation.

[Additional difficult boundaries and exclusions](data/ambiguous_cases.md) and [supplemental report cases](data/supplemental_cases.md) preserve competing interpretations. No label was changed to satisfy balance or improve model scores.

## The Training Run

The original Unit 5 run fine-tuned **`distilbert-base-uncased`** with a four-class classification head for **3 epochs**, learning rate **2e-5**, training/evaluation batch size **16**, maximum sequence length **128** and **seed 42**. Hardware was **Apple Silicon MPS**, PyTorch **2.14.1**. The notebook maps labels in this order: technical report, help request, discussion, resource share.

Stratified 70/15/15 splitting used the same seed for the split and model initialization. The notebook's floating-point validation-share calculation yields **139 train / 31 validation / 30 test**, rather than nominal 140/30/30. Train supports are 25/40/35/39, validation supports 6/9/8/8 and test supports 5/9/8/8 in the stated label order. With nine batches per epoch and no dropped last batch, the original fit performs **27 optimizer updates**. The exact original notebook, dataset and split identities are preserved.

The authoritative seed-42 [results.json](results.json) records **53.3333% test accuracy (16/30)** and **macro F 1 0.383207** on [test_split.csv](test_split.csv). Per-class outcomes are:

| Label | Precision | Recall | F 1 | Test support |
|---|---:|---:|---:|---:|
| `technical_report` | 0.000000 | 0.000000 | 0.000000 | 5 |
| `help_request` | 0.466667 | 0.777778 | 0.583333 | 9 |
| `discussion` | 1.000000 | 0.125000 | 0.222222 | 8 |
| `resource_share` | 0.571429 | 1.000000 | 0.727273 | 8 |

The original seed-42 validation-loss curve was **1.368994 → 1.347105 → 1.335875**. Falling loss suggested further investigation, but did not establish improved four-class decisions. The later runs below were completed separately; they did not overwrite Unit 5 evidence.

## How I Used AI

**Collection and annotation:** Codex helped implement archive collection and supplemental retrieval, preserve source provenance and read the full stored posts to propose 297 original undecided decisions plus 15 supplemental report labels. The original 20 cold labels were completed independently and preserved. Titles/keywords were retrieval leads, not substitutes for reading and applying the taxonomy. The source material is real archived Reddit text, not invented posts.

**Curation and human review:** I asked for all usable non-help categories to be retained and help requests to be sampled reproducibly. Codex implemented seeded curation, backups, hash checks, the resumable CLI and `attest-offline`. I completed the selected 180-post review outside the CLI, approved the proposals without corrections, and entered the exact batch confirmation myself. Codex's code records that assertion as one attestation; it did not observe or record 180 individual reviews. This is AI-assisted review, not independent inter-annotator agreement.

**Code, experiments and documentation:** Codex helped configure and diagnose the DistilBERT workflow, implement validation-only truncation audits and controlled training comparisons, save train/validation predictions and prepare a separate one-time final evaluator. The original notebook outputs and the saved follow-up evaluation are the evidence for what ran. Codex assisted with tests, integrity checks, interpretation and this closeout write-up. No additional collection, training, model inference or hyperparameter search was performed during closeout. AI involvement does not establish that the taxonomy is objectively correct or that the model generalizes.

## Original Three-Seed Results

[results_three_seeds_before.json](results_three_seeds_before.json) preserves the original setup for seeds 42, 7 and 2024. All test splits contain 30 posts. These seeds reuse overlapping examples, so they are not independent replications.

| Seed | Test accuracy | Macro F 1 | Technical F 1 | Help F 1 | Discussion F 1 | Resource F 1 |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 0.533333 | 0.383207 | 0.000000 | 0.583333 | 0.222222 | 0.727273 |
| 7 | 0.366667 | 0.238722 | 0.000000 | 0.428571 | 0.000000 | 0.526316 |
| 2024 | 0.400000 | 0.271111 | 0.000000 | 0.444444 | 0.000000 | 0.640000 |

Mean original accuracy: **0.433333 (43.33%)**. Mean original macro F 1: **0.297680**. Accuracy ranges from 0.366667 to 0.533333; macro F 1 from 0.238722 to 0.383207.

### Original confusion matrices

Rows are gold labels; columns are predictions. Each matrix sums to 30, and every row support is 5/9/8/8. These are copied from saved results, not new evaluations.

#### Seed 42

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 3 | 0 | 2 |
| `help_request` | 0 | 7 | 0 | 2 |
| `discussion` | 0 | 5 | 1 | 2 |
| `resource_share` | 0 | 0 | 0 | 8 |

#### Seed 7

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 4 | 0 | 1 |
| `help_request` | 0 | 6 | 0 | 3 |
| `discussion` | 0 | 6 | 0 | 2 |
| `resource_share` | 0 | 3 | 0 | 5 |

#### Seed 2024

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 1 | 1 | 3 |
| `help_request` | 0 | 4 | 3 | 2 |
| `discussion` | 0 | 4 | 0 | 4 |
| `resource_share` | 0 | 0 | 0 | 8 |

The largest original seed-42 off-diagonal cell is **5 discussions predicted as help requests**, while no help requests are predicted as discussions. All five technical reports are assigned to help or resources; the classifier never predicts technical reports. That is evidence of an unlearned purpose distinction, not proof that those source labels are incorrect.

## Exploratory Improvement Experiment

**Status: selected and evaluated; experimentation is complete.** The selected candidate is **`controlled-len256-epoch6`**, the saved epoch-6 checkpoint of an **eight-epoch learning-rate schedule**. It has **54 of 72 planned optimizer updates**, with learning rate **5e-6** at capture. It is **not a freshly trained six-epoch model**. Learning rate at initialization, batch size, dataset, taxonomy, label mapping, seed set and test examples stayed fixed.

The [frozen protocol](experiments/validation-20261018T234742Z/protocol.json) first reproduced the original three-epoch schedule at 128 tokens, then compared epochs 3/6/8 along one eight-epoch trajectory for each length/seed. The shared trajectory controls the scheduler history within each duration comparison. Epoch 3 of an eight-epoch schedule differs from a run whose scheduler ends at epoch 3. There were **nine fits**, seven eligible configurations and **513 total optimizer updates**. [The experiment record](experiments/validation-20261018T234742Z/EXPERIMENT.md) and [saved validation results](experiments/validation-20261018T234742Z/validation_results.json) retain the design and diagnostics.

### Validation-only selection and truncation

The audit inspected **training and validation inputs only**, counting tokens including special tokens. About **69.7%** of partition-level inputs exceed 128 tokens; at 256 about 42.4% still truncate. Moving to 256 retains about **16.9 percentage points more input tokens** on average across the six seed/partition groups. Technical reports are particularly affected: **24/25 training reports and all 6/6 validation reports truncate at 128 in every seed**. Long posts dominate total tokens, so 128 retains only 25–31% of all tokens per partition, versus 38–50% at 256. See [the per-class audit](experiments/validation-20261018T234742Z/truncation_audit.json). Full dataset text was not shortened.

A data-only rule included 256 when at least 20% truncate at 128 and retained-token fraction rises by at least 10 percentage points. Candidate selection then maximized **mean validation macro F 1 across the same three seeds**, with precommitted tie-breaks for minimum seed F 1, loss, length, epoch and name. No test outcome was queried during candidate selection. The original three-epoch reference remained eligible.

| Candidate | Mean validation accuracy | Mean validation macro F 1 | Mean validation loss |
|---|---:|---:|---:|
| `reference-len128-epoch3` | 0.473118 | 0.346883 | 1.307298 |
| `controlled-len128-epoch3` | 0.494624 | 0.369099 | 1.227979 |
| `controlled-len128-epoch6` | 0.462366 | 0.347800 | 1.102840 |
| `controlled-len128-epoch8` | 0.473118 | 0.356778 | 1.083635 |
| `controlled-len256-epoch3` | 0.494624 | 0.364395 | 1.220285 |
| `controlled-len256-epoch6` | 0.537634 | 0.448425 | 1.088021 |
| `controlled-len256-epoch8` | 0.526882 | 0.438160 | 1.063611 |

The selected checkpoint's mean training macro F 1 is **0.7081**, versus **0.4484 on validation**, a gap of about 0.260. Per-seed validation F 1 is 0.3890/0.4222/0.5341; two seeds still predict no technical reports. More fitting helps some decisions but leaves a substantial generalization gap. At 128, extending the shared run does not consistently improve F 1; at 256, epoch 8 has lower loss but lower F 1 than epoch 6. Loss alone was therefore insufficient for selection. The validation set has only 31 posts and 6–9 per class; one prediction changes its accuracy by 3.23 percentage points.

### Existing held-out follow-up outcomes

Adi selected the checkpoint in [the final evaluation plan](experiments/validation-20261018T234742Z/final_evaluation_plan.json). The separate evaluator completed at **2026-10-19T 00: 00: 06.233626+00: 00** and saved [final_test_results.json](experiments/validation-20261018T234742Z/final_test_results.json). Its metrics were verified against saved predictions during closeout; no inference was repeated. Original files were not overwritten.

**This follow-up evaluation is exploratory:** original test aggregates were already known before designing the intervention. Validation-only selection avoids repeatedly tuning on test outcomes, but does not make the follow-up a pristine confirmatory study.

| Seed | Original accuracy | Improved accuracy | Original macro F 1 | Improved macro F 1 |
|---|---:|---:|---:|---:|
| 42 | 0.533333 | 0.600000 | 0.383207 | 0.473508 |
| 7 | 0.366667 | 0.500000 | 0.238722 | 0.389526 |
| 2024 | 0.400000 | 0.400000 | 0.271111 | 0.305882 |
| **Mean** | **0.433333** | **0.500000** | **0.297680** | **0.389639** |

Mean accuracy improves by **6.67 percentage points** and macro F 1 by **0.091959**. Seed 2024's accuracy remains 0.4000; gains are not uniform. Improved accuracy spans 0.4000–0.6000 and macro F 1 spans 0.305882–0.473508.

| Improved seed | Technical F 1 | Help F 1 | Discussion F 1 | Resource F 1 |
|---|---:|---:|---:|---:|
| 42 | 0.000000 | 0.736842 | 0.461538 | 0.695652 |
| 7 | 0.000000 | 0.521739 | 0.400000 | 0.636364 |
| 2024 | 0.000000 | 0.400000 | 0.000000 | 0.823529 |

**Technical-report F 1 is zero on all three improved test runs.** Seeds 42 and 7 make no technical-report predictions; seed 2024 makes one incorrect technical prediction and correctly recognizes none of the five reports. Seed 2024 also has zero discussion F 1. Average improvement does not rescue these failures.

### Improved confusion matrices

Rows and columns use exactly the same order as the original matrices. Each seed uses its unchanged original 30-post test split.

#### Seed 42

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 1 | 1 | 3 |
| `help_request` | 0 | 7 | 1 | 1 |
| `discussion` | 0 | 2 | 3 | 3 |
| `resource_share` | 0 | 0 | 0 | 8 |

#### Seed 7

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 4 | 0 | 1 |
| `help_request` | 0 | 6 | 0 | 3 |
| `discussion` | 0 | 3 | 2 | 3 |
| `resource_share` | 0 | 1 | 0 | 7 |

#### Seed 2024

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---:|---:|---:|---:|
| `technical_report` | 0 | 4 | 0 | 1 |
| `help_request` | 0 | 5 | 4 | 0 |
| `discussion` | 1 | 6 | 0 | 1 |
| `resource_share` | 0 | 1 | 0 | 7 |

In seed 42, discussion→help errors fall from 5 to 2 and correct discussions rise from 1 to 3. However, three discussions and three technical reports are now predicted as resource shares. The model still misses the report category entirely. Each test prediction changes accuracy by 3.33 percentage points; report recall moves in steps of 20% with only five reports. Three overlapping splits cannot establish stable generalization or organic-community performance.

## Five Original Acceptance Criteria — Historical Exploratory Comparison

[criteria.md](criteria.md) is preserved byte-for-byte. Criteria 1–3 must hold for **every seed**, and criterion 3 for every class in every seed. Validation gains do not count as held-out passes.

| # | Original target | Original verdict | Improved verdict | Evidence |
|---|---|---|---|---|
| 1 | Test accuracy ≥ 0.70 for every seed | **FAIL** | **FAIL** | Original maximum 0.533333; improved maximum 0.600000, all below 0.70. |
| 2 | Test macro F 1 ≥ 0.60 for every seed | **FAIL** | **FAIL** | Original maximum 0.383207; improved maximum 0.473508, all below 0.60. |
| 3 | Every class test F 1 ≥ 0.40 for every seed | **FAIL** | **FAIL** | Technical-report F 1 is 0 in every original and improved seed. |
| 4 | Each full-dataset class share 15–40% | **PASS** | **PASS** | Unchanged shares 18%,29%,25.5%,27.5%; 200 genuine archived posts. |
| 5 | Staff-taxonomy agreement ≥ 23/30 | **NOT EVALUATED** | **NOT EVALUATED** | Separate Unit 6 personal annotation/staff comparison is absent. |

The evidence is consistent with too few effective training updates initially, severe context truncation, sparse technical-report examples and limited generalization from 139 training posts. These are hypotheses supported by diagnostics, not experimentally isolated causes of every error. No staff agreement or independent second annotation exists to distinguish model limitations from possible label inconsistency; the confusion matrices alone cannot establish annotation mistakes. Thresholds and labels were not changed after inspecting outcomes.

## Baseline vs. Trained — Unit 6 Started

**Baseline completed October 21, 2026.** [baseline_results.json](baseline_results.json) records the local `facebook/bart-large-mnli` zero-shot run on all 30 unchanged posts in [test_split.csv](test_split.csv), compared with the original seed-42 [results.json](results.json). The command was `.venv/bin/python baseline.py --trained results.json`; the pipeline reported `mps:0`. [label_definitions.txt](label_definitions.txt) now contains the four exact TakeMeter definitions from the taxonomy above, replacing the starter's unrelated running-forum examples. No labeled examples were supplied to the baseline. The prompt uses these short definitions; the longer ordered tie-break rules in the README are not included.

Baseline accuracy is **0.333333 (10/30)** and macro F1 is **0.311343**, versus the original trained model's **0.533333 (16/30)** and **0.383207**. Fine-tuning gains **20 percentage points** of accuracy and **0.071864** macro F1 on this split. A constant majority-class prediction would score 9/30 (30%) here, so the zero-shot accuracy is only one correct post above that reference.

The class-level picture is mixed. Baseline F1 is **0.500000 technical report**, **0.000000 help request**, **0.370370 discussion** and **0.375000 resource share**. The original trained F1 values are **0.000000**, **0.583333**, **0.222222** and **0.727273**, respectively. The trained model improves help requests and resource shares while losing ground on technical reports and discussions. Higher aggregate accuracy therefore does not establish better performance across all four purposes. This baseline comparison covers seed 42 only; the baseline has not been evaluated on the other seeds' test sets.

<!-- UNIT6_BASELINE_TABLE_START -->
| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy | 0.333 | 0.533 | +0.200 |
| Macro F1 | 0.311 | 0.383 | +0.072 |
| F1 — `technical_report` | 0.500 | 0.000 | -0.500 |
| F1 — `help_request` | 0.000 | 0.583 | +0.583 |
| F1 — `discussion` | 0.370 | 0.222 | -0.148 |
| F1 — `resource_share` | 0.375 | 0.727 | +0.352 |
<!-- UNIT6_BASELINE_TABLE_END -->

**Prediction provenance:** Original trained results were already known before Week 6 began. No pre-result student prediction is recorded, and none is supplied retroactively. This run and interpretation were completed with Codex assistance. The saved Unit 5 closeout reports remain historical snapshots; their pending-baseline statements describe October 19, before this run, and their pinned definition-file checksum describes the old starter definitions.

<!-- UNIT6_LENGTH_EXPERIMENT_START -->
## Unit 6 Single-Variable Experiment: 128 to 256 Tokens

**Completed: three fresh fits, three epochs each.** This is the required single-variable experiment. It is separate from the earlier exploratory eight-epoch-scheduler experiment. Only maximum input length changes from 128 to 256. Learning rate remains 2e-5, both batch sizes 16, epochs 3, seeds 42/7/2024, and the dataset, label mapping and split algorithm remain unchanged. The linear scheduler has exactly 27 optimizer updates per seed and ends at zero learning rate. No earlier checkpoint was used for initialization or as a substitute result.

[After results](results_three_seeds_after.json), [fixed protocol](experiments/unit6-length256-three-epochs/protocol.json), [runner](scripts/unit6_experiment.py) and compact per-seed metadata, histories and test predictions under `experiments/unit6-length256-three-epochs/runs/` record the actual execution. The runner compiles only function definitions from the unchanged original notebook. Weights remain local and ignored. GPU nondeterminism and the longer dropout tensors limit exact numerical reproducibility.

### Before and after on matching test splits

| Seed | Before accuracy | After accuracy | Accuracy difference | Before macro F1 | After macro F1 | F1 difference |
|---|---|---|---|---|---|---|
| 42 | 0.533333 | 0.533333 | +0.000000 | 0.383207 | 0.344322 | -0.038885 |
| 7 | 0.366667 | 0.366667 | +0.000000 | 0.238722 | 0.231801 | -0.006921 |
| 2024 | 0.400000 | 0.333333 | -0.066667 | 0.271111 | 0.217857 | -0.053254 |
| Mean | 0.433333 | 0.411111 | -0.022222 | 0.297680 | 0.264660 | -0.033020 |

### Per-class F1 before and after

| Seed | Label | Test support | Before F1 | After F1 | Difference |
|---|---|---|---|---|---|
| 42 | `technical_report` | 5 | 0.000000 | 0.000000 | +0.000000 |
| 42 | `help_request` | 9 | 0.583333 | 0.615385 | +0.032051 |
| 42 | `discussion` | 8 | 0.222222 | 0.000000 | -0.222222 |
| 42 | `resource_share` | 8 | 0.727273 | 0.761905 | +0.034632 |
| 7 | `technical_report` | 5 | 0.000000 | 0.000000 | +0.000000 |
| 7 | `help_request` | 9 | 0.428571 | 0.444444 | +0.015873 |
| 7 | `discussion` | 8 | 0.000000 | 0.000000 | +0.000000 |
| 7 | `resource_share` | 8 | 0.526316 | 0.482759 | -0.043557 |
| 2024 | `technical_report` | 5 | 0.000000 | 0.000000 | +0.000000 |
| 2024 | `help_request` | 9 | 0.444444 | 0.166667 | -0.277778 |
| 2024 | `discussion` | 8 | 0.000000 | 0.133333 | +0.133333 |
| 2024 | `resource_share` | 8 | 0.640000 | 0.571429 | -0.068571 |

### Actual three-seed run log

Original runs use 128 tokens and three epochs on MPS with PyTorch 2.14.1; their saved results remain unchanged. Each seed uses 139 train / 31 validation / 30 test posts. In label order `technical_report`, `help_request`, `discussion`, `resource_share`, the supports are 25/40/35/39 in training, 6/9/8/8 in validation and 5/9/8/8 in test. The original notebook output preserves the original execution; no original run timestamps have been invented. The following timestamps and measured training runtimes belong to the new 256-token fits.

| Seed | Device | Updates | Training seconds | Started UTC | Completed UTC |
|---|---|---|---|---|---|
| 42 | mps | 27 | 14.30 | 2026-10-22T00:13:27.202020+00:00 | 2026-10-22T00:13:42.763468+00:00 |
| 7 | mps | 27 | 10.35 | 2026-10-22T00:13:42.977919+00:00 | 2026-10-22T00:13:54.139403+00:00 |
| 2024 | mps | 27 | 10.34 | 2026-10-22T00:13:54.369520+00:00 | 2026-10-22T00:14:05.529093+00:00 |

### After confusion matrices

Rows are original human labels; columns are predictions, in the original four-label order. Every matrix sums to 30. The original matrices are preserved in **Original confusion matrices** above.

#### 256 tokens, three epochs, seed 42

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---|---|---|---|
| `technical_report` | 0 | 4 | 0 | 1 |
| `help_request` | 0 | 8 | 0 | 1 |
| `discussion` | 0 | 5 | 0 | 3 |
| `resource_share` | 0 | 0 | 0 | 8 |

#### 256 tokens, three epochs, seed 7

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---|---|---|---|
| `technical_report` | 0 | 1 | 0 | 4 |
| `help_request` | 0 | 4 | 0 | 5 |
| `discussion` | 0 | 3 | 0 | 5 |
| `resource_share` | 0 | 1 | 0 | 7 |

#### 256 tokens, three epochs, seed 2024

| Gold / predicted | `technical_report` | `help_request` | `discussion` | `resource_share` |
|---|---|---|---|---|
| `technical_report` | 0 | 0 | 1 | 4 |
| `help_request` | 0 | 1 | 5 | 3 |
| `discussion` | 0 | 2 | 1 | 5 |
| `resource_share` | 0 | 0 | 0 | 8 |

### Result, diagnosis and remaining failure

**The proposed improvement did not improve these measurements.** Mean accuracy falls from 0.4333 to 0.4111; mean macro F1 falls from 0.2977 to 0.2647. Seeds 42 and 7 have unchanged accuracy, while seed 2024 loses two correct posts. Macro F1 falls at every seed. More available context by itself was insufficient under the original short training schedule.

After accuracy spans 0.3333–0.5333 (spread 0.2000); macro F1 spans 0.2179–0.3443 (spread 0.1265). These overlapping splits are sensitivity checks on one small dataset, not independent replications. One test decision changes accuracy by 3.33 percentage points; each report-recall step is 20 percentage points.

Technical-report F1 remains zero for every seed, with zero report predictions in all three new runs. In seed 42, five discussions become help requests while zero help requests become discussions. In seed 7, five help requests and five discussions become resource shares; the reverse cells are one and zero. The directional pattern supports a failure to distinguish primary purpose. It does not establish that the human labels are wrong. The baseline’s report F1 of 0.50 on seed 42, versus zero for both trained versions, shows that aggregate accuracy gains conceal a lost category.

The pre-existing token audit shows truncation was substantial, but this controlled result rejects the claim that doubling context alone solves it. Sparse report examples (25 in training), only 27 updates, mixed-purpose text and the small archive sample remain plausible explanations. They have not been experimentally separated here. The earlier schedule-and-length exploration cannot establish a length-only gain.

Original test outcomes and earlier exploratory outcomes were already known. This is an honest exploratory follow-up with a fixed requested intervention; no post-result seed selection, threshold changes, relabeling or additional tuning was performed. Retain the original trained setup for the comparison; these results do not justify replacing it with the longer input model.

### Original acceptance-criteria verdicts for the required experiment

| Criterion | Original target | Before | After | Diagnosis |
|---|---|---|---|---|
| 1 | Accuracy ≥ 0.70 for every seed | FAIL | FAIL | Best before and after accuracy is 0.533333; all three seeds fall short. |
| 2 | Macro F1 ≥ 0.60 for every seed | FAIL | FAIL | Best after macro F1 is 0.344322; all three seeds fall short. |
| 3 | Every class F1 ≥ 0.40 for every seed | FAIL | FAIL | Technical-report F1 is zero at every seed; discussions also remain weak. |
| 4 | Each full-dataset class share 15–40% | PASS | PASS | Dataset unchanged: 36/58/51/55 posts out of 200. Balance does not imply reliable classification. |
| 5 | Independent staff-taxonomy agreement ≥ 23/30 | NOT EVALUATED | NOT EVALUATED | Requires original student selections and the authentic TF reference; no personal decisions are fabricated. |

Criterion 5 concerns `analysis`, `hot_take`, `reaction` under the staff rules. All model metrics above concern only `technical_report`, `help_request`, `discussion`, `resource_share`. There is no justified direct confusion-pair mapping across the two independent tasks. Any later staff disagreement can motivate reflection about rule application, but cannot prove inconsistency on the TakeMeter dataset.

<!-- UNIT6_LENGTH_EXPERIMENT_END -->

## Agreement Report — Unit 6 Pending

**PERSONAL SELECTIONS SAVED; AGREEMENT NOT EVALUATED.** The student explicitly supplied all 30 labels and reasons in chat: 10 `analysis`, 10 `hot_take` and 10 `reaction`. [The submitted selections and reasons](data/staff_review/submitted_labels.csv) retain those choices; [my_staff_labels.csv](my_staff_labels.csv) joins them to the exact original [staff post text](data/staff_posts.csv), with only `text,label` columns. [Import provenance](data/staff_review/label_import.json) records the source and file hashes. The timestamp records import, not when labeling occurred. No returned workbook or independently observed review process is claimed.

The authentic `data/staff_labels.csv` from the TF is still absent, so no agreement rate, criterion-5 verdict or adjudicated disagreement is reported. The supplied reasons are original labeling rationales, not final adjudications against unseen staff answers. The 180-post offline training-data attestation remains a separate exercise. These Unit 6 requirements do not block the completed Unit 5 submission.

[The review workbook](staff_review.xlsx) contains the 30 exact original posts, blank yellow `my_label` dropdowns with only `analysis`, `hot_take`, `reaction`, and the complete original staff taxonomy on a separate sheet. [Instructions](STAFF_REVIEW_INSTRUCTIONS.md) explain how to return it. No AI labels or suggestions are supplied. This staff taxonomy never enters TakeMeter training, baseline scoring or model criteria 1–4.

[The converter](scripts/import_staff_review.py) supports both returned workbooks and explicitly supplied ID/label selections. This submission used the latter route and preserves the chat transcription rather than inventing a completed workbook. Both routes refuse partial labels, altered original text or silent replacement. [The agreement workflow](scripts/staff_agreement_workflow.py) is ready for the authentic TF reference: it validates all 30 reference IDs, records the student-supplied TF provenance, preserves original decisions and prepares a file containing each disagreement with blank final-label, pile, rule, reasoning and approval fields. Each final decision requires explicit `human_approved=yes`; a taxonomy-gap decision also requires a proposed rule. No adjudication is automatically assigned or approved. These future outputs are not created until their genuine inputs exist.

## What's Still Broken

The classifier does not reliably recognize technical reports, and discussion performance is unstable across seeds. The intended taxonomy distinguishes primary purpose even when posts share model names, hardware and numbers; the matrices show the model repeatedly maps those purposes into help or resource categories instead. Balanced labels and a larger context window did not solve that boundary.

All three precommitted held-out model thresholds remain missed. The small, deliberately curated archive sample, overlapping seeds, tiny class supports, validation candidate selection and previously known test aggregates limit the strength of the improvement claim. No deployment-readiness claim is made. The Unit 6 baseline, new length-only three-seed experiment and import of the student's personal selections are complete; authentic staff answers, agreement and adjudication remain pending. The earlier exploratory schedule experiment remains historical evidence and is not substituted for the required length-only experiment.

## Unit 6 Verification and Evidence

Run [the Unit 6 checker](scripts/check_unit6.py) to verify saved baseline metrics, all original hashes or explicitly retained historical snapshots, the three fresh runs, matching held-out identities, per-class metrics, training configuration, checkpoint hashes when locally present, and the blank workbook's exact contents and dropdowns. It performs no training or inference. [The validation report](submission/unit6_validation_report.json) records the current status; `course_portal_submitted` remains false. [Quality-check evidence](submission/unit6_quality_checks.json) records 71 passing tests, environment checks and workbook verification.

The unchanged [Unit 5 closeout manifest](submission/closeout_manifest.json) still contains every original hash. The sole documented file evolution is the starter baseline definition file, whose original bytes are retained in [the historical snapshot](submission/unit5_originals/label_definitions.txt). [The Unit 6 manifest](submission/unit6_manifest.json) pins both versions and the new saved evidence; no original hash was overwritten. Training data, annotations, original four-label taxonomy, criteria, notebook and original results remain unchanged. Model weights, caches and verbose training logs stay outside Git.

## Unit 5 Submission and Verification

The completed Unit 5 evidence is the community exploration, unchanged taxonomy and stress test, five reasoned numeric criteria,200-row reviewed dataset, original executed notebook/results/test split and this write-up. The existing history contains more than four student project commits; closeout adds descriptive commits while preserving that history. Performance-target failures are documented rather than concealed.

Run read-only submission checks from the repository root with the project environment active:

```bash
source .venv/bin/activate
python test.py
python -m unittest discover -s tests -v
python scripts/check_submission.py
python scripts/validation_experiment.py verify --experiment experiments/validation-20261018T 234742Z
git diff --check
git status --short
```

The [submission validation report](submission/validation_report.md) records completed checks, integrity and remaining Unit 6 work. Necessary source response pages and hash manifests are committed. Model checkpoints, caches, duplicate local backups and verbose training intermediates stay local; [reproducibility notes](submission/REPRODUCIBILITY.md) explain the exact paths and verification behavior. No original files were deleted.

**Final student action:** submit **https://github.com/achopra5/ai201-project3-takemeter-starter-v2026** as the repository link in the **Unit 5 assignment submission**. Repository preparation/push does not itself submit the assignment in the course portal. Use the same repository URL for Unit 6.
