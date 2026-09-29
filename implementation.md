# Nexus — Current Implementation Plan

This is the canonical Nexus implementation plan. Follow this plan as the baseline and do not reorder, add, remove, or redesign steps unless explicitly requested.

---

## Phase 1 — Foundation

| Step | Status | Implementation |
|---|---|---|
| Define LangGraph state | 🟢 Done | `app/graph/state.py` → `AssistantState` |
| Build basic graph flow | 🟢 Done | `app/graph/graph.py` |

### Current state

```text
messages
user_id
request_type
health_result
productivity_result
final_response
```

---

## Phase 2 — Routing

| Step | Status | Implementation |
|---|---|---|
| LLM-based request classifier | 🟢 Done | `app/graph/routing.py` → `route()` |
| Test health/productivity/both routing | 🟢 Done | Routing tests / graph invocation |

---

## Phase 3 — Database

| Step | Status | Implementation |
|---|---|---|
| Supabase setup | 🟢 Done | `app/database/config.py` |
| `users` | 🟢 Done | Supabase |
| `workouts` | 🟢 Done | Supabase |
| `meals` | 🟢 Done | Supabase |
| `sleep_logs` | 🟢 Done | Supabase |
| `tasks` | 🟢 Done | Supabase |
| `habits` | 🟢 Done | Supabase |
| `reflections` | 🟢 Done | Supabase |
| `memories` + pgvector | 🟢 Done | Supabase/Postgres |

Database functions remain centralized in:

```text
app/database/db.py
```

---

# Phase 4 — Health Agent

## Core Health Agent

| Step | Status | Implementation |
|---|---|---|
| Design Health Agent | 🟢 Done | `app/agents/health_agent.py` |
| Health Agent LLM | 🟢 Done | `get_health_agent()` |

## `log_workout`

| Step | Status | Implementation |
|---|---|---|
| `log_workout` schema | 🟢 Done | `app/tools/health_tools.py` |
| `log_workout` DB function | 🟢 Done | `app/database/db.py` |
| Supabase insertion test | 🟢 Done | Verified |
| Bind `log_workout` to Health Agent | 🟢 Done | `health_agent.py` |
| Execute tool through LangGraph | 🟢 Done | `node.py` + `graph.py` + `ToolNode` |

## `log_meal`

| Step | Status | Implementation |
|---|---|---|
| `log_meal` schema | ⏳ | `app/tools/health_tools.py` |
| `log_meal` DB function | ⏳ | `app/database/db.py` |
| Supabase insertion test | ⏳ | Test meal insertion |
| Bind `log_meal` to Health Agent | ⏳ | `app/agents/health_agent.py` |
| Execute `log_meal` through LangGraph | ⏳ | `node.py` + `graph.py` + `ToolNode` |

## `log_sleep`

| Step | Status | Implementation |
|---|---|---|
| `log_sleep` schema | ⏳ | `app/tools/health_tools.py` |
| `log_sleep` DB function | ⏳ | `app/database/db.py` |
| Supabase insertion test | ⏳ | Test sleep insertion |
| Bind `log_sleep` to Health Agent | ⏳ | `app/agents/health_agent.py` |
| Execute `log_sleep` through LangGraph | ⏳ | `node.py` + `graph.py` + `ToolNode` |

## Shared Memory / Retrieval

| Step | Status | Implementation |
|---|---|---|
| Build shared embedding/retrieval utility | ⏳ | `app/memory/...` |
| Health retrieval + pgvector | ⏳ | Health Agent using shared utility |
| Complete Health Agent | ⏳ | `health_agent.py`, `node.py`, `graph.py` |

### Shared retrieval architecture

```text
                 app/memory/
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
    Health Agent         Productivity Agent
          │                     │
          └──────────┬──────────┘
                     ↓
                  pgvector
```

Build embedding and similarity-search logic once and reuse it across both domains.

---

# Early Observability — LangSmith

LangSmith is introduced immediately after the Health Agent foundation so the remaining agent development is observable.

| Step | Status | Implementation |
|---|---|---|
| LangSmith tracing setup | ⏳ | LangGraph / agent execution |
| Trace Health Agent | ⏳ | Health Agent + graph |
| Keep tracing active for subsequent phases | ⏳ | Productivity + synthesis + API |

---

# Phase 5 — Productivity Agent

| Step | Status | Implementation |
|---|---|---|
| Design Productivity Agent | ⏳ | `app/agents/productivity_agent.py` |
| Task tools | ⏳ | `app/tools/...` + `app/database/db.py` |
| Habit tools | ⏳ | `app/tools/...` + `app/database/db.py` |
| Reflection tools | ⏳ | `app/tools/...` + `app/database/db.py` |
| Productivity retrieval using shared utility | ⏳ | `app/memory/...` |
| Complete Productivity Agent | ⏳ | Agent/node/graph integration |

