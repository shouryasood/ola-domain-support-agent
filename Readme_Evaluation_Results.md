# Project Steps and Evaluation Results

This file summarizes why each capstone step was done, the implementation, and the observed result. The agent and judge runs use deterministic `MOCK_LLM` mode and require no LLM API key. The final evaluation and API demonstrations also ran with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` using the cached `sentence-transformers/all-MiniLM-L6-v2` model.

See [README.md](README.md) for environment setup and commands. This report describes the recorded outcomes; it does not claim the retrieval quality is production-ready.

## Results overview

| Area | Observed result |
|---|---|
| Dataset | 240 generated tickets; 48 in each of five required categories and five required statuses; 47 escalated (19.58%). |
| Knowledge base | 55 policy documents, including every required topic. |
| Vector indexes | 55 fixed-overlap chunks (90 words, 20-word overlap) and 166 sentence chunks in separate cosine ChromaDB collections. |
| Similarity threshold | 0.3730437159538269, chosen between measured in-scope and out-of-scope score clusters. |
| Retrieval evaluation | Fixed overlap mean precision 0.250 / recall 1.000; sentence mean precision 0.300 / recall 1.000. |
| API | `/ask` and `/add-document` both returned 200; WebSocket processed two turns, logged disconnect, and the app answered a follow-up HTTP request with 200. |
| JSONL | Six entries from the acceptance run all had trace IDs and durations; no raw test phone value was found. A full local-log scan found 15 entries, none missing either field. |
| 15-query judge averages | Accuracy 5.000, Grounding 5.000, Completeness 4.333, Safety 5.000. |
| AutoGen/governance/cache | Grounded draft approved; unsupported claim revised; unauthorized lookup wiring rejected; oversized request blocked; repeated query produced a cache hit. |

## Part 1 — Dataset and RAG

### 1. Generate and validate support tickets

**Why:** Repeatable ticket records support lookup demonstrations and let a grader reproduce category, status, and escalation counts.

**Implementation and result:** `src/ola_support/dataset.py` generates 240 records. The data seed is `2026`; escalation seed is `10`; category and status weights are equal (20% each); escalation probability is 0.20; resolution duration is 0.5–96 hours; ticket age is 0–30 days; synthetic `amount_inr` is ₹50–₹5,000. The generator produced 48 tickets per required category/status and 47 escalated (19.58%), inside the 10–30% band.

Evidence: [dataset JSON](data/generated/support_tickets.json) and [dataset report](data/reports/dataset_report.json).

### 2. Write the support-policy knowledge base

**Why:** Ground answers in authored policy text instead of model priors, and demonstrate every required support topic.

**Implementation and result:** `scripts/create_knowledge_base.py` generated 55 Markdown documents. The required 12 topics are present: ticket priority, SLA by severity, escalation, refund/compensation, communication channels, business hours/holidays, repeat complaints, service credits, feedback collection, VIP handling, outage communication, and ticket retention. These are demonstration policies and are not presented as real Ola policy.

### 3. Chunk, embed, and index both strategies

**Why:** Chunk size and boundaries affect what context is retrieved, so both required strategies are evaluated on the same corpus.

**Implementation and result:** The fixed strategy splits at 90 words with a 20-word overlap; the sentence strategy splits on sentence boundaries. Both use `sentence-transformers/all-MiniLM-L6-v2` and separate ChromaDB collections with cosine distance. The 55-document index has 55 fixed chunks and 166 sentence chunks. The final evaluation and API reindex ran offline with the cached model.

### 4. Calibrate fallback and demonstrate grounded generation

**Why:** Unsupported questions should receive a stable “I don’t know” answer instead of an answer inferred from general knowledge.

**Implementation and result:** On the sentence collection, in-scope top-1 scores were 0.630744, 0.600182, 0.708150, 0.589640, and 0.591528. Out-of-scope scores were 0.156447 (capital of France) and 0.106316 (sourdough bread). The selected midpoint threshold is 0.3730437159538269; retrieval below it returns `I don't know based on the available support policies.` Five in-scope examples and the France fallback are recorded.

Evidence: [calibration report](reports/rag_threshold.json) and [six-query RAG transcript](transcripts/rag_tests.md).

### 5. Compare document-level precision and recall

**Why:** Similarity does not prove that retrieved context is relevant. Precision and recall were computed after mapping chunks to parent document IDs and deduplicating.

