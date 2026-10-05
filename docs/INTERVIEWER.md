# INTERVIEWER guide (do not forward hidden files to candidates)

## Sealed files (never commit, never ship)
- `server/hidden_eval.json` — built by `hidden_eval_builder.py`, gitignored.
- `server/_hidden_retriever.py` + `server/_secrets.py` — in production move
  these behind a real API (`POST /retrieve` + `POST /submit`) with per-candidate
  keys. Jitter `k1/b/rrf_k` ±10% per key + shuffle poison IDs (see `_secrets.py`).
- `../RubbishRAG_reference_private/` (outside this repo, never pushed):
  `reference_solution/fixed_pipeline.py` + `run_validation.py`.

## Grading
1. From the private folder: `python3 run_validation.py` — must print DOABLE:YES
   (naive ~30%, reference ~97%: answer 100%, clarify ~87%).
   Hidden: 73 queries (35 base + 13 slot_swap + 15 ambiguous + 10 ood_typo).
   Override repo location if needed:
   `RUBBISH_REPO=/path/to/RubbishRAG_InterviewTakeHome python3 run_validation.py`
2. Candidate bar: hidden accuracy >65% + clarify_acc >50% +
   `PROOF.md` with 2 real plots + trace IDs + interview defense (30 min).
3. Logs: `traces/trace.jsonl` shows probe diversity (length/number/slot tests).
   Quota 1000 prevents scraping the full KB via top-k.

## Deploy options
- Cheap: single VPS, this repo + gunicorn/uvicorn around `server/app.py`.
- Zero-ops: give candidates this repo as-is; honor-system "DO NOT OPEN server/".
  `hidden_eval.json` is rebuilt locally and scored via `POST /submit` only by you.

## Refresh per hiring round
Change seed in `hidden_eval_builder.py`, re-run private `run_validation.py`,
confirm reference still >85% before sending out.
