# TakeMeter — Milestone 1: Community Exploration

**Date:** October 18, 2026  
**Community:** [r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) — public subreddit about running and developing local language models  
**Status:** Exploratory observations, not a finalized taxonomy and not training annotations.

## What I did and why

I inspected **38 distinct public posts**: **24** in the community's recent-post feed and **14** additional posts from its top-this-week feed. I reviewed the visible post text where available, and identified cases where the post was predominantly an image or an external link. This is a purposive convenience sample, not a random or prevalence-representative sample. The browsing captures are snapshots, and some post descriptions may change over time.

The goal was to identify **observable differences in the actual community**, rather than inventing labels such as "good" and "bad" before reading anything. Each entry below is a short original description of the post's role in the discussion, not a copy of the post. The patterns are **exploratory tags only**. They must not be imported as gold labels for training.

## Three primary distinctions observed

1. **Evidence-backed reports versus speculation/opinion.** Some posts state configurations, measurements, benchmark procedures, or comparisons (e.g. #16 and #17). Others predict model behavior, give subjective takes, or propose ideas without a comparable experiment (#1, #9, #29). A number mentioned in an anecdote does not by itself establish strong analysis.
2. **Sharing findings versus seeking assistance.** Hardware-purchasing questions and configuration requests are primarily advice-seeking (#3, #12). Posts such as #10 report real measured outcomes but also ask for optimization ideas; the eventual taxonomy needs an explicit main-purpose decision rule.
3. **Firsthand investigations versus relayed information.** Some authors report what they themselves ran (#16, #23). Others announce a release, link model weights, relay third-party results, or summarize external reporting (#27, #28, #30, #37). These are useful posts, but their evidence provenance differs.

## A fourth pattern that may require its own label

**Announcements, tutorials, and resource sharing** occur regularly: new model releases (#4, #26), link-only releases (#11, #37), and detailed how-to guides (#32). Forcing these into either "technical report" or "opinion" would introduce annotation noise. We should decide whether to create a separate content-purpose label or define an explicit priority rule after inspecting representative full-text examples.

## Hard boundary cases to carry into Milestone 2

- **#10, report vs request:** The mixed-GPU build supplies a configuration and throughput; the last lines ask for split-ratio advice. Proposed stress test: would the post still substantially inform readers if the request were deleted?
- **#4 and #17, report vs announcement:** A new model/engine launch can include extensive test tables. Is its central intent to introduce a release, or report experimental comparisons?
- **#31, empirical evaluation vs subjective opinion:** This model ranking lists criteria and personal trials, but judgments are partly subjective and may not be independently reproducible.
- **#32, guide vs report:** A tutorial has technical substance but is primarily instructional, not a controlled experiment.
- **#13, investigation vs unsupported allegation:** The author gives evidence and caveats for allegations. Any category should describe **what evidence the post presents**, not certify that the allegations are true.

## Important collection and modeling cautions

- **These 38 rows are not the 200 labeled training examples.** Milestone 4 needs a single CSV containing whole post text, a final label, and a note; the first 20 must be labeled by the student unaided ('cold').
- **Image-only and link-only posts are a problem for a text classifier.** Entries marked `[image-led]` or `[link-led]` must be revisited: a headline alone usually does not represent the substantive content. Prefer complete textual submissions for the future dataset; do not invent or reconstruct missing text.
- **Subreddit flair is not a gold label.** A post flaired 'Question | Help' may report a benchmark; a post flaired 'New Model' may contain detailed evaluation. Classify from the defined post text and a written rule, not the flair.
- **Do not assert that user-reported benchmark numbers or linked headlines have been independently verified.** This exercise categorizes rhetorical/communicative roles, not factual truth.
- **Class proportions from this sample do not estimate true subreddit proportions.** Recent and top posts are affected by submission timing and popularity. For Milestone 4, track counts by final label, ensure no label exceeds 70%, and record any deliberate oversampling of rare classes.
- **Keep duplicate/cross-post text out of multiple splits.** The notebook creates a stratified 70/15/15 split after labeling. Do not manually pre-split the data.
- **Acceptance criteria are written by the student before seeing training metrics.** This exploration can inform the difficulty and target definitions, but it does not supply those five criteria.

## Source review log (38 posts)

Each linked item has a tentative *observable pattern* and a short reason. Patterns are not final class labels.

**1. [architecture](https://www.reddit.com/r/LocalLLaMA/comments/1x8zshy/architecture/)** — *discussion.* Short, speculative idea about architecture; few specifics to verify.

**2. [New quant types suggested: IQ2_K, IQ3_K, IQ4_K, IQ5_K and IQ6_K](https://www.reddit.com/r/LocalLLaMA/comments/1x8zj9j/new_quant_types_suggested_iq2_k_iq3_k_iq4_k_iq5_k/)** — *announcement + discussion.* Links to an upstream proposal and summarizes its measurements; sourced information is not necessarily firsthand testing.

**3. [Buying Strix Halo right now?](https://www.reddit.com/r/LocalLLaMA/comments/1x8za17/buying_strix_halo_right_now/)** — *request.* Asks whether a specific used 128 GB system is worth its asking price.

**4. [Agens Volundr 32B v1: we fixed what you flagged in the Preview](https://www.reddit.com/r/LocalLLaMA/comments/1x8yc8d/agens_volundr_32b_v1_we_fixed_what_you_flagged_in/)** — *announcement + report.* Team announces release while supplying detailed benchmark comparisons and caveats.

**5. [told Qwen3.8 27b to hack my router](https://www.reddit.com/r/LocalLLaMA/comments/1x8wmbp/told_qwen38_27b_to_hack_my_router/)** — *discussion + experience.* Firsthand anecdote about changing router firmware followed by a prediction/question about future models; anecdote is not a controlled benchmark.

**6. [Made sum crap that beats Jev](https://www.reddit.com/r/LocalLLaMA/comments/1x8vl4i/made_sum_crap_that_beats_jev/)** — *announcement + request.* Shares a demo and specifically invites feedback; ambiguous release/help boundary.

**7. [We all joke about our rigs being space heaters, so I had Qwen vibecode it](https://www.reddit.com/r/LocalLLaMA/comments/1x8v97a/we_all_joke_about_our_rigs_being_space_heaters_so/)** — *report + showcase.* Documents a functioning hobby project and links a repository; humorous framing does not erase technical content.

**8. [Ling 3.1 Flash (560B MoE) loaded across 4 DGX Sparks using llama.cpp RPC](https://www.reddit.com/r/LocalLLaMA/comments/1x8v7cp/ling_31_flash_560b_moe_loaded_across_4_dgx_sparks/)** — *showcase [image-led].* Hardware/model setup is visible in heading; much of evidence is image-based, so review carefully for a text-only dataset.

**9. [What are the odds Qwen 4 models are going to think less?](https://www.reddit.com/r/LocalLLaMA/comments/1x8uqig/what_are_the_odds_qwen_4_models_are_going_to/)** — *discussion.* Uses firsthand speed anecdote to motivate speculation about unreleased models.

**10. [My 5070 ti/3070 Chimera build.](https://www.reddit.com/r/LocalLLaMA/comments/1x8u6eg/my_5070_ti3070_chimera_build/)** — *report + request.* Reports GPU split, configuration and throughput; ends by soliciting advice on split ratios. Hard boundary case.

**11. [DeepSeek v4.1 Flash 1017 for Dwarfstar (ds4)](https://www.reddit.com/r/LocalLLaMA/comments/1x8tr2c/deepseek_v41_flash_1017_for_dwarfstar_ds4/)** — *announcement [link-led].* Model/quant link with minimal authored post text. May not be suitable for supervised text classification.

**12. [3xrtx8000 48gb... what to do?](https://www.reddit.com/r/LocalLLaMA/comments/1x8st56/3xrtx8000_48gb_what_to_do/)** — *request.* Lists hardware and asks how best to use three GPUs.

**13. [AutoTrust's HF models are trending thanks to thousands of farmed likes](https://www.reddit.com/r/LocalLLaMA/comments/1x8sq4z/autotrusts_hf_models_are_trending_thanks_to/)** — *investigative report.* Author presents cross-account observations supporting an allegation, explicitly noting limits in identifying responsibility; distinguish allegations from verified facts.

**14. [You don’t need that expensive of a build for local llms.](https://www.reddit.com/r/LocalLLaMA/comments/1x8s73i/you_dont_need_that_expensive_of_a_build_for_local/)** — *report + opinion.* Shows a less-expensive configuration and reported token speeds. Despite forum flair, primary text shares results.

**15. [Muse Spark on M3U 256 GB](https://www.reddit.com/r/LocalLLaMA/comments/1x8qvaj/muse_spark_on_m3u_256_gb/)** — *showcase [image-led].* Setup demonstration with little machine-readable post text.

**16. [Nine models, five coding tasks, one 16GB GPU](https://www.reddit.com/r/LocalLLaMA/comments/1x8qlvw/nine_models_five_coding_tasks_one_16gb_gpu/)** — *experiment.* Detailed multi-model comparison with held-out grading procedure, test definitions, and measured results.

**17. [DeepSeek V4.1 Flash 1017 on 2x DGX Spark: 57 tok/s text, 92 tok/s code with TensorFold](https://www.reddit.com/r/LocalLLaMA/comments/1x8q6t6/deepseek_v41_flash_1017_on_2x_dgx_spark_57_toks/)** — *experiment + release.* Benchmark of runtime engine against another configuration; also links released artifacts.

**18. [Follow-up: Tested my 9 thinking rules on long-horizon agent tasks (Terminal-Bench 2.0)](https://www.reddit.com/r/LocalLLaMA/comments/1x8q308/followup_tested_my_9_thinking_rules_on/)** — *experiment [image-led].* Testing-oriented heading but evidence is primarily image-based in the listing; inspect full usable text before inclusion.

**19. [Basalt: NVFP4 + faster prefill for Qwen3.8 Flash-Next on Blackwell](https://www.reddit.com/r/LocalLLaMA/comments/1x8piwz/basalt_nvfp4_faster_prefill_for_qwen38_flashnext/)** — *release + experiment.* New feature release with quality and throughput comparisons.

**20. [DeepSeek V4.1 Flash 1017 vs V4.1 Flash, Pi vs DeepSeek Harness](https://www.reddit.com/r/LocalLLaMA/comments/1x8mq6f/deepseek_v41_flash_1017_vs_v41_flash_pi_vs/)** — *benchmark [link-led].* Benchmark results are claimed in heading and external link; check authored body before training.

**21. [Alignment on SOTA Chinese Models like Qwen 3.8 Flash Next / GLM 5.3 Flash](https://www.reddit.com/r/LocalLLaMA/comments/1x8meib/alignment_on_sota_chinese_models_like_qwen_38/)** — *discussion + request.* Opinion, experience, and open-ended question about alignment; not a repeatable experimental report.

**22. [Qwen Flash Next on Mac Mini is runnable without maxing out your memory](https://www.reddit.com/r/LocalLLaMA/comments/1x8m9rg/qwen_flash_next_on_mac_mini_is_runnable_without/)** — *showcase [image-led].* Claims streaming memory-use findings, with results primarily in images.

**23. [Xolotl (Strata based) - DeepSeek-V4.1-Flash (552B) on a single 4090](https://www.reddit.com/r/LocalLLaMA/comments/1x8m0jj/xolotl_strata_based_deepseekv41flash_552b_on_a/)** — *release + experiment.* New inference engine, implementation description, and author-reported speeds and checks.

**24. [if you're on Strata before 0.1.45 and your client doesn't set sampling, you're running greedy](https://www.reddit.com/r/LocalLLaMA/comments/1x8lwa1/if_youre_on_strata_before_0145_and_your_client/)** — *technical report + advice.* Diagnoses a setting, compares configurations and advises users; informative despite instructional tone.

**25. [Linux creator says anti-AI rules are idiotic (Absolute god-tier take)](https://www.reddit.com/r/LocalLLaMA/comments/1x8e4wd/linux_creator_says_antiai_rules_are_idiotic/)** — *reaction [image-led].* Framed as strong agreement with quoted opinion; original post is image-led.

**26. [Introducing Muse Spark Open: the most capable US open-weight model to date](https://www.reddit.com/r/LocalLLaMA/comments/1x6r9pz/introducing_muse_spark_open_the_most_capable_us/)** — *announcement [image-led].* New model announcement; performance slogan in heading is not proof of firsthand experimentation.

**27. [Someone is running Qwen 27B at ~20 tok/s on a jailbroken PS5's GPU](https://www.reddit.com/r/LocalLLaMA/comments/1x5ak2n/someone_is_running_qwen_27b_at_20_toks_on_a/)** — *news/repost [link-led].* Shares someone else's reported technical achievement; avoid confusing a repost with the author's own experiment.

**28. [deepseek-ai/DeepSeek-V4.1-Flash-1017 · Hugging Face](https://www.reddit.com/r/LocalLLaMA/comments/1x84po4/deepseekaideepseekv41flash1017_hugging_face/)** — *announcement [link-led].* Links official model page; title alone provides little training text.

**29. [Anyone feel like reverse-engineering CUDA?](https://www.reddit.com/r/LocalLLaMA/comments/1x4n6sg/anyone_feel_like_reverseengineering_cuda/)** — *discussion + proposal.* Makes an aspirational suggestion and invites community participation without tests.

**30. [China proposes export controls on 23 AI technologies](https://www.reddit.com/r/LocalLLaMA/comments/1x7g3zq/china_proposes_export_controls_on_23_ai/)** — *news + explanation.* Summarizes an outside policy proposal with a source. Treat claims as attributed, not independently verified in this exploration.

**31. [Every Model That Can Be Run On 10-16GB VRAM Ranked](https://www.reddit.com/r/LocalLLaMA/comments/1x3gpyi/every_model_that_can_be_run_on_1016gb_vram_ranked/)** — *review + experience.* Subjective ranking with stated evaluation dimensions and personal trials; hard boundary with evidence-backed analysis.

**32. [10 Things you maybe didn't know you can do with Qwen 3.6 27B right now](https://www.reddit.com/r/LocalLLaMA/comments/1x7sq8e/10_things_you_maybe_didnt_know_you_can_do_with/)** — *tutorial / resource.* Long how-to/advice article based on experience; neither a help request nor a controlled benchmark.

**33. [NVIDIA Nemotron Bolt 3.5 74B A9B releases Oct. 15th](https://www.reddit.com/r/LocalLLaMA/comments/1x5t1tm/nvidia_nemotron_bolt_35_74b_a9b_releases_oct_15th/)** — *announcement [link-led].* Shares a release reference rather than independent measurements.

**34. [DeepSeek V4.1 Flash (1017) Now Leads Open-Weight Models](https://www.reddit.com/r/LocalLLaMA/comments/1x8bb6b/deepseek_v41_flash_1017_now_leads_openweight/)** — *reaction/ranking [image-led].* Leaderboard-oriented claim; supporting evidence is image-led in the post.

**35. [New AI fake text generator may be too dangerous to release (2019 Guardian headline)](https://www.reddit.com/r/LocalLLaMA/comments/1x52lsb/new_ai_fake_text_generator_may_be_too_dangerous/)** — *reaction + commentary.* Shares an old article to make an ironic observation; original commentary rather than technical experiment.

**36. [Here’s why RTX 5090 costs $5,000: AI firms are buying gaming GPUs by the pallet](https://www.reddit.com/r/LocalLLaMA/comments/1x37tg6/heres_why_rtx_5090_costs_5000_ai_firms_are_buying/)** — *news/repost [link-led].* Links outside reporting; don't treat headline claims as verified measurements.

**37. [LiquidAI/LFM2.5-24B-A2B](https://www.reddit.com/r/LocalLLaMA/comments/1x52kco/liquidailfm2524ba2b/)** — *announcement [link-led].* Model repository link with little authored text.

**38. [Decision 3.0: open, multimodal decision models from 0.6B to 27B](https://www.reddit.com/r/LocalLLaMA/comments/1x3th4p/decision_30_open_multimodal_decision_models_from/)** — *announcement [image-led].* Release/performance claim that would need text evidence before labeling.

## End-of-Milestone 1 conclusions

The community supplies enough variety for TakeMeter. **The hardest provisional boundary is a post that documents a setup and asks for help.** Other boundary cases include evidence-rich release announcements and subjective rankings with self-reported experiments. The best label design will distinguish **primary communicative purpose** from secondary technical characteristics and will give a one-sentence rule for mixed-purpose posts.

**Next:** Milestone 2 — choose 2–4 mutually exclusive labels, define each in one sentence, find two actual full-text examples for each, write the primary-purpose tie-break rule, and challenge it with eight synthetic borderline posts. No training yet.
