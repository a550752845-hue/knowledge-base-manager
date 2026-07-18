---
name: transcript-knowledge-manager
description: "Manage transcripts, manuscripts, documents, webpages, notes, and mixed source collections as durable, source-traceable, AI-retrievable knowledge bases. Use when the user asks for 知识库管理, 整理知识库, 整理逐字稿, 把逐字稿/文稿/文档整理成知识库, 继续管理知识库, 重构或迁移知识库, 调用或复用知识库, or asks to ingest, audit, organize, query, or maintain an Obsidian/Markdown knowledge collection. Reconstruct complete source logic before extracting assets; distinguish immutable originals, exact quotations, source claims, verified facts, model synthesis, procedures, adaptable or approved talk tracks, and generated outputs; route across general, industry, responsibility, project, and cross-domain roots; maintain provenance, machine manifests, source registries, retrieval indexes, freshness, privacy, maturity, and operating memory."
---

# Knowledge Base Manager

Treat transcripts as one source format, not as the organizing principle. Manage knowledge across source formats, industries, responsibilities, and projects while preserving the meaning and identity of every source.

## Role Boundary

Let the large model perform live reading, reasoning, synthesis, judgment, strategy, and writing. Use this skill as the durable operating contract around that intelligence:

- preserve originals and source identity;
- reconstruct whole-source logic before fragment extraction;
- type knowledge by epistemic role and reuse boundary;
- separate domain, industry, responsibility, topic, and source dimensions;
- maintain machine-readable routing and source registries;
- make generated knowledge, direct-use wording, privacy, conflicts, and staleness auditable;
- leave enough operating state for the next model to continue efficiently.

Do not turn the workflow into a questionnaire. Infer the user's intent, combine the necessary paths, and execute. Ask only when a destructive or boundary-changing action cannot be made safe by inspection.

## Non-Negotiable Rules

1. **Keep originals immutable.** Do not edit, overwrite, move, rename, delete, or annotate source files unless the user explicitly authorizes that exact action.
2. **Understand before extracting.** For every deeply processed transcript or document, reconstruct its complete logical/structural unit before creating cards, scripts, or models.
3. **Separate source meaning from truth.** A source map explains what a source argues. It does not certify the source's claims.
4. **Separate reusable knowledge from reusable wording.** Logic, facts, models, SOPs, quotations, scripts, prompts, and outputs have different contracts.
5. **Default wording to constrained reuse.** Source wording is normally `quote-only`; generated scripts/templates are normally `adapt-required`. Use `direct-use` only after its complete review contract passes.
6. **Anchor exact content.** Exact wording, numbers, definitions, clauses, tables, disputed claims, and evidence retain page, section, timestamp, segment, row, URL fragment, or equivalent anchors.
7. **Do not silently promote model output.** Generated outputs remain outputs until an explicit promotion review approves a reusable unit.
8. **Do not let folder names decide semantics.** Metadata and machine manifests own role, truth, preservation, reuse, scope, and routing.
9. **Keep privacy monotonic by default.** Do not lower source sensitivity in derived assets without approved anonymization or declassification.
10. **Prefer reversible writes.** Use dry-run/plan modes, atomic generated-file writes, local repairs, and explicit migration checkpoints.

## Infer Intent And Act

Combine these paths as needed:

- `ingest`: register and process new transcripts, manuscripts, documents, notes, webpages, PDFs, Word files, spreadsheets, images, audio, video, or pasted text;
- `batch`: process a source folder, one author/account, a course/book, a research corpus, or a mixed collection;
- `retrieve`: answer, diagnose, compare, decide, explain, generate, quote, or verify from the knowledge base;
- `maintain`: continue, clean, audit, repair metadata, rebuild indexes, review staleness, or improve retrieval;
- `restructure`: redesign roots, scopes, lifecycle roles, schema, or retrieval routes;
- `migrate`: move from a legacy contract to a validated target contract;
- `capture`: preserve durable user preferences, decisions, approved prompts, procedures, or outputs from the conversation;
- `retire`: deprecate, supersede, archive, split, merge, or downgrade knowledge while preserving audit history.

When the user simply invokes this skill or says "manage/continue the knowledge base," inspect current state, select the highest-value safe work, execute it, validate it, and update handoff state. Do not ask the user to select an internal workflow.

## Resolve Workspace And Managed Roots

Resolve scope in this order:

