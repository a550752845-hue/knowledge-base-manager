# Internal Work Prompts

Use these as internal reasoning contracts for complex work. Adapt to the source and root manifest; do not copy mechanically into user-visible output.

## Workspace And Root Resolution

```text
Resolve which managed knowledge-base root or roots own this task.

Inspect:
- explicit user path and current workspace
- machine and Markdown root registries
- each candidate root's scope, industries, responsibilities, sensitivity, owner, and status
- whether the task is general, industry-specific, responsibility-specific, project/private, or cross-domain
- whether one root is sufficient

Return the selected root(s), why they fit, access/privacy constraints, and the first machine routes to read. Do not create or merge roots merely because a new topic appears.
```

## Source Intake

```text
Inventory and register the source before analysis.

Identify:
- canonical source identity and all known paths, URLs, versions, or platform IDs
- source type, title, author/owner, date, edition/version, rights, and sensitivity
- original, raw extraction, corrected text, rendered, and structured derivative representations
- available page/section/timestamp/segment/row anchors
- content hashes and integrity baseline strength
- duplicate, new-version, correction, translation, abridgment, or disputed-match relations
- parsing, OCR, ASR, layout, access, or missing-source limitations

Do not modify the original. Return machine source-registry changes, preferred read path, and unresolved identity risks.
```

## Complete Transcript Logic Map

```text
Analyze the complete transcript as one argument before extracting any reusable asset.

Return:
1. source identity, coverage, and uncertain ranges
2. real problem, intended audience, situation, speaker goal, and assumed context
3. explicit premises, definitions, and hidden assumptions
4. thesis, supporting claims, subclaims, exceptions, and qualifications
5. facts, examples, stories, demonstrations, authorities, comparisons, and counterexamples
6. full reasoning chain, including missing steps and alternative explanations
7. sequence, transitions, reframes, objections, contrasts, emotional turns, conclusion, and CTA/action intent
8. rhetorical mechanisms and wording candidates, kept separate from logical claims
9. logic quality: evidence fit, jumps, contradictions, overgeneralization, missing context, and ASR uncertainty
10. candidate assets classified by role/truth/preservation/reuse/scope/provenance
11. rejected candidates and why they should not become durable knowledge

Prove coverage of beginning, middle, conclusion, and action intent. Attribute source claims. Do not turn the logic map into a script or verified fact.
```

## Long-Source Ordered Merge

```text
The source is too long for one read. Reconstruct it without losing global logic.

For each structural range in original order, record:
- range ID and neighboring context
- local purpose, claims, evidence, transitions, and uncertainty
- new/refined/repeated/reversed claims
- exact anchors needed later

Maintain a running claim-relation ledger. After all ranges:
- reconstruct one source-level outline and reasoning chain
- reconcile repeated or contradictory statements
- verify beginning/middle/conclusion/action coverage
- identify what cannot be concluded because context or ranges are missing
- only then classify candidate assets

Do not submit a list of chunk summaries as the final source map.
```

## Structured Document Map

```text
Analyze the document using its native structure.

Preserve:
- purpose, audience, scope, version, and heading hierarchy
- definitions, tables, lists, figures, formulas, notes, references, and appendices
- page/section/slide/sheet/row anchors
- claims and their local supporting evidence
- procedures, prerequisites, branches, outputs, exceptions, and failure conditions
- conclusions, caveats, unresolved questions, and revision history
- extraction, OCR, layout, comments, tracked changes, or hidden-content limitations

Do not use blind equal-size chunks when native sections are available. Distinguish source claims from independently verified facts.
```

## Asset Classification

```text
For each candidate durable asset, decide:
- knowledge_role
- truth_status
- preservation
- reuse_mode
- scope_type, domains, industries, responsibilities, topics, audiences, and retrieval_queries
- source IDs, precise anchors, conversation/task provenance, and relations
- confidence, maturity, evidence strength, time sensitivity, and sensitivity
- future retrieval purpose
- boundaries, counterexamples, conflicts, and stale conditions

Reject candidates that:
- repeat the source map without independent retrieval value
- lack a clear future task/question
- duplicate an existing asset
- cannot preserve necessary context/provenance
- convert source claim to fact
- convert logic to wording
- leak private/restricted content
- cost more to maintain than they are likely to return
```

