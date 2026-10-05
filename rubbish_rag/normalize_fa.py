"""Persian text normalization (currently a no-op).

TODO:
  1. Take 5 queries and their correct rows. Compare the query's wording
     with the row's wording character by character. What differs?
     (digits? kaf/yeh? half-spaces? colloquial vs formal?)
  2. Decide what 'the same word' means for this corpus, and implement it.
  3. Prove the effect: same probe before/after, logged in traces/.
"""


def normalize_fa(text: str) -> str:
    # TODO: implement. Currently returns the input (stripped) unchanged.
    return (text or "").strip()
