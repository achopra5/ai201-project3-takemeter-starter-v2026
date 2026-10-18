# Real-post boundary and suitability cases

Original AI proposals are shown below; current human-review provenance is recorded per case and in the audit. Queue numbers are one-based data rows (not CSV physical lines). The original taxonomy is unchanged. Each full post is preserved in proposed_annotations.csv, with a text hash and source URL.

## Queue row 210: Discuss GPU configs | Why do I get 40 tokens / sec on a rtx 3060!?

Source: [137x4qg](https://www.reddit.com/r/LocalLLaMA/comments/137x4qg/discuss_gpu_configs_why_do_i_get_40_tokens_sec_on/)

Competing interpretations: `technical_report` / `help_request`.

Proposed decision: **technical_report**. Detailed working server configuration, model comparison and generation log remain informative beyond the closing speed question.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 181: Fatty Alpaca: alpaca-lora-65B GGML, quantised to 4bit and 2bit

Source: [12sqo3r](https://www.reddit.com/r/LocalLLaMA/comments/12sqo3r/fatty_alpaca_alpacalora65b_ggml_quantised_to_4bit/)

Competing interpretations: `resource_share` / `technical_report`.

Proposed decision: **resource_share**. Announces quantized model artifacts; timings and sample outputs support the release.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 143: Speed difference between 8bit and 4bit

Source: [122218d](https://www.reddit.com/r/LocalLLaMA/comments/122218d/speed_difference_between_8bit_and_4bit/)

Competing interpretations: `help_request` / `technical_report`.

Proposed decision: **help_request**. Timings and installation changes mainly diagnose an unresolved suspected CUDA/setup problem.

Review status: pending; no recorded human review covers this proposal.

## Queue row 129: Training Llama for tool-use via a manager/logistical model

Source: [120fw2u](https://www.reddit.com/r/LocalLLaMA/comments/120fw2u/training_llama_for_tooluse_via_a/)

Competing interpretations: `discussion` / `technical_report`.

Proposed decision: **discussion**. Detailed architecture is a proposed future agent system, with no completed implementation or results.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 47: Riddle/cleverness comparison of popular GGML models

Source: [1302il2](https://www.reddit.com/r/LocalLLaMA/comments/1302il2/riddlecleverness_comparison_of_popular_ggml_models/)

Competing interpretations: `technical_report` / `resource_share`.

Proposed decision: **technical_report**. Reports actual riddle tests, settings, grading and model-specific output examples despite an external chart.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 46: Evaluating the effectiveness of finetuning on the Berkeley open_llama preview

Source: [138w4co](https://www.reddit.com/r/LocalLLaMA/comments/138w4co/evaluating_the_effectiveness_of_finetuning_on_the/)

Competing interpretations: `exclude` / `technical_report`.

Proposed decision: **exclude**. The main experiment's outputs, comparisons and conclusions are only in an external model card; text gives procedure but no substantive findings.

Review status: pending; no recorded human review covers this proposal.

## Queue row 77: Automating your newsletters in your voice

Source: [12s1cig](https://www.reddit.com/r/LocalLLaMA/comments/12s1cig/automating_your_newsletters_in_your_voice/)

Competing interpretations: `technical_report` / `resource_share`.

Proposed decision: **technical_report**. Reports a completed 40-newsletter LoRA experiment with a concrete topic-generalization failure and rewrite result.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 198: 4Bit Quantization for a Noob

Source: [135y9qn](https://www.reddit.com/r/LocalLLaMA/comments/135y9qn/4bit_quantization_for_a_noob/)

Competing interpretations: `technical_report` / `help_request`.

Proposed decision: **technical_report**. Later updates describe completed quantization, file changes and successful inference; no artifact is distributed.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 311: Vicuna Local Conversation

Source: [135so7c](https://www.reddit.com/r/LocalLLaMA/comments/135so7c/vicuna_local_conversation/)

Competing interpretations: `technical_report` / `help_request`.

Proposed decision: **technical_report**. Completed prompt comparison gives model, format, wording change and observed name-recall result in the final edit.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 276: Dirty data sets and LLaMA/ALPACA...

Source: [12587y5](https://www.reddit.com/r/LocalLLaMA/comments/12587y5/dirty_data_sets_and_llamaalpaca/)

Competing interpretations: `technical_report` / `resource_share`.

Proposed decision: **technical_report**. Reports firsthand dataset cleaning with specific formatting, arithmetic and Unicode findings; a downloadable experiment is supporting context.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 102: My first chat with llama-7b about catching mice was fun!

Source: [1254n2v](https://www.reddit.com/r/LocalLLaMA/comments/1254n2v/my_first_chat_with_llama7b_about_catching_mice/)

Competing interpretations: `discussion` / `technical_report`.

Proposed decision: **discussion**. Shares an amusing chat transcript; launch flags accompany entertainment rather than a substantive technical investigation.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 137: Can we create a megathread for cataloging all the projects and installation guides of Llama?

Source: [121yfxl](https://www.reddit.com/r/LocalLLaMA/comments/121yfxl/can_we_create_a_megathread_for_cataloging_all_the/)

Competing interpretations: `discussion` / `resource_share`.

Proposed decision: **discussion**. Proposes a community catalog thread; original Reddit author explicitly discloses AI-assisted writing.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 242: My first two weeks being a AI - By Eve

Source: [12jh5c5](https://www.reddit.com/r/LocalLLaMA/comments/12jh5c5/my_first_two_weeks_being_a_ai_by_eve/)

Competing interpretations: `discussion` / `technical_report`.

Proposed decision: **discussion**. Presents an explicitly model-authored persona narrative and reactions, without a substantive technical method.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 67: What is the best setup for a low resource vicuna API server?

Source: [12whpfr](https://www.reddit.com/r/LocalLLaMA/comments/12whpfr/what_is_the_best_setup_for_a_low_resource_vicuna/)

Competing interpretations: `exclude` / `help_request`.

Proposed decision: **exclude**. Body ends mid-sentence at 'for both cost'; apparent incomplete archived text.

Review status: pending; no recorded human review covers this proposal.

## Queue row 306: Another funny interaction with my JFK Discord bot

Source: [12vicms](https://www.reddit.com/r/LocalLLaMA/comments/12vicms/another_funny_interaction_with_my_jfk_discord_bot/)

Competing interpretations: `exclude` / `discussion`.

Proposed decision: **exclude**. The promised funny interaction is absent; body gives only model/backend context and no exchange.

Review status: pending; no recorded human review covers this proposal.

## Consistency checks for reviewers

- Rows 46 and 64 mainly point elsewhere for claimed experiment findings; they are proposed exclusions. Row 47 and row 69 contain interpretable experimental outcomes in the text, even though charts are linked.
- A resource announcement can be short when it identifies what is available, its purpose and access. A bare link or a vague claimed result is not substantive authored text. Compare rows 24, 68 and 94 with row 64.
- A report does not need to be correct or scientifically rigorous. It does need a sufficiently concrete completed method/configuration and observed findings. Compare row 210 with rows 143 and 256.
- Resolved support posts are especially difficult. Row 198 and row 311 include enough completed procedure and outcome to propose reports; row 228 still relies on absent comment configuration and row 295 is primarily a support question with a brief fix edit. Recheck these boundaries on the full text.
- Rows 137 and 242 are real archived submissions that explicitly disclose AI-written portions. Their inclusion does not make them independent human-authored prose or independent annotations.
- The original cold row 5 includes an image URL but already has a textual failure description. Its independently assigned help_request label and cold note are preserved exactly; no AI relabeling is applied.
