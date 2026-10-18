# Supplemental report boundary cases

All 15 cases originated as AI suggestions; current human-review provenance is recorded per case and in the audit. Each full title/body, source URL and hash is in supplemental_proposals.csv. Raw source evidence is preserved independently. No competing label was resolved merely to reach a count.

## Queue row 321: I ran quantized Falcon-180B Q4 on a home/consumer computer and it is not good (maybe need help?)

Source: [16i15qc](https://www.reddit.com/r/LocalLLaMA/comments/16i15qc/i_ran_quantized_falcon180b_q4_on_a_homeconsumer/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed consumer-hardware Falcon-180B run specifies model quantization, loader, GPU layers and 0.3 tokens/s; closing quality troubleshooting does not erase the useful capacity/speed result.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 322: HF transformers vs llama 2 example script performance

Source: [16hzpv4](https://www.reddit.com/r/LocalLLaMA/comments/16hzpv4/hf_transformers_vs_llama_2_example_script/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed backend comparison supplies model, hardware, generation code/command and measured 132-versus-60-second runtimes; optimization request follows a substantive result.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 323: Some Lessons Learned from Building a Fine Tuned Model + RAG Question Answering App

Source: [1686ul6](https://www.reddit.com/r/LocalLLaMA/comments/1686ul6/some_lessons_learned_from_building_a_fine_tuned/)

Proposed: `technical_report`; competing interpretation: `resource_share`.

Reports a deployed RAG system, training corpus and controlled same-document model comparison with full textual outputs; lessons are findings from completed work rather than an installation guide.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 324: New Model RP Comparison/Test (7 models tested)

Source: [15ogc60](https://www.reddit.com/r/LocalLLaMA/comments/15ogc60/new_model_rp_comparisontest_7_models_tested/)

Proposed: `technical_report`; competing interpretation: `resource_share`.

Reports seven existing models tested using a shared roleplay procedure, backend, quantization and context with model-specific observations and ratings.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 325: What I've learned from orca-mini-3b.ggmlv3.q4_1 using LLamaCPP (_python), so far.

Source: [15g5419](https://www.reddit.com/r/LocalLLaMA/comments/15g5419/what_ive_learned_from_orcamini3bggmlv3q4_1_using/)

Proposed: `technical_report`; competing interpretation: `discussion`.

Reports completed orca-mini testing with exact quantization, backend, GPU offloading and throughput plus detailed observed prompt/context behavior.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 326: 70b q3_K_S at 1.4 t/s 32gb cpu ram showcase

Source: [15794m2](https://www.reddit.com/r/LocalLLaMA/comments/15794m2/70b_q3_k_s_at_14_ts_32gb_cpu_ram_showcase/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed 70B quantization comparison states RAM, OS, context load and 1.4-versus-0.2 tokens/s outcomes; memory-extension question is secondary.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 327: The Choice of a Particular Generation Parameters Preset Can Make or Break a Model!

Source: [14kip27](https://www.reddit.com/r/LocalLLaMA/comments/14kip27/the_choice_of_a_particular_generation_parameters/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed Nous-Hermes experiment identifies two presets and a reversible math-performance change; linked chart is supplementary to the textual finding.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 328: Compare TheBloke_WizardLM-13B-V1.0-Uncensored-GPTQ with TheBloke_WizardLM-13B-V1-0-Uncensored-SuperHOT-8K-GPTQ

Source: [14kfsi8](https://www.reddit.com/r/LocalLLaMA/comments/14kfsi8/compare_thebloke_wizardlm13bv10uncensoredgptq/)

Proposed: `technical_report`; competing interpretation: `resource_share`.

Completed long-context comparison specifies both models, rotary compression and sequence length, gives full textual outputs and interprets the difference.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 329: llama.cpp and thread count optimization [Revisited]

Source: [14jk108](https://www.reddit.com/r/LocalLLaMA/comments/14jk108/llamacpp_and_thread_count_optimization_revisited/)

Proposed: `technical_report`; competing interpretation: `resource_share`.

Completed thread-count investigation specifies a six-core CPU, RAM, interference controls and the best-performing thread count in text; chart is supplementary.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 330: When did this happen? re: Oobabooga, AtuoGPTQ vs GPTQ-for-Llama

Source: [14iz0p9](https://www.reddit.com/r/LocalLLaMA/comments/14iz0p9/when_did_this_happen_re_oobabooga_atuogptq_vs/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed same-model loader comparisons report GPU/RAM, quantization and 2-versus-13/14-versus-19/20 tokens/s; curiosity about the change is secondary.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 331: Bigger isn't always better: Smaller LLMs and quants can deliver better outputs

Source: [14iw25d](https://www.reddit.com/r/LocalLLaMA/comments/14iw25d/bigger_isnt_always_better_smaller_llms_and_quants/)

Proposed: `technical_report`; competing interpretation: `discussion`.

Completed model/quant comparisons name tested artifacts, procedure and qualitative winners, and explicitly discuss a discovered sampling confound.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 332: PSA: New Nvidia driver 536.23 still bad, don't waste your time

Source: [1498gdr](https://www.reddit.com/r/LocalLLaMA/comments/1498gdr/psa_new_nvidia_driver_53623_still_bad_dont_waste/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Reports a completed driver-version comparison with exact GPU, OS, loader and high-VRAM test condition, finding the new driver still slower.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 333: Local models on laptops: AMD 6900HS/32GB/Nvidia 3050TI 4GB vs. Apple M2/24GB vs.

Source: [1493fes](https://www.reddit.com/r/LocalLLaMA/comments/1493fes/local_models_on_laptops_amd_6900hs32gbnvidia/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed two-laptop comparison specifies exact model, backends, offloaded layers, commands and measured timings; later results supersede the original buying question.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 334: British/American spelling of one word changes the output on the same seed.

Source: [148df70](https://www.reddit.com/r/LocalLLaMA/comments/148df70/britishamerican_spelling_of_one_word_changes_the/)

Proposed: `technical_report`; competing interpretation: `discussion`.

Completed controlled spelling test fixes model, backend and seed and states both prompts and observed output change.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.

## Queue row 335: My results using a Tesla P40

Source: [13n8bqh](https://www.reddit.com/r/LocalLLaMA/comments/13n8bqh/my_results_using_a_tesla_p40/)

Proposed: `technical_report`; competing interpretation: `help_request`.

Completed P40 deployment comparison reports host configurations, driver conditions, models and numerical throughput outcomes.

Review status: approved by offline batch attestation `offline-dd35e6add7ac2f1144f5553a61c46b099b15219db9713ce6bd9e93890b371ef8`; no individual review time recorded.
