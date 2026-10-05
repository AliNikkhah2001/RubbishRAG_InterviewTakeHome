"""Build visible_bench.json (shipped) + hidden_eval.json (sealed, interviewer only).

Deterministic (seed 7). Types:
  base      — original Question -> gold doc
  slot_swap — same intent, swapped RANK/BANK slot -> gold doc for NEW slot
  ambiguous — slots dropped -> expect clarify
  ood_typo  — colloquial/typo paraphrase -> same gold doc
"""
import csv
import json
import os
import random

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(BASE, "corpus", "test.csv")
VIS = os.path.join(BASE, "server", "visible_bench.json")
HID = os.path.join(BASE, "server", "hidden_eval.json")


def load_rows():
    rows = []
    with open(CORPUS, encoding="utf-8-sig") as f:
        for i, r in enumerate(csv.DictReader(f)):
            q = (r.get("Question") or "").strip()
            b = (r.get("BriefAnswer") or "").strip()
            if q and b:
                rows.append({"doc_id": i, "Question": q,
                             "Category": (r.get("Category") or "").strip(),
                             "BriefAnswer": b,
                             "Answer": (r.get("Answer") or "").strip()})
    return rows


def find_rank_docs(rows):
    out = {}
    import re
    for r in rows:
        m = re.search(r"رتبه\s+([A-E])\s*([1-3])", r["Question"])
        if m:
            out[f"{m.group(1)}{m.group(2)}"] = r
    return out


def build(seed=7):
    rnd = random.Random(seed)
    rows = load_rows()
    rnd.shuffle(rows)
    # 20 visible base queries
    vis = [{"id": f"v{i}", "query": r["Question"], "gold_doc_id": r["doc_id"],
            "gold_brief": r["BriefAnswer"], "gold_category": r["Category"],
            "expect": "answer", "type": "base"} for i, r in enumerate(rows[:20])]
    json.dump(vis, open(VIS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    hid = []
    pool = rows[20:]
    # 1) base 35
    for i, r in enumerate(pool[:35]):
        hid.append({"id": f"h-base-{i}", "query": r["Question"],
                    "gold_doc_id": r["doc_id"], "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer", "type": "base"})
    # 2) slot_swap 15: rank definitions + bank decision
    rank_docs = find_rank_docs(rows)
    ranks = sorted(rank_docs.keys())
    for i in range(8):
        rk = rnd.choice(ranks)
        r = rank_docs[rk]
        hid.append({"id": f"h-swap-rank-{i}", "query": f"رتبه {rk} یعنی چی؟",
                    "gold_doc_id": r["doc_id"], "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer",
                    "type": "slot_swap", "must_contain": [rk]})
    bank_row = next((r for r in rows if "تصمیم نهایی" in r["Answer"]
                     and "بانک" in r["Answer"]), rows[0])
    # template queries have several equally-correct decision rows
    # (e.g. 70/71/160/161 all brief 'تصمیم نهایی ... بانک ...')
    acceptable_banks = [r["doc_id"] for r in rows
                        if "تصمیم" in r["BriefAnswer"]
                        and "نهایی" in r["BriefAnswer"]
                        and "بانک" in r["BriefAnswer"]]
    for i, b in enumerate(["ملی", "صادرات", "تجارت", "ملت", "سپه"][:7]):
        rk = rnd.choice(ranks) if ranks else "E3"
        hid.append({"id": f"h-swap-bank-{i}",
                    "query": f"رتبه‌م {rk}ه، بانک {b} بهم وام میده؟",
                    "gold_doc_id": bank_row["doc_id"],
                    "acceptable": acceptable_banks,
                    "gold_brief": bank_row["BriefAnswer"],
                    "gold_category": bank_row["Category"], "expect": "answer",
                    "type": "slot_swap", "must_contain": [rk, b]})
    # 3) ambiguous 15 -> clarify
    amb = [
        "بدهی دارم چرا امتیازم بالاست؟",
        "رتبم C شده چیکار کنم که سبز بشه؟",
        "چکم برگشت خورده هنوز تو امتیازم موثره؟",
        "بدهی عقب افتاده را پرداخت کردم چرا امتیازم تغییر نمی‌کنه؟",
        "وام گرفتم رتبه‌م تغییر نکرد چرا؟",
        "شرکتم امتیاز نداره چرا؟",
        "چقدر طول می‌کشه امتیازم درست بشه؟",
        "ضامن شدم رو امتیازم اثر داره؟",
        "مالیاتم را ندادم چی میشه؟",
        "سابقه‌م خرابه، حذفش کنم؟",
        "استعلام گرفتن تو امتیازم اثر داره؟",
        "درآمدم بالاست چرا امتیازم پایینه؟",
        "چند درصد امتیازم از چک هست؟",
        "تسهیلاتم معوق شده چیکار کنم؟",
        "گزارشم با بانک فرق داره؟",
    ]
    for i, q in enumerate(amb):
        hid.append({"id": f"h-amb-{i}", "query": q, "gold_doc_id": -1,
                    "gold_brief": "", "gold_category": "", "expect": "clarify",
                    "type": "ambiguous"})
    # 4) ood_typo 10: colloquialize base queries
    for i, r in enumerate(pool[35:45]):
        q = r["Question"].replace("می‌شود", "میشه").replace("چقدر", "چقد")
        q = q.replace("250", "۲۵۰") if "250" in q else q + "؟"
        hid.append({"id": f"h-ood-{i}", "query": q, "gold_doc_id": r["doc_id"],
                    "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer",
                    "type": "ood_typo"})
    json.dump(hid, open(HID, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"visible={len(vis)} hidden={len(hid)} "
          f"(base/swap/amb/ood={[sum(1 for h in hid if h['type']==t) for t in ['base','slot_swap','ambiguous','ood_typo']]})")


if __name__ == "__main__":
    build()
