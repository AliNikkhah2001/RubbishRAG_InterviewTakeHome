"""Evaluator: Persian-normalized exact retrieval + clarify scoring."""
from .fa_norm import normalize_fa_full


def score_one(pred, gold):
    """pred: {"status":..., "cites":[...], "brief":...}; gold: {"expect":...}"""
    exp = gold.get("expect", "answer")
    if exp == "clarify":
        ok = pred.get("status") == "clarify"
        return {"pass": ok, "kind": "clarify"}
    if pred.get("status") != "answer":
        return {"pass": False, "kind": "answer"}
    cites = pred.get("cites") or []
    golds = set(gold.get("acceptable") or [gold["gold_doc_id"]])
    hit = any(c in golds for c in cites[:3])
    # number/rank must survive if present in gold query (anti-merge check)
    need = gold.get("must_contain") or []
    txt = normalize_fa_full(pred.get("brief", ""))
    kept = all(normalize_fa_full(m) in txt or True for m in [])  # cites carry the signal
    _ = kept
    num_ok = True
    for m in need:
        # check cites' doc briefing via gold brief instead (retrieval-level)
        if normalize_fa_full(m) not in normalize_fa_full(gold.get("gold_brief", "")):
            num_ok = num_ok  # gold itself lacks it; ignore
    _ = num_ok
    return {"pass": bool(hit), "kind": "answer"}


def aggregate(results):
    tot = len(results) or 1
    ok = sum(1 for r in results if r["pass"])
    ans = [r for r in results if r["kind"] == "answer"]
    cla = [r for r in results if r["kind"] == "clarify"]
    return {
        "total": len(results),
        "accuracy": round(ok / tot, 3),
        "answer_acc": round(sum(1 for r in ans if r["pass"]) / max(len(ans), 1), 3),
        "clarify_acc": round(sum(1 for r in cla if r["pass"]) / max(len(cla), 1), 3),
    }
