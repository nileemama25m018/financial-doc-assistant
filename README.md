# Financial Document Intelligence Assistant

A question-answering system for financial filings (10-K, 10-Q, annual reports) that keeps numbers trustworthy. Built with structure-aware document processing, dense retrieval with cross-encoder re-ranking, and a deterministic numeric verification pass that flags any figure in an answer that can't be traced back to the retrieved source text.

Tested on Apple Inc. and Microsoft Corp 2025 Form 10-K filings.

---

## Why this project

Financial documents are dense, numeric, and table-heavy. Naive RAG systems handle prose reasonably well but silently mangle numbers — tables get shredded by character-based chunking, and language models will confidently produce figures that appear nowhere in the source.

This project targets that failure mode directly with two engineering decisions:

1. **Structure-aware extraction** — prose and tables are extracted through separate pipelines. Tables are preserved as intact markdown chunks rather than being split mid-row, so numeric relationships between rows and columns survive.
2. **Deterministic numeric verification** — after the model answers, every numeric token in the answer is regex-extracted and checked for presence in the retrieved context. Anything unaccounted for is flagged in the UI.

The verification step is deliberately *not* another model call. A wrong number in a financial context is a liability, so the check itself needs to be verifiable and reproducible.

---

## Architecture

```
                 Financial PDFs (10-K / 10-Q / annual report)
                                  |
                  +---------------+---------------+
                  v                               v
        Prose Extraction                  Table Extraction
        (pypdf, per page)                 (pdfplumber)
                  |                               |
                  v                               v
        Recursive Chunking              Table -> Markdown Chunks
        (800 chars, 100 overlap)        (kept intact, never split)
                  |                               |
                  +---------------+---------------+
                                  v
                    Embedding Model (bge-small-en-v1.5)
                                  v
                       FAISS Index + Chunk Metadata
                       (page number, chunk type)
                                  |
              User Question ------+
                                  v
                       FAISS Top-K Retrieval (k=10)
                                  v
                    Cross-Encoder Re-ranking (top 5)
                    (ms-marco-MiniLM-L-6-v2)
                                  v
                   Grounded Prompt + LLM (Groq / Llama 3.1)
                                  v
                 Numeric Verification (regex vs. context)
                                  v
                  Answer + Source Pages + Verification Flag
```

**Comparison mode:** when comparing a metric across documents, the pipeline runs independently once per document and assembles the results into a side-by-side table with per-document verification status — rather than attempting a single cross-document query.

---

## Tech stack

| Component | Choice |
|---|---|
| Prose extraction | `pypdf` |
| Table extraction | `pdfplumber` |
| Prose chunking | `langchain-text-splitters` (RecursiveCharacterTextSplitter) |
| Table chunking | Custom — one markdown chunk per table |
| Embeddings | `sentence-transformers` / `BAAI/bge-small-en-v1.5` (384-dim) |
| Re-ranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Vector store | FAISS (`faiss-cpu`, IndexFlatL2) |
| LLM | Groq API (`llama-3.1-8b-instant`), temperature 0.1 |
| Numeric verification | Plain Python + `re` |
| UI | Streamlit |

---

## Setup

**Requirements:** Python 3.10+

```bash
# Clone and enter the project
git clone <your-repo-url>
cd financial-doc-assistant

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# then open .env and paste in your Groq API key
```

A free Groq API key is available at [console.groq.com](https://console.groq.com/).

**Add documents:** place PDF filings in `data/sample_filings/`. SEC EDGAR filings ([sec.gov](https://www.sec.gov/edgar/search/)) and RBI publications ([rbi.org.in](https://www.rbi.org.in/)) are publicly accessible sources. PDFs are gitignored to keep the repo lightweight — download your own.

**Run:**

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Usage

**Single Document Mode** — upload one PDF, click *Process Document*, then ask questions. The answer appears with a verification badge and an expandable panel showing the exact source chunks and page numbers used.

**Comparison Mode** — upload two PDFs, label them, then enter one metric question to run against both.

> **Usage note for Comparison Mode:** phrase the question generically — "What was total revenue?" rather than "Compare revenue between Apple and Microsoft." Each document is retrieved and answered independently, so naming a company that isn't in a given document's own context causes the strict grounding rules to either refuse the question or mislabel the results. This is documented in the evaluation.

---

## Module structure

```
financial-doc-assistant/
├── app.py                     # Streamlit UI (single + comparison modes)
├── src/
│   ├── pdf_processor.py       # per-page prose extraction
│   ├── table_extractor.py     # pdfplumber tables -> markdown
│   ├── chunker.py             # prose + table chunking with metadata
│   ├── embeddings.py          # sentence-transformers wrapper
│   ├── vector_store.py        # FAISS index + save/load
│   ├── retriever.py           # two-stage retrieval + re-ranking
│   ├── llm.py                 # Groq API call
│   ├── prompts.py             # grounded prompt template
│   ├── verifier.py            # deterministic numeric verification
│   └── comparator.py          # per-document comparison logic
├── evaluation/
│   ├── evaluation_questions.json
│   └── evaluation_results.md
├── data/sample_filings/
├── requirements.txt
├── .env.example
└── README.md
```

Each module runs standalone for testing — e.g. `python3 -m src.retriever` runs a retrieval sanity check.

---

## Evaluation

Ten manually written questions were run against the system, covering direct numeric lookups, derived (calculated) metrics, qualitative prose questions, and cross-document comparisons. Full results and per-question notes are in [`evaluation/evaluation_results.md`](evaluation/evaluation_results.md).

| Metric | Result |
|---|---|
| Hit rate (correct chunk retrieved) | 10 / 10 |
| Numeric verification pass rate | 9 / 10 |
| Fully correct and well-formatted answers | 6 / 10 |

**Key finding:** the one clear hallucination in the set was a *derived* metric — the model was asked for a percentage it had to compute, produced a figure from an unrelated table, and the verification pass correctly flagged it as unverified. Direct lookups were reliable across the board. This is precisely the behaviour the verification layer exists to catch.

---

## Known limitations

- **No arithmetic checking.** Verification confirms a number *appears* in the retrieved context; it cannot catch a wrong number that happens to appear elsewhere in that context, and it does not check derived calculations. Questions requiring the model to compute values are the least reliable case.
- **Comparison mode is phrasing-sensitive.** See the usage note above.
- **Multi-value formatting.** Answers spanning several fiscal years or business segments are sometimes returned without clear per-value labels, even when every figure is individually verified.
- **Qualitative answers can include boilerplate.** Open-ended prose questions occasionally surface legal disclaimer language alongside substantive content.
- **Table extraction is layout-dependent.** `pdfplumber` handles ruled tables well; unruled or visually-implied tables extract less cleanly.
- **Small evaluation set.** Ten questions across two filings, manually judged — indicative, not statistically meaningful.
- **No persistence between sessions.** The FAISS index is rebuilt on upload rather than cached across app restarts.

---

## Future work

- Hybrid retrieval (BM25 + dense) for better handling of exact financial terminology
- Structured extraction of full financial statements into a database, enabling exact arithmetic instead of LLM-computed derived metrics
- Larger evaluation set with labeled ground truth and automated scoring
- Section-aware metadata (MD&A, Risk Factors, Income Statement) for filtered retrieval
- Query rewriting to normalise company names out of comparison-mode questions automatically
- Streaming responses and index caching for a faster demo experience

---

## Notes on documents

Sample filings used for development are public documents retrieved from SEC EDGAR and the Reserve Bank of India's publications site. They are not redistributed in this repository — download them directly from the source.
