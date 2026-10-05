"""Query entities: reference lists + empty extractor.

Observation: swapping one word in a query can flip the correct answer
(a bank name, a rank code, حقیقی vs حقوقی, an amount, a date...).

TODO:
  1. Find 3 pairs of corpus rows where a single swapped span changes the answer.
  2. Decide which spans your system must detect — and what it should do
     when the query does NOT contain them.
  3. Implement it here (this stub currently detects nothing).

Below are starter lists mined from the corpus. Extend or replace them
as your experiments dictate.
"""

BANKS = [
    "ملی", "صادرات", "تجارت", "توسعه صادرات", "ملت", "سپه",
    "پاسارگاد", "دیجی‌پی", "اسنپ‌پی", "تارا", "دیجی‌کالا",
]

RANKS = [f"{L}{N}" for L in "ABCDE" for N in "123"]


def extract_slots_broken(query: str) -> dict:
    # TODO: implement. Currently detects nothing.
    return {"BANK": None, "RANK": None, "PERSONA": None, "DEBT": None,
            "AMOUNT": None, "TIME": None}