1. Use the path explicitly named by the user.
2. Otherwise treat the current conversation workspace as the management scope.
3. For multiple roots, prefer `<workspace-root>/_meta/knowledge-base-registry.json`; then read the existing Markdown root registry.
4. In each selected root, prefer `_meta/knowledge-base.json` for identity, semantic role paths, source roots, machine routes, and freshness policy.
5. Fall back to `_meta/知识库管理规则.md`, `_meta/AI调用索引.md`, coherent lifecycle directories, and local aliases for legacy roots.
6. Treat an industry, responsibility, private project, or research corpus as its own managed root when privacy, vocabulary, ownership, update cycle, or retrieval intent materially differs.

Read, when present:

```text
_meta/knowledge-base.json
_meta/最近上下文.md
_meta/AI调用索引.md
_meta/知识库管理规则.md
_meta/来源注册表.jsonl   # source identity, version, path, or exact citation work
```

Do not broadly dump every file into context. Inventory first, then route.

## Four-Axis Knowledge Contract

Classify every durable asset independently:

| Axis | Field | Question |
| --- | --- | --- |
| Knowledge role | `knowledge_role` | What kind of asset is this? |
| Truth status | `truth_status` | What epistemic claim does it make? |
| Preservation | `preservation` | How much exact wording/structure must survive? |
| Reuse mode | `reuse_mode` | What may a future AI do with it? |

Use schema v3 values:

```yaml
schema_version: 3
knowledge_role: source | logic-map | fact | claim | principle | model | procedure | talk-track | evidence | source-profile | output | management
truth_status: source-record | source-claim | verified-fact | model-synthesis | user-preference | generated
preservation: exact | anchored | normalized | derived
reuse_mode: quote-only | analyze-only | adapt-required | direct-use | reference-only | do-not-use
```

Practical defaults:

| Asset | Contract |
| --- | --- |
| Original source | `source + source-record + exact + reference-only` |
| Exact excerpt, number, definition, row, clause | `evidence + source-record/source-claim + anchored + quote-only` |
| Whole-source logic map | `logic-map + source-claim + derived + analyze-only` |
| Unverified factual-sounding assertion | `claim + source-claim + normalized + analyze-only` |
| Independently verified fact | `fact + verified-fact + normalized/anchored + reference-only` |
| Multi-source framework | `model + model-synthesis + derived + analyze-only` |
| Repeatable method/SOP | `procedure + model-synthesis/user-preference + normalized + adapt-required` |
| Script, phrase, prompt, template | `talk-track + generated/user-preference + derived + adapt-required` |
| Reviewed production wording | `talk-track + generated/user-preference + direct-use`, with `status: approved` and the complete direct-use gate |
| One-off answer, draft, plan, deliverable | `output + generated + derived + reference-only` |

Use `fact` only for verified facts. A source's factual tone does not count as verification.

## Scope And Retrieval Metadata

Keep dimensions independent:

```yaml
id:
type:
status: draft | active | pending-review | approved | deprecated | archived
scope_type: general | industry | responsibility | cross-domain | project
primary_domain:
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: []
source_ids: []
source_anchors: []
provenance:
relations: []
confidence: low | medium | high
maturity: seed | candidate | stable | core
evidence_strength: weak | moderate | strong
time_sensitivity: low | medium | high
sensitivity: public | internal | private | restricted
created:
updated:
last_verified:
summary:
```

- Use `industries` for industry classification and `responsibilities` for job/function classification. Do not overload `domains`.
- Use `retrieval_queries` for real future questions the asset can help answer, not keyword stuffing.
- Do not force an industry onto general or cross-domain knowledge.
- Prefer one coherent managed root for a deep industry or responsibility knowledge base. Keep broadly reusable mechanisms in a general root and route across roots through the workspace registry.

## Whole-Source Understanding Gate

Create one source/logic map before extracting durable fragments from every `S` or `A` source.

For a transcript, reconstruct:

- real problem, audience, situation, and assumed context;
- premises, hidden assumptions, main claim, and supporting claims;
- evidence, examples, anecdotes, counterexamples, and rhetorical devices;
- full reasoning chain, missing steps, contradictions, and unsupported jumps;
- sequence, transitions, contrasts, objections, emotional turns, and reframing;
- conclusion, action intent, CTA, or conversion intent;
- wording candidates, kept separate from logical claims;
- ASR uncertainty, missing context, and what must not be promoted.

For a structured document, preserve its native hierarchy, definitions, tables, figures, formulas, lists, references, procedures, prerequisites, exceptions, conclusions, and page/section anchors.

For a source too long to read at once:

