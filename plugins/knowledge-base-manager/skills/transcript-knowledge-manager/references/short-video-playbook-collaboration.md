# Short Video Playbook Collaboration

Use this reference when the user asks to save, deposit, organize, retrieve, or reuse outputs from `$short-video-ops-playbook`, including 7-day playbooks, account review upgrades, goal-matrix outputs, topic/copy scoring, scripts, storyboards, conversion handoff, and review decisions.

## Boundary

- `short-video-ops-playbook` owns live strategy, research synthesis, goal matrix, topic scoring, copy scoring, playbook writing, and review decision trees.
- `transcript-knowledge-manager` owns durable knowledge-base hygiene: ingestion, card splitting, directory-role mapping, source profiles, indexes, confidence/maturity fields, and confirmed Obsidian write-in.

Do not rewrite the full operations plan inside this skill. Accept the playbook's structured deposit block as an input artifact, then organize it into durable knowledge assets.

## Accepted Deposit Inputs

The playbook skill may hand off:

- Run mode: quick, standard, or deep.
- Final playbook title and brief.
- Compressed evidence pack with evidence IDs, source layers, confidence, decision impact, and reuse boundaries.
- Operating decision card: stage, bottleneck, goals, weekly validation question, content ratio, traffic type, CTA pressure, and rejudgment trigger.
- Source map: user input, private KB, public KB, web/public sources, model common knowledge.
- Industry insight card.
- Account-stage judgment card.
- Goal matrix card: primary/secondary goal, 7-content ratio, correction note.
- High-scoring topic/hook/script cards.
- Video work-order cards: goal, account stage, format, hook, proof asset, CTA, experiment, metric, review decision, and deposit reason.
- Representative rejected topics/copy and rejection reasons.
- Operator bottleneck diagnosis and main operating bet.
- A/B/C topic grades, B-to-A rewrites, and C-grade rejection lessons.
- Strong hook patterns, strong copy structures, and editorial review results.
- Spread mechanisms and conversion journey stages that worked or should be tested.
- Day-7 review metrics and next-round hypotheses.
- Sensitive/private-source boundaries.

## Asset Mapping

Map playbook deposits to local directory roles rather than fixed directory names:

| Deposit type | Role |
|---|---|
| Full playbook | output artifact |
| Topic, hook, script, CTA, RACI, shooting checklist | execution/content asset |
| Video work order, storyboard, production blocker, experiment card | execution/content asset or review/iteration asset |
| Goal matrix, operator bottleneck diagnosis, industry insight, review model, rejected-pattern lesson | knowledge/reasoning asset |
| Account stage, competitor account, source profile | source/profile asset |
| Day-7 data and next hypothesis | review/iteration asset |
| A-grade topic/hook/script sample | execution/content asset with reuse constraints |
| B-to-A rewrite pattern or C-grade rejection reason | knowledge/reasoning asset |

If the current knowledge base has the short-video/IP adapter directories, prefer:

- `03-短视频运营资产/` for execution/content assets.
- `04-IP资产库/` for knowledge/reasoning assets.
- `05-账号案例库/` for account/source profiles.
- `06-输出成品/` for full playbooks.

Preserve existing local aliases recorded in `_meta/知识库管理规则.md`.

## Card Fields

Every durable card created from a playbook deposit should include:

- `schema_version: 3`.
- `knowledge_role`: procedure, talk-track, principle, model, evidence, source-profile, or output.
- `truth_status`: user-preference, generated, source-claim, verified-fact, or model-synthesis.
- `preservation`: exact, anchored, normalized, or derived.
- `reuse_mode`: quote-only, analyze-only, adapt-required, direct-use, reference-only, or do-not-use.
- `scope_type`, `primary_domain`, and `domains`; do not force an industry when the asset is general or cross-domain.
- `industries` and `responsibilities` as independent arrays; do not encode either only inside `domains`.
- `topics`.
- `retrieval_queries` phrased as real future operating questions.
- 平台.
- 账号阶段.
- 内容目标: 涨粉, 互动, 信任, 教育, 转化, 战役.
- 内容等级: A, B, C, or upgraded-B-to-A when applicable.
- 工单编号: D1-D7, backup ID, or source video ID when applicable.
- 内容角色: cold-start test, winner exploit, trust proof, objection handling, conversion handoff, campaign sequence, or review rewrite.
- 运营瓶颈: exposure, audience fit, trust, education, conversion, execution, or review when applicable.
- 强触发: pain, contrast, benefit, identity, misconception, case/result, avoidance, urgency, curiosity.
- 表现形式: 口播, 案例拆解, 教程, 对比, 探店, 评论回复, UGC模拟, 直播切片, etc.
- 实验假设 and primary metric when the card comes from a work order.
- 复盘决策: scale, rewrite, split-test, stop, deposit, or defer when available.
- 来源层级: user input, private KB, public KB, web/public source, model common knowledge.
- 判断类型: data conclusion, observation judgment, assumption judgment.
- `source_ids` and useful source anchors.
- `confidence`.
- `maturity`: seed, candidate, stable, or core.
- `time_sensitivity` and `sensitivity`.
- 适用场景.
- 不适用边界.
- 复用方式.

