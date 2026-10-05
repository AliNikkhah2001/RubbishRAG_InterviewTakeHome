"""Correct Persian normalization (for evaluator + reference fix — NOT the broken starter)."""
import re

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EN_DIGITS = "0123456789"
_TR = {}
for a, b in zip(FA_DIGITS + AR_DIGITS, EN_DIGITS * 2):
    _TR[ord(a)] = b

COLLOQUIAL = {
    "میشه": "می‌شود", "نمیشه": "نمی‌شود", "چیه": "چیست",
    "چقد": "چقدر", "واسم": "برایم", "بهم": "بهم",
    "نمیخوام": "نمی‌خواهم", "میخوام": "می‌خواهم",
}


def normalize_fa_full(s: str) -> str:
    s = (s or "").translate(_TR)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("ـ", "")
    s = s.replace("\u200c", " ")
    s = re.sub(r"\s+", " ", s).strip()
    for k, v in COLLOQUIAL.items():
        s = s.replace(k, v)
    return s.lower()
