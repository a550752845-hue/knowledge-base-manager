# Retrieval And Reuse

Use this reference when answering, diagnosing, comparing, deciding, explaining, generating, researching, quoting, or verifying with managed knowledge.

## Retrieval Goal

Read the smallest source-traceable set that can answer the task responsibly. Optimize for decision relevance and safety, not minimum file count alone and not broad vault dumping.

Preferred route:

```text
workspace root registry
-> selected root manifest + recent context
-> deterministic machine-index shortlist
-> selected assets
-> evidence/source only when required
```

## Select Roots Before Assets

For each task, determine:

- general vs industry vs responsibility vs project scope;
- privacy/access boundary;
- relevant industries and responsibilities;
- whether the task spans several roots;
- whether exact source access is required.

Use one primary root when possible. Use several roots only when the question genuinely crosses boundaries. Keep source attribution and conflicting root assumptions visible.

## Orient Once

Read when present:

```text
<workspace>/_meta/knowledge-base-registry.json
<workspace>/_meta/知识库根目录注册表.md
<root>/_meta/knowledge-base.json
<root>/_meta/最近上下文.md
<root>/_meta/AI调用索引.md
```

Read management rules when aliases or change boundaries are unclear. Read the source registry only for source identity, duplicate/version resolution, exact citation, or privacy/right checks.

## Intent Routes

| Intent | Start with | Escalate to |
| --- | --- | --- |
| Diagnose | Models, principles, procedures | Evidence, source maps, counterexamples |
| Generate | Eligible talk tracks, procedures, models | Evidence/examples for specificity and current facts |
| Decide | Models, procedures, verified facts | Conflicts, counterexamples, primary evidence |
| Explain | Principles, models, facts, logic maps | Original sections for nuance |
| Research/compare | Logic maps, source profiles, claims, evidence | Originals and independent verification |
| Verify/quote | Evidence, fact records, source registry | Original representation and exact anchor |
| Continue management | Manifest, recent context, doctor output, queues | Affected assets and source registry |

## Deterministic Shortlist

Use the generated index path from the root manifest. Query before reading asset bodies:

```text
python <skill-root>/scripts/kb.py query <root> \
  --intent <generate|diagnose|decide|explain|research|verify|quote|manage> \
  --industry <industry> \
  --responsibility <responsibility> \
  --query "<task question>" \
  --top 12 --json
```

The CLI must authenticate the index as skill-owned and compare it with a canonical rebuild before
filtering or ranking. If that check fails, stop retrieval, rebuild with `index --write`, verify with
`index --check`, and retry. Do not inspect or return rows from the rejected index.

Useful index fields:

```text
id, title, path, asset_hash
knowledge_role, truth_status, preservation, reuse_mode, status
scope_type, primary_domain, domains, industries, responsibilities
topics, retrieval_queries, audiences, languages
confidence, maturity, evidence_strength
time_sensitivity, sensitivity, updated, last_verified
source_ids, source_anchors, provenance, relations, summary
```

The deterministic score combines intent-role fit and lexical/scope matches. It is not a truth, permission, maturity, evidence, or quality score. The model must still judge context and boundaries.

## Selection Policy

Select by this order:

1. root and access fit;
2. task intent and role fit;
3. industry/responsibility/domain/topic/audience/scenario fit;
4. reuse eligibility;
5. truth/evidence requirements;
6. freshness and version fit;
7. confidence/maturity/evidence strength;
8. conflict/counterexample coverage;
9. smallest sufficient set.

Do not always prefer core/stable assets if a candidate asset is materially better matched. Do not use a direct-use asset outside its approved context merely because it ranks first.

## Reading Escalation

Use four levels:

1. **Route**: registry, manifest, recent context, AI entry, index.
2. **Asset**: selected fact, claim, principle, model, procedure, talk track, source map, profile.
3. **Evidence**: exact excerpt, case, data, conflict, counterexample, validation record.
4. **Source**: original page, section, timestamp, table, file, or capture.

Stop at the lowest level that responsibly supports the task. Escalate when:

- exact wording or quotation is requested;
- numbers, legal/policy/compliance, financial, medical, or other high-stakes facts matter;
- assets conflict or evidence is weak;
- source identity/version is uncertain;
- confidence is low or maturity is seed;
- high-time-sensitivity knowledge may be stale;
- a direct-use asset's context/approval is questionable;
- the user asks why/how the knowledge base knows something.

