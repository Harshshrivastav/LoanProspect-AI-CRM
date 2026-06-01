# 🎨 LoanProspect AI CRM — Frontend Architecture & UI Components

This document details the React frontend architecture, state management hook, custom widgets, and interaction flows designed for the **Unified Agentic Chat Workspace** in LoanProspect AI CRM.

---

## 🎛️ State Management: `useStreaming.js` Hook

The front-end state machine is governed by the custom hook `useStreaming.js` (located in `src/hooks/useStreaming.js`). This hook translates real-time NDJSON streaming packets into component state updates.

### Stream Parsing and State Machine

When a stream begins, `useStreaming` manages:
- **`isStreaming`**: Boolean flag indicating active stream processes.
- **`agentActivity`**: A linear timeline of chronological events emitted by the agent (e.g. status changes, tool calls, results, thoughts, memory compactions).
- **`steps`**: Tracks the status and outputs of plan steps.
- **`currentText`**: Accumulates the streaming text responses from conversational agents.
- **`error`**: Logs exceptions or timeout alerts.

### NDJSON Event Routing Map

The hook iterates over parsed JSON event objects and updates state dynamically:

| Event Type (`event.type`) | Front-End State Action | Visual Manifestation |
| :--- | :--- | :--- |
| **`plan`** | Compiles initial steps list, complexity metrics, and plan IDs. | Displays the vertical plan timeline. |
| **`step_start`** | Marks the active step as `running`. | Timeline bullet shifts to an amber pulse. |
| **`thought`** | Appends internal thoughts to `agentActivity` and step-specific thoughts. | Renders as CoT details under the step. |
| **`tool_call`** | Captures tool invocations, inputs, and steps. | Renders a specialized tool card. |
| **`tool_result`** | Attaches output responses to matching steps. | Timeline displays success tags or result previews. |
| **`paused_hitl`** | Pauses stream rendering and sets up feedback states. | Opens WhatsApp preview and message draft editor. |
| **`loop_decision`** | Adds decision status logs (e.g. continue, replan). | Displays active control alerts. |
| **`replanned`** | Rewrites scheduled steps with dynamic branch overrides. | Renders updated timeline steps dynamically. |
| **`memory_summary`** | Appends compacted summaries to activity feeds. | Displays memory compaction alerts. |
| **`chunk`** | Appends textual markdown streams to active answers. | Streams text inline inside chat bubbles. |
| **`done`** | Saves final results and closes streaming locks. | Renders contextual next-step suggestion buttons. |

---

## 📅 The Stepper Timeline Component: `PlanCard.jsx`

The sequential timeline and Human-in-the-Loop (HITL) draft editors are combined into a single, cohesive component: `PlanCard.jsx`.

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Agentic Execution Plan                                   │
│ [ running ]                                                 │
├─────────────────────────────────────────────────────────────┤
│   ● Step 1: Scans portfolio for loan prospects              │
│     🔧 list_customers_brief                                 │
│   ● Step 2: Analyzes credit risk and salary trends          │
│     🔧 get_customer_risk_summary  [active pulse]            │
│     🧠 Agent Thoughts:                                      │
│        💭 Analyzing inflow trend for CUST002...             │
│        🔧 Calling get_customer_risk_summary                 │
│   ○ Step 3: Generates personalized WhatsApp messages        │
│     🔧 generate_whatsapp_message  ⚡ REQUIRES REVIEW         │
└─────────────────────────────────────────────────────────────┘
```

### Features of `PlanCard`
1. **Collapsible Accordions**: RMs can expand step rationales and internal CoT (Chain of Thought) logs directly inside the stepper card.
2. **Dynamic Badges**: Displays state values like `pending`, `running`, `success`, `failed`, or `paused_hitl` with corresponding HSL colors.
3. **Retry Indicator**: Displays retry counters and warning banners if a step is experiencing intermittent failures.
4. **Step Result Previews**: Shows compact, code-styled previews of successful tool observations directly in the timeline without cluttering the chat thread.
5. **Interactive Controls**:
   - **Plan Approval Banner**: Blocks subsequent steps and presents the RM with a button to *"Approve Plan & Launch Autopilot"*.
   - **Inline Message Composer**: When outreach is generated, a virtual WhatsApp phone preview card opens, letting the RM review, edit, approve, or dismiss drafts.

---

## 📊 Tabular Data Renderer: `InlineDataGrid.jsx`

When tools return lists or multi-dimensional records (e.g., search queries matching specific filters, or ranked prospect summaries), traditional Markdown lists can be difficult to read. The `InlineDataGrid` component handles these scenarios beautifully:

- **Automatic Headers**: Parses keys from JSON arrays to compile structured data tables.
- **Scrollable Layouts**: Provides a horizontal scroll wrapper to handle extensive row structures.
- **Interactive Row Selection**: Integrates with global React contexts (like `useClientPortal`), letting RMs click customer rows to open detailed overlays instantly.
- **Micro-Animations**: Utilizes Framer Motion transitions for elegant row entry animations.

---

## 🤝 Unifying Context & Sidebar Navigation

The page controller (`pages/ConversationWorkspace.jsx`) integrates conversational threads with the rest of the application context:

### 1. Contextual Suggestions Bar
When a chat interaction completes, `TemplateSuggestionBar` displays 4 customized next-step recommendations (e.g. *"Generate messages for CUST012"*, *"Review compliance audit logs"*). RMs can click these templates to run subsequent queries instantly.

### 2. Client Portal Modals
Clicking any customer ID (like `CUST015`) anywhere in the chat bubbles parses the string, resolves the customer's state, and opens the full-screen customer profile modal (`ClientPortal.jsx`). The RM can view transaction histories, KYC records, and credit scores without leaving the chat thread.

---

> [!NOTE]
> All interface components use harmonious, tailored HSL color palettes and micro-animations to look premium. The sidebar has been cleaned to remove any separated `/planner` routes, unifying all agent interactions inside the `/chat` route.
