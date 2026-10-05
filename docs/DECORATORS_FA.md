# راهنمای دکوراتورها — سازوکار (نه راه‌حل)

هر مرحله یک تابع است که با دکوراتور ثبت می‌شود. برای تغییر رفتار، کافی است
تابعی با همان دکوراتور در کد خودتان تعریف کنید — همان جایگزین می‌شود:

```python
import rubbish_rag as R

@R.chunker
def chunk(docs):
    # ورودی: [{"doc_id","Question","Category","BriefAnswer","Answer","Keyword"}]
    # خروجی: [{"doc_id","chunk_id","text","category"}]
    # رفتار فعلی: برش ۳۰۰ کاراکتری Answer. (TODO فایل pipeline.py را ببینید.)

@R.retriever
def retrieve(query, topk=5):
    # ورودی: کوئری خام. خروجی: لیست hits شامل bm25/dense/fused.
    # رفتار فعلی: ارسال دست‌نخورده به API ریموت. (TODO فایل pipeline.py را ببینید.)

@R.reranker
def rerank(query, hits):
    # ورودی/خروجی: لیست hits. رفتار فعلی: مرتب‌سازی با شمارش کلمات مشترک.

@R.resolver
def resolve(query, hits):
    # خروجی باید قرارداد docs/README_FA.md را رعایت کند (answer یا clarify).
    # رفتار فعلی: همیشه answer. (TODO فایل pipeline.py را ببینید.)
```

چه چیزی را کِی بازنویسی کنید؟ تصمیم با شماست — اما قاعده بازی:
API ریموت مال شما نیست؛ نرمال‌سازی، بازنویسی کوئری، فیلتر، رتبه‌بندی مجدد و
تصمیم نهایی همه سمت شماست و همه باید با trace و نمودار توجیه شوند.
