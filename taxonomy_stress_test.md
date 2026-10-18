# TakeMeter — Milestone 2 taxonomy stress test

**Purpose:** Use deliberately ambiguous **synthetic examples**, not training observations, to test whether the four-label rules in README.md resolve common boundaries. These were generated with AI to challenge the taxonomy. No synthetic posts should be copied into `labels.csv` as real community submissions.

| # | Synthetic borderline post | Competing labels | Proposed label | Rule applied |
|---|---|---|---|---|
| 1 | "Ran Qwen3 on two GPUs: here are my exact settings, 48 tok/s, memory use, and logs. Is there a faster split?" | `technical_report` / `help_request` | `technical_report` | Completed, informative real run outweighs closing request. |
| 2 | "I bought two 3090s and only get 4 tok/s. Any ideas? I haven't tested configs." | `help_request` / `technical_report` | `help_request` | Numbers are symptoms supporting an unresolved help request. |
| 3 | "Launching FastMoE v2 today. Here's the repo, install steps, and our benchmark versus v1." | `resource_share` / `technical_report` | `resource_share` | Introducing newly available artifact is primary goal. |
| 4 | "Benchmarked two already-released models on 50 prompts, including metrics and failure examples." | `technical_report` / `resource_share` | `technical_report` | Main contribution is original comparative experiment, not new resource. |
| 5 | "Could future Qwen models skip thinking tokens? Mine feels sluggish right now." | `discussion` / `help_request` | `discussion` | Invites speculation, not specific actionable support. |
| 6 | "Which inference backend should I install for my 48 GB workstation? My goal is highest context length." | `help_request` / `discussion` | `help_request` | Specific personal usage recommendation requested. |
| 7 | "Here are ten ways to configure KV caching, with commands and explanations from my experience." | `resource_share` / `technical_report` | `resource_share` | Main purpose is teaching a procedure, not reporting a discrete result. |
| 8 | "This benchmark ranking looks misleading because the prompts favor one architecture; here's my interpretation of the chart." | `discussion` / `technical_report` | `discussion` | Interpretation of external evidence without a completed firsthand experiment. |

## Findings and limits

All eight synthetic posts can be classified with the written precedence rules. This checks internal *resolvability*, **not inter-annotator agreement**, **not classification accuracy**, and **not whether the sample of four labels is well-balanced**. The next test should involve real posts, independent annotation, and logging any disagreements. If real examples cannot be classified consistently, revise the rules and document why **before training**, instead of changing labels to optimize measured test-set scores.

### Two particularly challenging boundaries

- `technical_report` vs `help_request`: both contain measurements. The key question is whether a substantive completed result exists independently of a request for help.
- `resource_share` vs `technical_report`: announcements often have benchmarks. Label by whether the primary contribution is delivering an artifact/tutorial or reporting original experimental findings.

**Milestone 3 reminder:** The project's five acceptance criteria must be authored by the student and committed **before** inspecting training results. This document does not choose criteria or metric thresholds.
