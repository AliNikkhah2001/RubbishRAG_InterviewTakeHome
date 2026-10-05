"""Server-side indexing. DO NOT OPEN during the interview (honor system)."""
import csv
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(BASE, "corpus", "test.csv")
OUT = os.path.join(BASE, "server", "server_index.json")


def load_corpus():
    docs = []
    with open(CORPUS, encoding="utf-8-sig") as f:
        for i, row in enumerate(csv.DictReader(f)):
            q = (row.get("Question") or "").strip()
            b = (row.get("BriefAnswer") or "").strip()
            a = (row.get("Answer") or "").strip()
            if not q or (not b and not a):
                continue
            docs.append({"doc_id": i, "Question": q,
                         "Category": (row.get("Category") or "").strip(),
                         "BriefAnswer": b, "Answer": a,
                         "Keyword": (row.get("Keyword") or "").strip()})
    return docs


def bad_chunk(text, size=300):
    return [text[i:i + size] for i in range(0, len(text), size) if text[i:i + size].strip()]


def build():
    from .poison_docs import POISON_TEMPLATES, SMART_POISON
    docs = load_corpus()
    # server indexes Answer (+BriefAnswer prefix) with bad chunking; question NOT indexed
    chunks = []
    for d in docs:
        blob = ((d["BriefAnswer"] + "\n") if d["BriefAnswer"] else "") + d["Answer"]
        for j, part in enumerate(bad_chunk(blob)):
            chunks.append({"doc_id": d["doc_id"], "chunk_id": f'{d["doc_id"]}:{j}',
                           "text": part, "category": d["Category"]})
    for p in POISON_TEMPLATES + SMART_POISON:
        blob = (p["BriefAnswer"] + "\n") + p["Answer"]
        for j, part in enumerate(bad_chunk(blob)):
            chunks.append({"doc_id": p["doc_id"], "chunk_id": f'{p["doc_id"]}:{j}',
                           "text": part, "category": p["Category"]})
    # naive df over whitespace tokens
    from ._hidden_retriever import naive_tokens
    df, total_len = {}, 0
    for c in chunks:
        total_len += len(naive_tokens(c["text"]))
        for t in set(naive_tokens(c["text"])):
            df[t] = df.get(t, 0) + 1
    idx = {"chunks": chunks, "df": df, "N": len(chunks),
           "avgdl": total_len / max(len(chunks), 1), "ndocs": len(docs)}
    json.dump(idx, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"indexed {len(docs)} docs + {len(POISON_TEMPLATES) + len(SMART_POISON)} poison -> "
          f"{len(chunks)} chunks. N={idx['N']} avgdl={idx['avgdl']:.1f}")
    return idx


if __name__ == "__main__":
    build()
