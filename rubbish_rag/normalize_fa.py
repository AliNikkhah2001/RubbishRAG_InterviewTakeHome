"""Broken Persian normalizer (RubbishRAG default — DO NOT SHIP LIKE THIS).

This is the 1-minute-AI version: it does nothing.
Your job: fix it (see docs/DECORATORS_FA.md).
"""

from . import chunker as _chunker_reg  # noqa (keeps import style uniform)


def normalize_fa(text: str) -> str:
    # RUBBISH: no digit conversion, no kaf/yeh fix, no ZWNJ handling.
    return (text or "").strip()
