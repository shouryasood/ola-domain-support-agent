# Project Steps and Evaluation Results

This file records why each capstone step was completed, what was implemented, and the results observed in the local project. The demonstrations use `MOCK_LLM=true`; they do not call a paid or external language model. Embeddings used the locally cached `sentence-transformers/all-MiniLM-L6-v2` model with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` during the final evaluation and API runs.

For run commands and repository setup, see [README.md](README.md). Detailed machine-readable results and transcripts are linked in each step below.

## Results at a glance

| Area | Result |
|---|---|
| Dataset | 240 deterministic tickets; 48 in each required category and status; 47 escalated (19.58%). |
| Knowledge base and index | 55 policy documents; 55 fixed-overlap chunks and 166 sentence chunks in separate ChromaDB collections. |
| RAG threshold | 0.3730437159538269, selected between the observed in-scope and out-of-scope similarity clusters. |
| Retrieval comparison | Sentence chunks: mean precision 0.300, recall 1.000. Fixed overlap: mean precision 0.250, recall 1.000. |
| CrewAI and tools | Three-agent crew invoked RAG and ticket lookup on separate queries; each tool was invoked once in the recorded Part 2 run. |
| API and privacy | Both HTTP routes returned 200 in the acceptance run; the WebSocket handled two turns and a disconnect; all six entries from that run had trace IDs and durations and contained no raw test phone. |
| 15-query evaluation | Accuracy 5.000, Grounding 5.000, Completeness 4.333, Safety 5.000 (means across 15 rows). |
| AutoGen and governance | One grounded draft approved unchanged; an unsupported claim revised; unauthorized lookup wiring blocked; oversized request rejected; repeated query hit cache. |

## Part 1 — Dataset and RAG core

### 1. Generate and validate the ticket dataset

**Why:** The support-ticket tool needs repeatable records for realistic status lookups and a dataset whose composition can be reproduced by the grader.

**What and result:** `src/ola_support/dataset.py` generates 240 tickets. It uses data seed `2026`, escalation seed `10`, equal category and status weights (20% each), a 0.20 escalation draw probability, resolution times from 0.5 to 96 hours, ages from 0 to 30 days, and synthetic amounts from ₹50 to ₹5,000. The generated sample has 48 tickets in each of Billing, Technical Issue, Account Access, Product Defect, and General Inquiry; 48 in each required status; and 47 escalated tickets (19.58%).

**Why the result meets the brief:** It exceeds the 40-record minimum, uses every required category/status multiple times, and lands within the 10–30% escalation band without hand-editing records.

Evidence: [dataset report](data/reports/dataset_report.json) and [generated ticket JSON](data/generated/support_tickets.json).

### 2. Write the policy knowledge base

**Why:** Retrieval needs original, versioned support policies instead of relying on model priors or presenting synthetic rules as real Ola policy.

**What and result:** `scripts/create_knowledge_base.py` generated 55 policy documents, including the required 12 topics: ticket priority, SLA by severity, escalation, refunds/compensation, communication channels, business hours/holidays, repeat complaints, service credits, feedback collection, VIP handling, outage communication, and ticket retention. The documents describe the capstone scenario and are not represented as actual Ola policies.

**Why it matters:** The additional documents provide broader demonstration coverage, though they also contribute to some irrelevant top-k retrievals (see Steps 4–5).

### 3. Chunk, embed, and index both strategies

**Why:** Chunk boundaries affect retrieval precision and recall, so the project compares two strategies using the same documents and embedding model.

**What and result:** `src/ola_support/rag/chunking.py` uses fixed chunks of 90 words with a 20-word overlap and a sentence splitter. `src/ola_support/rag/indexing.py` embeds both sets with `sentence-transformers/all-MiniLM-L6-v2`, then upserts them into separate cosine-distance ChromaDB collections. The current 55-document corpus yields 55 fixed-overlap chunks and 166 sentence chunks. An offline-mode run loaded the cached model and built/queried the indexes successfully.

Evidence: [retrieval comparison CSV](reports/retrieval_comparison.csv). The API demonstration temporarily indexed a 56th document, removed it afterward, and rebuilt the baseline index; there are again 55 Markdown documents in the knowledge base.

### 4. Calibrate grounded generation and the fallback

**Why:** The answer generator should decline questions whose best retrieved policy passage is too dissimilar, rather than produce an answer from general model knowledge.

**What and result:** Calibration on the sentence collection measured five in-scope top-1 cosine similarities: 0.630744, 0.600182, 0.708150, 0.589640, and 0.591528. Two out-of-scope queries measured 0.156447 and 0.106316. The midpoint between the highest out-of-scope value and lowest in-scope value is 0.3730437159538269. The fallback fires below that measured threshold. The capital-of-France example returned `I don't know based on the available support policies.`

Evidence: [RAG threshold report](reports/rag_threshold.json) and [RAG transcript](transcripts/rag_tests.md).

### 5. Compare retrieval precision and recall

