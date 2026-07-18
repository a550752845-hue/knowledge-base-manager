# Douyin Indexed Transcript Adapter

Use this reference only when the source folder contains artifacts produced by `$douyin-video-transcript` or an equivalent indexed Douyin workflow.

## Ownership

- Transcript capture/ASR workflow owns media capture, transcription, Markdown, and JSONL generation.
- This skill owns source registration, whole-source understanding, reusable assets, provenance, indexes, and governance.

Do not modify capture outputs by default.

## Read Order

Prefer:

```text
summary.json
-> index.jsonl
-> segment_ranges.jsonl
-> segments.jsonl
-> transcript Markdown only when needed
```

- `summary.json`: artifact paths, bundle metadata, and read budget.
- `index.jsonl`: video-level identity and metadata; select candidates here.
- `segment_ranges.jsonl`: no-body range catalog; plan coverage here.
- `segments.jsonl`: bounded transcript text; read selected IDs/ranges.
- `.md`: exact formatting/frontmatter, full-source verification, or explicit request.

Use `aweme_id` as canonical source ID when available.

Register the bundle representations in the machine source registry. Keep capture paths external/read-only when that is how the transcript workflow owns them. For any workflow writing near bundle files, snapshot and verify bundle integrity with `scripts/kb.py source`.

## Single Video

Reconstruct the complete video logic before carding:

- problem and audience;
- premises and claims;
- evidence/examples;
- sequence and transitions;
- conclusion and CTA;
- neighboring context around useful excerpts.

If the full video fits the bundle read budget, read all ranges. Otherwise process ranges in order and merge into one source map.

The merged map must cover the opening, middle reasoning, conclusion, and CTA/action intent. A list of selected segment summaries is not a complete video logic map.

## Batch Or Account

1. Inventory from `index.jsonl` without opening every transcript.
2. Sample representative/high-value videos using title, date, duration, metadata, and range catalog.
3. Build/update the account source profile.
4. Deep-process selected sources.
5. Register repetitive/low-value videos without duplicate assets.
6. Reassess topic drift, duplicate cards, and model candidates every 20 processed videos.

## Source Representations

Treat capture artifacts as source representations:

```text
media/original URL       source record
raw ASR segments         exact raw extraction
transcript Markdown      rendered derivative
corrected transcript     separate corrected derivative, if created
source/logic map         derived analysis
```

Do not confuse ASR wording with verified exact speech. Mark uncertainty when names, numbers, or terms may be misrecognized.

## Asset Defaults

- Whole-video logic map: `analyze-only`.
- Exact quote: `quote-only`, anchored to timestamps/segment IDs.
- Knowledge claim/model: `analyze-only`, source-backed with maturity.
- Hook/script/talk track: `adapt-required` by default.
- Approved production wording: `direct-use` only after review and context fields are complete.

Classify `industries`, `responsibilities`, `topics`, and representative `retrieval_queries` independently. Do not infer that every Douyin source belongs to short-video operations; the subject matter may belong to any industry or responsibility.

Store analysis and reusable assets inside the managed knowledge-base root, not in the transcript bundle.

## Required Links

Durable assets should retain, when available:

- `aweme_id`;
- author/account;
- original Douyin URL;
- transcript Markdown path;
- selected segment/range IDs;
- `segments.jsonl` and `segment_ranges.jsonl` paths;
- exact timestamps for quotations.

After creating or changing durable assets, rebuild the selected root's machine asset index and run strict doctor/index checks. Never write analysis back into the capture bundle merely to mark it processed.
