# 🏦 LoanProspect AI CRM

> **Enterprise-grade agentic banking CRM** — Multi-agent personal loan prospect identification, evidence analysis, and personalized outreach generation for Indian bank Relationship Managers.

Powered by **CrewAI** (multi-agent orchestration) · **Gemini** (LLM via LiteLLM) · **FastAPI** · **React + Tailwind**

---

## 📋 Table of Contents

1. [What It Does](#what-it-does)
2. [Architecture Overview](#architecture-overview)
3. [Modular Documentation Reference](#-modular-documentation-reference)
4. [Multi-Agent System](#multi-agent-system)
5. [Database Schema](#database-schema)
6. [API Reference](#api-reference)
7. [Tool Reference](#tool-reference)
8. [Setup & Run](#setup--run)
9. [Sample Workflows](#sample-workflows)
10. [Scoring Algorithm](#scoring-algorithm)
11. [Seed Data Strategy](#seed-data-strategy)
12. [Frontend Structure](#frontend-structure)
13. [Compliance & Governance](#compliance--governance)
14. [Trade-offs & Limitations](#trade-offs--limitations)
15. [Future Enhancements](#future-enhancements)

---

## 📂 Modular Documentation Reference

For a deep-dive into each technical layer, review our detailed modular documents inside the new `documentation/` directory:
- 🧭 **[Architectural Overview](file:///c:/Users/harsh/Projects/BusinessNextProject/LoanProspect-AI-CRM/documentation/architecture_overview.md)** — Explains the Unified Chat Workspace system conception and system lifecycle flows.
- ⚙️ **[Backend Architecture & Core Services](file:///c:/Users/harsh/Projects/BusinessNextProject/LoanProspect-AI-CRM/documentation/backend.md)** — Deep dive into Plan/Step models, MemoryStore variables, MemorySummariser LLM compaction, and LoopController thresholds.
- 🎨 **[Frontend Architecture & UI Components](file:///c:/Users/harsh/Projects/BusinessNextProject/LoanProspect-AI-CRM/documentation/frontend.md)** — Breakdown of `useStreaming.js` hook, `PlanCard.jsx` vertical timeline, `InlineDataGrid.jsx`, and contextual next-step suggestions.

---

## What It Does

LoanProspect AI CRM helps Relationship Managers at Indian banks:

1. **Identify** the highest-probability personal loan prospects from their customer portfolio using deterministic behavioral scoring
2. **Understand** exactly why each customer is a prospect — life events, spending patterns, salary stability, balance behavior
3. **Generate** hyper-personalized WhatsApp messages referencing the customer's actual transaction signals
4. **Manage** campaigns with multi-customer outreach batches
5. **Interact** with an agentic AI assistant that can answer questions, analyze customers, and take actions via natural language

All actions are logged to a full audit trail and comply with marketing consent rules.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Vite + Tailwind)                  │
│                                                                       │
│  ┌──────────────────┐  ┌────────────────────────────────────────┐   │
│  │   Sidebar        │  │  Dashboard (/)                         │   │
│  │  - Chat Sessions │  │  - ProspectRankingTable (expandable)   │   │
│  │  - Campaigns     │  │  - KPI Cards                           │   │
│  │  - New Chat      │  │  - UrgentActionsPanel                  │   │
│  │  - Settings      │  │  - CampaignIntelligencePanel           │   │
│  └──────────────────┘  │  - AgentActivityFeed                   │   │
│                         └────────────────────────────────────────┘   │
│                         ┌────────────────────────────────────────┐   │
│  ┌──────────────────┐   │  Conversation Workspace (/chat)        │   │
│  │  ClientPortal    │   │  - Streaming chat with agent activity  │   │
│  │  (Full Modal)    │   │  - Tool execution cards                │   │
│  │  - KYC Profile   │   │  - TemplateSuggestionBar               │   │
│  │  - Transactions  │   │  - MessageBubble with markdown         │   │
│  │  - Prospect Why  │   └────────────────────────────────────────┘   │
│  │  - Agent Evidence│                                                 │
│  │  - Outreach      │                                                 │
│  └──────────────────┘                                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP / NDJSON SSE
┌─────────────────────────────▼───────────────────────────────────────┐
│                    FASTAPI BACKEND (uvicorn)                          │
│                                                                       │
│  /api/prospects  /api/customers  /api/campaigns  /api/message        │
│  /api/chat/stream (NDJSON SSE)  /api/audit  /api/agent/status        │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              CrewAI Orchestration Layer                       │    │
│  │                                                               │    │
│  │  ProspectAnalysisCrew (4 agents, sequential)                 │    │
│  │  BulkOutreachCrew (3 agents, sequential)                     │    │
│  │  StreamingConversationCrew (3 agents + step_callback + SSE)  │    │
│  └───────────────────┬─────────────────────────────────────────┘    │
│                       │ LiteLLM → Gemini                              │
│  ┌────────────────────▼────────────────────────────────────────┐    │
│  │              Tool Layer (16 @tool functions)                  │    │
│  │  customer · transaction · scoring · outreach · compliance    │    │
│  │  campaign · audit · conversation                             │    │
│  └────────────────────┬────────────────────────────────────────┘    │
│                        │                                              │
│  ┌─────────────────────▼───────────────────────────────────────┐    │
│  │              Service Layer                                    │    │
│  │  scoring_service · customer_service · message_service        │    │
│  │  campaign_service · chat_service                             │    │
│  └─────────────────────┬───────────────────────────────────────┘    │
│                         │                                             │
│  ┌──────────────────────▼──────────────────────────────────────┐    │
│  │              Repository Layer (SQLAlchemy)                    │    │
│  │  customer_repo · transaction_repo · campaign_repo · audit    │    │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                          │ sqlite3                                     │
│  ┌───────────────────────▼──────────────────────────────────────┐   │
│  │              SQLite DB (data/banking_crm.db)                   │   │
│  │  12 tables · 75 customers · ~5,000 transactions               │   │
│  └───────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Multi-Agent System

### Agent Framework: CrewAI

All agents use **Gemini** as the backing LLM via **LiteLLM**:
```python
from crewai import LLM
llm = LLM(model="gemini/gemini-2.5-flash", api_key=GEMINI_API_KEY)
```

### The 6 Agents

| Agent | Role | Tools |
|-------|------|-------|
| **ProspectDiscoveryAgent** | Scans portfolio, ranks loan prospects | `list_customers_brief`, `rank_personal_loan_prospects`, `fetch_customer_profile` |
| **EvidenceAggregationAgent** | Builds behavioral evidence dossier | `fetch_customer_profile`, `fetch_transaction_summary`, `detect_life_event_spends`, `calculate_cashflow_trend` |
| **LoanReadinessAgent** | Produces readiness score + explanation | `compute_loan_readiness_score`, `get_prospect_explanation` |
| **OutreachWriterAgent** | Generates personalized WhatsApp messages | `generate_whatsapp_message`, `generate_bulk_messages` |
| **ComplianceAgent** | Validates consent + message safety | `validate_compliance`, `get_compliance_summary` |
| **CampaignCoordinatorAgent** | Builds campaign batches, manages execution | `get_top_prospect_ids_for_campaign`, `create_campaign_payload`, `rank_personal_loan_prospects` |

### The 3 Crews

**ProspectAnalysisCrew** (triggered when RM clicks "Analyze with AI"):
```
EvidenceAgent → LoanReadinessAgent → ComplianceAgent → OutreachWriterAgent
```

**BulkOutreachCrew** (triggered when creating a campaign):
```
CampaignCoordinatorAgent → ComplianceAgent → OutreachWriterAgent
```

**StreamingConversationCrew** (powers direct simple chat responses):
```
Routes to most relevant agent based on simple conversation intents.
Emits plain message text chunks and direct tool activity inline.
```

### 1. Direct Simple Queries Stream (NDJSON)
Simple queries return inline text stream chunks:
```json
{"type": "status",      "message": "Analyzing request...", "agent": "Orchestrator"}
{"type": "agent_start", "agent": "EvidenceAggregationAgent", "task": "Fetching data..."}
{"type": "tool_call",   "tool": "detect_life_event_spends", "input": "CUST012"}
{"type": "tool_result", "tool": "detect_life_event_spends", "output": "Medical: ₹1.8L..."}
{"type": "chunk",       "text": "Based on the analysis, CUST012 is..."}
{"type": "done",        "steps": [...], "final_answer": "..."}
```

### 2. Autopilot Plan-then-Execute Stream (SSE / NDJSON)
Complex queries compile a multi-step plan, await human approval, and then open a dedicated SSE event stream to execute the plan steps:
```json
{"type": "plan", "plan_id": "8a72b5c...", "steps": [{"step_number": 1, "tool_name": "list_customers_brief", "description": "Fetch prospects"}], "requires_approval": true}
{"type": "status", "message": "Starting Plan Execution", "phase": "executing"}
{"type": "step_start", "step_number": 1, "description": "Fetch prospects"}
{"type": "thought", "text": "I will scan the customer base to isolate targets.", "step_number": 1}
{"type": "tool_call", "tool": "list_customers_brief", "input": "{}", "step_number": 1}
{"type": "tool_result", "tool": "list_customers_brief", "output": "[CUST001, CUST002]", "step_number": 1}
{"type": "loop_decision", "step_number": 1, "decision": "continue", "reason": "Valid output received"}
{"type": "memory_summary", "summary": "Compacted history...", "step_number": 1}
{"type": "paused_hitl", "feedback_type": "outreach_review", "draft": "Hello from RM...", "step_number": 3}
{"type": "done", "final_answer": "Execution successfully completed.", "steps": [...]}
```

---

## Database Schema

12 tables in SQLite (`data/banking_crm.db`):

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `customers` | Customer KYC + profile | customer_id, full_name, city, occupation, annual_income, consent_marketing |
| `customer_accounts` | Banking relationship | account_type, current_balance, avg_monthly_balance, monthly_inflow/outflow |
| `transactions` | Transaction history | txn_date, txn_type, category, amount, balance_after, is_recurring |
| `product_holdings` | Products owned | product_type, outstanding_amount, emi_amount |
| `loan_signals` | Detected behavioral signals | signal_type, signal_value, confidence_score |
| `outreach_history` | Messages sent/drafted | message_text, sent_status, approved_by_rm |
| `campaigns` | Campaign management | campaign_name, status, target_count, approved_by_rm |
| `rm_notes` | RM observations | note_text, rm_id |
| `audit_logs` | Full audit trail | actor_type, action_type, tool_name |
| `chat_sessions` | Conversation history | title, is_pinned, is_archived |
| `chat_messages` | Message content | role, content, agent_steps (JSON) |
| `app_settings` | Runtime config | setting_key, setting_value |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + LLM status |
| GET | `/api/customers` | Paginated customer list |
| GET | `/api/customers/{id}` | Full customer detail |
| GET | `/api/prospects` | All customers ranked by loan readiness |
| GET | `/api/prospects/{id}` | Single prospect score |
| POST | `/api/prospects/score` | Score a specific customer |
| POST | `/api/prospects/analyze/{id}` | Run full CrewAI analysis |
| GET | `/api/transactions/{id}` | Transaction history |
| GET | `/api/campaigns` | List all campaigns |
| POST | `/api/campaigns` | Create campaign |
| POST | `/api/campaigns/approve` | Approve a campaign |
| POST | `/api/campaigns/run-bulk-outreach` | Run BulkOutreachCrew |
| POST | `/api/message/generate` | Generate single WhatsApp message |
| POST | `/api/message/bulk` | Generate messages for multiple customers |
| POST | `/api/message/approve` | Approve a message for sending |
| GET | `/api/chat/sessions` | List chat sessions |
| POST | `/api/chat/sessions` | Create session |
| POST | `/api/chat/stream` | **Streaming chat** (Simple direct / plan generator) |
| GET | `/api/chat/stream/{plan_id}` | **Event-Loop Executor Stream** (SSE timeline execution logs) |
| POST | `/api/chat/sessions/{session_id}/approve-plan` | Approve or edit scheduled plan steps |
| POST | `/api/chat/sessions/{session_id}/feedback` | Submit Human-in-the-Loop feedback / outreach edits |
| GET | `/api/audit` | Audit log |
| GET | `/api/agent/status` | Agent/crew status |
| POST | `/api/agent/config` | Update Gemini API key + model |

---

## Tool Reference

16 tools decorated with `@tool` from `crewai.tools`:

### Customer Tools
| Tool | Description |
|------|-------------|
| `fetch_customer_profile` | Full profile with account, products, signals |
| `list_customers_brief` | Quick overview of all customers |
| `get_customer_risk_summary` | Risk assessment with debt ratios |

### Transaction Tools
| Tool | Description |
|------|-------------|
| `fetch_transaction_summary` | Income/expense totals + categories |
| `detect_life_event_spends` | Medical, renovation, education, wedding, travel signals |
| `calculate_cashflow_trend` | Month-over-month spending trend |

### Scoring Tools
| Tool | Description |
|------|-------------|
| `compute_loan_readiness_score` | Full 8-dimension deterministic score (0-100) |
| `rank_personal_loan_prospects` | Ranked list of all prospects |
| `get_prospect_explanation` | Human-readable explanation of prospect rating |

### Outreach Tools
| Tool | Description |
|------|-------------|
| `generate_whatsapp_message` | Personalized message via LiteLLM/Gemini |
| `generate_bulk_messages` | Messages for up to 5 customers |

### Compliance Tools
| Tool | Description |
|------|-------------|
| `validate_compliance` | Consent + KYC + content safety check |
| `get_compliance_summary` | Quick compliance status |

### Campaign Tools
| Tool | Description |
|------|-------------|
| `create_campaign_payload` | Creates campaign in DB |
| `get_campaign_status_summary` | All campaigns + status |
| `get_top_prospect_ids_for_campaign` | Top N customer IDs for targeting |

### Utility Tools
| Tool | Description |
|------|-------------|
| `log_audit_event` | Writes to audit trail |
| `get_audit_trail` | Fetches formatted audit log |
| `list_chat_sessions` | All chat sessions |
| `create_chat_session` | New conversation session |
| `save_chat_message` | Persist a message |

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (free at https://aistudio.google.com/app/apikey)

### Step 1 — Backend Setup

```bash
cd LoanProspect-AI-CRM/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# or: source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Seed the database (auto-runs on first startup too)
python -m app.seed.run_seed

# Start the API server
python app/main.py
# Or: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at `http://127.0.0.1:8000`.
Interactive API docs: `http://127.0.0.1:8000/docs`

### Step 2 — Frontend Setup

```bash
cd LoanProspect-AI-CRM/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Step 3 — Configure API Key in UI

1. Open the app at `http://localhost:5173`
2. Click the ⚙️ Settings icon in the sidebar
3. Enter your Gemini API key
4. The dashboard works immediately with seed data

> **Note:** The dashboard, client portal, and scoring all work **without** an API key — they use deterministic rules. Only the AI chat and message generation require a Gemini key.

### Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Sample Workflows

### Workflow 1: Find Top Loan Prospects
1. Open the Dashboard (`/`)
2. The `ProspectRankingTable` shows 20 customers ranked by readiness score
3. Filter by "High" conversion band to see the best prospects
4. Click any row to expand — see score breakdown, signals, next best action

### Workflow 2: Deep-Dive on a Specific Customer
1. Click any customer name anywhere in the app
2. The **ClientPortal** opens as a full-screen overlay
3. **Overview tab**: Account balance, cashflow chart, product holdings
4. **Transactions tab**: 90-day transaction history with life-event highlights
5. **Prospect Analysis tab**: Readiness score, all signals, score breakdown chart
6. **Outreach tab**: Click "Generate Message" → personalized WhatsApp draft appears
7. Review, edit, and click "Approve" — message saved to outreach history

### Workflow 3: AI Chat Analysis
1. Open Conversation Workspace (`/chat`)
2. Click a template: "Show customers with recent medical expenses above ₹1 lakh"
3. Watch agent activity panel:
   - EvidenceAggregationAgent starts
   - Tool: `detect_life_event_spends` called for each customer
   - Tool: `compute_loan_readiness_score` called for matches
4. Agent returns ranked list with reasons
5. Follow up: "Generate WhatsApp messages for the top 3"
6. ComplianceAgent validates each, OutreachWriterAgent generates messages

### Workflow 4: Create a Campaign
1. On Dashboard, click "Create Campaign" in the Campaign panel
2. Or in Chat: "Create a personal loan campaign for customers with renovation expenses"
3. BulkOutreachCrew runs: finds prospects → validates compliance → generates messages
4. Campaign appears in sidebar and dashboard
5. Click "Approve Campaign" to activate

### Workflow 5: Run Full AI Analysis on a Customer
1. Open ClientPortal for any customer
2. Click "Analyze with CrewAI" in the Agent Evidence panel
3. All 4 agents run in sequence (60-120s)
4. Results update: evidence summary, score, compliance check, message draft

---

## Scoring Algorithm

The loan readiness score (0-100) is computed deterministically — no ML:

| Dimension | Max Points | Signals |
|-----------|-----------|---------|
| Salary stability | 20 | Regular salary credits for 5+ months |
| Income level | 15 | ≥₹12L → 15pts, ≥₹6L → 10pts, ≥₹3.6L → 5pts |
| Life event signals | 25 | Medical ≥₹50k (+15), Renovation ≥₹1L (+12), Education ≥₹50k (+12), Wedding ≥₹1L (+10), Travel ≥₹80k (+8) |
| Balance health | 15 | Avg balance > 3× monthly salary → 15pts |
| No personal loan | 10 | No active personal loan product → +10pts |
| Spending trend | 10 | Recent 3m spend > prior 3m spend by 15%+ → +10pts |
| Tenure | 10 | ≥36 months → 10pts, ≥12m → 5pts |
| Credit behavior | 5 | EMI burden < 20% of income → +5pts |

**Conversion Bands:**
- `high` : score ≥ 70 → "📞 Call immediately"
- `medium`: score ≥ 45 → "💬 Send WhatsApp message"
- `low`   : score < 45 → "📧 Add to nurture campaign"

**Risk Flags:**
- `no_marketing_consent` — blocks outreach
- `existing_personal_loan` — reduces score
- `high_expense_ratio` — outflow > 90% inflow
- `high_debt_burden` — EMI > 50% monthly income
- `low_balance` — balance < 50% monthly income

---

## Seed Data Strategy

75 customers seeded with `random.seed(42)` for reproducibility.

| Customer Type | Count | Profile |
|--------------|-------|---------|
| High-intent loan prospects | 15 | Medical/renovation/education spends, stable salary, no personal loan |
| Salaried tech professionals | 12 | Software Engineers, Data Analysts, Bangalore/Hyderabad/Pune |
| Self-employed professionals | 10 | Doctors, CAs, Lawyers, Architects |
| Business owners | 8 | Mumbai, Delhi, high income |
| Young professionals | 8 | 22-30 years, rising income trend |
| Deposit-heavy customers | 7 | High balance, multiple FDs, no loans |
| High-spend lifestyle | 6 | High travel/dining/shopping |
| Dormant customers | 5 | Minimal recent transactions |
| High-risk customers | 4 | Volatile income, high existing debt |

**Per customer, seeded:**
- 1 customer record + 1 account record
- 50-120 transactions over 6 months (realistic patterns)
- 2-5 product holdings (most without personal loan)
- 1-3 loan signals
- 1-2 RM notes
- 0-2 outreach history records

Also seeded: 3 campaigns, 5 chat sessions with messages, 20 audit log entries.

---

## Frontend Structure

```
frontend/src/
├── api/
│   └── client.js                  # All API calls + streamChat generator
├── context/
│   ├── AppContext.jsx              # Global: client portal, notifications, settings
│   └── ChatContext.jsx             # Chat: sessions, messages, streaming state
├── hooks/
│   ├── useProspects.js             # Fetch + cache prospect list
│   ├── useClientPortal.js          # Client portal data + message generation
│   └── useStreaming.js             # Streaming chat state machine
├── layouts/
│   └── AppLayout.jsx               # Sidebar + main content wrapper
├── pages/
│   ├── Dashboard.jsx               # Landing page (actionable intelligence)
│   └── ConversationWorkspace.jsx   # Agentic chat interface
├── components/
│   ├── dashboard/
│   │   ├── KPICards.jsx            # 5 stat cards
│   │   ├── ProspectRankingTable.jsx # Expandable ranked table
│   │   ├── UrgentActionsPanel.jsx   # Top HIGH-band prospects
│   │   ├── CampaignIntelligencePanel.jsx
│   │   └── AgentActivityFeed.jsx    # Recent audit events
│   ├── client/
│   │   ├── ClientPortal.jsx         # Full-screen overlay modal
│   │   ├── KYCProfileCard.jsx       # Profile + account summary
│   │   ├── TransactionOverviewPanel.jsx  # Charts + transaction list
│   │   ├── ProspectReasonPanel.jsx   # Score + signals + loan factors
│   │   ├── AgentEvidencePanel.jsx    # Agent contributions
│   │   └── OutreachPanel.jsx         # Message composer + history
│   ├── conversation/
│   │   ├── MessageBubble.jsx         # Chat bubbles + tool accordion
│   │   ├── MessageInput.jsx          # Input with streaming state
│   │   └── TemplateSuggestionBar.jsx # 8 quick-action templates
│   ├── agents/
│   │   ├── AgentActivityPanel.jsx    # Real-time agent timeline
│   │   └── ToolExecutionCard.jsx     # Single tool call card
│   ├── campaigns/
│   │   ├── CampaignCard.jsx          # Campaign status card
│   │   └── CampaignApprovalModal.jsx  # Approve/create modal
│   └── shared/
│       ├── ScoreBar.jsx              # Colored score visualization
│       ├── ConfidenceMeter.jsx        # Progress bar 0-100%
│       ├── ComplianceBanner.jsx       # Compliance status
│       ├── SignalChip.jsx             # Colored signal tags
│       ├── LoadingSkeleton.jsx        # Pulse skeleton states
│       ├── SettingsModal.jsx          # API key configuration
│       └── NotificationToast.jsx      # In-app notifications
```

---

## Compliance & Governance

1. **Marketing Consent** — `ComplianceAgent` checks `consent_marketing=True` before any outreach
2. **KYC Validation** — KYC status must be `verified` to proceed
3. **Message Safety** — Prohibited terms list blocks non-compliant content
4. **Human Approval** — All messages stay in `draft` status until RM approves via UI
5. **Audit Trail** — Every agent action, tool call, and approval logged to `audit_logs`
6. **PII Masking** — Phone/email masked in tool outputs (`98XXXXX901`)
7. **Risk Segmentation** — High-risk customers flagged with warnings

---

## Trade-offs & Limitations

### Trade-offs Made
- **SQLite over PostgreSQL** — MVP-appropriate; change `DATABASE_URL` to migrate
- **Deterministic scoring over ML** — No training data needed; fully explainable
- **CrewAI sequential process** — Simpler than hierarchical; easier to debug
- **LiteLLM for Gemini** — Consistent with CrewAI's internal LLM routing
- **Thread-based streaming** — SSE via thread+queue; works without async CrewAI support

### Current Limitations
- CrewAI's `step_callback` timing may miss some intermediate tool events
- Bulk outreach capped at 5 customers per batch (performance)
- No real WhatsApp API integration — messages saved as drafts
- Single RM user (no multi-user auth)
- SQLite has write concurrency limitations for production

---

## Future Enhancements

1. **PostgreSQL migration** — Change `DATABASE_URL` in `.env`; all code works unchanged
2. **WhatsApp Business API** — Connect approved messages to WA Business Cloud API
3. **Multi-RM support** — Add auth layer (JWT) and per-RM customer segmentation
4. **ML model layer** — Replace deterministic scoring with gradient-boosted model trained on conversion data
5. **Real-time DB sync** — WebSocket updates when new signals are detected
6. **Campaign A/B testing** — Message variant testing with response tracking
7. **Voice integration** — RM call notes → auto-extracted loan signals
8. **Regulatory reporting** — RBI-compliant outreach compliance reports

---

## Project Structure

```
LoanProspect-AI-CRM/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── agent_definitions.py  # 6 CrewAI agents with Gemini LLM
│   │   │   └── crews.py              # 3 crews + streaming conversation
│   │   ├── api/                      # FastAPI routers (8 files)
│   │   ├── db/
│   │   │   ├── models.py             # SQLAlchemy ORM (12 tables)
│   │   │   ├── database.py           # Engine + session management
│   │   │   └── repositories/         # Data access layer (4 files)
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── seed/                     # 75-customer seed generator
│   │   ├── services/                 # Business logic layer (5 files)
│   │   ├── tools/                    # 16 @tool functions (8 files)
│   │   ├── utils/                    # Logger, helpers, formatters
│   │   ├── config.py                 # Pydantic settings
│   │   └── main.py                   # FastAPI app + lifespan
│   ├── tests/                        # pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.js             # All API + streaming functions
│   │   ├── context/                  # App + Chat React contexts
│   │   ├── hooks/                    # useProspects, useClientPortal, useStreaming
│   │   ├── layouts/AppLayout.jsx     # Sidebar + main content
│   │   ├── pages/                    # Dashboard + ConversationWorkspace
│   │   └── components/              # 22 feature components
│   ├── package.json
│   └── vite.config.js
└── README.md
```
