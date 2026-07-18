# Practical Workflow

Use this workflow for ingestion, batch processing, retrieval-backed output, maintenance, restructuring, migration, conversation capture, and retirement. Adapt to the root manifest and local aliases instead of forcing folder renames.

## 1. Resolve And Orient

Determine from the request and workspace:

- management scope and selected root(s);
- intent or combined intents;
- source locations and representations;
- whether sources are internal, external, public, private, or restricted;
- expected result: actual edits, query answer, artifact, audit, migration, or repair;
- destructive, privacy, permission, and overwrite risks.

Read the workspace machine/Markdown root registry when several roots may apply. Read the selected root manifest, recent context, AI call index, and management rules before writing.

Do not ask the user to choose an internal workflow. Ask only when the root cannot be inferred safely or a protected boundary would change.

## 2. Inventory Before Deep Reading

For a folder or mixed collection, inventory:

- file count, formats, sizes, dates, owners, and encoding;
- source IDs, URLs, duplicate-looking names, hashes, and versions;
- originals, raw extraction, corrected text, source maps, cards, models, procedures, talk tracks, evidence, and outputs;
- OCR/ASR/JSONL/manifests/section indexes and extraction limitations;
- likely domains, industries, responsibilities, projects, and privacy boundaries;
- unprocessed, stale, deprecated, disputed, missing, or orphaned material;
- current machine manifest, source registry, index, and route health.

Sample representative sources before deeply processing a large batch. Do not spend full reading effort before understanding collection shape.

## 3. Establish Source Integrity

When model work will write near source locations, when a migration is planned, or when proving immutability matters:

1. identify explicit source files/directories;
2. create a hash baseline outside immutable source locations;
3. perform only derivative/management writes;
4. verify the baseline after work;
5. report changed, missing, and unexpected files.

Use:

```text
python <skill-root>/scripts/kb.py source snapshot \
  --source <source-path> --output <managed-root>/_meta/source-integrity.json --apply

python <skill-root>/scripts/kb.py source verify \
  --manifest <managed-root>/_meta/source-integrity.json --check-new --json
```

Do not treat an absent baseline as proof that originals are unchanged. When no baseline exists, use current hashes/mtime/file counts as weaker evidence and say so.

## 4. Register Source Identity

Before extracting reusable knowledge:

1. assign or reuse a canonical `source_id`;
2. record source type, title, author/owner, date/version, URL/external ID, rights, sensitivity, and status;
3. record all known paths and representations;
4. choose a preferred read path without deleting alternatives;
5. record content hash when practical;
6. classify duplicate/version/translation/corrected relationships;
7. keep raw extraction and corrected text distinct.

Update the machine JSONL registry first, then its human Markdown view. Use `source-preservation.md` for detailed rules.

## 5. Allocate Processing Depth

Use `S/A/B/C` only for effort allocation:

| Grade | Processing |
| --- | --- |
| S | Complete source map, selected assets, evidence relations, model/procedure review, retrieval updates |
| A | Complete source map plus selected reusable assets |
| B | Source registration, structural summary, topics, limited links |
| C | Source registration and short disposition only |

Score or judge these separately:

- source/evidence reliability;
- expected reusability;
- freshness/time sensitivity;
- privacy/sensitivity;
- processing status;
- duplication with current assets.

## 6. Build The Complete Source Map

For every S/A source, analyze the source as one coherent unit before fragment extraction.

For transcripts, reconstruct:

- problem, audience, situation, and assumed context;
- premises, hidden assumptions, main/supporting claims;
- evidence, examples, stories, rhetoric, and counterexamples;
- full reasoning chain, transitions, objections, emotional turns, conclusion, and CTA;
- missing steps, unsupported jumps, contradictions, ASR uncertainty, and absent context;
- wording candidates separated from logical claims;
- candidate assets and rejected candidates.

For documents, preserve native headings, sections, tables, figures, formulas, lists, references, procedures, prerequisites, caveats, conclusions, and anchors.

For long sources, process structural ranges in order and merge them into one map. Reconcile repeated or changing claims. Do not save disconnected chunk summaries as the final map.

Use:

```yaml
knowledge_role: logic-map
truth_status: source-claim
preservation: derived
reuse_mode: analyze-only
```

## 7. Extract Only Useful Assets

Classify every candidate before writing:

```text
source / exact evidence / fact / claim / principle / model / procedure / talk track / source profile / output
```

Then assign:

```text
truth_status + preservation + reuse_mode
+ industries/responsibilities/domains/topics/retrieval_queries
+ source IDs/anchors/provenance/relations
+ confidence/maturity/evidence strength/freshness/sensitivity
```

Rules:

- exact language exists only where wording matters;
- unverified factual-sounding statements remain source claims;
- models require coherent multi-asset organization;
- procedures require inputs, steps, decisions, outputs, failures, and boundaries;
- scripts/templates default to adapt-required;
- direct-use requires complete recorded approval;
- one-off work stays in outputs;
- generated durable assets require explicit promotion status;
- duplicate candidates merge into or relate to existing assets rather than multiplying cards.

