# Templates

Adapt these templates to the root manifest and local role aliases. Preserve the four-axis contract and independent scope dimensions. Remove fields that genuinely do not apply; never invent values to make a template look complete.

## Workspace Root Registry

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
    }
  ]
}
```

## Root Manifest

Prefer generating this with `scripts/kb.py init`.

```json
{
  "schema_version": 3,
  "knowledge_base_id": "stable-id",
  "name": "Human name",
  "scope": {
    "type": "general",
    "industries": [],
    "responsibilities": []
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
  "source_roots": [],
  "freshness_policy": {
    "high_days": 30,
    "medium_days": 180,
    "low_days": 3650
  }
}
```

## Base Reusable Asset

```markdown
---
schema_version: 3
id: "claim-stable-id"
type: knowledge-card
knowledge_role: claim
truth_status: source-claim
preservation: normalized
reuse_mode: analyze-only
status: draft
scope_type: general
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: ""
relations: []
confidence: medium
maturity: seed
evidence_strength: weak
time_sensitivity: low
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: ""
summary: ""
---

# 完整判断句

## 核心内容

## 来源与证据

## 适用范围

## 边界、冲突与反例

## 相关资产

## 可回答的问题
```

## Machine Source Registry Row

One JSON object per line:

```json
{"source_id":"src-stable-id","title":"来源标题","source_type":"transcript","author_or_owner":"","publication_or_platform":"","original_date":"YYYY-MM-DD","captured_at":"YYYY-MM-DDThh:mm:ssZ","source_url":"","external_id":"","preferred_read_path":"","all_known_paths":[],"representations":[],"versions":[],"content_hash":"sha256:","rights_or_permission":"","sensitivity":"internal","status":"active"}
```

## Human Source Registry

```markdown
# 来源注册表

机器可读主表：`来源注册表.jsonl`。

| source_id | 标题 | 类型 | 作者/所有者 | 日期/版本 | 首选读取路径 | sensitivity | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 重复与版本关系

| source_id | 关系 | 相关 ID/路径 | 判断依据 | 处理 |
| --- | --- | --- | --- | --- |
```

## Source / Logic Map

```markdown
---
schema_version: 3
id: "logic-src-id"
type: source-map
knowledge_role: logic-map
truth_status: source-claim
preservation: derived
reuse_mode: analyze-only
status: active
scope_type: general
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: [src-id]
source_anchors: []
provenance: "source-registry:src-id"
relations: []
confidence: medium
maturity: seed
evidence_strength: weak
time_sensitivity: low
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: ""
summary: ""
grade: A
coverage:
  beginning: true
  middle: true
  conclusion: true
  action_intent: true
---

# 来源名 - 来源解析

## 来源身份、版本与表示层

## 原始结构与覆盖范围

## 问题、受众与语境

## 前提、定义与隐藏假设

## 主张层级

## 证据、案例、反例与修辞

## 完整推理链条与转折

## 结论、行动意图与 CTA

## 逻辑质检

- 证据是否支持主张：
- 缺失步骤或跳跃：
- 内部矛盾或变化：
- 来源主张与可核事实：
- 不确定、ASR/OCR/解析错误：
- 未覆盖范围：

## 话术候选（与逻辑分开）

## 可提炼资产

| 候选 | role | truth | preservation | reuse | 是否创建 | 理由 |
| --- | --- | --- | --- | --- | --- | --- |

## 不应沉淀的内容
```

## Claim Or Principle

```markdown
---
schema_version: 3
id: "claim-stable-id"
type: knowledge-card
knowledge_role: claim
truth_status: source-claim
preservation: normalized
reuse_mode: analyze-only
status: active
scope_type: cross-domain
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: [src-id]
source_anchors: []
provenance: "source-map:logic-src-id"
relations: []
confidence: medium
maturity: seed
evidence_strength: weak
time_sensitivity: low
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: ""
summary: ""
---

# 完整观点句

## 核心判断与机制

## 在来源逻辑中的位置

## 来源与证据

## 适用范围

## 边界、冲突、反例与风险

## 可回答的问题

## 相关资产
```

For a synthesized principle, change `knowledge_role` to `principle`, `truth_status` to `model-synthesis`, and link every contributing asset/source.

## Verified Fact

```markdown
---
schema_version: 3
id: "fact-stable-id"
type: fact
knowledge_role: fact
truth_status: verified-fact
preservation: normalized
reuse_mode: reference-only
status: active
scope_type: industry
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: ""
relations: []
confidence: high
maturity: candidate
evidence_strength: strong
time_sensitivity: medium
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: "YYYY-MM-DD"
verification_method: ""
verification_sources: []
valid_scope: ""
summary: ""
---

# 事实标题

## 标准化事实

## 验证方法与依据

## 时间、版本、地区与适用范围

## 冲突与易混淆点
```

## Model

```markdown
---
schema_version: 3
id: "model-stable-id"
type: model
knowledge_role: model
truth_status: model-synthesis
preservation: derived
reuse_mode: analyze-only
status: active
scope_type: cross-domain
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: ""
relations: []
confidence: medium
maturity: candidate
evidence_strength: moderate
time_sensitivity: low
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: "YYYY-MM-DD"
summary: ""
validation_records: []
---

# 模型名

## 定义与要解决的问题

## 结构、变量与关系

## 诊断/决策步骤

## 适用场景与前置条件

## 证据结构与来源多样性

## 案例、反例与冲突

## 边界与失败条件

## 可交付形式

## 证据缺口与升级/降级/拆分条件

## 可回答的问题
```

## Procedure / SOP

```markdown
---
schema_version: 3
id: "procedure-stable-id"
type: procedure
knowledge_role: procedure
truth_status: model-synthesis
preservation: normalized
reuse_mode: adapt-required
status: active
scope_type: responsibility
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: ""
relations: []
confidence: medium
maturity: candidate
evidence_strength: moderate
time_sensitivity: medium
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: "YYYY-MM-DD"
summary: ""
tested_status: untested
---

# SOP 名称

## 目标与验收标准

## 前置条件与输入

## 步骤

## 决策点与分支

## 输出标准

## 失败状态、回滚与恢复

## 例外、边界与版本依赖

## 验证记录
```

## Talk Track / Script / Prompt

```markdown
---
schema_version: 3
id: "talk-stable-id"
type: talk-track
knowledge_role: talk-track
truth_status: generated
preservation: derived
reuse_mode: adapt-required
status: draft
scope_type: responsibility
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: ""
relations: []
confidence: medium
maturity: seed
evidence_strength: weak
time_sensitivity: medium
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: ""
summary: ""
audience: ""
scenario: ""
goal: ""
variables: []
tone: ""
boundary: ""
compliance_risk: ""
rights_or_permission: ""
tested_status: untested
promotion_status: not-reviewed
---

# 话术/脚本/提示词名称

## 使用条件

## 正文或模板

## 变量说明

## 不适用边界与禁止承诺

## 来源、逻辑机制与改编说明

## 测试/审核记录
```

For direct use, set `status: approved`, `reuse_mode: direct-use`, `promotion_status: approved`, a current `last_verified`, and complete every review field.

For an approved sensitivity downgrade, also record `anonymization_status: approved` or `declassification_status: approved` together with `privacy_reviewed_by`, `privacy_review_reason`, and `privacy_reviewed_at`. A status flag alone is not approval evidence.

## Exact Evidence

```markdown
---
schema_version: 3
id: "evidence-src-id-anchor"
type: evidence
knowledge_role: evidence
truth_status: source-record
preservation: anchored
reuse_mode: quote-only
status: active
scope_type: general
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: [src-id]
source_anchors:
  - type: timestamp
    value: "00:00-00:00"
provenance: "source-registry:src-id"
relations: []
confidence: medium
maturity: seed
evidence_strength: moderate
time_sensitivity: low
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: "YYYY-MM-DD"
summary: ""
supports: []
relation: supports
---

# 证据标题

## 精确内容

## 来源锚点与邻近语境

## 支撑、冲突或反驳什么

## 权利、证据与适用边界
```

## Output

```markdown
---
schema_version: 3
id: "output-date-stable-id"
type: output
knowledge_role: output
truth_status: generated
preservation: derived
reuse_mode: reference-only
status: draft
scope_type: project
primary_domain: ""
domains: []
industries: []
responsibilities: []
topics: []
retrieval_queries: []
audiences: []
languages: [zh-CN]
source_ids: []
source_anchors: []
provenance: "task-or-conversation-id"
relations: []
confidence: medium
maturity: seed
evidence_strength: weak
time_sensitivity: medium
sensitivity: internal
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
last_verified: ""
summary: ""
promotion_status: not-reviewed
---

# 输出名称

## 任务、受众与约束

## 正文

## 使用的知识资产与来源

## 待验证内容、冲突与风险

## 晋升判断
```

## Recent Context

```markdown
# 最近上下文

本文件是有界交接快照，不是永久日志。

## 最近完成

| 日期 | 动作 | 影响范围 | 关键变化 |
| --- | --- | --- | --- |

## 下次先读

| 场景 | 首读 | 再读 | 注意 |
| --- | --- | --- | --- |

## 当前待决

| 事项 | 风险 | 建议动作 |
| --- | --- | --- |
```

## Maintenance Log

```markdown
# 维护日志

| 日期 | 动作 | 文件/范围 | 原因 | 验证 | 残余风险 |
| --- | --- | --- | --- | --- | --- |
```
