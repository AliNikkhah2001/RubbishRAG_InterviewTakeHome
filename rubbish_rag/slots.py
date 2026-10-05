"""Slot lists + BROKEN extractor (always returns empty).

Slots are mandatory for this task:
  BANK, RANK (A1..E3), PERSONA (حقیقی/حقوقی), DEBT (تسهیلاتی/مالیاتی/چک/محکومیت),
  AMOUNT, TIME.

Fix me: implement regex-based extraction AFTER normalization.
See docs/DECORATORS_FA.md for examples.
"""

BANKS = [
    "ملی", "صادرات", "تجارت", "توسعه صادرات", "ملت", "سپه",
    "پاسارگاد", "دیجی‌پی", "اسنپ‌پی", "تارا", "دیجی‌کالا",
]

RANKS = [f"{L}{N}" for L in "ABCDE" for N in "123"]


def extract_slots_broken(query: str) -> dict:
    # RUBBISH: sees nothing.
    return {"BANK": None, "RANK": None, "PERSONA": None, "DEBT": None,
            "AMOUNT": None, "TIME": None}