| Query | Fixed precision | Fixed recall | Sentence precision | Sentence recall |
|---|---:|---:|---:|---:|
| Ticket priority | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| SLA severity | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| Escalation | 1/4 = 0.250 | 1/1 = 1.000 | 1/4 = 0.250 | 1/1 = 1.000 |
| Refund review | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| Account-specific channel | 1/4 = 0.250 | 1/1 = 1.000 | 1/4 = 0.250 | 1/1 = 1.000 |
| **Mean** | **0.250** | **1.000** | **0.300** | **1.000** |

Sentence chunking is the provisional choice because its mean precision is 0.050 higher with the same recall. Both collections still retrieve unrelated documents, so relevance needs further tuning.

Evidence: [per-query retrieval CSV](reports/retrieval_comparison.csv).

## Part 2 — CrewAI tools, memory, and guardrails

### 6. Look up ticket status and compute escalation score

**Why:** Status lookup must be factual and the escalation recommendation explainable from ticket data.

**Implementation and result:** The score formula is `0.75 * float(escalated) + 0.25 * (1 - days_since_created / 30)`. The threshold is 0.25, the 80th percentile of this dataset’s scores. `TKT-00001` returned `Closed`, 91.32 hours, and a score of 0.191667; escalation was not recommended. An unknown ID returns not found.

Evidence: [escalation report](data/reports/escalation_report.json).

### 7. Build and run the three-agent CrewAI crew

**Why:** Separate policy retrieval from private record lookup, then compose a structured answer from the selected evidence.

**Implementation and result:** The Policy Retrieval Agent receives `rag_lookup`, the Ticket Lookup Agent receives `check_support_ticket_status`, and the Response Composer combines tool output. Separate kickoffs invoked each tool once. Outputs were validated as Pydantic `SupportResponse` objects. The policy sample included unrelated sources, noted as a retrieval quality issue.

Evidence: [CrewAI transcript](transcripts/crew_tests.md).

### 8. Preserve session context and isolate fresh chats

**Why:** A user should be able to refer to an earlier ticket in the same conversation, while another session must not inherit that context.

**Implementation and result:** Session A introduced `TKT-00001`; a later turn identified that same ticket. Fresh Session B reported no ticket ID. Memory is in-process and resets on restart. The expected LangChain deprecation warning was observed.

Evidence: [memory transcript](transcripts/memory_tests.md).

### 9. Validate structured responses

**Why:** A stable schema lets the API validate output instead of forwarding malformed model text.

**Implementation and result:** `SupportResponse` defines answer, source IDs, ticket fields, a bounded escalation score, and fallback status. Crew outputs are converted to and validated against this Pydantic schema.

### 10. Apply PII, injection, and groundedness guards

**Why:** Prevent fixed-format phone values from reaching the model unmasked, block prompt override attempts, and refuse unsupported answers.

**Implementation and result:** Demonstrations show a phone replaced with `[PHONE REDACTED]`, an injection detected, supported input proceeding, out-of-scope input falling back, and an intentionally ungrounded claim rejected. Free-text names, addresses, and payment details are explicitly outside the masker’s fixed-format scope.

Evidence: [guardrail transcript](transcripts/guardrail_tests.md).

## Part 3 — API, logging, and evaluation

### 11. Expose HTTP routes and WebSocket chat

**Why:** Riders, drivers, and support staff need request/response endpoints, document ingestion, and a multi-turn channel.

**Implementation and result:** `POST /ask` and `POST /add-document` returned HTTP 200 in the API acceptance run. The temporary document test reported 56 documents / 56 fixed chunks / 168 sentence chunks, confirmed the phone was masked before storage, then removed the test document and rebuilt the baseline index of 55 documents. The WebSocket handled two ticket-status turns; after disconnect, `/openapi.json` still returned 200.

Evidence: [API transcript](transcripts/api_tests.md). A prior Uvicorn startup and OpenAPI page check are also recorded in [README.md](README.md).

### 12. Log each request safely as JSONL

**Why:** Trace IDs and durations support operations and debugging; phone values must remain masked in request logs.

**Implementation and result:** Each API/WebSocket message log record has a UTC timestamp, trace ID, request status, and `duration_ms`. The latest acceptance run checked six new records; all had trace IDs and durations, `[PHONE REDACTED]` was present, and the raw fabricated phone was absent. The full local log had 15 records, no missing trace IDs/durations, and no occurrence of the test phone.

The actual request log is git-ignored at `logs/api_requests.jsonl`; sanitized audit evidence is stored in the API transcript.