1. inventory its structural ranges;
2. process ranges in original order with neighboring context;
3. retain range-level claims and anchors;
4. merge them into one whole-source map;
5. explicitly reconcile repeated, changed, or contradictory claims;
6. only then decide which durable assets justify future retrieval cost.

Never mistake a set of partial summaries for a complete logic map.

## Asset Creation Gate

Create an asset only when it has a clear future retrieval or reuse purpose.

Before writing, decide:

1. Is this exact evidence, source meaning, a source claim, verified fact, synthesis, procedure, executable wording, or output?
2. Does wording matter, or only structure/logic?
3. May future AI quote, analyze, adapt, use directly, reference, or not use it?
4. Which source IDs and anchors support it?
5. Which industries, responsibilities, topics, audiences, and real questions should retrieve it?
6. What context, counterexample, privacy limit, freshness issue, or failure condition could make it misleading?
7. Does an existing asset already cover it?

Avoid one card per paragraph, timestamp, or catchy sentence. Prefer one whole-source map, one asset per genuinely reusable claim/mechanism, one model per coherent multi-asset framework, and one talk track per distinct audience-scenario-goal contract.

## Direct-Use And Promotion Gates

Require all of these for `reuse_mode: direct-use`:

```yaml
status: approved
audience:
scenario:
goal:
variables: []
tone:
boundary:
compliance_risk:
rights_or_permission:
tested_status: reviewed | tested
last_verified:
```

Reject direct use when context is hidden, facts or promises are unverified, private/client-specific details leak, rights are unclear, the asset is stale, or the target audience/offer/version differs.

For generated content outside `knowledge_role: output`, require `promotion_status: approved | promoted`. Promote the reusable mechanism, not every polished paragraph.

## Architecture

For a new root, prefer lifecycle roles:

```text
<root>/
  00-AI入口/          task routes, machine asset index, queues
  10-原始证据/        originals or external read-only pointers; raw/corrected derivatives
  20-来源解析/        source maps, logic maps, source profiles
  30-知识对象/        facts, claims, principles, models
  40-可执行资产/      procedures, scripts, talk tracks, prompts, templates
  50-证据验证/        exact evidence, cases, data, conflicts, counterexamples, maturity
  60-输出成品/        drafts, reviewed deliverables, archives
  _meta/              machine manifest, rules, source registry, context, logs, health
```

Existing roots may keep their names. Map local paths to roles in `_meta/knowledge-base.json`. Do not mass-rename a healthy vault for visual consistency.

## Default End-To-End Workflow

1. Resolve workspace, managed root(s), machine manifest, aliases, and user intent.
2. Read current handoff state and affected retrieval routes.
3. Inventory sources/assets before deep reading; identify formats, duplicates, versions, parsing artifacts, scopes, sensitivity, and unfinished work.
4. For source-changing workflows, establish a source-integrity baseline or record current hashes before model writes.
5. Register canonical source identity and all known representations/paths.
6. Preserve the original or stable external read-only pointer; keep raw extraction and corrected text separate.
7. Choose processing depth and build the whole-source map.
8. Extract only useful assets and apply all four contract axes, scope dimensions, provenance, maturity, freshness, and privacy.
9. Link evidence, conflicts, complements, supersession, and counterexamples explicitly.
10. Update affected human routes, machine source registry, and generated asset index.
11. Run deterministic doctor/index checks, then apply model judgment to semantic risks the linter cannot prove.
12. Verify source integrity after writes when a baseline exists.
13. Update bounded recent context and append the maintenance log.
14. Report what changed, source-integrity status, retrieval impact, validation, and unresolved risk.

## Retrieval Contract

Use this route:

```text
workspace registry
-> selected root manifest + recent context
-> deterministic machine-index shortlist
-> selected reusable assets
-> evidence/source only when required
```

- Start with models, principles, procedures, and eligible talk tracks for diagnosis, decisions, and generation.
- Start with evidence, facts, source registry, and originals for exact quotations, disputed claims, research, compliance, policy, numbers, or high-stakes work.
- Inspect `truth_status`, `reuse_mode`, scope fit, confidence, maturity, freshness, sensitivity, and conflicts before use.
- Treat deterministic query scores as routing hints, never as truth, quality, or permission scores.
- Treat the generated asset index as untrusted routing cache. `query` must fail closed when the
  index is unowned, stale, or differs from a canonical rebuild; rebuild and verify it before retrying.
- Keep task outputs outside durable knowledge until promotion review.