## 8. Connect Evidence And Relations

Every durable source-derived asset should resolve to:

- source ID and preferred source representation;
- page, section, timestamp, row, paragraph, segment, or equivalent anchor;
- source/logic map;
- supporting/conflicting facts, claims, models, procedures, scripts, and evidence;
- duplicates, versions, complements, supersession, and counterexamples.

Use explicit relation labels. Never overwrite disagreement with a blended paragraph that loses provenance.

## 9. Update Human And Machine Routes

Update only affected routes:

- machine source registry and human source view;
- source processing index or source profile;
- domain/industry/responsibility/topic route;
- model maturity/evidence-gap dashboard;
- pending/review/stale/conflict queue;
- machine asset index;
- AI entry and recent context when retrieval behavior changed.

The AI entry is a router, not a duplicated knowledge dump.

Rebuild the machine asset index atomically after asset changes:

```text
python <skill-root>/scripts/kb.py index <root> --write --summary
```

## 10. Batch Workflow

For a large batch:

1. inventory all candidates;
2. identify duplicates, versions, source patterns, and root boundaries;
3. sample 5-10 representative sources, fewer for a small batch;
4. build/update the author/institution/account profile early when relevant;
5. process high-value and structurally representative sources first;
6. register repetitive/low-value sources without duplicate cards;
7. process independent sources concurrently only when writes are disjoint and integration remains deterministic;
8. reconcile taxonomy, duplicate assets, model candidates, evidence gaps, and retrieval quality every 20 sources;
9. leave exact next-batch scope and stopping criteria.

Stop and consolidate when added volume no longer reduces future retrieval cost or improve decisions.

## 11. Retrieval And Output

For an answer, diagnosis, decision, or generated artifact:

1. route to the correct root(s);
2. shortlist through the machine asset index by intent, industry, responsibility, topic, and query;
3. inspect role, truth, reuse, maturity, freshness, sensitivity, and conflict state;
4. read the smallest sufficient set of assets;
5. escalate to evidence/source when exactness, risk, disagreement, or uncertainty requires it;
6. generate or answer while preserving attribution and reuse boundaries;
7. store task-specific work as output only when a durable artifact is required;
8. promote reusable units separately.

Use `retrieval.md` for the detailed route.

## 12. Maintenance Workflow

When the user says continue, improve, clean up, audit, or manage:

1. read the manifest and bounded recent context;
2. run doctor with index checking;
3. inspect missing provenance, broken/ambiguous links, duplicate IDs, index drift, stale assets, privacy downgrades, invalid direct-use assets, weak mature models, and unreviewed generated knowledge;
4. repair local deterministic hygiene directly;
5. use model judgment for semantic misclassification, over-carding, weak logic maps, bad retrieval questions, and root-boundary drift;
6. rebuild indexes;
7. verify source integrity when a baseline exists;
8. update recent context and append the log.

## 13. Restructure Or Migrate

Do not begin by moving files. Use this order:

1. freeze originals/legacy roots as read-only references;
2. record integrity baseline and complete inventory;
3. map current paths and metadata to semantic roles;
4. define target root boundaries, machine manifest, schema, source registry, and retrieval contract;
5. create a parallel target root for substantial changes unless the user explicitly approves in-place migration;
6. pilot one transcript, one structured document, one exact evidence item, one model/procedure, and one execution asset when available;
7. test realistic diagnosis, generation, research, and quotation queries;
8. migrate high-value assets first and register low-value sources without deep conversion;
9. validate source identity, hashes, links, metadata, privacy, index drift, and retrieval routes;
10. promote the target only after pass criteria; preserve rollback until the user explicitly retires the old root.

Do not claim migration is complete because files were moved. Completion requires usable routes and retrieval tests.

## 14. Conversation Capture

Capture only durable outcomes:

- explicit user preferences and operating rules;
- reviewed decisions and unresolved choices;
- reusable prompts, procedures, models, or templates;
- approved outputs worth future retrieval.

Use `truth_status: user-preference` for explicit user rules and `generated` for model-produced content. Record conversation/task provenance. Do not present conversation-derived material as external evidence.

## 15. Retirement

When knowledge becomes wrong, stale, unsafe, redundant, or superseded:

- mark `deprecated` or `archived` rather than deleting audit history;
- add `supersedes`, `conflicts`, or `duplicate` relations;
- route indexes away from retired assets;
- downgrade direct-use immediately when its contract fails;
- retain exact evidence needed to explain the decision;
- update maturity dashboards, recent context, and logs.

## 16. Closeout Transaction

Finish meaningful work in this order:

1. write all intended derivative and management changes;
2. rebuild machine indexes;
3. run strict doctor and index verification;
4. verify source integrity;
5. perform semantic review for whole-source logic, truth/reuse classification, privacy, and over-carding;
6. update recent context with next-read routes and unresolved decisions;
7. append maintenance log with scope, reason, validation, and residual risk;
8. report exact created/updated assets, source status, retrieval impact, tests, and remaining uncertainty.
