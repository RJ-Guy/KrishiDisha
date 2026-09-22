# KrishiDisha — Autonomous Multi-Agent Registry

This directory contains the operational profiles, boundaries, and prompt specifications for autonomous agents working on the **KrishiDisha** project (Smart India Hackathon 2026, Problem Statement 26132).

---

## Agent Directory & Access Matrix

| Agent Identifier | Role | Allowed Read Scope | Allowed Write Scope | Status |
|---|---|---|---|---|
| [`system_architect`](file:///D:/KrishiDisha/Agents/SYSTEM_ARCHITECT.md) | Master System & Software Architect | `Information/`, Architecture specs | `Architecture/` only | **Configured & Active** |
| [`frontend_agent`](file:///D:/KrishiDisha/Agents/FRONTEND_AGENT.md) | Lead Frontend & UI/UX Engineer | `Information/`, `Agents/`, `Frontend/`, `Backend/` (read-only) | `Frontend/` only | **Configured & Active** |
| [`backend_database_agent`](file:///D:/KrishiDisha/Agents/BACKEND_DATABASE_AGENT.md) | Lead Backend Engineer & Database Architect | `Information/`, `Agents/`, `Frontend/` (read-only), `Backend/` | `Backend/` only | **Configured & Active** |
| [`ml_data_pipeline_agent`](file:///D:/KrishiDisha/Agents/ML_DATA_PIPELINE_AGENT.md) | ML & Data Pipeline Engineer | `Information/`, `Agents/`, `Frontend/` (read-only), `Backend/` | `Backend/` only (ML modules) | **Configured & Active** |
| [`business_logic_agent`](file:///D:/KrishiDisha/Agents/BUSINESS_LOGIC_AGENT.md) | Algorithms & Decision Logic Engineer | `Information/`, `Agents/`, `Frontend/` (read-only), `Backend/` | `Backend/app/services/` | **Configured & Active** |

---

## Access Governance
1. **Separation of Concerns:** Each agent must strictly operate within its defined write scope.
2. **Cross-Read Collaboration:**
   * **Backend Agents** have **read-only** access to `Frontend/` to inspect client API calls, models, and presentation expectations (strictly NO writing to `Frontend/`).
   * **Frontend Agent** has **read-only** access to `Backend/` to inspect FastAPI routers, Pydantic schemas, and ML response formats (strictly NO writing to `Backend/`).
3. **Single Source of Truth:** All agents must treat [`D:/KrishiDisha/Information/EXECUTION_PLAN.md`](file:///D:/KrishiDisha/Information/EXECUTION_PLAN.md) as the authoritative master blueprint.
4. **Architectural Compliance:** Downstream agents must follow the blueprints and contracts created by the [`system_architect`](file:///D:/KrishiDisha/Agents/SYSTEM_ARCHITECT.md).
