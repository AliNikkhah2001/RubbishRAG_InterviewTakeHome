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
> مصاحبه‌شونده باید ثابت کنید اشتباه می‌کند: خطاهایش را پیدا کنید، با لاگ و
> نمودار اثبات کنید، و با دکوراتور اصلاحش کنید.

An **AI-proof take-home for AI engineers**: a deliberately broken Persian RAG
over real credit-scoring QA. Generic AI advice (tuned for GPT-4) fails here —
only empirical probing of *this* black box passes. AI assistants are allowed;
they are not sufficient.

---

## What makes it AI-proof?

| property | how |
|---|---|
| 🔒 Hidden black box | Flawed hybrid retriever lives behind `POST /retrieve` (or sealed `server/`). Its bugs exist nowhere on the internet. |
| 🧪 Must probe to know | Fusion math, BM25 params, poison docs and OOD brittleness are discoverable **only** by running queries and reading traces/plots. |
| 🪤 Memorisation trap | Full `corpus/test.csv` is given — but hidden eval swaps slots (`ملی+E2` → `تجارت+D1`), paraphrases colloquially and drops slots into ambiguity. Copy-paste caps at ~40%. |
| 📉 Weak-box realism | Small-box behaviour: bad chunking, stuffed-keyword poison docs, flat score distributions on ambiguous queries. |
| 👁️ Observable process | Quota'd API + `trace.jsonl` per probe + hashed `submission.zip` — we grade the *process*, then defend it in a 30-min interview. |

Validated difficulty — hidden set (73 queries): **naive 30% vs reference fix 97%**.
The reference lives privately with interviewers; candidates never see it.

## 60-second quickstart

```bash
pip install -r requirements.txt

# 1) meet the rubbish
python3 rubbish.py salam
python3 rubbish.py bepar "رتبه C1 یعنی چی؟" --topk 5

# 2) run the visible bench (20 queries, no gold needed)
python3 rubbish.py bench            # -> traces/metrics.json

# 3) generate your evidence plots
python3 rubbish.py bekesh           # -> plots/*.png

# 4) pack and send
python3 rubbish.py bastesh          # -> submissions/submission.zip
```

## Test it via API (Swagger)

```bash
uvicorn server.app:app --port 8000 --reload
```

| page | URL |
|---|---|
| 🧪 Swagger UI (click-and-try) | http://localhost:8000/docs |
| 📖 ReDoc | http://localhost:8000/redoc |

```bash
curl -X POST localhost:8000/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"رتبه C1 یعنی چی؟","topk":5,"api_key":"demo-key"}'

curl -X POST localhost:8000/submit \
  -H 'Content-Type: application/json' \
  -d '{"api_key":"demo-key","predictions":[
        {"id":"h-base-0","status":"answer","cites":[240],"brief":"..."}]}'
```

Full reference: [`docs/API.md`](docs/API.md).

## The 7 planted bugs (find them all)

| # | layer | bug | theory |
|---|---|---|---|
| F1 | server | raw-score fusion instead of RRF | Cormack et al. 2009 |
| F2 | server | BM25 `b≈0.9`, no BM25+ floor — long docs lose | Lv & Zhai 2011 |
| F3 | server | 8 keyword-stuffed poison docs (`doc_id ≥ 9000`) | keyword dilution |
| F4 | server | overlap-`dense`, no expansion — paraphrase/typo collapse | SPLADE intuition |
| F5 | starter | 300-char chunks, no `Category/Keyword` header | entity-aware chunking |
| F6 | starter | lexical-overlap reranker loves poison | cross-encoder discipline |
| F7 | starter | never clarifies — merges banks/ranks into hallucinations | Self-RAG / ambiguity |

Details + fixes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
Decorator how-to: [`docs/DECORATORS_FA.md`](docs/DECORATORS_FA.md) (فارسی) ·
Task brief: [`docs/README_FA.md`](docs/README_FA.md) (فارسی).

## Mandatory slots & numbers (فارسی)

`BANK | RANK=A1..E3 | PERSONA=حقیقی/حقوقی | DEBT | AMOUNT | TIME` —
missing slot + flat scores → `clarify` in Persian, else `answer` with cites.
Digits `۰-۹/٠-٩→0-9`, `ي→ی`, `ك→ک`, half-space, `میشه→می‌شود`.
Only distinctive numbers (≥2 digits: `۲۵۰`, `۲۴ ساعت`) boost — single digits are noise.

## Repo layout

```
corpus/test.csv            real Persian QA (given, all of it)
rubbish_rag/               YOUR code: @chunker @retriever @reranker @resolver + art.py
rubbish.py                 CLI: salam / bepar / bench / bekesh / bastesh
server/app.py              FastAPI black box + Swagger  (POST /retrieve, /submit)
server/_hidden_retriever.py  flawed scorer — DO NOT OPEN (honor system)
server/visible_bench.json  20 practice queries (gold withheld)
docs/                      README_FA · DECORATORS_FA · ARCHITECTURE · API · PROOF_template · INTERVIEWER
```
Candidate self-checks: `rubbish bench` (visible) + `POST /submit` (hidden aggregates, no gold leak).
Interviewers validate with the private reference (`docs/INTERVIEWER.md`).

## Deliverables (candidates)

1. Fixed `rubbish_rag/` (decorators rewritten, remote API untouched)
2. `docs/PROOF.md` — 1 page + 2 plots from *your* logs (RRF vs raw-score, BM25 length, poison effect)
3. `submissions/submission.zip` from `bastesh` (code + traces + metrics + plots + proof, hashed)

Hidden bar: accuracy >65%, clarify >50%, plus 30-min defense
(*"Why did XML/FAQ-matching beat raw dense here? Show me the failing trace."*).

## Interviewers

See [`docs/INTERVIEWER.md`](docs/INTERVIEWER.md): sealed files, per-candidate
key jitter, quota, grading rubric, refresh-per-round. The reference fix and
`run_validation.py` live in the private `RubbishRAG_reference_private/`
folder — never in this repo.
