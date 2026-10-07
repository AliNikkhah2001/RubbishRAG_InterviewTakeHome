# 📋 RubbishRAG Challenge Redesign Change Log

**Document Purpose:** Complete architectural record of problems identified, design decisions made, implementations delivered, and expected engineering impact.

---

## Change 1: Three-Tier Task Architecture & Explicit Time Budget

- **Problem:** The original challenge presented an open-ended laundry list of 10 faults with no clear distinction between minimum passing requirements, elective deep dives, and staff-level bonuses. Candidates had no guidance on whether to spend 3 hours or 20 hours.
- **Decision:** Restructure into a transparent 3-tier hierarchy:
  1. **Tier 1: Required Core (~3–4 Hours)** — 4 foundational tasks (Retrieval Diagnostics, Hybrid Fusion, Persian Normalization, Chunking Strategy).
  2. **Tier 2: Choose-2 Engineering Tracks (~2 Hours)** — Candidate chooses 2 of 4 elective topics (Reranking & Diversity, Adversarial Defense, Polarity & Negation, Grounded Clarification).
  3. **Tier 3: Staff-Level Bonus Track (~3–4 Hours, Optional)** — Adaptive System-1 RAG Decision Judge.
- **Implementation:** Updated `README.md`, created `docs/tasks.html`, and documented explicit grading weights.
- **Expected Impact:** Equalizes candidate expectations, prevents take-home burnout, and gives senior candidates a dedicated surface to showcase advanced system design without penalizing candidates with limited time.

---

## Change 2: Progressive Information Architecture (Symptom-First vs. Spoiler Catalog)

- **Problem:** The documentation previously functioned like an answer key, explicitly naming "F1: RRF", "F2: b=0.9", "F3: doc 9000", which destroyed the investigative inquiry of a senior interview.
- **Decision:** Shift candidate-facing documentation to **symptom-driven investigation areas** and empirical diagnostic workflows. Seeded implementation secrets (e.g. server jitter seeds, exact scoring weights) remain strictly within private grader docs.
- **Implementation:** Refactored `README.md`, `docs/architecture.html`, and created `docs/guide.html` focusing on hypothesis formulation, probe design, and trace analysis.
- **Expected Impact:** Candidates are evaluated on their ability to isolate variables, formulate hypotheses, and interpret distributions rather than blindly executing pre-given instructions.

---

## Change 3: Enhanced Observability & Experimental CLI Tooling

- **Problem:** Candidates only had `bepar` (single query) and `bench` (batch score), requiring manual JSON parsing of `traces/trace.jsonl` to locate evidence for `PROOF.md`.
- **Decision:** Provide first-class developer tooling:
  - `rubbish inspect-trace <TRACE_ID>`: Pretty-prints full retrieval and resolver state for any logged query.
  - `rubbish compare <RUN_A> <RUN_B>`: Side-by-side terminal comparison of benchmark metrics, accuracy delta, and latency percentiles.
  - Enriched trace schema capturing normalized query, extracted slots, decision codes, and latency breakdowns.
- **Implementation:** Added subcommands to `rubbish.py`, updated logging in `server/_hidden_retriever.py` and `rubbish_rag/orchestrator.py`.
- **Expected Impact:** Drastically speeds up candidate feedback loops and ensures `PROOF.md` citations are backed by verifiable trace data.

---

## Change 4: Open-Weight Adaptive System-1 RAG Decision Judge

- **Problem:** The system was restricted to static retrieve-then-read execution, missing modern agentic RAG paradigms (pre-retrieval query routing, dynamic context budgeting, post-retrieval evidence sufficiency, and calibrated escalation).
- **Decision:** Design a state-of-the-art **Adaptive RAG Decision Judge** bonus track inspired by Self-RAG, Adaptive-RAG, CRAG, and JEV-as-a-Judge:
  - Structured decision schemas (`PreRetrievalDecision`, `RetrievalPlan`, `EvidenceDecision`, `FinalDecision`).
  - Provider-neutral protocol (`RAGDecisionJudge`) with a fast, zero-dependency local CPU-viable model and adapters for small open-weight LLMs (e.g., Llama-3.2-1B, Qwen2.5-0.5B/1.5B).
  - Explicit multi-step state machine with bounded retrieval rounds.
  - Calibrated confidence scoring (Brier score, ECE) for selective escalation.
  - Standalone evaluation dataset (`data/judge_dataset.json`) with train/dev/test splits.
- **Implementation:**
  - `rubbish_rag/judge.py`: Typed protocol, decision engine, heuristic classifier, and local Llama/Qwen adapter.
  - `data/judge_dataset.json`: 80+ labeled routing and sufficiency examples.
  - `rubbish.py judge` and `rubbish.py judge-bench` CLI commands.
  - `docs/adaptive-judge.html`: Comprehensive guide with state machine diagrams and calibration math.
- **Expected Impact:** Allows senior and staff candidates to demonstrate high-level multi-stage AI systems architecture and quantitative calibration analysis on local hardware.

---

## Change 5: Test Suite, Reproducibility & CI Infrastructure

- **Problem:** The repository had zero automated tests (`tests/` directory did not exist) and no CI pipeline, risking regressions during candidate development.
- **Decision:** Introduce a complete testing suite and GitHub Actions workflow.
- **Implementation:**
  - `tests/test_normalization.py`: Unit tests for digits, Arabic letters, ZWNJ, and colloquial verbs.
  - `tests/test_slots.py`: Unit tests for bank names, credit ranks (A1–E3), persona, debt categories, and negation.
  - `tests/test_pipeline.py`: Tests for chunking, decorator registration, and scoring.
  - `tests/test_judge.py`: Tests for pre-retrieval routing, dynamic top-k, evidence sufficiency, and calibration metrics.
  - `tests/test_cli.py`: Smoke tests for all CLI subcommands (`salam`, `bepar`, `bench`, `judge`, etc.).
  - `tests/test_packaging.py`: Validation of `bastesh` zip integrity and manifest.
  - `.github/workflows/ci.yml`: Automated CI running on Python 3.11 with pytest, linting, and smoke checks.
- **Expected Impact:** Gives candidates instant verification of their changes, guarantees zero broken imports, and enables automated grading in CI.

---

## Change 6: Multi-Page Documentation Suite & Metrics Glossary

- **Problem:** Key information retrieval concepts (MRR, nDCG, Brier score, ECE, Pareto frontiers) were assumed rather than documented, disadvantaging candidates without academic IR backgrounds.
- **Decision:** Build a cohesive, responsive documentation site on GitHub Pages with dedicated guides and a clear glossary.
- **Implementation:**
  - `docs/index.html`: Premise, quickstart, and challenge story.
  - `docs/tasks.html`: Comprehensive breakdown of Required, Choose-N, and Bonus tracks.
  - `docs/architecture.html`: Visual data flow diagrams for both baseline and adaptive pipelines.
  - `docs/adaptive-judge.html`: Adaptive judge specification, state machine, and calibration theory.
  - `docs/glossary.html`: Metrics glossary defining Recall@K, MRR, nDCG, Hit@K, Brier Score, ECE, and latency trade-offs.
  - `docs/guide.html`: Hands-on scientific probing methodology.
  - `docs/deliverables.html`: Packaging instructions, evaluation criteria, and presentation expectations.
  - `docs/ui.html`: Interactive Studio UI and LangChain orchestrator reference.
  - `docs/style.css`: Unified dark-theme responsive design with sidebar navigation and card layouts.
- **Expected Impact:** Professional, candidate-centric developer experience that acts as a gold-standard interview take-home.