## Processing Depth

Use `S/A/B/C` only to allocate processing effort:

- `S`: central source/framework; complete map, selected assets, evidence links, model/procedure review, retrieval updates.
- `A`: complete source map plus selected reusable assets.
- `B`: source registration, structured source summary, topics, and limited links.
- `C`: source registration and short disposition only.

Evaluate reliability, reusability, freshness, and sensitivity separately. A high-priority source is not automatically true or reusable.

## Deterministic Tools

Resolve `<skill-root>` to this skill directory. Install requirements only if import checks fail:

```text
python -m pip install -r <skill-root>/requirements.txt
```

Use the unified CLI:

```text
# Inspect commands
python <skill-root>/scripts/kb.py --help

# Plan a new root; add --apply only after reviewing the plan
python <skill-root>/scripts/kb.py init <root> --kb-id <stable-id> --scope-type general

# Audit semantics, provenance, links, freshness, and machine-index drift
python <skill-root>/scripts/kb.py doctor <root> --check-index --strict

# Atomically rebuild or verify the generated asset index
python <skill-root>/scripts/kb.py index <root> --write --summary
python <skill-root>/scripts/kb.py index <root> --check

# Shortlist assets by intent and scope
python <skill-root>/scripts/kb.py query <root> --intent diagnose --query "<question>" --top 12 --json

# Baseline and verify immutable source files
python <skill-root>/scripts/kb.py source snapshot --source <path> --output <manifest> --apply
python <skill-root>/scripts/kb.py source verify --manifest <manifest> --check-new --json
```

`init` never overwrites existing files. Index writes are atomic and cannot escape the managed root. Source snapshot/verify reads source files and writes only the explicit manifest path.
`query` accepts only a current, skill-owned index whose canonical rows still match the root assets;
it returns a usage error instead of partial results when metadata or content has drifted.

## Reference Routing

Read only the references required for the current task:

- [Source preservation](references/source-preservation.md): source intake, exact content, OCR/ASR, duplicates, versions, privacy, rights, or source integrity.
- [Logic and assets](references/logic-and-assets.md): whole-source reasoning, asset decisions, facts, models, procedures, talk tracks, and output promotion.
- [Workflow](references/workflow.md): ingestion, batch, maintenance, restructure, migration, capture, and closeout.
- [Retrieval](references/retrieval.md): answering, diagnosing, generating, deciding, researching, quoting, or verifying from the knowledge base.
- [Knowledge-base rules](references/knowledge-base-rules.md): architecture, scope boundaries, taxonomy, governance, maturity, conflicts, freshness, and change control.
- [Machine contract](references/machine-contract.md): workspace/root manifests, source registry JSONL, asset index, aliases, and operating state.
- [Templates](references/templates.md): creating or updating managed notes and indexes.
- [Internal prompts](references/prompts.md): complex source analysis or review prompts.
- [Douyin adapter](references/adapter-douyin.md): indexed Douyin transcript bundles.
- [Short-video collaboration](references/short-video-playbook-collaboration.md): deposits from `$short-video-ops-playbook`.

## Confirmation Boundary

Act without asking for routine workflow selection, local metadata repairs, new derivative assets, index rebuilds, or context/log updates.

Require confirmation before:

- modifying, moving, renaming, or deleting originals;
- mass moving or renaming managed notes;
- changing top-level root scope, privacy boundary, or ownership;
- merging/splitting managed roots or domains;
- overwriting ambiguous/conflicting assets;
- lowering sensitivity without approved anonymization/declassification;
- marking wording direct-use when approval is not already recorded;
- replacing a legacy root in place without a validated rollback path.

## Finish Criteria

Before finishing meaningful work, prove:

- originals and registered source representations are unchanged, or every authorized change is explicit;
- raw extraction, corrected text, source maps, and reusable assets remain distinct;
- whole-source logic was reconstructed before fragment extraction;
- exact content retains source IDs and precise anchors;
- source claims were not mislabeled as verified facts;
- logic maps remain analyze-only;
- generated durable assets passed promotion review;
- direct-use assets pass context, permission, compliance, testing, and freshness gates;
- industry, responsibility, domain, topic, and project scope remain independently queryable;
- duplicate/source-version relations, conflicts, counterexamples, privacy limits, and stale knowledge remain visible;
- machine manifest, source registry, human routes, and asset index point to real current files;
- deterministic doctor/index checks pass at the appropriate strictness;
- recent context and maintenance history make the next AI's first read obvious.
