# Data Analysis — `data/raw/`

## Dataset Overview

| Metric | Value |
|---|---|
| Files | 254 |
| Format | `.txt` (plain text, parsed from HTML — formatting lost) |
| Total words | ~173k |
| Approx. tokens | ~230k |
| Duplicates | 0 |

All files are Deutsche Telekom press releases. 245/254 explicitly mention "Telekom" or "Deutsche Telekom", 73 mention "T-Systems".

## Content Statistics

| Metric | Min | Median | Mean | Max |
|---|---|---|---|---|
| Characters | 989 | 3,960 | 4,464 | 16,552 |
| Words | 159 | 601 | 681 | 2,510 |
| Lines | 1 | 9 | 31 | 893 |
| Sections (split on blank lines) | 1 | 5 | 16 | 447 |

### Word Count Distribution

| Range | Files |
|---|---|
| 0–200 | 1 |
| 200–400 | 47 |
| 400–600 | 77 |
| 600–800 | 66 |
| 800–1,000 | 33 |
| 1,000–1,500 | 18 |
| 1,500–2,000 | 6 |
| 2,000+ | 6 |

Most files (190/254) fall in the 200–800 word range — fairly short press releases. The 6 files above 2,000 words are quarterly/annual financial reports with tabular data.

## Structure Patterns

- **153 files** have heading-like sections (short standalone lines acting as sub-headings between paragraphs).
- **183 files** contain direct quotes with speaker attribution (`says ...`).
- **44 files** are a single unbroken paragraph (no section structure).
- **28 files** contain the artifact: `"Sorry, we are not allowed to show you this content due to your cookie settings."` — a scraping leftover that should be cleaned.

### Typical structure

```
[Opening paragraph — lead summary]

[Section heading]

 [Body paragraph with details]

[Section heading]

 [Body paragraph, often with a quote]
```

Some body paragraphs have a leading space (` `) — another HTML parsing artifact.

### Outlier files (financial reports)

Files like `198.txt`, `62.txt`, `109.txt`, `163.txt` have 800+ lines. These are quarterly earnings reports with many short lines from parsed HTML tables (numbers, labels on separate lines). They need special handling during chunking.

## Topic Categories

Files can span multiple categories (keyword-based heuristic — counts are approximate):

| Category | Files |
|---|---|
| Partnerships / Investments | 193 |
| Product / Service Announcements | 139 |
| Security / Data Protection | 93 |
| Financial / Quarterly Reports | 79 |
| Sustainability | 64 |
| AI / Digital | 62 |

## Metadata Patterns

### Year / Publication Date

- 177/254 files mention at least one year (2020–2025 range).
- 77 files (30%) contain no year at all.
- File index loosely correlates with recency (lower index ≈ newer), but it's noisy.
- The most-common year in the text is a reasonable proxy for publication year but not fully reliable — best extracted by LLM.

### Business Segment

Clear signal from explicit mentions:

| Segment | Files |
|---|---|
| T-Systems | 73 |
| Telekom Deutschland | 66 |
| T-Mobile US | 24 |
| Deutsche Telekom Group (no specific segment) | remainder |

### Document Type (heuristic, mutually exclusive)

| Type | Files |
|---|---|
| General Press Release | 114 |
| Product / Service Launch | 46 |
| Deal / Partnership | 35 |
| Financial Report | 31 |
| Award / Recognition | 28 |

### Recommended Metadata to Extract

Have the LLM extract three fields per document during the chunking step:

| Field | Type | Values |
|---|---|---|
| `year` | `int \| null` | Publication year inferred from content |
| `business_segment` | `enum` | `t_systems`, `telekom_deutschland`, `t_mobile_us`, `deutsche_telekom_group` |
| `document_type` | `enum` | `financial_report`, `product_launch`, `partnership`, `award`, `general` |

These go into the `Document` table in SQLite alongside the source text, and are inherited by each `Chunk`. They can be used as pre-filters in hybrid search and are queryable via the SQL tool on the backend.

## Implications for the Pipeline

1. **Cleaning step needed**: Strip the cookie-consent artifact (28 files) and leading spaces on paragraphs.
2. **LLM chunking is appropriate**: Since HTML formatting is lost, rule-based splitting on blank lines alone won't produce semantic chunks — especially for single-paragraph files (44) and financial reports with fragmented table data. LLM should infer meaningful boundaries.
3. **Financial report handling**: The 6 large financial reports should likely be chunked differently (tables, KPIs, narrative sections). Consider flagging these as a distinct document type.
4. **Chunk size target**: Given median file length of ~600 words, many files may be 1–3 chunks. Aim for chunks of ~200–400 words for retrieval, with the larger surrounding context stored for LLM (small-to-big).
5. **RAPTOR summaries**: Useful for questions like "How is Deutsche Telekom performing overall?" or "What are Telekom's sustainability goals?" — abstractive summaries across many documents.
6. **Metadata extraction**: LLM should extract `year`, `business_segment`, and `document_type` per document. Stored in the `Document` table and used for retrieval filtering and SQL queries.
7. **Corpus size is small**: ~230k tokens total. The entire corpus fits in a single LLM context window. This is good for RAPTOR (cheap to summarize) but means retrieval quality matters more than scale optimization.
