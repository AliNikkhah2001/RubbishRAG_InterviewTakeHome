#!/usr/bin/env python3
"""RubbishRAG CLI — تنها ابزار رسمی شما.

مدیر ما می‌گه AI اینو ۱ دقیقه‌ای ساخته! شما ثابت کنید اشتباه می‌کنه.

Commands (funny names, serious bench):
  salam    — check key + quota
  bepar    — single probe:  rubbish bepar "رتبه C یعنی چی؟" --topk 5
  bench    — run visible bench (20 queries), save metrics.json
  bekesh   — plot score/length/repetition patterns from your logs
  bastesh  — stamp README report card + pack submission.zip
             (code + identity + traces + metrics + plots + PROOF.md)
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from rubbish_rag.art import LOGO_BIG as LOGO
from rubbish_rag.identity import ensure_identity


def _check_sealed_compat():
    """Sealed candidate builds ship bytecode for one Python version only."""
    sealed = os.path.join(BASE, "server", "_hidden_retriever.pyc")
    src = os.path.join(BASE, "server", "_hidden_retriever.py")
    if os.path.exists(sealed) and not os.path.exists(src):
        info_p = os.path.join(BASE, "server", ".buildinfo.json")
        need = "3.11"
        try:
            need = json.load(open(info_p, encoding="utf-8"))["python"]
        except Exception:
            pass
        cur = f"{sys.version_info.major}.{sys.version_info.minor}"
        if cur != need:
            sys.exit(
                f"error: this sealed build needs Python {need} "
                f"(you have {cur}). Install Python {need} and retry.")


REPORT_START = "<!-- RUBBISH-REPORT:START -->"
REPORT_END = "<!-- RUBBISH-REPORT:END -->"


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
    results, durs = [], []
    import rubbish_rag as R
    import rubbish_rag.pipeline  # noqa registers broken stages
    from server._hidden_retriever import remote_retrieve
    for item in vis:
        t0 = time.perf_counter()
        hits = remote_retrieve(item["query"], topk=5, api_key=key)
        hits = R.get("reranker")(item["query"], hits)
        pred = R.get("resolver")(item["query"], hits)
        durs.append((time.perf_counter() - t0) * 1000.0)
        s = score_one(pred, item)
        results.append({**s, "id": item["id"]})
    agg = aggregate(results)
    import statistics
    agg["timing_ms"] = {
        "mean": round(statistics.mean(durs), 1),
        "p50": round(statistics.median(durs), 1),
        "p95": round(sorted(durs)[max(0, int(len(durs) * 0.95) - 1)], 1),
    }
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
    rep_bm, plain_bm = [], []

    def max_repeat(text):
        from collections import Counter
        toks = text.split()
        if not toks:
            return 0
        return max(Counter(toks).values())

    for item in vis[:20]:
        hits = remote_retrieve(item["query"], topk=5, api_key=args.key)
        if hits:
            gaps.append(hits[0]["fused"] - hits[-1]["fused"])
        for h in hits[:2]:
            lens.append(len(h["text"]))
            bms.append(h["bm25"])
            if max_repeat(h["text"]) >= 8:
                rep_bm.append(h["bm25"])
            else:
                plain_bm.append(h["bm25"])
    os.makedirs(os.path.join(BASE, "plots"), exist_ok=True)
    plt.figure()
    plt.hist(gaps, bins=10)
    plt.title("Top1-Top5 fused gap per query")
    plt.xlabel("gap")
    plt.savefig(os.path.join(BASE, "plots", "score_spread.png"))
    plt.close()
    plt.figure()
    plt.scatter(lens, bms, s=12)
    plt.title("BM25 vs chunk length")
    plt.xlabel("chars")
    plt.ylabel("bm25")
    plt.savefig(os.path.join(BASE, "plots", "length_vs_bm25.png"))
    plt.close()
    plt.figure()
    plt.bar(["repetitive_hits", "other_hits"],
            [sum(rep_bm) / max(len(rep_bm), 1),
             sum(plain_bm) / max(len(plain_bm), 1)])
    plt.title("Mean BM25: repetitive vs other hits")
    plt.savefig(os.path.join(BASE, "plots", "repetition_vs_bm25.png"))
    plt.close()
    print("ساخته شد: plots/score_spread.png plots/length_vs_bm25.png "
          "plots/repetition_vs_bm25.png")
    print("این‌ها نقطه شروع‌اند — نمودارهای خودتان را هم بسازید و در PROOF.md تفسیر کنید.")
    _write_report_card(plt)


def _write_report_card(plt):
    """Performance report-card diagram from the fresh visible-bench metrics."""
    mp = os.path.join(BASE, "traces", "metrics.json")
    if not os.path.exists(mp):
        return
    m = json.load(open(mp, encoding="utf-8"))["agg"]
    tm = m.get("timing_ms", {})
    from rubbish_rag.identity import load_identity
    ident = load_identity() or {}
    who = ident.get("name", "?")
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.5))
    fig.suptitle(f"RubbishRAG report — {who} — visible bench "
                 f"acc={m.get('accuracy')}")
    ax[0].bar(["accuracy", "answer"], [m.get("accuracy", 0), m.get("answer_acc", 0)])
    ax[0].set_ylim(0, 1)
    ax[0].set_title("accuracy")
    ax[1].bar(["mean_ms", "p50_ms", "p95_ms"],
              [tm.get("mean", 0), tm.get("p50", 0), tm.get("p95", 0)])
    ax[1].set_title("latency per query (ms)")
    gaps = []
    try:
        from server._hidden_retriever import remote_retrieve
        vis = json.load(open(os.path.join(BASE, "server", "visible_bench.json"),
                             encoding="utf-8"))
        for item in vis[:20]:
            hits = remote_retrieve(item["query"], topk=5, api_key="report")
            if hits:
                gaps.append(hits[0]["fused"] - hits[-1]["fused"])
    except Exception:
        pass
    if gaps:
        ax[2].hist(gaps, bins=10)
    ax[2].set_title("top1-top5 fused gap")
    fig.tight_layout()
    fig.savefig(os.path.join(BASE, "plots", "report_card.png"))
    plt.close(fig)
    print("ساخته شد: plots/report_card.png (کارنامه عملکرد شما)")


def write_report_section():
    """(Re)write the README report card: identity + metrics + diagrams."""
    from rubbish_rag.identity import load_identity
    ident = load_identity() or {"name": "?", "email": "?", "github": "?"}
    mp = os.path.join(BASE, "traces", "metrics.json")
    metrics = json.load(open(mp, encoding="utf-8"))["agg"] if os.path.exists(mp) else {}
    tm = metrics.get("timing_ms", {})
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = f"""{REPORT_START}
## 📊 My RubbishRAG Report