## Fact Verification Review

```text
Decide whether this factual-sounding statement qualifies as a verified fact.

Check:
- exact proposition and definitions
- independent or authoritative verification sources
- verification method and date
- valid time, version, jurisdiction, population, and measurement scope
- source conflicts and alternative interpretations
- whether the claim is time-sensitive

If verification is insufficient, keep knowledge_role: claim and truth_status: source-claim. Do not use confident wording as evidence.
```

## Direct-Use Review

```text
Decide whether this script, talk track, prompt, template, or procedure may be direct-use.

Check:
- known audience, scenario, goal, channel, tone, product/offer/version, and target environment
- explicit variables and prerequisites
- factual accuracy, promises, legal/policy/platform constraints, and current verification
- privacy, client-specific details, rights, and permission
- tested/reviewed status and approver
- failure/misuse boundaries
- whether any source wording is being reused beyond quotation rights

If any material condition is missing, use adapt-required. Explain the missing conditions and do not invent approval.
```

## Output Promotion Review

```text
Review whether this generated output contains a durable reusable unit.

Promote only units that:
- solve a recurring problem and stand independently
- link to provenance, supporting assets, sources, and evidence
- have explicit role/truth/preservation/reuse
- have independent scope dimensions and representative retrieval questions
- remove or restrict private/context-specific details
- include boundaries, conflicts, counterexamples, and failure cases
- have user/reviewer approval where direct wording or policy requires it

Keep the rest as an output artifact. Do not promote polished wording merely because it sounds complete. Set explicit promotion status on promoted generated assets.
```

## Retrieval Shortlist Review

```text
Given a deterministic machine-index shortlist and the user's task:

1. verify selected root and privacy boundary
2. remove assets with poor industry/responsibility/audience/scenario fit
3. remove do-not-use, stale direct-use, deprecated, or unauthorized assets
4. inspect truth, preservation, reuse, confidence, maturity, evidence, freshness, and conflicts
5. choose the smallest sufficient set
6. decide which claims require evidence/source escalation
7. explain any missing knowledge or uncertainty

Treat retrieval score as a routing signal, never as truth, permission, or quality.
```

## Semantic Knowledge-Base Audit

```text
Audit what deterministic lint cannot prove.

Check:
- whether logic maps genuinely cover whole-source reasoning
- whether assets over-card fragments or duplicate each other
- whether source claims are disguised as facts
- whether models claim maturity beyond evidence
- whether procedures omit decisions, failure recovery, or environmental assumptions
- whether talk tracks confuse source wording, generated adaptation, and approved copy
- whether retrieval queries reflect real tasks
- whether industry/responsibility/root boundaries are coherent
- whether private information leaks through derived assets or indexes
- whether conflicts/counterexamples are hidden
- whether recent context is a bounded handoff rather than a growing history dump

Return concrete repairs, affected assets, evidence, and priority. Do not recommend folder churn without retrieval benefit.
```

## Final Closeout Review

```text
Before finishing, prove:
- originals remain unchanged using the strongest available integrity evidence
- raw extraction, corrected text, source maps, and reusable assets remain distinct
- complete source logic precedes fragment extraction
- exact wording/data retain precise anchors
- source meaning is not mislabeled as truth
- logic maps remain analyze-only
- verified facts retain verification records
- direct-use assets satisfy approval/context/testing/freshness
- generated durable assets passed promotion review
- independent scope dimensions and retrieval questions are usable
- source IDs, duplicates, versions, conflicts, privacy, and rights are explicit
- manifest, human routes, source registry, and generated index are current
- deterministic doctor/index checks pass
- recent context and maintenance log make continuation obvious
```
