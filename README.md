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

<!-- Where you collected from, how you labelled, your counts, and three hard
     cases. -->

**Where the posts came from:**

**How I labelled them:** <!-- Cold first? Pre-labelled with AI and corrected?
Say so plainly — the disclosure is required, not penalised. -->

**Counts per label:**

| Label | Count | Share |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |
| **Total** |  | 100% |

**Three hard cases**

<!-- Any post that made you pause: what it was, which two labels it could have
     been, and what you chose. These are worth more than the easy 190. -->

**1.**
> *The post:*
>
> *Could have been:*
>
> *I chose, because:*

**2.**
> *The post:*
>
> *Could have been:*
>
> *I chose, because:*

**3.**
> *The post:*
>
> *Could have been:*
>
> *I chose, because:*

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

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Pre-labelling disclosure:**

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
