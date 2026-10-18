# Acceptance Criteria — TakeMeter (Unit 5, Before Training)

**Community:** r/LocalLLaMA  
**Task:** Classify each complete text post into exactly one of `technical_report`, `help_request`, `discussion`, or `resource_share`, using the definitions and tie-break rules documented in `README.md`.  
**Decision date:** October 18, 2026  
**Status:** Five student-selected targets committed before inspecting training results.

These are **precommitted evaluation targets**, not claims about achieved performance. The student's choices are the five numeric thresholds below; the rationales and measurement details were refined with AI coaching. We will evaluate model criteria using the held-out 15% test split produced by the notebook, and examine all three Unit 6 seeds (42, 7, 2024). For a model criterion to be met in Unit 6, **every seed must meet it**; a good average does not rescue a failed seed. Criteria 4 and 5 measure data and annotation process rather than model predictions.

---

## 1. Overall held-out accuracy is at least 0.70

**Acceptance target:** Test-set accuracy **>= 0.70** for **each of the three Unit 6 seeds (42, 7, 2024)**.

**How to check:** Inspect `accuracy` in each seed's evaluation result; correct predictions divided by the number of held-out posts. With 200 posts and a 15% test split, approximately 30 are tested, so this requires at least **21/30 correct** when there are exactly 30.

**Why this target:** We designed four mutually exclusive categories, and a naive most-common-label classifier would get only about 0.25 accuracy **if** the four labels were exactly balanced. A 0.70 threshold is a meaningful improvement over that illustrative baseline and would suggest the classifier learned something beyond a majority-class shortcut. It may be ambitious for roughly 140 training examples and subtle mixed-purpose posts.

**Challenge / caveat:** The real majority-class baseline depends on our actual label shares (it could be as high as 0.40 within our criterion 4 limit). On 30 test posts, one decision changes accuracy by ~0.033. Compare against the actual majority baseline and report variation across seeds; do not infer stable generalization from a single pass.

---

## 2. Held-out macro F1 is at least 0.60

**Acceptance target:** `f1_macro` **>= 0.60** for **each of the three Unit 6 seeds**.

**How to check:** Inspect `f1_macro` in each seed's result. Macro F1 is the arithmetic mean of F1 for our **four** classes, giving each equal weight independent of its frequency.

**Why this target:** r/LocalLLaMA includes direct experiments, assistance requests, speculation, and resource announcements, all of which matter to the product. Overall accuracy could look healthy while a rarer category receives poor predictions. A 0.60 macro F1 target pushes the model to learn across categories rather than only the most common one.

**Challenge / caveat:** Macro F1 averages classes and can still conceal one especially weak class, which is why criterion 3 separately checks the minimum. Estimates are noisy with such small class-specific test supports.

---

## 3. Every individual label has held-out F1 of at least 0.40

**Acceptance target:** Each of `technical_report`, `help_request`, `discussion`, and `resource_share` has F1 **>= 0.40** for **each of the three Unit 6 seeds**.

**How to check:** For every seed, inspect `per_label.<label>.f1` in the saved result for all four labels. Calculate F1 as the harmonic mean of precision and recall; the notebook records F1 with a zero convention when a denominator is undefined.

**Why this target:** A classifier that predicts one category well but ignores another is not useful as a four-way sorter. The lower 0.40 per-class floor reflects the particularly difficult boundaries in this taxonomy (especially reports that also ask for help) and the few held-out posts per class.

**Challenge / caveat:** At the lower bound of our class-balance target, a class with 30/200 examples contributes only approximately **4–5 test examples**; each mistake changes the score dramatically. An F1 of 0.40 is a minimum diagnostic floor, **not** evidence of production readiness or fairness.

---

## 4. Each label represents 15%–40% of the labeled dataset

**Acceptance target:** In the final **single, unsplit** `labels.csv`, each of the four labels accounts for **at least 15% and at most 40%** of the nonempty labeled rows; the dataset also targets **at least 200 genuine public posts** as required by the main project brief.

**How to check:** Count rows for each exact label string, divide by the total number of labeled posts, and check `0.15 <= count / total <= 0.40` for all four labels. At exactly 200 rows, each class must have **30–80 examples**. Record counts in README before splitting; remove exact duplicate posts to reduce leakage.

**Why this target:** These four functions of community posts may not naturally be equally common. Capping the largest at 40% (stricter than the course's 70% cap) and protecting a 15% floor ensures the learner has meaningful examples of reports, help requests, discussions, and resource shares.

**Challenge / caveat:** This is a **dataset construction** check, not a model-performance metric, and it is checked once rather than per seed. Oversampling rare classes changes the distribution relative to organic Reddit traffic; document sampling and never claim the balanced sample estimates natural prevalence. Balance alone cannot fix mislabeled posts or duplicate leakage.

---

## 5. Agreement with the staff-labeled taxonomy is at least 0.75

**Acceptance target:** On the **30 staff-provided posts in Unit 6**, personally assigned labels agree with the staff labels on **at least 75%** of posts — which requires at least **23/30** exact matches (76.7%) to clear the threshold.

**How to check:** First label the 30 posts *under the definitions in `data/staff_taxonomy.md`*, without seeing staff answers. Then use the `agreement.py` process once staff labels are available. Compute `number_of_exact_matches / 30`; preserve and adjudicate every disagreement.

**Why this target:** The hardest part of fine-tuning a niche classifier is reliably assigning meaning to subjective category boundaries. A 0.75 minimum demands that we can apply documented labeling decisions with reasonable consistency rather than constantly changing interpretations.

**Challenge / caveat:** This agreement test deliberately uses the **staff's taxonomy, not TakeMeter's four-label taxonomy**. It is a proxy for skill in following written rules, **not a measurement of annotation agreement on our own 200 posts**, nor proof of model accuracy. Thirty items provide limited precision; one disagreement moves the rate by 3.33 percentage points. Review each disagreement rather than relying on the percentage alone.

---

## Evaluation integrity / Unit 6 instructions

1. Keep these original numeric targets unchanged after seeing training outputs. If an unmeasurable criterion needs revision in Unit 6, append an explicitly marked explanation **without deleting the original**.
2. Criteria 1–3 apply to all three saved seeds, not just seed 42 or an average; criterion 4 is assessed on the full pre-split CSV; criterion 5 is assessed once from the staff exercise.
3. Record hardware (`mps` on the checked Apple Silicon machine), split sizes, label supports, and the seed-to-seed spread alongside metrics. Do not mix baseline and trained results from different test splits.
4. The model-training notebook computes accuracy and macro F1 and saves each class's F1 under `per_label`; the staff agreement procedure is separate.
5. Meeting a numeric target is not equivalent to a statistically precise or deployment-ready claim. These are learning-oriented, falsifiable standards set before training.
