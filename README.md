# 🏦 LoanProspect AI CRM

> **Enterprise-grade agentic banking CRM** — Multi-agent personal loan prospect identification, evidence analysis, and personalized outreach generation for Indian bank Relationship Managers.

Powered by **CrewAI** (multi-agent orchestration) · **Gemini** (LLM via LiteLLM) · **FastAPI** · **React + Tailwind**

---

## 📋 Table of Contents

1. [What It Does](#what-it-does)
2. [Dual-Path Intelligence Engine](#dual-path-intelligence-engine)
3. [Architecture Overview](#architecture-overview)
4. [Modular Documentation Reference](#-modular-documentation-reference)
5. [Multi-Agent System](#multi-agent-system)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Tool Reference](#tool-reference)
9. [Setup & Run](#setup--run)
10. [Sample Workflows](#sample-workflows)
11. [Scoring Algorithm](#scoring-algorithm)
12. [Seed Data Strategy](#seed-data-strategy)
13. [Frontend Structure](#frontend-structure)
14. [Compliance & Governance](#compliance--governance)
15. [Trade-offs & Limitations](#trade-offs--limitations)
16. [Future Enhancements](#future-enhancements)

---

## 📂 Modular Documentation Reference

For a deep-dive into each technical layer, review our detailed modular documents inside the `documentation/` directory:
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

## Dual-Path Intelligence Engine

Unlike standard banking chatbots, LoanProspect AI CRM features a custom **Dual-Path Intelligence Engine** that dynamically routes relationship manager requests based on their complexity:

```
                  ┌────────────────────────────────────────┐
                  │        Relationship Manager Query      │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                      [ Heuristic Intent Classifier ]
                      (is_simple_query heuristic check)
                               /             \
                   Simple / Direct          Complex / Strategic
                             /                 \
                            ▼                   ▼
             ┌─────────────────────────┐  ┌─────────────────────────┐
             │ StreamingConversation   │  │    Planner Service      │
             │ Crew (Inline Direct)    │  │ (Multi-step Formulation)│
             └──────────┬──────────────┘  └─────────────┬───────────┘
                        │                               │
                        │                               ▼
                        │                  ┌─────────────────────────┐
                        │                  │   RM Plan Review &      │
                        │                  │  HITL Editing Stepper   │
                        │                  └────────────┬────────────┘
                        │                               │ (RM Approved)
                        │                               ▼
                        │                  ┌─────────────────────────┐
                        │                  │  SSE Execution Loop     │
                        │                  │   - Dynamic resolution  │
                        │                  │   - Memory Compaction   │
                        │                  │   - Loop Controller     │
                        └──────────┬───────└────────────┬────────────┘
                                   │                    │
                                   ▼                    ▼
                               ┌──────────────────────────┐
                               │ Renders Chat Workspace   │
                               └──────────────────────────┘
```

### 1. Direct Streaming Path (Conversational Mode)
For simple queries (e.g. *"Show details for CUST001"* or *"KYC status of John Doe"*), the query is routed to `StreamingConversationCrew`. It executes instantly, bypassing plan authorization:
* **Real-time Streaming**: Returns an inline stream of direct text chunks, thoughts, and status variables over a raw `application/x-ndjson` stream.
* **Intelligent Auto-Suggestions**: Uses Gemini to analyze the assistant's final response and generate 4 dynamic, actionable "next step" contextual recommendations (e.g. *"Compute loan readiness for CUST001"*) that map directly to the system's tools.

### 2. Autopilot Plan-then-Execute Path (Strategic Mode)
For strategic requests involving multi-phase workflows (e.g. *"Find customers with wedding spends, validate their compliance, and draft a bulk campaign"*), the **Planner Service** compiles a detailed, structured execution plan:
* **Interactive Plan Card Stepper**: The user is presented with a vertical timeline timeline (`PlanCard`) detailing the proposed sequential operations. The RM can edit step descriptions, tools, or inputs before launching.
* **Server-Sent Events (SSE) Execution**: Once approved, the backend schedules execution over a persistent SSE connection (`GET /api/chat/stream/{plan_id}`).
* **Dynamic Parameter Resolution**: High-level steps automatically pass variable outputs (e.g. passing a customer list from step 1 to transaction tools in step 2) using notation references like `"$step1.output.customer_ids"`.
* **Memory Compaction & Control Loops**:
  * **MemoryStore & Summariser**: Tracks logging variables in real-time. If logs exceed **4,000 tokens**, a compaction loop triggers Gemini to compress historical logs by up to **80%** while preserving immutable pinned facts.
  * **Loop Controller**: Monitors execution limits (max 10 steps), catches exceptions to run a single dynamic recovery/replanning branch (`replan_failed_step`), and aborts if empty values recur.
  * **Human-in-the-Loop (HITL)**: Automatically pauses execution and raises a sliding outreach draft editor panel whenever an outreach step requires RM approval.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       REACT FRONTEND (Vite + Tailwind)                          │
│                                                                                 │
│  ┌──────────────────┐  ┌─────────────────────────────────────────────────────┐  │
│  │   Sidebar        │  │  Dashboard (/)                                      │  │
│  │  - Workspace     │  │  - ProspectRankingTable (expandable)                │  │
│  │  - Analytics     │  │  - KPI Cards                                        │  │
│  │  - New Conversat.│  │  - UrgentActionsPanel                               │  │
│  │  - Recent Queries│  │  - CampaignIntelligencePanel                        │  │
│  │  └────────────────┘  │  - AgentActivityFeed                                │  │
│  │                     └─────────────────────────────────────────────────────┘  │
│  │                     ┌─────────────────────────────────────────────────────┐  │
│  │  ┌───────────────┐  │  Conversation Workspace (/chat)                     │  │
│  │  │ ClientPortal  │  │  - Streaming chat with agent activity               │  │
│  │  │ (Full Modal)  │  │  - Interactive PlanCard (vertical stepper)          │  │
│  │  │ - KYC Card    │  │  - InlineDataGrid (automatic tables)                │  │
│  │  │ - Txn Panel   │  │  - OutreachPreviewDrawer (WhatsApp sliding review)  │  │
│  │  │ - Score Panel │  │  - TemplateSuggestionBar (contextual next-steps)    │  │
│  │  │ - Agent Evid. │  └─────────────────────────────────────────────────────┘  │
│  │  │ - Outreach    │                                                           │
│  │  └───────────────┘                                                           │
│  └──────────────────────────────────────┬───────────────────────────────────────┘
│                                         │ HTTP / SSE / NDJSON
┌─────────────────────────────────────────▼───────────────────────────────────────┐
│                       FASTAPI BACKEND (uvicorn)                                 │
│                                                                                 │
│  /api/prospects   /api/customers   /api/campaigns   /api/message  /api/audit    │
│  /api/chat/stream (NDJSON SSE classification)  /api/chat/stream/{plan_id} (SSE)   │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                       CrewAI Orchestration Layer                          │  │
│  │                                                                           │  │
│  │  ProspectAnalysisCrew (4 agents, sequential)                              │  │
│  │  BulkOutreachCrew (3 agents, sequential)                                  │  │
│  │  StreamingConversationCrew (3 agents + step_callback + SSE)               │  │
│  └────────────────────────────────────┬──────────────────────────────────────┘  │
│                                       │ LiteLLM → Gemini                        │
│  ┌────────────────────────────────────▼──────────────────────────────────────┐  │
│  │                       Tool Layer (21 @tool functions)                     │  │
│  │  customer · transaction · scoring · outreach · compliance · campaign ·    │  │
│  │  audit · conversation                                                     │  │
│  └────────────────────────────────────┬──────────────────────────────────────┘  │
│                                       │                                         │
│  ┌────────────────────────────────────▼──────────────────────────────────────┐  │
│  │                       Service Layer (10 Core Services)                    │  │
│  │  planner · executor · memory_store · summariser · loop_controller ·       │  │
│  │  scoring · customer · campaign · message · chat                           │  │
│  └────────────────────────────────────┬──────────────────────────────────────┘  │
│                                       │                                         │
│  ┌────────────────────────────────────▼──────────────────────────────────────┐  │
│  │                       Repository Layer (SQLAlchemy)                       │  │
│  │  customer_repo · transaction_repo · campaign_repo · audit_repo            │  │
│  └────────────────────────────────────┬──────────────────────────────────────┘  │
│                                       │ sqlite3                                 │
│  ┌────────────────────────────────────▼──────────────────────────────────────┐  │
│  │                       SQLite DB (data/banking_crm.db)                     │  │
│  │  14 tables · 75 customers · ~5,000 transactions · execution state logs    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
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

**ProspectAnalysisCrew** (triggered when RM clicks "Analyze with AI" in Client Portal):
```
EvidenceAgent → LoanReadinessAgent → ComplianceAgent → OutreachWriterAgent
```

**BulkOutreachCrew** (triggered when running campaign outreach batches):
```
CampaignCoordinatorAgent → ComplianceAgent → OutreachWriterAgent
```

**StreamingConversationCrew** (powers direct conversational chat responses):
```
Routes to most relevant agent based on conversation context. Emits plain text chunks and direct tool activity.
```

---

## Database Schema

We use SQLAlchemy ORM mapping to **14 tables** in a local SQLite file (`data/banking_crm.db`). This includes the core relational business tables and the execution state tables that drive our Planner-Executor loops:

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `customers` | Customer KYC + profile | customer_id, full_name, city, annual_income, consent_marketing, risk_segment, kyc_status |
| `customer_accounts` | Banking relationship details | account_id, account_type, current_balance, avg_monthly_balance, monthly_inflow |
| `transactions` | Historical transaction records | transaction_id, customer_id, txn_date, txn_type, category, amount, balance_after |
| `product_holdings` | Products held by customers | holding_id, customer_id, product_type, product_status, outstanding_amount, emi_amount |
| `loan_signals` | Detected propensity signals | signal_id, customer_id, signal_type, signal_value, confidence_score |
| `outreach_history` | Generated WhatsApp drafts & logs | outreach_id, customer_id, campaign_id, message_text, sent_status, approved_by_rm |
| `campaigns` | Marketing campaigns | campaign_id, campaign_name, status, target_count, success_count |
| `rm_notes` | Relationship Manager observations | note_id, customer_id, rm_id, note_text, created_at |
| `audit_logs` | Security & activity trail | audit_id, actor_type, actor_name, action_type, tool_name, created_at |
| `chat_sessions` | Conversational session headers | session_id, title, is_pinned, is_archived, customer_context |
| `chat_messages` | Chat history messages | message_id, session_id, role, content, agent_steps (JSON logs) |
| `app_settings` | Dynamic app environment variables | setting_key, setting_value, updated_at |
| `plans` 🆕 | Execution plan headers | plan_id, session_id, original_query, status (`planning`, `running`, `completed`, `failed`) |
| `execution_steps` 🆕 | Plan execution steps | step_id, plan_id, step_number, description, tool_name, tool_args (JSON), status, retry_count, hitl_required |

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
| POST | `/api/chat/stream` | **Streaming chat router** (Direct simple response OR complex plan generator) |
| GET | `/api/chat/stream/{plan_id}` | **SSE Event Loop Executor** (Streams steps, tool logs, CoT, and summaries) |
| POST | `/api/chat/sessions/{session_id}/approve-plan` | Approve, schedule, or override steps of a plan |
| POST | `/api/chat/sessions/{session_id}/feedback` | Submit feedback, message edits, or approval to paused streams |
| GET | `/api/audit` | Audit log list |
| GET | `/api/agent/status` | Agent/crew status |
| POST | `/api/agent/config` | Update Gemini API key + model |

---

## Tool Reference

We expose **21 specialized @tool functions** from `crewai.tools`, split logically by features:

### 💼 Customer Tools
* `list_customers_brief`: Summary list of all customers.
* `fetch_customer_profile`: Comprehensive profile details (accounts, signals, holdings).
* `get_customer_risk_summary`: Analyzes debt-to-income and overall financial risk segments.

### 💳 Transaction Tools
* `fetch_transaction_summary`: Inflow, outflow, and category transaction breakdowns.
* `detect_life_event_spends`: Scans transaction history for specific high-value medical, wedding, renovation, or education expenses.
* `calculate_cashflow_trend`: Computes month-over-month cash trajectories.

### 📈 Scoring Tools
* `compute_loan_readiness_score`: Calculates deterministic loan readiness score (0-100) across 8 vectors.
* `rank_personal_loan_prospects`: Evaluates and ranks the entire customer portfolio.
* `get_prospect_explanation`: Renders a friendly, explaining narrative for score values.

### ✉️ Outreach Tools
* `generate_whatsapp_message`: Personalized message template builder.
* `generate_bulk_messages`: Message builder optimized for batch operations.

### 🛡️ Compliance Tools
* `validate_compliance`: Runs checks for marketing consent, verified KYC, and text policies.
* `get_compliance_summary`: Aggregates metrics regarding portfolio-wide consent and KYC rates.

### 📣 Campaign Tools
* `create_campaign_payload`: Saves campaign headers and targeted segments to database.
* `get_campaign_status_summary`: Lists campaigns and active completion ratios.
* `get_top_prospect_ids_for_campaign`: Selects the top N prospects matching campaign rules.

### ⚙️ Utility & Conversation Tools
* `log_audit_event`: Records actors, tools, and actions to the audit database.
* `get_audit_trail`: Retrieves security logs.
* `list_chat_sessions`: Fetches non-archived chat history headers.
* `create_chat_session`: Spawns a new chat session database entry.
* `save_chat_message`: Persists messages and agent execution logs inside sessions.

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (free at [Google AI Studio](https://aistudio.google.com/app/apikey))

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

### Step 3 — Configure API Key

1. Ensure your `GEMINI_API_KEY` is set in the backend `.env` file for AI-driven planning and chat features.
2. The dashboard works immediately with seed data out-of-the-box.

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

The React web application lives in `frontend/src/` and is divided logically into pages, state machines, contexts, and highly reusable HSL-styled widgets:

```
frontend/src/
├── api/
│   └── client.js                  # API fetch clients & streamChat NDJSON reader
├── context/
│   ├── AppContext.jsx             # Active portal overlays, settings, & notifications
│   └── ChatContext.jsx            # Active sessions history & message lists
├── hooks/
│   ├── useProspects.js            # Paginated portfolio caching hook
│   ├── useClientPortal.js         # Single customer detail compiler
│   └── useStreaming.js            # State machine parsing NDJSON stream tokens
├── layouts/
│   └── AppLayout.jsx              # Sidebar workspace grid layout
├── pages/
│   ├── Dashboard.jsx              # Customer scanning & KPI aggregates
│   └── ConversationWorkspace.jsx  # Main routing hub for agent chat
├── styles/
│   └── index.css                  # Tailored dark-mode & harmonious HSL variables
├── components/
│   ├── dashboard/
│   │   ├── KPICards.jsx           # Stat count aggregates (High, Medium, consent)
│   │   ├── ProspectRankingTable.jsx # Portfolio scanning table with accordion detail
│   │   ├── UrgentActionsPanel.jsx  # Top targeted prospect lists
│   │   ├── CampaignIntelligencePanel.jsx # Campaigns listing visual cards
│   │   └── AgentActivityFeed.jsx   # Live updates on backend events
│   ├── client/
│   │   ├── ClientPortal.jsx        # Fullscreen overlay modal manager
│   │   ├── KYCProfileCard.jsx      # Financial indices & accounts breakdown
│   │   ├── TransactionOverviewPanel.jsx # High-density chart & search records
│   │   ├── ProspectReasonPanel.jsx  # Scoring factors & signals panel
│   │   ├── AgentEvidencePanel.jsx   # Sequence logs for CrewAI analysis
│   │   ├── OutreachPanel.jsx        # Historical message list
│   │   ├── AgentContributionPanel.jsx 🆕 # Interactive contribution gauges
│   │   ├── CampaignHistoryList.jsx 🆕   # Visual campaigns targeting details
│   │   ├── ComplianceStatusBanner.jsx 🆕 # Compliance checks & warning highlights
│   │   ├── EvidenceTimeline.jsx 🆕      # Time-series behavioral signal nodes
│   │   ├── LoanFitFactorChips.jsx 🆕    # Dynamic credit fit tags
│   │   ├── NextBestActionCard.jsx 🆕    # RM-facing action triggers
│   │   ├── OutreachPreviewDrawer.jsx 🆕 # WhatsApp sliding draft composer & simulator
│   │   └── ProspectReasonCard.jsx 🆕    # Detailed radar score breakdown cards
│   ├── conversation/
│   │   ├── MessageBubble.jsx       # Chat bubble with markdown support
│   │   ├── MessageInput.jsx        # Input bar with stream status locks
│   │   ├── TemplateSuggestionBar.jsx # 4 quick-action contextual next steps
│   │   ├── InlineDataGrid.jsx 🆕    # Autogenerated tables inside chat bubbles
│   │   └── PlanCard.jsx 🆕          # Vertical interactive plan step timeline
│   ├── campaigns/
│   │   ├── CampaignApprovalModal.jsx 🆕 # Batch approval trigger overlay
│   │   └── CampaignCard.jsx 🆕          # Dashboard mini campaign visual cards
│   ├── agents/
│   │   ├── AgentActivityPanel.jsx 🆕  # Real-time CrewAI timeline widget
│   │   └── ToolExecutionCard.jsx 🆕   # Tool call inputs/outputs inspector card
│   └── shared/
│       ├── ScoreBar.jsx           # Progress-bar indicator for readiness
│       ├── ConfidenceMeter.jsx     # Visual indicator for signal scores
│       ├── ComplianceBanner.jsx    # Small compliance status check badges
│       ├── SignalChip.jsx          # Color-coded lifestyle spend flags
│       ├── LoadingSkeleton.jsx     # Pulse shimmer component skeletons
│       ├── SettingsModal.jsx       # Side-drawer config for API keys
│       └── NotificationToast.jsx   # Toast alert dispatcher
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
│   │   │   ├── models.py             # SQLAlchemy ORM (14 tables mapping)
│   │   │   ├── database.py           # Engine + session management
│   │   │   └── repositories/         # Data access layer (4 files)
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── seed/                     # 75-customer seed generator
│   │   ├── services/                 # Business logic layer (10 core services)
│   │   ├── tools/                    # 21 @tool functions (8 files)
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
│   │   └── components/               # 34 modular feature UI components
│   ├── package.json
│   └── vite.config.js
└── README.md
```
