# Capstone Acceptance Criteria Checklist

Status is based on the local code, reports, and transcripts inspected on 2026-11-08. A checked item has supporting code or evidence; unchecked items need the stated external action or verification.

## Part 1 — Dataset and RAG

- [x] `dataset.py` produces at least 40 tickets, covers each required category/status, and has 10–30% escalated. **Evidence:** 240 tickets; 48 per category and status; 47 escalated (19.58%). Design choices are in [README.md](README.md#2-dataset-design-decisions); output in [dataset_report.json](data/reports/dataset_report.json).
- [x] Knowledge base has at least 12 documents covering every required topic. **Evidence:** 55 documents are indexed.
- [x] Fixed-overlap and sentence chunking are embedded and indexed in separate ChromaDB collections. **Evidence:** 55 fixed chunks and 166 sentence chunks; sample queries are in [rag_tests.md](transcripts/rag_tests.md).
- [x] Grounded generation is demonstrated on at least five in-scope queries and one out-of-scope query that falls back. **Evidence:** five supported questions plus France fallback in [rag_tests.md](transcripts/rag_tests.md).
- [x] Precision and recall are computed for both collections on the same five queries, with arithmetic and a numbers-based recommendation. **Evidence:** mean fixed precision/recall 0.250/1.000; sentence 0.300/1.000; per-query arithmetic in [retrieval_comparison.csv](reports/retrieval_comparison.csv) and recommendation in [README.md](README.md#5-compare-retrieval-precision-and-recall).

## Part 2 — CrewAI, memory, and guardrails

- [x] `check_support_ticket_status` returns ticket status, resolution time, and a designed escalation score. **Evidence:** score formula `0.75 * escalated + 0.25 * (1 - days_since_created / 30)`; recommendation threshold 0.25 at the 80th percentile; see [escalation_report.json](data/reports/escalation_report.json).
- [x] The CrewAI crew has Retrieval, Lookup, and Composer agents; RAG and lookup are invoked on separate queries via `.kickoff()`. **Evidence:** counters `rag_lookup: 1`, `ticket_lookup: 1` in [crew_tests.md](transcripts/crew_tests.md).
- [x] Multi-turn memory carries context within a session and is absent in a fresh session. **Evidence:** [memory_tests.md](transcripts/memory_tests.md).
- [x] Crew responses validate against a declared Pydantic schema. **Evidence:** `SupportResponse` is validated by the crew adapter and API response model; see [schemas.py](src/ola_support/schemas.py).
- [x] Input PII masking and injection detection, plus output groundedness refusal, each fire on deliberate examples. **Evidence:** [guardrail_tests.md](transcripts/guardrail_tests.md).

## Part 3 — FastAPI, logs, and evaluation

- [x] FastAPI exposes at least two working HTTP endpoints and a WebSocket; disconnect does not stop the app. **Evidence:** `/ask` and `/add-document` returned 200; `/ws/chat` handled two turns, logged disconnect, and a later `/openapi.json` returned 200. See [api_tests.md](transcripts/api_tests.md).
- [x] JSONL request logs include a trace ID and timing and do not contain the raw fixed-format test phone. **Evidence:** all six records from the acceptance run had `trace_id` and `duration_ms`; whole local log scan found 15 entries with no missing fields and no test phone. See [api_tests.md](transcripts/api_tests.md).
- [x] All four scores are reported per query for all 15 cases under `MOCK_LLM`, with four averages. **Evidence:** [evaluation_scores.csv](reports/evaluation_scores.csv), [evaluation_summary.json](reports/evaluation_summary.json), and [evaluation_tests.md](transcripts/evaluation_tests.md). Means: Accuracy 5.000, Grounding 5.000, Completeness 4.333, Safety 5.000.

## Part 4 — AutoGen, governance, and cache

- [x] AutoGen demonstrates one unchanged approval and one revision, with structured Pydantic verdicts. **Evidence:** [autogen_tests.md](transcripts/autogen_tests.md).
- [x] Lookup tool is restricted to the Lookup Agent; risk and runtime cap are documented; an oversized request is rejected. **Evidence:** unauthorized Composer wiring was blocked; risk is Medium; 7,756-token estimate was rejected against the 2,000 cap before tool calls. See [governance_tests.md](transcripts/governance_tests.md).
- [x] Response cache records a hit on repeated normalized text and avoids a redundant tool call. **Evidence:** one miss/producer call followed by one hit; RAG invocation remained at one in [governance_tests.md](transcripts/governance_tests.md).

## Submission

- [x] A public GitHub repository exists: [shouryasood/ola-domain-support-agent](https://github.com/shouryasood/ola-domain-support-agent). GitHub repository metadata confirmed its visibility is `public`.
- [x] The public repository includes the dataset generator, knowledge base, RAG/crew/API code, reports, and task transcripts; GitHub file fetches confirmed the dataset source, API transcript, evaluation scores/summary, and API routes.
- [x] The main `README.md` states the Ola track and explains `MOCK_LLM`/no-key execution.
- [x] Submit the repository URL through the capstone’s submission channel. This external submission cannot be confirmed from the repository.

## Evidence files

- Project-wide step-by-step explanation: [Readme_Evaluation_Results.md](Readme_Evaluation_Results.md)
- API acceptance: [api_tests.md](transcripts/api_tests.md)
- 15-query evaluation: [evaluation_tests.md](transcripts/evaluation_tests.md)
- Full project guide: [README.md](README.md)
