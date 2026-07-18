# Source Preservation

Use this reference whenever material enters the knowledge base or work depends on exact wording, numbers, versions, duplicate identity, rights, privacy, or provenance.

## Source Principle

Treat each original as immutable evidence. Perform corrections, annotations, analysis, and restructuring in derivative files. A source may live inside the managed root or remain in an external read-only location.

An external source is valid when the machine source registry records stable identity, all known representations, a preferred read path, access/sensitivity, and current status.

## Representation Stack

Keep representations distinct:

| Representation | Purpose | Mutation rule |
| --- | --- | --- |
| Original | Native binary/text/media/web capture/spreadsheet | Never modify by default |
| Raw extraction | Parser, OCR, ASR, scraper, or export output | Preserve exactly for audit |
| Corrected derivative | Human/AI-corrected readable text | New file/version; never overwrite raw extraction |
| Structured source map | Sections, timestamps, tables, entities, logic | Derived analysis linked to anchors |
| Reusable asset | Fact/claim/model/procedure/talk track/evidence | Governed by four-axis contract |

Never call corrected text or normalized Markdown the original. Record correction method, agent/person, date, and uncertainty.

## Machine Source Registry

Assign one canonical `source_id` per real-world source, not per copied file. Use JSONL as the deterministic identity layer.

Recommended record:

```json
{
  "source_id": "src-stable-id",
  "title": "Source title",
  "source_type": "transcript",
  "author_or_owner": "owner",
  "publication_or_platform": "platform",
  "original_date": "YYYY-MM-DD",
  "captured_at": "YYYY-MM-DDThh:mm:ssZ",
  "source_url": "https://...",
  "external_id": "stable-platform-id",
  "preferred_read_path": "D:/sources/file.md",
  "all_known_paths": ["D:/sources/file.md"],
  "representations": [],
  "versions": [],
  "content_hash": "sha256:...",
  "rights_or_permission": "internal-use",
  "sensitivity": "private",
  "status": "active"
}
```

Use a stable platform/publication ID when available. Otherwise create a local ID from durable identity plus a short stable suffix. Never change source ID merely because a title/path changes.

## Source Integrity Baseline

When proving non-modification matters, hash sources before and after work:

```text
python <skill-root>/scripts/kb.py source snapshot \
  --source <source-path> \
  --output <knowledge-root>/_meta/source-integrity.json \
  --apply

python <skill-root>/scripts/kb.py source verify \
  --manifest <knowledge-root>/_meta/source-integrity.json \
  --check-new --json
```

- Store the baseline outside immutable source directories.
- Hash actual file bytes, not normalized text.
- Record symlink targets without following them by default.
- Treat changed, missing, and unexpected files as separate findings.
- A current hash without a prior baseline cannot prove that no earlier modification occurred.
- Do not commit private absolute source paths to a public repository.

## Exact Preservation

Preserve exact wording and anchors for:

- contracts, policies, standards, regulations, formal definitions;
- numbers, dates, prices, measurements, formulas, table rows;
- quoted/disputed/sensitive/high-stakes claims;
- wording whose phrasing is itself studied or cited;
- approved scripts/copy where exact language matters;
- evidence supporting or rejecting a model.

Exact evidence should record:

```yaml
source_ids: [src-id]
source_anchors:
  - type: page | section | timestamp | segment | row | paragraph | url-fragment
    value: ""
preservation: anchored
reuse_mode: quote-only | reference-only
```

Never create a quotation from a paraphrase. Never strip neighboring context needed to preserve meaning.

## Transcript Sources

Preserve when available:

- media bytes or stable media URL;
- platform/video/audio ID;
- raw ASR segments and engine/model metadata;
- timestamps, segment/range IDs, and speaker labels;
- transcript Markdown/rendered derivative;
- corrected transcript as a separate version;
- uncertainty markers for names, numbers, jargon, and overlapping speech.

Do not promote ASR wording to an exact quotation or direct-use script without checking audio/context and obvious recognition errors.

Analyze the complete speaking logic after preservation; do not rewrite the transcript into a smooth narrative and then treat that narrative as source wording.

## Structured Documents

For PDF, Word, article, book, report, slide deck, spreadsheet, or webpage, preserve meaningful native structure:

- heading hierarchy and section order;
- page/section/slide/sheet/row anchors;
- tables with row/column meaning;
- lists, footnotes, captions, formulas, figures, references;
- document version, edition, effective date, author, and owner;
- extraction limitations such as missing images, OCR uncertainty, hidden sheets, comments, tracked changes, or layout loss.

Do not split a structured document into arbitrary equal chunks when native sections define better units. Do not flatten tables into prose when row/column relationships matter.

## Web Sources

URLs are mutable. For important web evidence, record:

- canonical URL and final resolved URL;
- page title, author/publisher, publication/update date;
- capture time and capture method;
- exact excerpt with section/fragment;
- archived snapshot or local capture path when rights permit;
- content hash of the capture;
- access failures, paywall, dynamic content, or missing media.

Treat a later page revision as a new version, not as proof the prior capture never existed.

## Duplicate And Version Resolution

Do not merge files because titles match. Compare:

- source/external IDs and canonical URLs;
- byte/content hashes;
- author, date, edition, duration, and structure;
- exact and fuzzy content similarity;
- correction/translation/abridgment context.

Use explicit relations:

```text
same-source
duplicate-copy
new-version
corrected-derivative
abridged-version
translation
supersedes
disputed-match
```

Choose a preferred read path without deleting alternatives. Preserve old versions needed for audit.

## Missing Or Unreadable Sources

Do not fabricate source content from filenames or metadata. Register:

- `status: missing` for unavailable files;
- parsing/extraction error details;
- what representations remain available;
- whether derived assets are still supportable;
- retry or recovery path.

Downgrade or quarantine assets whose only supporting source becomes unavailable or unreadable.

## Privacy, Rights, And Sensitivity

Default client, customer, employee, internal business, unpublished, and personal material to `private` or `restricted`.

- Do not copy private names, metrics, screenshots, or proprietary examples into broadly reusable assets.
- Prefer anonymized mechanisms and conclusions.
- Record permission and usage constraints with source identity.
- Do not mark copyrighted wording direct-use because it is useful.
- Separate quotation rights from knowledge reuse rights.
- Do not lower derived sensitivity without approved anonymization/declassification.
- Exclude restricted assets from broad indexes when local policy requires it.

## Source Intake Gate

Before analysis, verify:

- source identity can be assigned or reused;
- original/stable pointer exists or missing status is explicit;
- raw, corrected, structured, and reusable representations are not confused;
- best practical anchors are available;
- duplicate/version status is explicit;
- privacy, rights, and permission boundaries are visible;
- no original must be modified to record processing state;
- integrity evidence is strong enough for the risk of the operation.
