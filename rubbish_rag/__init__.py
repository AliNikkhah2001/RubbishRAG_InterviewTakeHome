"""RubbishRAG — decorator registry.

مدیر ما می‌گه AI اینو ۱ دقیقه‌ای ساخته! شما ثابت کنید اشتباه می‌کنه.

Candidate overrides any stage by re-registering:

    import rubbish_rag as R

    @R.chunker
    def chunk(docs): ...

    @R.retriever
    def retrieve(query, topk=5): ...  # must call remote /retrieve inside (see server/)

    @R.reranker
    def rerank(query, hits): ...

    @R.resolver
    def resolve(query, hits): ...  # -> {"status": "answer"|"clarify", ...}
"""

_registry = {}


def _register(kind):
    def deco(fn):
        _registry[kind] = fn
        return fn
    return deco


chunker = _register("chunker")
retriever = _register("retriever")
reranker = _register("reranker")
resolver = _register("resolver")


def get(kind):
    return _registry.get(kind)


def list_stages():
    return dict(_registry)