---

# Phase 6 — Synthesis

| Step | Status | Implementation |
|---|---|---|
| Handle `both` requests | ⏳ | `app/graph/graph.py` + `node.py` |
| Final response synthesis | ⏳ | `synthesis_node()` in `node.py` |

### Flow

```text
                  Router
                 /                  Health    Productivity
               \        /
                \      /
                 Synthesis
                     ↓
              final_response
```

For `"both"` requests, `health_result` and `productivity_result` are available to synthesis.

---

# Phase 7 — FastAPI

| Step | Status | Implementation |
|---|---|---|
| `/chat` | ⏳ | `app/api/...` |
| `/logs` GET/POST | ⏳ | `app/api/...` |
| `/health` | ⏳ | `app/api/...` |

---

# Phase 8 — Authentication & Sessions

Authentication identity and LangGraph conversation state are separate.

| Step | Status | Implementation |
|---|---|---|
| Signup | ⏳ | Auth/API layer + `users` |
| Login | ⏳ | Auth/API layer |
| User/session handling (`user_id`) | ⏳ | Auth context |
| LangGraph checkpointer setup | ⏳ | LangGraph |
| `thread_id` wiring | ⏳ | Graph invocation config |
| Connect authenticated user → graph session | ⏳ | Auth + graph |
| Add auth middleware/checks to `/chat` and `/logs` | ⏳ | `app/api/...` |

### Authentication vs LangGraph state

```text
Authentication
     ↓
  user_id
```

```text
LangGraph session
     ↓
 thread_id
     ↓
checkpointer
     ↓
saved graph state
```

`thread_id` has already been used during testing, but persistent checkpointer wiring is not implemented yet.

No separate `sessions` table is planned.

---

# Phase 9 — Frontend

| Step | Status | Implementation |
|---|---|---|
| Signup/Login UI | ⏳ | `UI/` |
| Chat UI | ⏳ | `UI/` |
| Connect frontend → FastAPI | ⏳ | `UI/` + API |

Planned frontend:

```text
HTML + CSS + JavaScript
```

Streamlit remains the fallback.

---

# Phase 10 — End-to-End Testing

| Step | Status | Implementation |
|---|---|---|
| End-to-end application testing | ⏳ | `tests/` |
| Authentication → graph → persistence flow | ⏳ | `tests/` |
| Health/Productivity/Both flows | ⏳ | `tests/` |

LangSmith tracing is already active before this phase.

---

# Exact Remaining Build Order

```text
1. Finish Health Agent
   ├── log_meal
   │   ├── schema
   │   ├── DB function
   │   ├── Supabase insertion test
   │   ├── bind to Health Agent
   │   └── execute through LangGraph
   │
   ├── log_sleep
   │   ├── schema
   │   ├── DB function
   │   ├── Supabase insertion test
   │   ├── bind to Health Agent
   │   └── execute through LangGraph
   │
   ├── build shared embedding/retrieval utility
   ├── health retrieval + pgvector
   └── complete Health Agent

2. LangSmith
   ├── tracing setup
   ├── trace Health Agent
   └── keep tracing active

3. Productivity Agent
   ├── design
   ├── task tools
   ├── habit tools
   ├── reflection tools
   ├── shared retrieval
   └── complete agent

4. Synthesis
   ├── both requests
   └── final response

5. FastAPI
   ├── /chat
   ├── /logs GET/POST
   └── /health

6. Authentication & Sessions
   ├── signup
   ├── login
   ├── user_id/session handling
   ├── LangGraph checkpointer
   ├── thread_id wiring
   ├── authenticated user → graph session
   └── auth middleware/checks on /chat and /logs

7. Frontend
   ├── signup/login UI
   ├── chat UI
   └── frontend → FastAPI

8. End-to-End Testing
   ├── complete application flow
   └── verify auth + persistence + Health/Productivity/Both
```

# Current Exact Position

```text
Phase 4 — Health Agent

✅ log_workout
✅ Health Agent LLM
✅ user_id injection through LangGraph state
✅ LLM → ToolNode → Supabase → LLM loop

NEXT:
→ log_meal schema
→ log_meal DB function
→ log_meal Supabase test
→ bind log_meal
→ execute log_meal through LangGraph
→ log_sleep (same 5 steps)
→ shared embedding/retrieval utility
→ health retrieval + pgvector
→ complete Health Agent
```
