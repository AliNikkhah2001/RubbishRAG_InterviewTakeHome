"""Hidden retriever — SIMULATES the remote API. In production this lives server-side.

DO NOT OPEN during the interview (honor system). The CLI is the only client.
Flaws (intentional, see docs for theory):
  F1 raw-score fusion (0.5*normBM25 + 0.5*normDense) instead of RRF
  F2 BM25 b=0.9 over-penalizes long Answers, no BM25+ floor
  F3 poison docs with stuffed keywords win on BM25
  F4 overlap-`dense` with no expansion: paraphrase/typo collapse
"""
import json
import math
import os
import time
from collections import Counter

from ._secrets import SECRETS_BY_KEY, QUOTA

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE, "server", "server_index.json")
TRACE_PATH = os.path.join(BASE, "traces", "trace.jsonl")
QUOTA_PATH = os.path.join(BASE, "traces", "quota.json")


PUNCT = "؟?،,.:;!()[]«»\"\"''“”‘’…/-–—\n\t"


def naive_tokens(s: str):
    toks = []
    for t in (s or "").split():
        t = t.strip(PUNCT)
        if t:
            toks.append(t)
    return toks


def _load_index():
    if not os.path.exists(INDEX_PATH):
        from .build_index import build
        build()
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def _bm25(query_toks, doc_toks, df, N, avgdl, k1=1.2, b=0.9):
    tf = Counter(doc_toks)
    dl = max(len(doc_toks), 1)
    score = 0.0
    for t in query_toks:
        f = tf.get(t, 0)
        if f == 0:
            continue
        n = df.get(t, 0)
        idf = math.log(1 + (N - n + 0.5) / (n + 0.5))
        denom = f + k1 * (1 - b + b * dl / max(avgdl, 1))
        score += idf * (f * (k1 + 1)) / denom
    return score


def _overlap_dense(query_toks, doc_toks):
    q, d = set(query_toks), set(doc_toks)
    if not q or not d:
        return 0.0
    inter = len(q & d)
    return inter / math.sqrt(len(q) * len(d))


def _log_trace(api_key, query, topk, hits):
    try:
        os.makedirs(os.path.dirname(TRACE_PATH), exist_ok=True)
        rec = {"ts": time.time(), "key": api_key, "q": query[:300],
               "topk": topk,
               "hits": [{"doc_id": h["doc_id"], "fused": round(h["fused"], 4)} for h in hits[:topk]]}
        with open(TRACE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        # quota
        q = {}
        if os.path.exists(QUOTA_PATH):
            q = json.load(open(QUOTA_PATH, encoding="utf-8"))
        n = int(q.get(api_key, 0)) + 1
        q[api_key] = n
        json.dump(q, open(QUOTA_PATH, "w", encoding="utf-8"))
        if n > QUOTA["max_retrieve"]:
            raise RuntimeError("quota exceeded")
    except RuntimeError:
        raise
    except Exception:
        pass


def remote_retrieve(query, topk=5, use_normalization=False, slot_filter=None,
                    api_key="demo-key"):
    """Simulated POST /retrieve. slot_filter is IGNORED (you must filter client-side)."""
    _ = use_normalization  # flaw: server never normalizes, even if you ask
    _ = slot_filter  # flaw: server ignores metadata — correction layer is yours
    sec = SECRETS_BY_KEY.get(api_key, SECRETS_BY_KEY["demo-key"])
    idx = _load_index()
    chunks, df, N, avgdl = idx["chunks"], idx["df"], idx["N"], idx["avgdl"]
    qt = naive_tokens(query)
    scored = []
    for c in chunks:
        dt = naive_tokens(c["text"])
        bm = _bm25(qt, dt, df, N, avgdl, k1=sec["k1"], b=sec["b"])
        dn = _overlap_dense(qt, dt)
        scored.append((c, bm, dn))
    max_bm = max((s[1] for s in scored), default=0) or 1.0
    max_dn = max((s[2] for s in scored), default=0) or 1.0
    hits = []
    for c, bm, dn in scored:
        fused = 0.5 * (bm / max_bm) + 0.5 * (dn / max_dn)  # F1: raw-score add
        hits.append({"doc_id": c["doc_id"], "chunk_id": c["chunk_id"],
                     "text": c["text"], "category": c.get("category", ""),
                     "bm25": round(bm, 4), "dense": round(dn, 4),
                     "fused": round(fused, 4)})
    hits.sort(key=lambda h: h["fused"], reverse=True)
    out = hits[:topk]
    _log_trace(api_key, query, topk, out)
    return out
