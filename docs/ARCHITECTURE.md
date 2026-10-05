# ARCHITECTURE — how RubbishRAG works (and why it fails)

This is the technical reference for the interview task. Candidates: read this
*after* you have probed the API — every claim below is verifiable with
`rubbish bepar` + `rubbish bekesh`.

```
 ┌────────────┐   raw CSV    ┌──────────────────┐   300-char chunks   ┌───────────────┐
 │ corpus/    │ ──────────▶ │  SERVER (hidden) │ ──────────────────▶ │ server_index  │
 │ test.csv   │              │  bad chunking    │   + 8 poison docs   │ 612 chunks    │
 │ 330 docs   │              └──────────────────┘                     └───────┬───────┘
 └────────────┘                                                              │
        ▲ candidate owns chunking idea, NOT the index                        │ POST /retrieve
 ┌──────┴────────────────────────────────────────────────────────────────────▼──────┐
 │  query ─▶ BM25(k1=1.2, b=0.9) ─┐                                                 │
 │                                 ├─▶ raw-score fuse ─▶ top-k ─▶ YOUR correction ─▶ answer/clarify
 │  query ─▶ overlap-`dense` ─────┘   0.5*normBM25 + 0.5*normDense     layer (decorators)
 └───────────────────────────────────────────────────────────────────────────────────┘
```

## 1. Data model

`corpus/test.csv` — Persian credit-scoring QA (~330 usable rows):

| column | meaning | example |
|---|---|---|
| `Question` | user phrasing (often colloquial) | `وام جدید زیاد بگیرم رتبه رو بهتر میکنه؟` |
| `Category` | subpart — the disambiguation axis | `تسهیلات، وام‌گیری، ...` |
| `BriefAnswer` | 1-line gold — exact-retrieval target | `تأثیر مثبت تعهدات با گذشت زمان...` |
| `Answer` | full gold — faithfulness source | long paragraph |
| `Keyword` | contamination surface | `وام جدید، اثر بر امتیاز` |

Two rows can share 90% of their text and differ only in a rank code
(`A1: 680-900` vs `A3: 640-659`) or a persona (`چک 12% حقیقی` vs `6% حقوقی`).
That is the whole game: **semantic similarity cannot separate them; slots must.**

## 2. Fault model (F1–F7)

**F1 — raw-score fusion instead of RRF.**
`fused = 0.5·(bm25/maxBM25) + 0.5·(dense/maxDense)`. BM25 is unbounded
(~0–20), dense is bounded (0–1); after per-query max-normalisation the two
distributions still have different shapes, so one channel dominates depending
on query length. Fix (theory): rank transform — RRF,
`score(d) = Σ 1/(k + rankᵢ(d))`, `k=60` (Cormack, Clarke & Buettiger, SIGIR 2009).
Ranks are distribution-free; raw scores are not. Candidates cannot change the
server, so they must build the correction client-side: re-rank with their own
RRF over `bm25`+`dense` ranks, or bypass fusion with slot/number boosts.

**F2 — BM25 length over-penalisation, no BM25+ floor.**
`b≈0.9` in `tf·(k1+1)/(tf+k1·(1-b+b·dl/avgdl))` crushes long authoritative
answers (rank definitions, red-line rules). Fix (theory): BM25+ lower bound
(Lv & Zhai 2011) or length-binned re-weighting. Evidence:
`plots/length_vs_bm25.png` — recall collapses for chunks >200 chars.

**F3 — keyword contamination.**
8 poison docs (`doc_id ≥ 9000`) repeat high-value keywords 8–12×
(`امتیاز چک وام رتبه مالیات...`) with wrong answers (`امتیاز شما ۹۰۰ است!`).
Naive BM25 ranks them top-3 on keyword queries. Fix: repetition penalty
(`max token count > 8 → −0.4`), unknown-doc penalty, slot-mismatch veto.

**F4 — overlap-`dense` with no expansion.**
`dense = |Q∩D|/√(|Q|·|D|)` — no SPLADE-style expansion, no typo tolerance.
`می‌شود` vs `میشه`, `۲۵۰` vs `250`, unseen bank aliases all score 0.
Fix: normalise *before* sending (digits, kaf/yeh, ZWNJ, colloquial map) and
expand numbers to both scripts.

**F5 — chunking (visible, broken).**
`rubbish_rag/pipeline.py::chunk` splits `Answer` into fixed 300-char pieces
with **no header** — `Category`, `Keyword`, bank/rank context is lost, and
`A1..E3` tables are split mid-row. Fix: header-aware chunking —
`[دسته|کلید|حقیقی/حقوقی]` prefix, 400-char sliding window + 80 overlap,
never split a rank row. (Server index stays badly chunked — the candidate's
chunker is graded on `sample` behaviour + its effect on their rerank/filter.)

**F6 — reranker (visible, broken).**
Pure query-term overlap count — poison docs win by construction. Fix:
slot-match boost (+0.35), distinctive-number boost (+0.3, ≥2 digits only —
single digits like `2` are noise), poison penalty (−0.6).

**F7 — resolver (visible, broken).**
Always answers top-1, never clarifies → merges banks/ranks into hallucinations
(`$10` average of `$5` and `$15`). Fix: entropy + length gate (below).

## 3. Slots (mandatory)

| slot | extractor | example |
|---|---|---|
| `BANK` | substring vs bank list | `ملی، صادرات، تجارت` |
| `RANK` | regex `([A-E])\s*([1-3])` after digit-normalisation | `C2، E3` (also `C۲`) |
| `PERSONA` | keyword sets | `حقیقی / حقوقی` (چک 12% vs 6%) |
| `DEBT` | keyword sets | `تسهیلاتی / مالیاتی / چک / محکومیت` |
| `AMOUNT/TIME` | number regex + units | `۲۵۰ هزار تومان، ۵ سال، ۲۴ ساعت` |

Rule: extraction runs on **normalised** text. Latin ranks are lowercased by
normalisation — match case-insensitively.

## 4. Clarify contract (auto-graded)

```
no hard slots AND (words ≤ 8 OR (trigger word AND fused top5 gap < 0.20))
  → {"status":"clarify","question":"...؟","options":[...]}
else
  → {"status":"answer","brief":"...","cites":[doc_id ×3]}   # gold must be in first 3
```

Trigger words: `بدهی، رتبه، امتیاز، چک، وام، تسهیلات، مالیات`.
Topic-specific Persian questions: debt-type (`تسهیلاتی یا مالیاتی؟ + امتیاز ۲۵۰؟`),
rank (`رتبه دقیق + حقیقی/حقوقی؟`), cheque (`کی برگشت خورد؟ رفع سواثر؟`).
Long self-contained queries are answered even without slots — length is signal.

## 5. Evaluation

- **Retrieval:** `gold_doc_id ∈ cites[:3]` (hit@3 — near-duplicates make hit@1 noise).
- **Clarify:** `status == clarify` iff `expect == clarify`.
- **Hidden set (73, sealed):** 35 base + 13 slot-swap (`ملی+E2` seen → `تجارت+D1`
  hidden) + 15 ambiguous + 10 typo/colloquial OOD. Memorisation caps at ~40%.
- **Anti-share:** per-key jitter (`k1/b/rrf_k`, poison IDs), quota 1000,
  `trace.jsonl` per probe, `submission.zip` hash.

## 6. Validated difficulty

`run_validation.py` (private, interviewers only) → naive **30%**
(clarify 0%) vs reference **97%** (answer 100%, clarify ~87%).
Visible bench naive: 40% — matches the story.
