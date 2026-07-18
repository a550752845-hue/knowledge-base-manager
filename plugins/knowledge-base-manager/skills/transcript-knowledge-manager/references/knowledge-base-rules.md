# Knowledge Base Architecture And Governance

Use this reference when initializing, restructuring, auditing, or changing the operating contract of a knowledge base.

## Design Principle

Separate four concerns that are often incorrectly collapsed into one folder tree:

1. **Evidence plane**: immutable originals, source identity, exact excerpts, versions, and integrity records.
2. **Understanding plane**: source maps, complete logic maps, structure maps, and source profiles.
3. **Knowledge/action plane**: facts, claims, principles, models, procedures, scripts, prompts, and templates.
4. **Control/retrieval plane**: machine manifest, source registry, indexes, routes, freshness, queues, context, and logs.

Folders express lifecycle roles. Metadata expresses epistemic status, scope, source, topic, reuse, maturity, freshness, and sensitivity. Do not make one directory hierarchy encode all dimensions.

## Workspace Topology

A workspace may contain several managed roots:

```text
<workspace>/
  _meta/
    knowledge-base-registry.json
    知识库根目录注册表.md
  <general-root>/
  <industry-root>/
  <responsibility-root>/
  <private-project-root>/
```

Create or preserve separate roots when any of these materially differ:

- sensitivity or access boundary;
- owner/steward;
- industry vocabulary and factual sources;
- responsibility and operational workflow;
- update/freshness cycle;
- audience and output intent;
- source rights or retention policy;
- expected retrieval questions.

Do not create a new root only because a new topic appears. Do not merge roots merely because their physical structures differ.

For deep single-industry or single-responsibility knowledge, use one coherent managed root for that scope. Keep broadly portable methods in a general root and use the workspace registry to route across roots.

## Lifecycle Layout

For a new root, prefer:

```text
00-AI入口/      task routes, machine index, queues
10-原始证据/    immutable sources or external pointers; raw/corrected derivatives
20-来源解析/    source maps, logic maps, source profiles
30-知识对象/    facts, claims, principles, models
40-可执行资产/  procedures, scripts, talk tracks, prompts, templates, checklists
50-证据验证/    quotations, cases, data, conflicts, counterexamples, maturity reviews
60-输出成品/    drafts, reviewed outputs, approved deliverables, archives
_meta/          manifest, rules, registries, context, logs, health
```

Existing vaults may keep local names. Record semantic aliases in `_meta/knowledge-base.json`. Optimize manifests and indexes before considering a rename.

## Machine Root Contract

Schema-v3 roots should contain `_meta/knowledge-base.json`. It owns:

- stable knowledge-base ID and human name;
- scope type, industries, and responsibilities;
- paths to AI entry, asset index, rules, context, source registries, and log;
- lifecycle role path aliases;
- external source roots with `mode: read-only`;
- freshness thresholds.

See `machine-contract.md` and `knowledge-base-manifest.schema.json`.

The manifest does not own source content or asset semantics. Source records and asset frontmatter own those layers.

## Asset Schema Contract

Use `schema_version: 3` for newly created or materially upgraded durable assets. Validate every schema-v3 asset against `asset-frontmatter.schema.json`.

Required base fields:

```yaml
schema_version: 3
id:
type:
knowledge_role:
truth_status:
preservation:
reuse_mode:
status: draft | active | pending-review | approved | deprecated | archived
scope_type: general | industry | responsibility | cross-domain | project
primary_domain:
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
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

Not every optional field must be non-empty. Do not invent false precision merely to fill metadata.

## Knowledge Roles

| Role | Owns | Must not imply |
| --- | --- | --- |
| `source` | Original or registered source representation | Truth beyond what exists in the source |
| `logic-map` | Whole-source structure and reasoning | Verification or ready-made wording |
| `fact` | Independently verified normalized fact | Unchecked source assertion |
| `claim` | Source or knowledge-base viewpoint | Universal truth |
| `principle` | Portable judgment with scope/boundary | Procedure completeness |
| `model` | Framework organizing several assets | Evidence merely because it is detailed |
| `procedure` | Repeatable steps and decision rules | Environment-independent approval |
| `talk-track` | Script, prompt, phrase, template, approved copy | Permission to use directly by default |
| `evidence` | Exact excerpt, case, data, counterexample, validation | General rule without synthesis |
| `source-profile` | Author/account/institution/publication characteristics | Independent truth certification |
| `output` | Task-specific generated/reviewed deliverable | Durable knowledge automatically |
| `management` | Rules, indexes, context, logs, governance | Business evidence |

## Truth, Preservation, And Reuse

Truth status:

- `source-record`: exact content or metadata present in a source.
- `source-claim`: what a source asserts.
- `verified-fact`: independently checked or authoritative fact with verification record.
- `model-synthesis`: knowledge-base/model synthesis.
- `user-preference`: explicit user rule, choice, or style preference.
- `generated`: model-created output.

Preservation:

- `exact`: wording/structure must remain unchanged.
- `anchored`: normalized container with exact anchored content inside.
- `normalized`: wording may be standardized without changing meaning.
- `derived`: analysis or synthesis whose wording is not source wording.

Reuse:

- `quote-only`: quote exactly with an anchor and rights boundary.
- `analyze-only`: use for reasoning, not direct wording.
- `adapt-required`: tailor before operational use.
- `direct-use`: reviewed for a recorded scenario and verification window.
- `reference-only`: consult as context/evidence.
- `do-not-use`: retain for audit but block from output.

Never infer these values from a directory name.

## Independent Taxonomy

Keep these dimensions separate:

- **scope type**: general, industry, responsibility, cross-domain, project;
- **domain**: broad problem or body of practice;
- **industry**: healthcare, tourism, software, finance, etc.;
- **responsibility**: growth, sales, product, operations, legal, research, etc.;
- **topic/problem**: what questions the asset helps answer;
- **audience/scenario**: who and where it applies;
- **source**: where it came from;
- **role/truth/preservation/reuse**: what it is and what may be done with it.

Use `retrieval_queries` for representative future questions. Use controlled vocabulary only where repeated retrieval justifies it. Preserve aliases rather than mass-renaming historical terms.

## Identity And Relations

IDs must be stable and independent of titles/paths. Prefer lowercase ASCII IDs:

```text
src-<stable-external-id-or-slug>
logic-<source-id>
claim-<slug>-<short-stable-suffix>
model-<slug>
procedure-<slug>
talk-<scenario>-<slug>
evidence-<source-id>-<anchor>
output-<date>-<slug>
```

Use explicit relations:

```text
derived-from
supports
conflicts
counterexample
complements
duplicate
same-source
new-version
supersedes
narrows
broadens
translation
pending-verification
```

Do not resolve disagreement by silently merging wording or deleting the losing record.

## Confidence, Evidence, And Maturity

These are independent:

- `confidence`: current reliability judgment.
- `evidence_strength`: quality and diversity of support.
- `maturity`: readiness for repeated reuse.

Maturity guidance:

- `seed`: new, single-source, partial, or untested.
- `candidate`: coherent enough for careful use; boundaries and gaps are visible.
- `stable`: distinct supporting sources/cases or repeated validation, clear boundaries, and maintained freshness.
- `core`: preferred route with repeated cross-scenario success, strong evidence, validation records, counterexamples, and an active steward.

Allow downgrade, split, merge, deprecation, or retirement when evidence changes. A polished long page is not mature merely because it looks complete.

The maturity dashboard should record supporting evidence, conflicts, counterexamples, upgrade criteria, and downgrade/split triggers.

## Procedure Governance

A procedure must state:

- intended outcome;
- prerequisites and inputs;
- ordered steps and decision points;
- expected outputs and acceptance criteria;
- failure states and recovery;
- boundaries, exceptions, and environment/version dependencies;
- evidence or experience basis;
- validation/test status and last verification.

Default to `adapt-required`. Mark direct-use only for a reviewed target environment whose prerequisites are satisfied.

## Talk-Track Governance

Keep distinct:

- exact source quotation: anchored and `quote-only`;
- editable template: variables and `adapt-required`;
- approved production copy: complete direct-use contract.

Downgrade direct-use when audience, offer, product facts, pricing, policy, regulation, platform rules, performance evidence, rights, or privacy boundaries change.

Editorial quality or an A-grade score alone does not permit direct use.

## Output Promotion

Generated outputs do not become knowledge automatically. Promote only a reusable unit that:

- solves a recurring problem;
- stands independently;
- links to provenance and supporting assets;
- has explicit truth/preservation/reuse status;
- removes or restricts private/context-specific details;
- records boundaries and failure cases;
- has approval when direct-use wording is involved.

Use `promotion_status: approved | promoted` on generated durable assets outside the output role.

## Freshness

Use root-specific thresholds from the machine manifest. Defaults:

- high: 30 days;
- medium: 180 days;
- low: 3650 days.

Examples:

- High: laws, platform rules, prices, product specs, current metrics, approved live scripts.
- Medium: tactics, market conditions, operating assumptions.
- Low: historical records, stable definitions, durable conceptual models.

High-sensitivity assets require `last_verified`. A stale direct-use asset is ineligible until reviewed.

## Privacy And Rights

- Keep source sensitivity in the machine source registry.
- Derived assets may not become less sensitive by default.
- Lower sensitivity only with `anonymization_status: approved` or `declassification_status: approved` plus `privacy_reviewed_by`, `privacy_review_reason`, and `privacy_reviewed_at`.
- Separate quotation rights from knowledge reuse rights.
- Avoid private names, metrics, screenshots, or proprietary wording in cross-client reusable assets.
- Preserve restricted evidence for audit without exposing it through broad indexes or public outputs.

## Change Control

The skill may automatically:

- add or update one source registration;
- create derivative source maps and selected candidate assets;
- repair local metadata, aliases, or links;
- rebuild generated indexes atomically;
- update bounded context and append logs;
- mark stale, deprecated, pending-review, or conflicting assets;
- create seed/candidate synthesis conservatively.

Require confirmation before:

- modifying originals;
- mass moving/renaming files;
- changing root scope, access, ownership, or privacy;
- merging/splitting roots or top-level domains;
- overwriting ambiguous/conflicting assets;
- lowering sensitivity;
- promoting ambiguous models to core;
- approving direct-use wording without recorded approval;
- replacing a legacy root without rollback evidence.

## Health Contract

Periodic checks should cover:

- machine manifest and path safety;
- required management routes and generated index drift;
- invalid YAML, missing fields, invalid enums, and non-array dimensions;
- broken or ambiguous Obsidian links, including aliases;
- duplicate asset IDs and source IDs;
- missing provenance and unknown source IDs;
- exact content without anchors;
- source claims mislabeled as facts;
- logic maps violating analyze-only;
- generated knowledge without promotion;
- direct-use assets missing approval/context/testing/freshness;
- stale high-sensitivity knowledge;
- weak stable/core assets;
- unresolved conflicts and missing counterexamples;
- sensitivity downgrades without approval;
- source-integrity changes;
- recent-context bloat and machine/human route drift.
