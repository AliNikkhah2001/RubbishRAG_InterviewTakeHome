#!/usr/bin/env python3
"""RubbishRAG CLI — تنها ابزار رسمی شما.

مدیر ما می‌گه AI اینو ۱ دقیقه‌ای ساخته! شما ثابت کنید اشتباه می‌کنه.

Commands (funny names, serious bench):
  salam    — check key + quota
  bepar    — single probe:  rubbish bepar "رتبه C یعنی چی؟" --topk 5
  bench    — run visible bench (20 queries), save metrics.json
  bekesh   — generate plots from your logs (score spread, length, poison)
  bastesh  — pack submission.zip (code + traces + metrics + plots + PROOF.md)
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from rubbish_rag.art import LOGO_BIG as LOGO


def _quota(key):
    p = os.path.join(BASE, "traces", "quota.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")).get(key, 0)
    return 0


def cmd_salam(args):
    print(LOGO)
    print(f"سلام! کلید شما: {args.key}")
    print(f"مصرف /retrieve تاکنون: {_quota(args.key)} / 1000")
    print("داده: corpus/test.csv (کامل، همین فایل نمونه)")
    print("شروع: rubbish bepar \"رتبه C یعنی چی؟\"")


def cmd_bepar(args):
    print(LOGO)
    sys.path.insert(0, BASE)
    import rubbish_rag as R
    import rubbish_rag.pipeline  # noqa registers RubbishRAG stages
    # note: pipeline.retrieve ignores key; call remote directly for logging key
    from server._hidden_retriever import remote_retrieve
    hits = remote_retrieve(args.query, topk=args.topk, api_key=args.key)
    hits = R.get("reranker")(args.query, hits)
    pred = R.get("resolver")(args.query, hits)
    print("--- hits (fused) ---")
    for h in hits[:args.topk]:
        print(f'doc={h["doc_id"]} fused={h["fused"]} bm25={h["bm25"]} '
              f'dense={h["dense"]} cat={h.get("category","")[:30]}')
        print("   " + h["text"][:160].replace("\n", " "))
    print("--- resolve ---")
    print(json.dumps(pred, ensure_ascii=False, indent=1)[:1500])


def _run_bench(key="demo-key"):
    from server.evaluator import score_one, aggregate
    vis = json.load(open(os.path.join(BASE, "server", "visible_bench.json"),
                         encoding="utf-8"))
    results = []
    import rubbish_rag as R
    import rubbish_rag.pipeline  # noqa registers broken stages
    from server._hidden_retriever import remote_retrieve
    for item in vis:
        hits = remote_retrieve(item["query"], topk=5, api_key=key)
        hits = R.get("reranker")(item["query"], hits)
        pred = R.get("resolver")(item["query"], hits)
        s = score_one(pred, item)
        results.append({**s, "id": item["id"]})
    agg = aggregate(results)
    os.makedirs(os.path.join(BASE, "traces"), exist_ok=True)
    json.dump({"pipe": "naive", "agg": agg, "results": results},
              open(os.path.join(BASE, "traces", "metrics.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    return agg, results


def cmd_bench(args):
    print(LOGO)
    agg, _ = _run_bench(args.key)
    print("pipe=naive (RubbishRAG)")
    print(json.dumps(agg, ensure_ascii=False, indent=1))
    print("ذخیره شد: traces/metrics.json (لاگ هر probe در traces/trace.jsonl)")


def cmd_bekesh(args):
    print(LOGO)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from server._hidden_retriever import remote_retrieve
    vis = json.load(open(os.path.join(BASE, "server", "visible_bench.json"),
                         encoding="utf-8"))
    gaps, lens, bms = [], [], []
    p_bm, g_bm = [], []
    for item in vis[:20]:
        hits = remote_retrieve(item["query"], topk=5, api_key=args.key)
        if hits:
            gaps.append(hits[0]["fused"] - hits[-1]["fused"])
        for h in hits[:2]:
            lens.append(len(h["text"]))
            bms.append(h["bm25"])
            if h["doc_id"] >= 9000:
                p_bm.append(h["bm25"])
            if h["doc_id"] == item.get("gold_doc_id"):
                g_bm.append(h["bm25"])
    os.makedirs(os.path.join(BASE, "plots"), exist_ok=True)
    plt.figure()
    plt.hist(gaps, bins=10)
    plt.title("Top1-Top5 fused gap (flat=flat=ambiguous?)")
    plt.xlabel("gap")
    plt.savefig(os.path.join(BASE, "plots", "score_spread.png"))
    plt.close()
    plt.figure()
    plt.scatter(lens, bms, s=12)
    plt.title("BM25 vs chunk length (long docs penalized?)")
    plt.xlabel("chars")
    plt.ylabel("bm25")
    plt.savefig(os.path.join(BASE, "plots", "length_vs_bm25.png"))
    plt.close()
    plt.figure()
    plt.bar(["poison_hits", "gold_hits"],
            [sum(p_bm) / max(len(p_bm), 1), sum(g_bm) / max(len(g_bm), 1)])
    plt.title("Mean BM25: poison vs gold (contamination?)")
    plt.savefig(os.path.join(BASE, "plots", "poison_vs_gold.png"))
    plt.close()
    print("ساخته شد: plots/score_spread.png plots/length_vs_bm25.png "
          "plots/poison_vs_gold.png")
    print("از این سه نمودار در PROOF.md استفاده کنید.")


def cmd_bastesh(args):
    print(LOGO)
    out = os.path.join(BASE, "submissions", "submission.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(os.path.join(BASE, "rubbish_rag")):
            for fn in files:
                if fn.endswith(".py"):
                    fp = os.path.join(root, fn)
                    z.write(fp, os.path.relpath(fp, BASE))
        for rel in ["traces/trace.jsonl", "traces/metrics.json",
                    "plots/score_spread.png", "plots/length_vs_bm25.png",
                    "plots/poison_vs_gold.png",
                    "server/visible_bench.json"]:
            fp = os.path.join(BASE, rel)
            if os.path.exists(fp):
                z.write(fp, rel)
        proof = os.path.join(BASE, "docs", "PROOF.md")
        tmpl = os.path.join(BASE, "docs", "PROOF_template.md")
        if os.path.exists(proof):
            z.write(proof, "docs/PROOF.md")
        elif os.path.exists(tmpl):
            z.write(tmpl, "docs/PROOF.md")
            print("هشدار: docs/PROOF.md ندارید — template خام بسته شد. آن را بنویسید!")
        mani = {"key": args.key, "quota_used": _quota(args.key)}
        z.writestr("manifest.json", json.dumps(mani, ensure_ascii=False))
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]
    print(f"بسته شد: {out}  sha={h}")
    print("همین فایل را ارسال کنید. دست‌کاری بعدی قابل تشخیص است.")


def main():
    ap = argparse.ArgumentParser(prog="rubbish")
    ap.add_argument("--key", default="demo-key")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("salam")
    p = sub.add_parser("bepar")
    p.add_argument("query")
    p.add_argument("--topk", type=int, default=5)
    sub.add_parser("bench")
    sub.add_parser("bekesh")
    sub.add_parser("bastesh")
    args = ap.parse_args()
    {"salam": cmd_salam, "bepar": cmd_bepar, "bench": cmd_bench,
     "bekesh": cmd_bekesh, "bastesh": cmd_bastesh}[args.cmd](args)


if __name__ == "__main__":
    main()
