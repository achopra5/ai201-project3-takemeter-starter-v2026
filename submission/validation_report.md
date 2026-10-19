# Unit 5 submission validation

**READY for Unit 5 submission.** This does not mean the model meets its performance targets.

Checked UTC: 2026-10-19T00:21:07.794465+00:00. Existing evidence only: no training, collection, search or model inference.

- Frozen evidence: 72 file hashes pass, including original data, annotations, acceptance criteria, original experiments and completed final results.
- Dataset: 200 unique full-text archived posts;36 technical reports,58 help requests,51 discussions,55 resources. All four shares satisfy15–40%. No missing text or invalid labels. Export matches recorded reviews.
- Provenance:20 independent cold annotations unchanged;180 AI suggestions covered by one explicit offline attestation; zero individual CLI reviews. Three original exclusions unchanged;132 parked AI proposals remain unreviewed.
- Experiment:9 completed fits,513 optimizer updates; frozen splits and saved metric/confusion/prediction consistency pass. No new test evaluation occurred during closeout.
- Checkpoints: 21 locally present weights verified; 0 absent locally. Weights stay outside Git; manifests are committed.
- Documentation: 13 files and 56 local links checked; README tables have consistent columns, no empty required cells/placeholders and valid Python entry points.

## Original criteria

- Criterion 1: **FAIL**, for both original and improved results.
- Criterion 2: **FAIL**, for both original and improved results.
- Criterion 3: **FAIL**, for both original and improved results.
- Criterion 4: **PASS**, for both original and improved results.
- Criterion 5: **NOT EVALUATED**, for both original and improved results.

Original and improved test means are respectively accuracy0.433333/0.500000 and macro F1 0.297680/0.389639. Improved technical-report F1 remains zero in every seed. The follow-up is exploratory because original test aggregates were known before intervention design.

## Other quality checks

The closeout also runs `python test.py`, `python -m unittest discover -s tests -v`, `git diff --check` and `git status --short`. The final command outcomes are recorded in [quality_checks.json](quality_checks.json). This integrity checker does not itself invoke those commands.

## Remaining work

Zero-shot baseline and personal/staff-taxonomy agreement are Unit 6 work and remain explicitly pending. They are not fabricated or required to finish this Unit 5 write-up. No unresolved Unit 5 repository-content blocker was found.

Submit https://github.com/achopra5/ai201-project3-takemeter-starter-v2026 as the repository URL in the Unit 5 course assignment. Git push does not submit the course portal form.
