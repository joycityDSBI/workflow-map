# JoyCity Ontology Builder — Accuracy Spike

Tests whether the Claude API prompt template can extract ontology entities
(Objects, Links, Actions) from Korean game company event operation documents
with **≥ 70% precision**.

---

## File Structure

```
spike/
├── README.md               ← this file
├── requirements.txt
├── prompt_template.py      ← system prompt + schema + user-prompt builder
├── run_spike.py            ← reads docs, calls Claude, saves JSON results
├── evaluate.py             ← precision scoring vs. ground truth
├── sample_docs/
│   ├── event_001.md        ← 출석 체크 이벤트 운영 프로세스
│   ├── event_002.md        ← 레이드 클리어 보상 지급 프로세스
│   └── event_003.md        ← 이벤트 CS 처리 프로세스
├── ground_truth/
│   ├── event_001.json
│   ├── event_002.json
│   └── event_003.json
└── results/                ← created automatically by run_spike.py
    └── <doc_stem>.json
```

---

## Prerequisites

- Python 3.10 or higher
- An Anthropic API key with access to `claude-sonnet-5`

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set the API key

**Option A — environment variable (recommended)**

```bash
# macOS / Linux
export ANTHROPIC_API_KEY=your_key_here

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your_key_here"

# Windows cmd
set ANTHROPIC_API_KEY=your_key_here
```

**Option B — .env file**

Create `spike/.env`:

```
ANTHROPIC_API_KEY=your_key_here
```

`run_spike.py` calls `load_dotenv()` automatically, so no other setup is needed.

---

## Running the Spike

### Quick test — 3 bundled sample documents

```bash
cd spike
python run_spike.py --docs-dir sample_docs
```

Expected output:

```
Found 3 document(s) in 'sample_docs'.

Processing doc 1/3: event_001.md… OK → results/event_001.json
Processing doc 2/3: event_002.md… OK → results/event_002.json
Processing doc 3/3: event_003.md… OK → results/event_003.json

Done. 3 succeeded, 0 failed.
```

### Full spike — exported Notion docs (up to 50)

Put your Notion-exported `.md` files in a directory, then:

```bash
python run_spike.py --docs-dir /path/to/notion-export --max-docs 50
```

`--max-docs` is optional. Without it, all `.md` files in the directory are processed.

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--docs-dir PATH` | `docs/` if it exists, else `sample_docs/` | Source directory for `.md` files |
| `--max-docs N` | all | Maximum number of documents to process |

---

## Evaluating Precision

After running the spike, compare results against ground truth:

```bash
python evaluate.py
```

Sample output:

```
=== Accuracy Spike Results ===
Documents tested: 3

Objects:
  Extracted: 21   | Matched: 17   | Precision: 81.0%

Links:
  Extracted: 21   | Matched: 16   | Precision: 76.2%

Overall precision: 78.5%
RESULT: PASS ✅ (threshold: 70%)
```

The script exits with code `0` on PASS and `1` on FAIL — suitable for CI pipelines.

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--results-dir PATH` | `results/` | Directory containing Claude extraction results |
| `--ground-truth-dir PATH` | `ground_truth/` | Directory containing ground truth JSON files |

---

## Matching Rules

| Element | Match criteria |
|---|---|
| **Object** | name similarity ≥ 80% (fuzzy) **and** same `category` |
| **Link** | `from_name` similarity ≥ 80% **and** `to_name` similarity ≥ 80% **and** `label` similarity ≥ 70% |

Fuzzy matching uses `difflib.SequenceMatcher` (no extra dependencies).

---

## Pass Criteria

**Overall precision ≥ 70%**

Overall precision = (total matched objects + total matched links) /
                    (total extracted objects + total extracted links)

---

## Extending to Real Notion Docs

1. Export your Notion event operation pages as Markdown (`.md`).
2. Place them in a directory (e.g. `docs/`).
3. Run: `python run_spike.py --docs-dir docs --max-docs 50`
4. Evaluate: `python evaluate.py`

For real docs you will need to create matching ground truth files in
`ground_truth/` using the same stem name (e.g. `ground_truth/my_event.json`
for `docs/my_event.md`). The ground truth schema mirrors the extraction schema
in `prompt_template.py`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ANTHROPIC_API_KEY is not set` | Export the key or create `.env` |
| `No .md files found` | Check the `--docs-dir` path |
| `No matching files found` between results and ground truth | Run `run_spike.py` first |
| Rate limit errors | The runner retries automatically with backoff; reduce parallelism if needed |
| Claude returns non-JSON | The model occasionally adds markdown fences; the runner strips them. If it persists, file a bug. |
