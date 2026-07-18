# Machine Contract

Use this reference when initializing a root, resolving directory aliases, validating metadata, building indexes, or optimizing future AI retrieval.

## Authority Order

Use this order when files disagree:

1. immutable original source for exact source content;
2. `_meta/knowledge-base.json` for root identity, role paths, freshness policy, and machine routes;
3. asset frontmatter for asset identity, epistemic status, preservation, reuse, scope, provenance, and lifecycle;
4. machine source registry for source identity and representation paths;
5. generated asset index for retrieval shortlisting;
6. Markdown management pages for human explanation and navigation;
7. recent context for current handoff state.

The asset index is generated. Never edit it as the source of truth.

## Workspace Registry

For a workspace with several managed roots, prefer a machine registry at:

```text
<workspace-root>/_meta/knowledge-base-registry.json
```

Recommended shape:

```json
{
  "schema_version": 1,
  "roots": [
    {
      "knowledge_base_id": "general-methods",
      "path": "knowledge-bases/general-methods",
      "scope_type": "general",
      "industries": [],
      "responsibilities": [],
      "sensitivity": "internal",
      "status": "active"
    },
    {
      "knowledge_base_id": "healthcare-growth",
      "path": "knowledge-bases/healthcare-growth",
      "scope_type": "industry",
      "industries": ["healthcare"],
      "responsibilities": ["growth", "sales"],
      "sensitivity": "private",
      "status": "active"
    }
  ]
}
```

Keep the existing Markdown root registry as the human view when present. Do not require a specific workspace folder name.

## Root Manifest

Each schema-v3 managed root should have:

```text
<root>/_meta/knowledge-base.json
```

Minimum example:

```json
{
  "schema_version": 3,
  "knowledge_base_id": "healthcare-growth",
  "name": "Healthcare Growth",
  "scope": {
    "type": "industry",
    "industries": ["healthcare"],
    "responsibilities": ["growth", "sales"]
  },
  "paths": {
    "ai_entry": "00-AI入口/AI首读.md",
    "asset_index": "00-AI入口/资产索引.jsonl",
    "management_rules": "_meta/知识库管理规则.md",
    "recent_context": "_meta/最近上下文.md",
    "source_registry_human": "_meta/来源注册表.md",
    "source_registry_machine": "_meta/来源注册表.jsonl",
    "maintenance_log": "_meta/维护日志.md"
  },
  "role_paths": {
    "ai_entry": "00-AI入口",
    "source": "10-原始证据",
    "source_analysis": "20-来源解析",
    "knowledge": "30-知识对象",
    "execution": "40-可执行资产",
    "evidence": "50-证据验证",
    "output": "60-输出成品",
    "management": "_meta"
  },
  "source_roots": [
    {
      "alias": "raw-transcripts",
      "path": "D:/sources/transcripts",
      "mode": "read-only",
      "sensitivity": "private"
    }
  ],
  "freshness_policy": {
    "high_days": 30,
    "medium_days": 180,
    "low_days": 3650
  }
}
```

Paths may use any language or local naming scheme. Resolve semantic roles through `role_paths`; do not infer contracts from names when the manifest exists.

Validate manifest shape against `knowledge-base-manifest.schema.json` on every schema-v3 `doctor` run. Treat missing required fields and wrong types as errors.

## Machine Source Registry

Use JSONL so one source record can be read or updated without parsing a Markdown table:

```json
{"source_id":"src-interview-20260715","title":"Customer interview","source_type":"transcript","author_or_owner":"research team","preferred_read_path":"D:/sources/interview.md","all_known_paths":["D:/sources/interview.md","D:/archive/interview.txt"],"versions":[],"content_hash":"sha256:...","rights_or_permission":"internal research","sensitivity":"private","status":"active"}
```

The Markdown source registry is a human view. The JSONL registry owns source identity for deterministic tools.

Validate every non-empty JSONL row against `source-registry-row.schema.json`. Keep `status` as a non-empty adapter-defined lifecycle value; keep `sensitivity` on the fixed privacy scale.

## Asset Frontmatter

Validate reusable asset metadata against `asset-frontmatter.schema.json` on every schema-v3 `doctor` run. Keep these independent scope dimensions:

```yaml
scope_type: cross-domain
primary_domain: customer-acquisition
domains: [marketing, sales]
industries: [healthcare, tourism]
responsibilities: [growth, sales]
topics: [audience-fit, trust]
retrieval_queries:
  - 如何判断内容和目标受众是否匹配
  - 首次咨询为什么没有建立信任
```

Do not use `primary_domain` as a substitute for industry or responsibility. One asset may be general, belong to several industries, or support several responsibilities.

## Generated Asset Index

Generate the index from current Markdown assets:

```text
python <skill-root>/scripts/kb.py index <root> --write --summary
```

Verify that committed or stored index state has not drifted:

```text
python <skill-root>/scripts/kb.py index <root> --check
```

Each row contains a stable asset ID, relative path, metadata needed for filtering, a short summary, and an `asset_hash`. A body or metadata change therefore makes index drift detectable.

Shortlist before model reading:

```text
python <skill-root>/scripts/kb.py query <root> \
  --intent diagnose \
  --industry healthcare \
  --responsibility growth \
  --query "为什么客户看完内容仍然不咨询" \
  --top 12 --json
```

The query score is a deterministic shortlist, not a truth score. The model still checks task fit, provenance, evidence, maturity, freshness, privacy, and reuse boundaries.

Before ranking, `query` must verify that the stored index has the skill-owned metadata header and
matches a canonical in-memory rebuild from the current assets. Reject the whole query when rows,
metadata, hashes, paths, build profile, or index ownership differ. Never return a partial shortlist
from a stale or user-authored index, because altered routing fields could weaken sensitivity,
status, role, or reuse restrictions. Rebuild with `index --write`, verify with `index --check`, and
then retry the query.

## Recent Context And Logs

- Keep `最近上下文.md` bounded to the current handoff: recent material changes, next-read routes, unresolved decisions, and immediate risks.
- Keep `维护日志.md` append-only for durable history.
- Move stable operating rules into management rules or the manifest instead of repeating them in recent context.
- Never use recent context as evidence that an original source says something.

## Legacy Roots

Do not force a legacy root to adopt these file names immediately. First map its current files to semantic roles. Add the machine manifest and indexes only after validating aliases and routes. A clean migration may use a parallel target root; an in-place migration requires explicit approval and rollback evidence.
