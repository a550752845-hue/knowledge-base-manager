# Logic Analysis And Asset Extraction

Use this reference to understand a source as a complete unit, distinguish source meaning from truth, and decide what durable knowledge or executable assets justify future retrieval cost.

## Source Map Before Assets

Create one complete source map for every deeply processed source or coherent batch. It is the bridge between immutable evidence and reusable assets.

Do not start by collecting catchy sentences, claims, hooks, or cards. First determine what the source is doing as a whole.

## Transcript Logic Reconstruction

For a transcript, reconstruct:

1. **Situation**: real problem, intended audience, occasion, assumed context, and speaker goal.
2. **Premises**: explicit premises, hidden assumptions, definitions, and shared beliefs.
3. **Claim hierarchy**: thesis, supporting claims, subclaims, exceptions, and qualifications.
4. **Evidence**: facts, examples, anecdotes, demonstrations, comparisons, authorities, and counterexamples.
5. **Reasoning**: cause/effect, analogy, induction, deduction, contrast, categorization, sequence, diagnosis, or persuasion.
6. **Flow**: opening, transitions, reframes, objections, emotional turns, escalation, conclusion, and CTA.
7. **Rhetoric**: hooks, repetition, stories, identity cues, urgency, social proof, framing, and audience manipulation.
8. **Quality**: evidence fit, missing steps, unsupported jumps, contradictions, overgeneralization, alternative explanations, and ASR uncertainty.
9. **Action intent**: what the audience is supposed to think, feel, decide, or do.
10. **Extraction judgment**: reusable mechanisms, exact wording candidates, and content that should not be promoted.

Do not smooth over contradictions merely to make the map elegant. Preserve the source's actual sequence and shifts.

## Structured Document Reconstruction

Preserve:

- heading/section hierarchy and document purpose;
- definitions, key terms, scope, and assumptions;
- claims and local supporting sections;
- tables, figures, formulas, examples, references, and appendices;
- procedures, prerequisites, decision rules, outputs, and exceptions;
- conclusions, caveats, unresolved questions, and revision history;
- page/section/slide/sheet/row anchors;
- extraction/layout limitations.

## Long-Source Merge

When the source exceeds practical read limits:

1. inventory structural ranges without summarizing them away;
2. process ranges in original order;
3. preserve range IDs, neighboring context, local claims, evidence, and transitions;
4. maintain a running claim/relation ledger;
5. merge into one source-level outline and reasoning chain;
6. reconcile repeated, refined, reversed, or contradictory claims;
7. verify the final map covers beginning, middle, conclusion, and action intent;
8. extract assets only from the merged understanding.

A list of chunk summaries is an intermediate artifact, not a complete source map.

## Logic-Map Contract

Use:

```yaml
knowledge_role: logic-map
truth_status: source-claim
preservation: derived
reuse_mode: analyze-only
source_ids: [src-id]
```

A logic map may describe exact evidence but should link to anchored evidence rather than pretend its own paraphrase is exact. It must never be reused directly as a script or presented as verified truth.

## Epistemic Boundary

Keep these objects explicit:

| Object | Meaning | Typical language |
| --- | --- | --- |
| Source record | The source literally contains this wording/data | "The source records..." |
| Source claim | The author/source asserts this | "The author argues..." |
| Verified fact | Independent/authoritative verification supports this | "Verified as of..." |
| Model synthesis | The knowledge base combines assets into a framework | "The model suggests..." |
| User preference | The user explicitly wants this rule/style/choice | "The user prefers..." |
| Generated output | A model produced this for a task | "Generated for..." |

Never silently convert source claim to verified fact, model synthesis to evidence, or polished output to durable knowledge.

## Wording Boundary

Separate three layers even when they appear in the same source:

1. **Exact wording**: preserve and anchor; normally quote-only.
2. **Logical/rhetorical mechanism**: describe in derived language; analyze-only or adapt-required.
3. **New execution wording**: generated for a specific audience/scenario; adapt-required until reviewed.

Do not lightly paraphrase copyrighted or private wording and then label it original execution copy. Record adaptation provenance and boundaries.

## Asset Decision Table