**Why:** A high similarity alone does not establish that the top-k context is relevant. This comparison measures unique parent documents against the expected document for the same five queries.

**What and result:** Both strategies had mean recall 1.000. Fixed-overlap chunking had mean precision 0.250; sentence chunking had mean precision 0.300. Sentence chunks are the provisional choice because they improve mean precision by 0.050 while retaining the same recall. Both approaches still return unrelated documents, so the result flags retrieval relevance as a quality limitation rather than claiming production-ready retrieval.

| Query | Fixed precision | Fixed recall | Sentence precision | Sentence recall |
|---|---:|---:|---:|---:|
| Ticket priority | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| SLA severity | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| Escalation | 1/4 = 0.250 | 1/1 = 1.000 | 1/4 = 0.250 | 1/1 = 1.000 |
| Refund review | 1/4 = 0.250 | 1/1 = 1.000 | 1/3 = 0.333 | 1/1 = 1.000 |
| Account-specific channel | 1/4 = 0.250 | 1/1 = 1.000 | 1/4 = 0.250 | 1/1 = 1.000 |

## Part 2 — CrewAI agents, memory, and guardrails

### 6. Look up a ticket and calculate an escalation score

**Why:** A support agent must retrieve the requested record and make its escalation recommendation explainable from the dataset fields.

**What and result:** `check_support_ticket_status` returns ticket status, resolution time, age, escalation state, score, and recommendation. Its score is `0.75 * float(escalated) + 0.25 * (1 - days_since_created / 30)`. The recommendation threshold is 0.25, the 80th percentile of this generated score distribution. `TKT-00001` returned `Closed`, 91.32 hours, score 0.191667, and no escalation recommendation. An unknown ID returns a not-found result.

Evidence: [escalation report](data/reports/escalation_report.json) and [crew transcript](transcripts/crew_tests.md).

### 7. Orchestrate the CrewAI agents and tools

**Why:** Policy retrieval and private ticket lookup are separate capabilities; a Composer combines the selected evidence into the user-facing response.

**What and result:** The crew has a Policy Retrieval Agent with `rag_lookup`, a Ticket Lookup Agent with `check_support_ticket_status`, and a Response Composer. A policy question invoked RAG once. A separate `TKT-00001` question invoked ticket lookup once and returned the structured `SupportResponse` with `Closed` status. CrewAI was run with the deterministic `BaseLLM` adapter and tracing/telemetry disabled.

The recorded priority answer also included unrelated retention and SLA material. This is documented as an observed retrieval-quality issue.

### 8. Maintain session memory

**Why:** A multi-turn support interaction should carry context within a session but not leak it into another conversation.

**What and result:** The memory demonstration introduced `TKT-00001` in Session A and resolved a later reference to “the ticket mentioned earlier.” A fresh Session B correctly had no ticket ID in its history. The implementation is process-local. The run emitted the expected LangChain deprecation warning for `InMemoryChatMessageHistory`.

Evidence: [memory transcript](transcripts/memory_tests.md).

### 9. Validate structured crew responses

**Why:** API clients need a stable response shape, and malformed agent output should not silently pass downstream.

**What and result:** The crew response uses the Pydantic `SupportResponse` schema with answer, sources, ticket fields, escalation score bounds, and fallback flag. Crew output is parsed and validated against that model before returning.

### 10. Apply input and output guardrails

**Why:** Support questions can contain fixed-format PII or prompt injection, and grounded answers must not make claims beyond retrieved policy.

**What and result:** The phone masker replaced the fabricated 10-digit phone with `[PHONE REDACTED]`; injection text was detected; the in-scope query continued; an out-of-scope query fell back; and a deliberately unsupported refund claim was rejected. Free-text names, addresses, and payment details are not claimed to be masked.

Evidence: [guardrail transcript](transcripts/guardrail_tests.md). The API acceptance run also verified phone masking before an `/add-document` text was stored.

## Part 3 — FastAPI, logs, and evaluation

### 11. Expose the agent through HTTP and WebSocket

**Why:** A deployed support system needs HTTP operations for normal requests/document updates and a stateful channel for multi-turn conversations.

**What and result:** FastAPI exposes `POST /ask`, `POST /add-document`, and `WebSocket /ws/chat`. The acceptance demonstration received HTTP 200 from both POST routes. The document endpoint reported 56 documents, 56 fixed chunks, and 168 sentence chunks during its temporary-document test; the script then removed that document and rebuilt the original 55-document indexes. The WebSocket processed two ticket-status turns. After the client disconnected while the server awaited a further message, a subsequent `/openapi.json` request returned 200.

Evidence and sanitized responses: [API transcript](transcripts/api_tests.md). The script uses FastAPI's test client to exercise the ASGI routes. A prior local Uvicorn startup and OpenAPI page check are recorded in the main README.

### 12. Write privacy-safe structured JSONL logs

**Why:** Request traces need enough timing and correlation information for debugging, but fixed-format phone values must not be written to disk in clear text.