## Truth Check

Before presenting a statement:

- `source-record`: say what the source contains.
- `source-claim`: attribute the assertion to the source.
- `verified-fact`: inspect verification method/date/scope and cite when material.
- `model-synthesis`: present as a framework with boundaries and evidence status.
- `user-preference`: treat as an operating preference, not external fact.
- `generated`: treat as model-produced unless explicitly promoted.

If metadata and content conflict, treat the asset as unsafe, inspect provenance, and repair or quarantine it before relying on it.

## Reuse Check

- `quote-only`: quote exact text with source anchor and rights boundary.
- `analyze-only`: use the mechanism for reasoning; do not reuse wording.
- `adapt-required`: tailor to audience, scenario, goal, constraints, current facts, and channel.
- `direct-use`: use only inside its recorded audience/scenario/version/verification window.
- `reference-only`: consult as context/evidence.
- `do-not-use`: exclude from output; retain for audit.

Never turn a logic map into a script or a source claim into an unattributed fact.

## Talk-Track Retrieval

Filter scripts/prompts/templates by:

- audience and scenario;
- goal and channel/platform;
- industry and responsibility;
- tone and language;
- product/offer/version;
- variables and boundaries;
- sensitivity, rights, and permission;
- tested status and last verification;
- adapt-required vs direct-use.

When adaptation is required, preserve the mechanism and variables, not private/source-specific wording. Revalidate current facts and promises.

## Model And Procedure Retrieval

Check:

- problem, scope, prerequisites, and target environment;
- confidence, maturity, and evidence strength;
- source diversity, validation records, and freshness;
- counterexamples, conflicts, and failure conditions;
- whether weaker subcomponents are hidden inside a mature parent;
- whether an operational procedure is approved for the current environment.

Read the maturity/evidence-gap dashboard before treating candidate models as default methods.

## Fact And Evidence Retrieval

For facts:

- inspect verification method/sources;
- confirm verification date and version/jurisdiction scope;
- check current conflicts and time sensitivity;
- return to authoritative evidence when material.

For exact evidence:

- resolve source ID through the machine registry;
- open the preferred original representation;
- verify page/section/timestamp/row anchor and neighboring context;
- quote exact bytes/text only when the representation supports it;
- disclose OCR/ASR uncertainty.

## Long-Source Retrieval

Use source structure:

- read manifest/index/range catalog first;
- select relevant sections/pages/time ranges;
- include neighboring context and conclusion needed to preserve logic;
- use range-level map-reduce only when needed;
- verify final claims against the whole-source map;
- return to original representation for exact quoting.

For indexed Douyin bundles, use `adapter-douyin.md`.

## Conflict-Aware Retrieval

When selected assets conflict:

1. preserve each claim and provenance;
2. compare source authority, evidence, scope, time/version, and definitions;
3. identify whether the conflict is real, contextual, temporal, or terminological;
4. surface unresolved disagreement;
5. avoid blending into a false consensus;
6. update conflict relations only when the task includes maintenance.

## Multi-Root Synthesis

When combining roots:

- keep root ID and sensitivity with each asset;
- prefer general mechanisms plus industry-specific facts/boundaries;
- prevent private project details from leaking into general outputs;
- reconcile vocabulary and version differences;
- record which conclusions are portable vs root-specific;
- do not silently duplicate or move assets merely to answer a query.

## Output Discipline

When answering from the knowledge base:

- state material caveats without flooding the answer with metadata;
- distinguish source claim, verified fact, model synthesis, and user preference;
- use direct wording only when eligible;
- cite source paths/anchors when exactness matters;
- make conflicts, staleness, missing evidence, and uncertainty visible;
- do not mutate the knowledge base simply because it was queried;
- keep generated work under outputs until promotion review.

## Retrieval Quality Review

Before finishing:

- Did root selection match industry, responsibility, project, and privacy boundary?
- Did the index shortlist the right role types?
- Did I read too much, too little, or the wrong abstraction level?
- Did I confuse source meaning with truth?
- Did I honor preservation, reuse, rights, and sensitivity?
- Is verification/current-source access required?
- Did conflicts/counterexamples materially change the answer?
- Would a route/index update help the next AI, or create unnecessary churn?
