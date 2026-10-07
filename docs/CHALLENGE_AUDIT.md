# 🔍 RubbishRAG Challenge Audit & Architectural Review

**Auditor:** Principal AI Engineer, Evaluation Engineer & Interview Architect  
**Target Repository:** `RubbishRAG — "AI made it in 1 minute! …prove it wrong"`  
**Target Role:** Senior / Staff AI Engineer, RAG Researcher, Machine Learning Engineer  
**Date:** October 2026  
**Scope:** Technical correctness, candidate feasibility, fairness, evaluation rigor, documentation, and candidate experience.

---

## 1. Executive Summary

RubbishRAG is a take-home interview challenge built around a Persian credit-scoring RAG system over 330 domain QA pairs (`corpus/test.csv`). The premise—diagnosing a naive, flawed pipeline that scores ~30% on visible retrieval and upgrading it with empirical rigor—is pedagogically strong and highly realistic. It tests actual engineering discipline (observability, hypothesis testing, error analysis) rather than prompt-engineering trivia.

However, a comprehensive audit reveals **six structural weaknesses** in the original artifact:

1. **Information Asymmetry & Spoilers:** The challenge previously listed all 10 internal flaws as a checklist, undermining the core diagnostic exercise (testing whether a candidate can discover failure modes vs. simply checking off a predetermined to-do list).
2. **Visible Benchmark Skew:** The 20 visible practice queries (`server/visible_bench.json`) were 100% `base` queries expecting `answer`. Zero ambiguous queries were included in the visible set, making it impossible for candidates to validate ambiguity detection or clarification gating before submission without blind trial-and-error.
3. **Undefined Scope & Time Budget:** The assignment lacked explicit boundaries between "Required Core", "Choose-N Deep Dives", and "Bonus Work", leading to extreme variance in candidate time commitment (from 2 hours to 20+ hours) and potential burnout.
4. **Language & Domain Friability:** For candidates without native Persian familiarity, script nuances (Arabic vs. Persian Yeh/Kaf, ZWNJ, Persian numerals) risked becoming an accidental disqualifier rather than a test of information retrieval and system architecture.
5. **Observability Gaps:** While `/retrieve` logged raw hits to `traces/trace.jsonl`, candidate tooling lacked trace inspection, trace diffing, run comparison (`rubbish compare`), and automated regression tests.
6. **Absence of Modern Decision Layer / RAG Judge Evaluation:** The architecture stopped at static rule-based heuristics rather than testing senior-level adaptive RAG concepts (pre-retrieval routing, dynamic context budgeting, post-retrieval evidence sufficiency, and calibrated confidence-based escalation).

---

## 2. Structured Component Inventory & Risk Matrix

| Area | Current Behavior | Intended Skill | Problem / Risk | Severity | Proposed Change | Evidence / Justification |
|---|---|---|---|---|---|---|
| **Visible Benchmark** | 20 queries, all `type: base`, all `expect: answer` | Validation of pipeline performance across all query types | Candidates cannot test clarification or ambiguity resolution locally; `clarify_acc` is always 0.0 on visible bench | **Critical** | Expand `visible_bench.json` to 25 queries including representative ambiguous and slot-sensitive samples | `rubbish bench` yields `clarify_acc: 0.0` with no way to measure clarification locally |
| **Documentation & Spoilers** | Previously listed 10 specific flaws and exact remedies | Diagnostic problem-solving & hypothesis formulation | Reveals diagnoses upfront; shifts test from diagnostic inquiry to mechanical implementation | **High** | Reframe candidate docs around observable symptoms & inquiry areas; reserve fault catalog for grading rubric | `README.md` and `docs/architecture.html` explicitly named RRF, $b=0.9$, and doc 9000 |
| **Time Budget & Scope** | Single monolithic task list with unclear completion boundaries | Senior time management & engineering prioritization | Unclear whether candidates must fix all 10 areas; high risk of candidate overwork or incomplete submissions | **High** | Restructure into **Required Core (3h)** + **Choose-2 Deep Dives (2h)** + **Staff Bonus Track** | Lack of stated time budget creates fairness disparity between candidates |
| **Adversarial / Poison Filtering** | Fake documents with IDs $\ge 9000$ in index | Evidence quality verification & grounding | If candidates filter purely on `doc_id >= 9000`, they test magic constants rather than data grounding | **High** | Clarify in docs that robust solutions verify chunks against verified corpus entries or detect keyword repetition | Server evaluator checks `c >= 9000`, but pipeline should use principled grounding |
| **Persian Normalization** | Starter code is a no-op; normalization left to candidate | Text processing & domain adaptation | Non-Persian speakers or unfamiliar candidates spend hours debugging Unicode tables instead of RAG architecture | **Medium** | Provide comprehensive normalization blueprint, unit test suite, and reference canonicalizer in starter kit | Digits (`۲۵۰` vs `250`) and half-space `\u200c` are domain friction, not IR architecture |
| **Observability & Tracing** | Traces written as minimal JSON lines in `traces/trace.jsonl` | Diagnostic observability & reproducibility | No CLI command to inspect a single trace ID or compare two benchmark runs side-by-side | **Medium** | Add `rubbish.py inspect-trace <ID>`, `rubbish.py compare <run1> <run2>`, and enriched trace schema | Candidates must open raw JSONL or write ad-hoc jq scripts |
| **Testing Strategy** | Zero unit or integration tests in repo; no `tests/` directory | Software quality & regression prevention | Regressions in normalization, chunking, or slot parsing go unnoticed until benchmark run | **High** | Add comprehensive `tests/` suite (unit, integration, CLI smoke, packaging) runnable via `pytest` | `find . -name "test_*.py"` returned 0 files |
| **CI / CD Automation** | No GitHub Actions workflow | Continuous integration & build verification | PRs and submissions cannot be validated automatically in CI | **Medium** | Add `.github/workflows/ci.yml` running lint, pytest, and CLI smoke tests | Missing `.github/` folder |
| **Decision Layer / Judge** | Static top-k=5 retrieval on all queries; no adaptive stopping | Adaptive RAG, dynamic routing, decision modeling | Fails to evaluate state-of-the-art agentic RAG patterns (Self-RAG, Adaptive-RAG, CRAG) | **High** | Design & implement open-weight System-1 Decision Judge bonus track with dynamic top-k and calibration | Modern production RAG requires routing, sufficiency checks, and selective prediction |