Default scripts, hooks, CTAs, and prompts to `reuse_mode: adapt-required`. Mark them `direct-use` only when audience, scenario, goal, variables, boundary, permission/compliance risk, test status, and last verification are recorded. A-grade editorial quality alone does not make wording safe for direct use.

## Private Source Handling

For private client/account/project sources:

- Do not expose raw private wording, customer names, screenshots, metrics, or proprietary examples unless explicitly approved.
- Deposit reusable mechanisms and anonymized conclusions by default.
- Keep source links and sensitive notes in private-source metadata when the vault contract supports it.
- If a private asset might be reused for another client, mark its non-transferable boundaries clearly.

## Index Updates

After saving playbook deposits, update relevant indexes when affected:

- AI retrieval index: add routes for industry, platform, account stage, content goal, and asset type.
- Machine asset index: rebuild after durable asset changes and verify index drift.
- Material/output index: register the full playbook and review status.
- Topic/model index: link goal-matrix patterns, spread mechanisms, conversion stages, and rejected-pattern lessons.
- Topic/copy index: link A-grade topics, strong hooks, B-to-A rewrite moves, C-grade rejection reasons, and operator bottleneck lessons.
- Account/source profile: update account positioning, pillars, top mechanisms, caveats, and pending tests.

## Fast Retrieval Contract

When `$short-video-ops-playbook` needs evidence, return a small evidence-ready set instead of a broad vault dump:

- Route by industry, platform, account stage, content goal, strong trigger, format, asset type, confidence, maturity, and public/private status.
- Prefer stable/core assets, then high-confidence candidate assets, then seed assets with caveats.
- Return the best matching cards/profiles and their source references; do not return entire transcript folders by default.
- Use the deterministic index shortlist first, then apply model judgment; never treat shortlist score as evidence or permission.
- Distinguish reusable mechanism from client-specific/private wording.
- Include missing evidence and freshness caveats so the playbook can decide whether web research is needed.
- Keep the retrieval result within the requested evidence budget: quick 5-8, standard 10-15, deep 15-25 decision-changing items.

## Operator-Grade Deposit Rules

When saving outputs from `$short-video-ops-playbook`, preserve the editorial judgment, not just the final polished copy:

- Save A-grade topics/hooks/scripts as reusable execution assets.
- Save B-to-A rewrites as reusable improvement patterns, including the weak point and fix.
- Save representative C-grade rejection reasons only when they teach a reusable lesson.
- Save operator bottleneck diagnosis as a reasoning asset tied to account stage and industry.
- Save strong trigger usage so future retrieval can find, for example, "本地生活 + 强反差 + 转化".
- Save reusable video work-order lessons only when they teach an execution pattern, experiment result, production blocker, or goal-specific CTA/handoff rule.
- Do not save every draft, every rejected idea, or every low-quality phrase.

Recommended card names:

- `选题卡 - <行业> - <强触发> - <目标>`
- `钩子卡 - <平台> - <触发机制>`
- `脚本结构卡 - <内容目标> - <表现形式>`
- `视频工单卡 - <账号阶段> - <目标> - <表现形式>`
- `实验假设卡 - <变量> - <指标> - <结论>`
- `改写模式卡 - B到A - <问题>到<修正>`
- `失败模式卡 - C档淘汰 - <原因>`
- `运营判断卡 - <账号阶段> - <瓶颈>`

## Quality Check

Before finishing a deposit workflow:

- Original source/transcript files were not modified.
- Private boundaries were preserved.
- Cards are not generic duplicates of the full playbook.
- High-scoring samples and representative failures are both captured when useful.
- A/B/C grades and rewrite/rejection reasons are preserved when they affect reuse.
- Next AI retrieval hints are clear enough for `$short-video-ops-playbook` to reuse.
