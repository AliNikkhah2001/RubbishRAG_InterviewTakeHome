# 🗑️ RubbishRAG — "AI made it in 1 minute!" …prove it wrong

```text
  ╔═════════════════════════════════════════════════════════════════╗
  ║    ____        _     _     _     _     ____      _    ____      ║
  ║   |  _ \ _   _| |__ | |__ (_)___| |__ |  _ \    / \  / ___|     ║
  ║   | |_) | | | | '_ \| '_ \| / __| '_ \| |_) |  / _ \| |  _      ║
  ║   |  _ <| |_| | |_) | |_) | \__ \ | | |  _ <  / ___ \ |_| |     ║
  ║   |_| \_\\__,_|_.__/|_.__/|_|___/_| |_|_| \_\/_/   \_\____|     ║
  ║                                                                 ║
  ║       "AI made it in 1 minute!" ... prove it wrong              ║
  ╚═════════════════════════════════════════════════════════════════╝
```

> **RubbishRAG** — Your boss claimed an AI built this Persian credit-scoring RAG in 1 minute. Prove them wrong.
> Measure its behavior, diagnose the root causes, fix the pipeline stages — and back every claim with logged traces and empirical plots.

A take-home interview challenge for **AI / ML / RAG Engineers**: a Persian retrieval-augmented generation system over real credit-scoring QA ([`corpus/test.csv`](corpus/test.csv), 330 verified QA pairs) that *looks* finished on the surface, but scores only **~25–30% on the visible benchmark**. 

Generic AI advice (tuned for English frontier models) fails here. The bugs are grounded inside Persian script variation, flawed score fusion, aggressive length penalties, server-injected poison documents, and ungrounded resolvers. AI assistants are permitted; **systematic engineering and empirical data are required**.

