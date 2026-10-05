"""Build visible_bench.json (shipped) + hidden_eval.json (sealed, interviewer only).

DO NOT OPEN during the interview (honor system) — it contains the hidden
query recipe. Use `rubbish bench` and `POST /submit` instead.

Deterministic (seed 7).
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
    # 1) base 70 — verbatim corpus questions (tests FAQ discovery + rerank)
    for i, r in enumerate(pool[:70]):
        hid.append({"id": f"h-base-{i}", "query": r["Question"],
                    "gold_doc_id": r["doc_id"], "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer", "type": "base"})
    # 2) slot_swap: every rank definition + bank x rank loan decisions
    rank_docs = find_rank_docs(rows)
    ranks = sorted(rank_docs.keys())
    for rk in ranks:
        r = rank_docs[rk]
        hid.append({"id": f"h-swap-rank-{rk}", "query": f"رتبه {rk} یعنی چی؟",
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
    for i, b in enumerate(["ملی", "صادرات", "تجارت", "توسعه صادرات",
                            "ملت", "سپه", "پاسارگاد"]):
        for j in range(3):
            rk = rnd.choice(ranks) if ranks else "E3"
            hid.append({"id": f"h-swap-bank-{i}-{j}",
                        "query": f"رتبه‌م {rk}ه، بانک {b} بهم وام میده؟",
                        "gold_doc_id": bank_row["doc_id"],
                        "acceptable": acceptable_banks,
                        "gold_brief": bank_row["BriefAnswer"],
                        "gold_category": bank_row["Category"], "expect": "answer",
                        "type": "slot_swap", "must_contain": [rk, b]})
    # 3) ambiguous -> clarify (short, under-specified, no near-verbatim row)
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
        "امتیازم بد شده چرا؟",
        "رتبم افت کرده چیکار کنم؟",
        "وامم عقب افتاده؟",
        "چک دارم امتیازم کم شده؟",
        "مالیات ندادم رتبه‌م میاد پایین؟",
        "ضامنم بدحساب بوده؟",
        "قسطامو دیر دادم چی میشه؟",
        "گزارشمو کجا ببینم؟",
        "بانک بهم وام نمیده چرا؟",
        "سابقه‌م پاک میشه؟",
        "سوءاثر چقدر طول میکشه؟",
        "چرا رتبم اومده پایین؟",
    ]
    for i, q in enumerate(amb):
        hid.append({"id": f"h-amb-{i}", "query": q, "gold_doc_id": -1,
                    "gold_brief": "", "gold_category": "", "expect": "clarify",
                    "type": "ambiguous"})
    # 4) ood_typo 25: colloquialize + digit-swap + punctuation drift
    for i, r in enumerate(pool[70:95]):
        q = r["Question"].replace("می‌شود", "میشه").replace("چقدر", "چقد")
        q = q.replace("است؟", "ه؟").replace("250", "۲۵۰")
        if "؟" not in q:
            q += "؟"
        hid.append({"id": f"h-ood-{i}", "query": q, "gold_doc_id": r["doc_id"],
                    "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer",
                    "type": "ood_typo"})
    # 5) poison_trap 10: server-side smart-poison docs (9100+) mimic these gold
    # rows with ONE flipped fact. Gold = real row; trap = its mimic.
    # Queries stay close to the gold question so BOTH surface top-3 and only
    # number-exactness + file-corroboration separate them.
    # (query, gold_doc_id, true distinctive tokens)
    TRAPS = [
        ("آیا بدهی با مبلغ خیلی کم هم باعث کاهش شدید امتیاز میشه؟", 326, ["250"]),
        ("سابقه چک برگشتی تا چه مدت تو گزارش اعتباری شرکت میمونه؟", 30, ["5"]),
        ("اقساط معوق شرکت تا چه مدت بعد از پرداخت بدهی رو امتیاز اثر میذاره؟", 88, ["24"]),
        ("سهم سابقه چک تو امتیاز اشخاص حقیقی چند درصده؟", 247, ["12"]),
        ("بازه امتیازی C2 از چند تا چنده؟", 107, ["C2", "559"]),
        ("هزینه گزارش اعتبارسنجی شرکت‌ها و سازمان‌ها چقدره؟", 81, ["12000"]),
        ("اگه شرکت محکومیت مالی داشته باشه رتبش چقدر میاد پایین؟", 56, ["250"]),
        ("بازه بررسی سابقه تسهیلاتی چند ساله؟", 5, ["5"]),
        ("چند درصد امتیاز شرکت به مالیات وابسته‌ست؟", 125, ["18"]),
        ("سقف تسهیلات مشمول بخشنامه جنگ دوم چقدره؟", 335, ["700", "500"]),
    ]
    _trows = {r["doc_id"]: r for r in rows}
    for i, (q, gid, must) in enumerate(TRAPS):
        r = _trows.get(gid)
        if r is None or not r["BriefAnswer"]:
            print(f"TRAP REVIEW: gold {gid} not usable")
            continue
        hid.append({"id": f"h-trap-{i}", "query": q,
                    "gold_doc_id": r["doc_id"], "gold_brief": r["BriefAnswer"],
                    "gold_category": r["Category"], "expect": "answer",
                    "type": "poison_trap", "must_contain": must})
    # (paraphrase section removed)
    json.dump(hid, open(HID, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:
        from server._vault import save_hidden
        save_hidden(hid)
    except Exception as e:
        print(f"(vault enc skipped: {e})")
    print(f"visible={len(vis)} hidden={len(hid)} "
          f"(base/swap/amb/ood/trap={[sum(1 for h in hid if h['type']==t) for t in ['base','slot_swap','ambiguous','ood_typo','poison_trap']]})")


def load_hidden():
    """Runtime loader: encrypted store first, plaintext fallback (dev only)."""
    import os as _os
    if _os.path.exists(HID):
        return json.load(open(HID, encoding="utf-8"))
    from server._vault import load_hidden as _lh
    return _lh()