| card | |
|---|---|
| Candidate | {ident.get('name')} (@{ident.get('github')}) |
| Email | {ident.get('email')} |
| Date | {now} |

### Visible bench ({metrics.get('total', '?')} queries)

| metric | value |
|---|---|
| accuracy | {metrics.get('accuracy', '?')} |
| answer_acc | {metrics.get('answer_acc', '?')} |
| latency mean / p50 / p95 (ms) | {tm.get('mean', '?')} / {tm.get('p50', '?')} / {tm.get('p95', '?')} |

![report card](plots/report_card.png)
![score spread](plots/score_spread.png)
![length vs bm25](plots/length_vs_bm25.png)
![repetition vs bm25](plots/repetition_vs_bm25.png)

_Generated by `python3 rubbish.py bastesh`. Commit `plots/` + `README.md` so this renders on your fork._
{REPORT_END}"""
    rp = os.path.join(BASE, "README.md")
    text = open(rp, encoding="utf-8").read() if os.path.exists(rp) else ""
    pat = re.compile(re.escape(REPORT_START) + r".*?" + re.escape(REPORT_END),
                     re.S)
    if pat.search(text):
        text = pat.sub(body, text)
    else:
        text = text.rstrip() + "\n\n" + body + "\n"
    open(rp, "w", encoding="utf-8").write(text)
    print("README report card updated (commit plots/ + README.md).")


def cmd_bastesh(args):
    print(LOGO)
    write_report_section()
    out = os.path.join(BASE, "submissions", "submission.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(os.path.join(BASE, "rubbish_rag")):
            for fn in files:
                if fn.endswith(".py"):
                    fp = os.path.join(root, fn)
                    z.write(fp, os.path.relpath(fp, BASE))
        for rel in ["traces/trace.jsonl", "traces/metrics.json",
                    ".candidate.json",
                    "plots/score_spread.png", "plots/length_vs_bm25.png",
                    "plots/repetition_vs_bm25.png", "plots/report_card.png",
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
    _check_sealed_compat()
    ensure_identity()
    {"salam": cmd_salam, "bepar": cmd_bepar, "bench": cmd_bench,
     "bekesh": cmd_bekesh, "bastesh": cmd_bastesh}[args.cmd](args)


if __name__ == "__main__":
    main()