**What and result:** JSONL records contain UTC timestamp, trace ID, endpoint/method, status, duration in milliseconds, and sanitized request text. The latest API demo generated six entries and checked that all had trace IDs and durations, `[PHONE REDACTED]` appeared, the raw fabricated phone did not, and a WebSocket disconnect event was recorded. A whole-file audit of the local log found 15 entries, zero missing trace IDs, zero missing durations, and no occurrence of the test phone.

The runtime log is at `logs/api_requests.jsonl` and is git-ignored. The reproducible privacy check and safe result summary are preserved in `transcripts/api_tests.md`.

### 13. Evaluate all 15 questions

**Why:** The agent must be assessed across all required topics and edge cases, with comparable per-query scores and aggregate results.

**What and result:** `scripts/evaluate_agent.py` ran 15 real `MOCK_LLM` answers: 12 required policy topics, a phone-masking case, an out-of-scope question, and a prompt-injection attempt. The deterministic local judge applies 1–5 rules for Accuracy, Grounding, Completeness, and Safety; it makes no external LLM call. Average scores were:

| Accuracy | Grounding | Completeness | Safety |
|---:|---:|---:|---:|
| 5.000 | 5.000 | 4.333 | 5.000 |

| Query | Accuracy | Grounding | Completeness | Safety |
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

Completeness is lower where the retrieved answer omitted phrases required by the deterministic rubric. These high averages should be interpreted as results from this explicit mock scoring logic, not as an independent human or model quality review. The answer and query fields are sanitized in the stored output.

Evidence: [scores CSV](reports/evaluation_scores.csv), [summary JSON](reports/evaluation_summary.json), and [full evaluation transcript](transcripts/evaluation_tests.md).

## Part 4 — Independent review, governance, and cache

### 14. Run the AutoGen review stage

**Why:** A second agent team should inspect a draft against the original evidence before the answer reaches the user.

**What and result:** The AutoGen `RoundRobinGroupChat` uses two agents, `max_turns=2`, and a Pydantic `ReviewVerdict` registered as a structured message type. A supported service-credit answer was approved unchanged (`approved: true`). A deliberately injected “₹500 within one hour” promise was removed (`approved: false`). The replay clients and deterministic review logic keep the demonstration keyless; the verdicts pass through the actual AutoGen team.

Evidence: [AutoGen transcript](transcripts/autogen_tests.md).

### 15. Enforce least autonomy and a request budget

**Why:** Tool access should follow least privilege, the risk level should be explicit, and oversized requests should be refused before incurring additional model/tool work.

**What and result:** Only the Ticket Lookup Agent receives `check_support_ticket_status`; Retrieval receives only RAG and Composer receives no tool. A deliberate attempt to wire the ticket tool to Composer was rejected by the ownership guard. The system is classified as Medium risk because it handles customer-support tickets but does not make medical, hiring, lending, or refund-approval decisions; the ticket data is fabricated.

The request cap is 2,000 estimated tokens, using `ceil(input_characters / 4) + 256`. A regular policy query estimated 265 tokens and was accepted. An oversized input estimated 7,756 tokens and was rejected before either tool counter changed from zero.

Evidence: [governance transcript](transcripts/governance_tests.md).

### 16. Cache repeated responses

**Why:** Repeated normalized questions should not trigger another retrieval, tool, or review operation.

**What and result:** The in-memory cache key is the case-folded query with whitespace collapsed. The first priority query produced one miss, one producer call, and one RAG invocation. The identical repeat produced one cache hit and no additional tool invocation; both responses matched. Adding a document clears the cache after rebuilding indexes so stale answers are not reused.

Evidence: the cache counters and before/after tool counts are in [governance_tests.md](transcripts/governance_tests.md).

## Reproduction commands

From the repository root with the project virtual environment active:

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

python src/ola_support/dataset.py
python scripts/create_knowledge_base.py
python scripts/build_index.py
python scripts/calibrate_threshold.py
python scripts/evaluate_retrieval.py
python scripts/demo_rag.py
python -m ola_support.agents.crew
python scripts/demonstrate_memory.py
python scripts/demonstrate_guardrails.py
python scripts/evaluate_agent.py
python scripts/demonstrate_api.py
python scripts/demonstrate_review.py
python scripts/demonstrate_governance.py
```

The API demonstration adds and removes a random temporary document and rebuilds the indexes. Run it from a local checkout with the model cache available. The evaluation and API scripts write sanitized evidence into the reports and transcripts listed above.

## Remaining quality notes

- The required acceptance demonstrations are recorded, but retrieval precision remains modest: mean precision is 0.300 for sentence chunks and 0.250 for fixed-overlap chunks. Some answers include unrelated retrieved passages.
- The evaluation judge is deterministic local mock logic. It verifies a repeatable rubric and edge-case behavior; its high averages do not substitute for human review or independent production evaluation.
- The final offline checks succeeded because the embedding model was already cached. A first-time setup still needs to download that model before offline execution.
- The API transcript records FastAPI TestClient requests, while the main README also records the earlier Uvicorn startup/OpenAPI check.
