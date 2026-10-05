# API reference — RubbishRAG black-box server

Start the server:

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Interactive test pages (Swagger):

| page | URL |
|---|---|
| Swagger UI (try-it-out) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Raw schema | http://localhost:8000/openapi.json |

## Endpoints

### `GET /health`
Liveness + index stats. Use it to confirm the box is up.

```bash
curl localhost:8000/health
# {"ok":true,"chunks":612,"avgdl":40.2,"note":"RubbishRAG black box is up..."}
```

### `POST /retrieve` — the black box
Flawed hybrid retrieval. `slot_filter`/`normalization` are intentionally
ignored server-side — the correction layer is your job (see `docs/ARCHITECTURE.md` F1–F4).

```bash
curl -X POST localhost:8000/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"query":"رتبه C1 یعنی چی؟","topk":5,"api_key":"demo-key"}'
```

Response: `hits[]` with `doc_id, chunk_id, text, category, bm25, dense, fused`
plus `quota_used`. Exceeding quota (1000) returns **429**.

### `GET /visible` — practice bench, no gold
20 `{id, query}` items. Probe them with `/retrieve`, check yourself with the
local CLI (`python3 rubbish.py bench`).

```bash
curl localhost:8000/visible | python3 -m json.tool | head -n 20
```

### `POST /submit` — hidden scoring, aggregates only
Post one prediction per hidden item id
(`h-base-*`, `h-swap-*`, `h-amb-*`, `h-ood-*`). Gold answers are **never**
returned — only `{total, accuracy, answer_acc, clarify_acc}`.

```bash
curl -X POST localhost:8000/submit \
  -H 'Content-Type: application/json' \
  -d '{"api_key":"demo-key","predictions":[
        {"id":"h-base-0","status":"answer","cites":[240,117,316],"brief":"..."},
        {"id":"h-amb-0","status":"clarify","cites":[],"brief":""}]}'
```

Prediction contract (same as the local pipeline):

```json
{"status": "answer",  "cites": [doc_id, ...], "brief": "..."}
{"status": "clarify", "cites": [],             "brief": ""}
```

### `GET /quota/{api_key}`
`{"key": ..., "used": ..., "max": 1000}`.

## Python client snippet

```python
import requests
API = "http://localhost:8000"
r = requests.post(f"{API}/retrieve",
                  json={"query": "رتبه C1 یعنی چی؟", "topk": 5,
                          "api_key": "demo-key"}).json()
for h in r["hits"]:
    print(h["doc_id"], h["fused"], h["text"][:80])
```

## Production notes (interviewers)

- One process per hiring round; put `server/` behind gunicorn + TLS.
- Issue per-candidate keys: add entries to `server/_secrets.py`
  (`k1/b/rrf_k` ±10%, new `poison_salt`), hand out the key only.
- Watch `traces/trace.jsonl` (probe diversity) and
  `traces/submissions.jsonl` (`/submit` history per key).
- Never ship `server/hidden_eval.json` — `/submit` returns aggregates precisely
  so candidates can iterate without ever seeing gold.