| Candidate value | Create | Default reuse |
| --- | --- | --- |
| Exact wording, number, clause, definition, table row | Anchored evidence/quote | `quote-only` or `reference-only` |
| Complete understanding of source argument | Logic map | `analyze-only` |
| Independently checked normalized fact | Fact asset | `reference-only` |
| Reusable source viewpoint | Claim | `analyze-only` |
| Portable judgment with scope/boundary | Principle | `analyze-only` |
| Multi-source diagnostic/decision framework | Model | `analyze-only` |
| Repeatable steps with inputs/failures | Procedure | `adapt-required` |
| Script, phrase, prompt, template | Talk track | `adapt-required` |
| Reviewed production wording | Approved talk track | `direct-use` within recorded contract |
| Case, data point, failure, counterexample | Evidence | `reference-only` or `quote-only` |
| Author/account/institution characteristics | Source profile | `analyze-only` |
| One-off answer, plan, draft, deliverable | Output | `reference-only` until promotion |

Create nothing when future use is unclear, context cannot be preserved, an existing asset already covers it, or retrieval cost exceeds expected value.

## Facts And Verification

Use `knowledge_role: fact` only with `truth_status: verified-fact` and record:

- verification method or verification sources;
- verification date;
- valid time/version/jurisdiction scope;
- source IDs and anchors;
- uncertainty and known conflicts.

If only one unverified source supports the statement, use `claim + source-claim` even when the wording sounds factual.

## Claims And Principles

Name a claim/principle as a complete judgment, not a vague noun.

A principle should include:

- statement;
- intended problem and scope;
- mechanism/reasoning;
- evidence and source basis;
- exceptions, failure cases, and counterexamples;
- relation to competing principles;
- representative retrieval questions.

Keep source-specific viewpoints as claims unless multi-source synthesis and boundaries justify a principle.

## Models

Create a model when it organizes several claims, evidence items, procedures, or decisions into a reusable structure.

Record:

- problem and diagnostic question;
- components and causal/decision relations;
- prerequisites and scope;
- supporting and conflicting evidence;
- counterexamples and failure conditions;
- confidence, evidence strength, and maturity;
- current evidence gaps;
- upgrade, downgrade, split, merge, and retirement conditions;
- deliverable forms and retrieval questions.

A detailed model is not mature merely because it is internally coherent.

## Procedures And SOPs

Require:

- intended outcome;
- prerequisites and inputs;
- ordered steps;
- decisions and branch conditions;
- expected outputs and acceptance criteria;
- failure states, rollback, and recovery;
- boundaries, exceptions, environment/version dependencies;
- evidence/experience basis;
- validation status and last verification.

Default to `adapt-required`. Use direct-use only when approved for the target environment and current prerequisites.

## Talk Tracks, Scripts, Prompts, And Templates

Classify:

- `source-quote`: exact, anchored, quote-only;
- `editable-template`: variables and adaptation rules;
- `approved-copy`: reviewed wording for a known audience/scenario/version.

Required for direct use:

```yaml
knowledge_role: talk-track
reuse_mode: direct-use
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

Do not mark direct-use when facts/promises are unverifiable, private details leak, context is hidden, rights are unclear, the asset is stale, or the target differs.

## Output Promotion

Keep generated work under output until review. Promote only a reusable unit that:

- solves a recurring problem;
- stands independently;
- links to provenance and support;
- has explicit role/truth/preservation/reuse;
- records scope, retrieval questions, boundaries, and failure cases;
- removes or restricts private/context-specific details;
- has user/reviewer approval where wording or policy requires it.

Set `promotion_status: approved | promoted` on generated durable assets. Preserve the original output separately when audit/history matters.

## Avoid Over-Carding

Prefer:

- one source map per coherent source;
- one claim/principle per genuinely reusable judgment;
- one model per coherent multi-asset framework;
- one procedure per distinct outcome and environment;
- one talk track per audience-scenario-goal contract;
- one evidence asset per independently useful exact item/case/counterexample.

Consolidate candidates that differ only in wording. Use variants inside one template when their mechanism and contract are the same.

## Final Extraction Review

Before saving assets, ask:

- Did I analyze the whole source, including conclusion and transitions?
- Is this exact evidence, source meaning, claim, verified fact, synthesis, procedure, wording, or output?
- Does wording matter, or only logic/structure?
- May future AI quote, analyze, adapt, use directly, reference, or not use it?
- Which source ID/anchor/provenance supports it?
- Which industry, responsibility, domain, topic, audience, and real question should retrieve it?
- What would make it fail, become stale, violate rights/privacy, or mislead?
- Is an existing asset a duplicate, conflict, broader/narrower version, or better home?
- Is this valuable enough to justify future retrieval and maintenance cost?
