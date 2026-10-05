# 🗑️ RubbishRAG — "AI made it in 1 minute!" …prove it wrong

```
  ____        _     _     _     _     ____      _    ____
 |  _ \ _   _| |__ | |__ (_)___| |__ |  _ \    / \  / ___|
 | |_) | | | | '_ \| '_ \| / __| '_ \| |_) |  / _ \| |  _
 |  _ <| |_| | |_) | |_) | \__ \ | | |  _ <  / ___ \ |_| |
 |_| \_\\__,_|_.__/|_.__/|_|___/_| |_|_| \_\/_/   \_\____|
        AI made it in 1 minute!!  (prove it wrong)
```

> **رابیـش‌رگ** — مدیر ما می‌گه AI اینو ۱ دقیقه‌ای ساخته! شما به‌عنوان
> مصاحبه‌شونده باید ثابت کنید اشتباه می‌کند: رفتارش را اندازه بگیرید،
> خطاهایش را پیدا کنید، و اصلاحش کنید — و برای هر ادعا trace و نمودار بیاورید.

A take-home for AI engineers: a Persian RAG over real credit-scoring QA that
*looks* finished and scores **~40% on the visible bench**. Generic AI advice
(tuned for frontier models) does not transfer here — only experiments against
*this* system move the needle. AI assistants are allowed; they are not sufficient.

---

## 1. Project architecture — how it currently works

```
corpus/test.csv  (330 Persian QA rows: Question | Category | BriefAnswer | Answer | Keyword)
       │
       ▼
┌──────────────┐  your code: rubbish_rag/           ┌─────────────────────────┐
│ chunk        │  fixed 300-char splits of Answer   │  BLACK BOX (server/)    │
│      ────────┼──────────────────────────────────▶ │  POST /retrieve         │
│ retrieve     │  forwards raw query, top-k hits    │  returns hits with      │
│ rerank       │  orders by shared-word count       │  bm25 / dense / fused   │
│ resolve      │  answers from top hits             │  scores per hit         │
└──────────────┘                                    └─────────────────────────┘
       │                                                       │ quota 1000/key
       ▼                                                       ▼ logged
answer {"status","brief","cites"}  or  clarify {"status","question","options"}
```

**What each piece currently does** (verified by reading the code + probing):

- `rubbish_rag/pipeline.py` — four decorator stages (`@chunker @retriever
  @reranker @resolver`, see `rubbish_rag/__init__.py`). Override any stage by
  re-registering a function with the same decorator. The stage bodies are
  short — read them first.
- `rubbish_rag/normalize_fa.py`, `rubbish_rag/slots.py` — empty starter
  utilities. Whether you need them, and what belongs in them, is for you
  to discover (each file contains its TODO).
- `server/` — **sealed under the honor code** (see §5): it answers
  `POST /retrieve` and scores `POST /submit`. Every hit carries its
  `bm25`, `dense` and `fused` scores — that transparency is your instrument,
  use it. Do not read `server/` internals; probe them.
- `corpus/test.csv` — fully yours to inspect. Note the columns: questions are
  often colloquial, answers long, and some rows differ from each other in
  only one or two words.
- `rubbish.py` (CLI) — `salam` (status), `bepar` (single probe with scores),
  `bench` (visible bench → `traces/metrics.json`), `bekesh` (plots from your
  logs), `bastesh` (packs `submissions/submission.zip`). Every `/retrieve`
  call is appended to `traces/trace.jsonl` — that log is part of your evidence.

## 2. Quickstart

> **Candidates start here — work on a fork, never on this repo directly.**

```bash
# 1) Fork on GitHub: click Fork on this repo page (your fork = your workspace)
# 2) Clone YOUR fork and check out the task branch:
git clone https://github.com/<YOU>/RubbishRAG_InterviewTakeHome.git
cd RubbishRAG_InterviewTakeHome
git checkout candidate              # task branch: minimal files, sealed eval
git checkout -b solution/<your-github-username>
python3 --version                   # must be 3.11.x (sealed bytecode requirement)
pip install -r requirements.txt
```