📖 **Full Multi-Page Documentation:** Hosted on [GitHub Pages](https://alinikkhah2001.github.io/RubbishRAG_InterviewTakeHome/) (or browse locally in [`docs/index.html`](docs/index.html)).

---

## 1. System Architecture & Data Flow

```text
corpus/test.csv  (330 Persian Credit-Scoring QA Pairs: Question | Category | BriefAnswer | Answer | Keyword)
       │
       ▼
┌──────────────┐  rubbish_rag/pipeline.py              ┌─────────────────────────────────┐
│ @chunker     │  Fixed 300-char splits of Answer      │  BLACK BOX (server/)            │
│      ────────┼─────────────────────────────────────▶ │  POST /retrieve                 │
│ @retriever   │  Forwards raw query, top-k hits       │  Computes BM25, Dense & Fused   │
│ @reranker    │  Orders by shared-word count          │  Returns hits with scores       │
│ @resolver    │  Answers from top hits                └─────────────────────────────────┘
└──────────────┘                                                       │ Quota: 1000 calls/key
       │                                                               ▼ Logged in trace.jsonl
       ▼
answer {"status":"answer","brief":"...","cites":[...]}  OR  clarify {"status":"clarify","question":"...","options":[...]}
```

### Components:
- **`rubbish_rag/pipeline.py`**: Four decorator stages (`@chunker`, `@retriever`, `@reranker`, `@resolver`). Override any stage by registering your improved functions.
- **`rubbish_rag/normalize_fa.py` & `slots.py`**: Persian normalization and entity slot extraction utilities.
- **`rubbish_rag/orchestrator.py`**: **(Bonus)** End-to-end production orchestrator with Reciprocal Rank Fusion, poison penalty, and dynamic clarification.
- **`server/`**: **Sealed under the honor code** (see §5). Answers `/retrieve` and computes scores. Every hit carries `bm25`, `dense`, and `fused` scores. Do not read server internals; probe them.
- **`corpus/test.csv`**: The ground-truth credit scoring dataset (330 distinct questions and answers).
- **`rubbish.py`**: Candidate CLI toolkit: `salam` (status), `bepar` (single probe), `bench` (visible benchmark), `bekesh` / `rapchik` (plots), `chat` (interactive clarification loop), `ui` (web playground), and `bastesh` (submission packager).

---

## 2. Quickstart

Work on a GitHub fork of this repository:

```bash
# 1) Clone your fork and create your solution branch:
git clone https://github.com/<YOUR-USERNAME>/RubbishRAG_InterviewTakeHome.git
cd RubbishRAG_InterviewTakeHome
git checkout -b solution/<your-github-username>

# 2) Environment setup (Python 3.11 required):
python3 --version                   # Must be 3.11.x (sealed bytecode requirement)
pip install -r requirements.txt
```

```bash
# 3) Meet the system (first run prompts for candidate identity):
python3 rubbish.py salam
python3 rubbish.py bepar "رتبه C1 یعنی چی؟" --topk 5
python3 rubbish.py bench            # Evaluates 20 visible queries -> traces/metrics.json
python3 rubbish.py bekesh           # Generates 4 diagnostic plots in plots/
python3 rubbish.py chat             # (Bonus) Interactive CLI clarification loop
python3 rubbish.py ui               # (Bonus) Launches interactive Studio UI at http://localhost:8000
python3 rubbish.py bastesh          # Stamps README report card + packs submissions/submission.zip
```

```bash
# 4) Commit your solution, plots, and proof:
git add rubbish_rag/ docs/PROOF.md plots/ README.md
git commit -m "RubbishRAG solution"
git push -u origin solution/<your-github-username>
```

> **Note on Local vs. Server Execution:** Everything runs 100% offline out-of-the-box via `python3 rubbish.py`. You do not need to host an external server. However, if you wish to run the FastAPI server with Swagger documentation or Web UI, run:
> ```bash
> uvicorn server.app:app --port 8000 --reload
> # Interactive Web Studio -> http://localhost:8000/ui
> # Swagger API Documentation -> http://localhost:8000/docs
> ```

---

## 3. The 10 Planted Faults (Starting Points for Investigation)

The black box and naive pipeline contain 10 deliberate flaws:

| Fault | Component | Description & Expected Remedy |
|---|---|---|
| **F1** | Score Fusion | Raw min-max combination `0.5*(bm25/max) + 0.5*(dense/max)` distorts ranking. Replace with client-side **Reciprocal Rank Fusion (RRF)**. |
| **F2** | BM25 Length Bias | Excessive penalty $b=0.9, k_1=1.2$ penalizes detailed gold answers. Analyze with `plots/length_vs_bm25.png`. |
| **F3** | Poison Documents | 8 keyword-stuffed fake documents (IDs 9000–9007). Citing a doc ID $\ge 9000$ automatically fails the item. |
| **F4** | Persian Normalization | Starter `normalize_fa` is a no-op. Fails on Persian/Arabic digits (`۲۵۰` vs `250`), Arabic characters (`ي/ك/ة`), and half-spaces (`\u200c`). |
| **F5** | Blind Chunking | Fixed 300-char slices discard question metadata, categories, and split sentences mid-number. |
| **F6** | Word-Overlap Trap | Naive reranker (`len(q & toks)`) favors repetitive spam over distinctive entities. |
| **F7** | Resolver Never Clarifies | Ambiguous queries (e.g. general "بدهی دارم") score 0% unless routed to `{"status": "clarify", ...}`. |
| **F8** | Polarity Blindness | Bag-of-words counters fail on negation particles (`نمی‌شود` vs `می‌شود`, `فاقد` vs `دارای`). |
| **F9** | Context Dilution | Multiple slices from the same document flood the top-$k$ window. Requires document deduplication. |
| **F10**| Smart Poison Mimics | 10 fake documents (IDs 9100–9109) mimic real answers with 1 flipped number. Grounding against `corpus/test.csv` is required. |

---

## 4. Deliverables & Evaluation

1. **Fixed `rubbish_rag/` Code**: Your implementations for `pipeline.py`, `normalize_fa.py`, `slots.py`, and `orchestrator.py`.
2. **`docs/PROOF.md`**: Structured evidence report following [`docs/PROOF_template.md`](docs/PROOF_template.md): Symptom → Probe & Trace IDs → Plot → Architectural Decision.
3. **`submissions/submission.zip`**: Automatically created by `python3 rubbish.py bastesh` (contains code, identity, traces, metrics, plots, and proof with SHA256 integrity check).

### Grading Standards:
- **Held-out hidden evaluation (~168 queries):** Paraphrases, slot swaps, ambiguous queries, and poison traps.
- **Technical Discussion:** In the follow-up technical discussion, be prepared to walk through your diagnostic process, key findings from `traces/trace.jsonl`, and the empirical trade-offs behind your decisions.

---

## 5. Bonus Features

### 🎨 1. Minimalistic Web Studio UI
Run `python3 rubbish.py ui` and open [http://localhost:8000/ui](http://localhost:8000/ui):
- **Live Mode Toggle:** Compare **Naive RubbishRAG** vs **Fixed Orchestrator** side-by-side.
- **Interactive Clarification Dialog:** Click clarifying options to resolve ambiguous queries in real time.
- **Retrieval Inspector:** Visual breakdown of BM25, Dense, Fused, and Rerank scores per hit with poison badges.

### 🤖 2. LangChain-Compatible LCEL Orchestrator
Packaged in [`rubbish_rag/orchestrator.py`](rubbish_rag/orchestrator.py) with standard LangChain Runnable interface:
```python
from rubbish_rag.orchestrator import get_orchestrator

orchestrator = get_orchestrator()
response = orchestrator.invoke("بانک صادرات به رتبه E3 وام میده؟")
print(response["brief"], response["cites"])
```

### 💬 3. Terminal Clarification Chat
Test multi-turn ambiguity resolution in your shell:
```bash
python3 rubbish.py chat
```

---

## 6. Honor Code

- **Probe, Don't Read `server/`:** All findings and fixes must be supported by logged probes in `traces/trace.jsonl`.
- **No Hard-coding:** Hidden evaluation queries are variations not present in the visible benchmark. Hard-coding yields low scores by construction.
- **Quota:** 1,000 `/retrieve` calls per key. Design disciplined probes; do not scrape.

---

## 7. Repository Layout & Multi-Page Documentation

```text
corpus/test.csv            The 330 credit-scoring QA records
rubbish_rag/               YOUR code: pipeline, orchestrator, slots, normalizer
rubbish.py                 CLI toolkit (salam, bepar, bench, bekesh, chat, ui, bastesh)
server/app.py              API server + Swagger UI + Web Studio playground
server/visible_bench.json  20 practice benchmark queries
docs/index.html            GitHub Pages overview & challenge story
docs/architecture.html     Detailed system architecture & scoring mathematics
docs/guide.html            Engineering guide: scientific probing & trace analysis
docs/deliverables.html     Deliverables checklist, grading rubric, and presentation guide
docs/ui.html               Interactive Studio & LangChain orchestrator guide
docs/DECORATORS.md         The pipeline decorator mechanism
docs/API.md                Endpoint, curl, and client reference
docs/PROOF_template.md     Evidence template for docs/PROOF.md
```

<!-- RUBBISH-REPORT:START -->
## 📊 My RubbishRAG Report

_(Empty — run `python3 rubbish.py bastesh` to stamp your candidate card, metrics, and diagrams here.)_
<!-- RUBBISH-REPORT:END -->