---

## 3. Detailed Audit by Evaluation Dimension

### 3.1 Technical Correctness
- **Sealed Evaluator:** `server/evaluator.py` correctly calculates Hit@3 against `acceptable` doc IDs and applies an immediate zero if any cited document has `doc_id >= 9000`. Clarify items correctly check `pred["status"] == "clarify"`.
- **Benchmark Execution:** `rubbish bench` executes cleanly and outputs `traces/metrics.json` with aggregate accuracy, answer accuracy, clarify accuracy, and timing percentiles (mean, p50, p95).
- **Plotting:** `rubbish bekesh` correctly generates `score_spread.png`, `length_vs_bm25.png`, `repetition_vs_bm25.png`, and `report_card.png` using matplotlib in headless `Agg` mode.
- **Packaging:** `rubbish bastesh` packages code, traces, plots, identity, and computes a valid SHA256 integrity digest.
- **Identified Flaw:** In `server/evaluator.py`, lines 27–34 contain an inert check (`all(normalize_fa_full(m) in txt or True for m in [])`) that does not penalize missing brief entities. This means evaluation is strictly Hit@3 + poison penalty. This is acceptable for candidate feasibility, but should be documented clearly so candidates know the evaluator checks Hit@3 citation accuracy.

### 3.2 Candidate Feasibility and Fairness
- **Hardware Viability:** The entire challenge runs 100% locally on CPU without GPUs, cloud accounts, or paid API keys. Memory usage is under 150 MB RAM, and disk footprint is under 20 MB.
- **Runtime:** A full benchmark run over 20 queries takes ~180 ms. Single probes take ~10 ms.
- **Python Compatibility:** Pinned to Python 3.11 for sealed builds. A clear version guard in `rubbish.py` (`_check_sealed_compat`) explains this immediately if a candidate runs on an incompatible version.
- **Fairness Risk Mitigation:** Providing structured Persian normalization helpers and tokenization tools ensures candidates are evaluated on information retrieval, search fusion, and evidence reasoning rather than rote Persian character code memorization.

### 3.3 Depth of AI/RAG Engineering Evaluation
- The challenge successfully tests:
  - Sparse vs. dense score calibration and rank fusion (RRF vs. naive linear scaling)
  - Information retrieval length bias ($b$ parameter compensation in BM25)
  - Corpus grounding and adversarial document filtering
  - Entity-slot extraction and query-document alignment
  - Gated ambiguity handling (when to clarify vs. when to answer)
  - Latency vs. accuracy trade-offs

### 3.4 Documentation and Developer Experience
- The documentation previously lacked:
  - An explicit Metrics Glossary defining IR metrics (Recall@K, MRR, nDCG, Hit@K, Brier Score, ECE).
  - A structured task matrix distinguishing core requirements from optional explorations.
  - Step-by-step guidance on reproducing diagnostic traces and validating hypotheses.
  - Interactive trace inspection tools.

### 3.5 Realism as a Senior AI Engineering Take-Home
- Real-world production RAG systems are not static linear scripts; they are dynamic decision loops.
- Adding the **Adaptive System-1 Decision Judge** track bridges the gap between basic academic RAG and modern production-grade agentic architectures (Adaptive-RAG, Self-RAG, CRAG).

---

## 4. Recommendations & Roadmap

1. **Restructure Tasks:**
   - **Tier 1: Required Core (3–4 Hours):** Retrieval Characterization (Task A), Hybrid Fusion (Task B), Persian Normalization (Task C), Chunking & Metadata (Task D).
   - **Tier 2: Choose-2 Engineering Tracks (2 Hours):** Reranking & Diversity (Task E), Adversarial Defense (Task F), Polarity & Negation (Task G), Grounded Resolution & Clarification (Task H).
   - **Tier 3: Staff-Level Bonus Track (Optional, 3–4 Hours):** Adaptive System-1 RAG Decision Judge (Task I).
2. **Expand Visible Benchmark:** Add 5 representative queries (2 ambiguous, 2 slot-sensitive, 1 colloquial) to `server/visible_bench.json` so candidates can locally validate clarification and slot routing.
3. **Enhance Observability:** Add `rubbish.py inspect-trace` and `rubbish.py compare` to give candidates first-class experimental tools.
4. **Implement the System-1 Judge:** Provide typed dataclasses/protocols, local CPU-viable adapter, dedicated dataset, calibration metrics (Brier score, ECE), and benchmark commands (`rubbish.py judge`, `rubbish.py judge-bench`).
5. **Add Test Suite & CI:** Create `tests/` with pytest coverage and `.github/workflows/ci.yml`.
6. **Redesign Documentation:** Publish updated multi-page GitHub Pages site with architecture diagrams, tasks breakdown, adaptive judge guide, and metrics glossary.