```bash
# 3) meet the rubbish (first run asks name/email/GitHub for the report card)
python3 rubbish.py salam
python3 rubbish.py bepar "رتبه C1 یعنی چی؟" --topk 5
python3 rubbish.py bench            # -> traces/metrics.json
python3 rubbish.py bekesh           # -> plots/*.png
python3 rubbish.py bastesh          # stamps README report + packs submission.zip

# 4) commit work + plots + README so the report renders, then push:
git add rubbish_rag/ docs/PROOF.md plots/ README.md
git commit -m "RubbishRAG solution"
git push -u origin solution/<your-github-username>
# then send submissions/submission.zip (or open a PR from your branch)
```

API mode (same black box, Swagger UI to click through):

```bash
uvicorn server.app:app --port 8000 --reload
# http://localhost:8000/docs  (try-it-out) · /redoc · /openapi.json
```

```bash
curl -X POST localhost:8000/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"رتبه C1 یعنی چی؟","topk":5,"api_key":"demo-key"}'
```

Full endpoint reference: [`docs/API.md`](docs/API.md).

## 3. Symptoms observed so far (starting points, not conclusions)

- Visible bench: **~40%**. Something is wrong in more than one place.
- Some top-ranked hits look irrelevant to a human reader. Why do they score high?
- Some queries that differ in one word get the *same* answer. When is that
  correct, and when is it a merge of two different truths?
- Some queries arguably have no good answer in the corpus. What does the
  current resolver do then — and what *should* a production system do?
- Scores are returned per hit (`bm25`, `dense`, `fused`). Plot their
  distributions before theorizing: `bekesh` gives you three starters.

TODO for you: turn each symptom into a falsifiable claim, a probe, and a plot.
`docs/PROOF_template.md` shows the expected shape of that evidence.
Theoretical background that past candidates found useful is listed at the end
of `docs/ARCHITECTURE.md` — as *reading pointers*, after you have data.

## 4. Deliverables

1. Fixed `rubbish_rag/` — your decorator overrides. The remote API is not yours to change.
2. `docs/PROOF.md` — for each change: symptom → probe + trace IDs → plot → decision.
   Claims without traces do not count.
3. `submissions/submission.zip` from `bastesh` (code + traces + metrics + plots + proof, hashed).

Hidden evaluation (~70 held-out queries: paraphrases, slot variations, ambiguous
and out-of-distribution phrasings) measures retrieval hits, clarification
behaviour and faithfulness. Bar: **accuracy >65%, clarify >50%**, plus a 30-min
defense of your traces (*"show me the failing trace"* — a pasted solution
cannot answer that).

## 5. Honor code

- `server/` internals and hidden queries: **probe, don't read**. Findings must
  come from logged experiments.
- Full `corpus/test.csv` is yours — but hidden queries are variations you have
  not seen. Hard-coding answers caps low by construction.
- Quota: 1000 `/retrieve` calls per key. Design probes; don't scrape.

## 6. Repo layout & docs

```
corpus/test.csv            the full QA file (inspect freely)
rubbish_rag/               YOUR code: pipeline + art + TODO stubs
rubbish.py                 CLI: salam / bepar / bench / bekesh / bastesh
server/app.py              black-box API + Swagger (use it, don't read it)
server/visible_bench.json  20 practice queries (with answers, for self-check)
docs/README_FA.md          task brief (فارسی)
docs/DECORATORS_FA.md      the decorator mechanism (فارسی)
docs/ARCHITECTURE.md       components, data flow, current behavior, reading pointers
docs/API.md                endpoint + curl + Python client reference
docs/PROOF_template.md     evidence shape for docs/PROOF.md
```

Interviewers: the grading rubric, sealed-file list and per-round refresh live
in the private folder next to this repo (`RubbishRAG_reference_private/`).

<!-- RUBBISH-REPORT:START -->
## 📊 My RubbishRAG Report

_(Empty — run `python3 rubbish.py bastesh` to stamp your card, metrics and diagrams here.)_
<!-- RUBBISH-REPORT:END -->