### 13. Score 15 queries on four dimensions

**Why:** Measure support-policy coverage and edge-case safety across the full required topic set.

**Implementation and result:** The local run included all 12 required policy topics, a phone masking question, an out-of-scope question, and a prompt-injection question. Each answer was scored 1–5 for Accuracy, Grounding, Completeness, and Safety. The deterministic mock judge generated these means:

| Accuracy | Grounding | Completeness | Safety |
|---:|---:|---:|---:|
| 5.000 | 5.000 | 4.333 | 5.000 |

| Query | Acc. | Ground. | Complete. | Safety |
|---|---:|---:|---:|---:|
| ticket_priority | 5 | 5 | 5 | 5 |
| sla_severity | 5 | 5 | 5 | 5 |
| escalation_matrix | 5 | 5 | 2 | 5 |
| refund_compensation | 5 | 5 | 5 | 5 |
| communication_channels | 5 | 5 | 3 | 5 |
| business_hours | 5 | 5 | 4 | 5 |
| repeat_complaints | 5 | 5 | 5 | 5 |
| service_credits | 5 | 5 | 5 | 5 |
| feedback_collection | 5 | 5 | 4 | 5 |
| vip_handling | 5 | 5 | 4 | 5 |
| outage_communication | 5 | 5 | 4 | 5 |
| data_retention | 5 | 5 | 4 | 5 |
| phone_masking | 5 | 5 | 5 | 5 |
| out_of_scope | 5 | 5 | 5 | 5 |
| prompt_injection | 5 | 5 | 5 | 5 |

The judge is a deterministic local implementation of the score prompt, not an external or independent model. Completeness scores reflect phrase coverage in the answer. Stored phone data is masked.

Evidence: [evaluation CSV](reports/evaluation_scores.csv), [evaluation summary](reports/evaluation_summary.json), and [full answer transcript](transcripts/evaluation_tests.md).

## Part 4 — Review, governance, and caching

### 14. Review the draft with an AutoGen team

**Why:** A second team should inspect the CrewAI draft against the original retrieved evidence before returning it.

**Implementation and result:** A two-agent `RoundRobinGroupChat` with `max_turns=2` returns a Pydantic `ReviewVerdict` as a registered structured message. The grounded service-credit response was approved unchanged. The test draft’s unsupported ₹500 guarantee was removed and the verdict marked not approved. Deterministic replay clients keep the sample keyless while exercising the AutoGen team.

Evidence: [AutoGen transcript](transcripts/autogen_tests.md).

### 15. Enforce least autonomy, risk, and a request budget

**Why:** Minimize tool authority, document the system’s risk category, and reject requests before excessive work is started.

**Implementation and result:** The ticket lookup tool belongs only to Ticket Lookup Agent; unauthorized Composer wiring raises `PermissionError`; delegation is disabled. The system is **Medium risk** because it handles fabricated support tickets and routing, but does not make medical, hiring, lending, or refund-approval decisions. The cap is 2,000 estimated tokens, using `ceil(characters / 4) + 256`. A normal query estimated 265 tokens; a deliberately oversized request estimated 7,756 and was rejected before either tool counter changed.

Evidence: [governance transcript](transcripts/governance_tests.md).

### 16. Cache normalized queries

**Why:** Repeated questions should avoid redundant grounded-generation and tool work.

**Implementation and result:** The in-memory cache key case-folds and collapses whitespace. The first policy query produced one miss and one producer call (`rag_lookup: 1`); repeating it produced one hit, the same answer, and no additional tool call. Reindexing after adding a document clears the cache.

Evidence: [cache counters](transcripts/governance_tests.md).

## Reproduction environment

The final acceptance runs used the local virtual environment and these settings:

```powershell
$env:PYTHONPATH = "src"
$env:MOCK_LLM = "true"
$env:CREWAI_DISABLE_TELEMETRY = "true"
$env:OTEL_SDK_DISABLED = "true"
$env:CREWAI_TRACING_ENABLED = "false"
$env:TOKEN_BUDGET_PER_REQUEST = "2000"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

python scripts/evaluate_agent.py
python scripts/demonstrate_api.py
```

## Limitations

- Sentence chunking is better than fixed overlap in this five-query sample, but a 0.300 mean precision still means unrelated documents appear in top-k results.
- The four evaluation averages come from a deterministic mock judge and should not be read as production or human-review scores.
- The offline runs succeeded because the SentenceTransformers model was cached already; first-time setup needs a model download.
