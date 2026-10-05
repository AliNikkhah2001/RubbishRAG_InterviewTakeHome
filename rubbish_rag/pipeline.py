"""RubbishRAG broken pipeline — the 1-minute version.

Stages (override each with @rubbish_rag.* decorators):
  chunk -> retrieve (remote) -> rerank (lexical-biased) -> resolve (never clarifies)
"""
import rubbish_rag as R
from .normalize_fa import normalize_fa
from .slots import extract_slots_broken


@R.chunker
def chunk(docs):
    """BROKEN: fixed 300-char split, drops Category/Keyword header."""
    chunks = []
    for d in docs:
        text = (d.get("Answer") or d.get("BriefAnswer") or "")
        for i in range(0, len(text), 300):
            part = text[i:i + 300]
            if part.strip():
                chunks.append({
                    "doc_id": d["doc_id"],
                    "category": d.get("Category", ""),
                    "text": part,  # no header -> bank/rank/persona lost
                    "chunk_id": f'{d["doc_id"]}:{i // 300}',
                })
    return chunks


@R.retriever
def retrieve(query, topk=5):
    """BROKEN wrapper: calls hidden server WITHOUT slot filter, no normalization."""
    from server._hidden_retriever import remote_retrieve
    return remote_retrieve(query, topk=topk, use_normalization=False,
                           slot_filter=None)


@R.reranker
def rerank(query, hits):
    """BROKEN: pure lexical overlap — loves poison docs with stuffed keywords."""
    q = set(query.split())
    for h in hits:
        toks = set(h["text"].split())
        h["rerank_score"] = len(q & toks)
    return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)


@R.resolver
def resolve(query, hits):
    """BROKEN: always answers top-1, never clarifies. Merges banks/ranks."""
    _ = extract_slots_broken(query)  # ignored
    top = hits[0] if hits else {"text": "", "doc_id": -1}
    return {"status": "answer", "brief": top["text"][:200],
            "cites": [h["doc_id"] for h in hits[:3]] or [top["doc_id"]]}
