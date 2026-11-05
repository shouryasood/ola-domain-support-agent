# ola-domain-support-agent
Ola Domain Support Agent: a production-minded, multi-agent customer-support system built with CrewAI, RAG (ChromaDB + SentenceTransformers), Autogen review, guardrails, governance, and a FastAPI/WebSocket backend. Runs fully offline under MOCK_LLM, with no API keys needed.

# Architecture
![OLA AI Support Agent Architecture](<Diagrams/OLA AI Support Agent Architecture.drawio.png>)

# File Structure
| Folder | Responsibility |
|---|---|
| `data/` | Generated ticket records |
| `knowledge_base/` | Your 12+ policy documents |
| `rag/` | Embedding, indexing and retrieval |
| `tools/` | Business lookup operations |
| `agents/` | CrewAI and AutoGen implementations |
| `governance/` | Budget, caching and autonomy controls |
| `api/` | FastAPI endpoints |
| `scripts/` | Executable demonstrations |
| `tests/` | Automated acceptance tests |
| `transcripts/` | Evidence that requirements work |
| `reports/` | Evaluation and measurement results |

# File Tree
```text
ola-domain-support-agent/
│
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── .env.example
├── Dockerfile
│
├── data/
│   ├── generated/
│   │   └── support_tickets.json
│   │
│   └── reports/
│       ├── dataset_report.json
│       └── escalation_report.json
│
├── knowledge_base/
│   ├── ticket_priority.md
│   ├── sla_policy.md
│   ├── escalation_matrix.md
│   ├── refund_compensation.md
│   ├── communication_channels.md
│   ├── business_hours.md
│   ├── repeat_complaints.md
│   ├── service_credits.md
│   ├── feedback_collection.md
│   ├── vip_handling.md
│   ├── outage_communication.md
│   └── data_retention.md
│
├── src/
│   └── ola_support/
│       ├── __init__.py
│       ├── config.py
│       ├── schemas.py
│       ├── dataset.py
│       ├── guardrails.py
│       │
│       ├── rag/
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   ├── indexing.py
│       │   ├── retrieval.py
│       │   ├── grounded_generation.py
│       │   └── evaluation.py
│       │
│       ├── tools/
│       │   └── ticket_lookup.py
│       │
│       ├── agents/
│       │   ├── mock_crewai_llm.py
│       │   ├── mock_autogen_client.py
│       │   ├── crew.py
│       │   ├── memory.py
│       │   └── review_team.py
│       │
│       ├── governance/
│       │   ├── budget.py
│       │   └── cache.py
│       │
│       └── api/
│           ├── main.py
│           ├── logging_config.py
│           └── routes.py
│
├── scripts/
│   ├── generate_dataset.py
│   ├── build_index.py
│   ├── calibrate_threshold.py
│   ├── evaluate_retrieval.py
│   ├── evaluate_agent.py
│   ├── demonstrate_memory.py
│   ├── demonstrate_guardrails.py
│   └── demonstrate_governance.py
│
├── tests/
│   ├── test_dataset.py
│   ├── test_rag.py
│   ├── test_tools.py
│   ├── test_guardrails.py
│   ├── test_memory.py
│   ├── test_api.py
│   └── test_governance.py
│
├── transcripts/
│   ├── rag_tests.md
│   ├── crew_tests.md
│   ├── memory_tests.md
│   ├── guardrail_tests.md
│   ├── evaluation_tests.md
│   └── autogen_tests.md
│
└── reports/
    ├── retrieval_comparison.csv
    ├── evaluation_scores.csv
    └── evaluation_summary.json
```