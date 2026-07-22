# Capstone Project: "DocOps" — Multi-Agent Research & Ticket-Resolution Assistant

A single coherent product idea so every technology has a *real* job to do, not a bolted-on demo.

## The product

An internal support assistant that:
1. Answers questions from a knowledge base (RAG) — e.g. product docs, runbooks, or your own SCCM/Intune/PSADT documentation (use what you know from your day job — great portfolio angle).
2. Can take actions via **MCP tools** (e.g. query a ticket system, check a "server status" mock API, create a ticket).
3. Uses a **multi-agent LangGraph workflow**: a Router agent → Retriever agent → Tool-calling agent → Critique/Verifier agent that loops back with retries if the answer is low-confidence or a tool call fails.
4. Pauses for **human-in-the-loop approval** before any "write" action (e.g. creating a ticket, sending an escalation) — LangGraph's `interrupt()` is built for exactly this.
5. Is served over **FastAPI**, containerized, deployed to AWS free tier, with **CI/CD** and **Langfuse** tracing every agent step, tool call, and retry.

This gives you one true end-to-end story instead of 8 disconnected proofs-of-concept — the thing interviewers actually want to see.

---

## Phased build order

### Phase 0 — Repo & environment skeleton
- Set up folder structure (below), `pyproject.toml`/`requirements.txt`, `.env.example`, pre-commit (black/ruff), `Makefile` with `run`, `test`, `lint` targets.
- **Learning goal:** production repo hygiene before writing any agent code.

### Phase 1 — RAG core (no agents yet)
- Ingest docs → chunk → embed → store in a vector DB (start with Chroma or FAISS locally, since it's free; note pgvector as the "real" prod option).
- Simple `retriever.py` + a `/query` FastAPI endpoint that does retrieval + Groq LLM call, no agent framework yet.
- **Learning goal:** get the RAG fundamentals rock solid in isolation before LangChain wraps around it — makes debugging later phases 10x easier.

### Phase 2 — Wrap RAG with LangChain
- Reimplement Phase 1's retriever/chain using LangChain's `Runnable`/LCEL, `ChatGroq`, and a proper prompt template + output parser.
- **Learning goal:** LangChain idioms (Runnables, chains, memory) on top of logic you already trust.

### Phase 3 — MCP tool server
- Build a small MCP server (Python `mcp` SDK) exposing 2–3 tools: `search_kb`, `create_ticket` (mock), `check_status` (mock).
- Connect it as a LangChain/LangGraph tool via an MCP client.
- **Learning goal:** MCP as the standard interface between your agent and "the outside world" — same shape as Claude's own tool use.

### Phase 4 — Multi-agent graph with retry loop
- Build the LangGraph graph: `Router → Retriever → Answerer → Verifier`, with a conditional edge: if Verifier scores the answer low or a tool call errors, loop back (max N retries) before falling through to a "give up / escalate" node.
- **Learning goal:** stateful graphs, conditional edges, and bounded retry loops — the actual "agentic" part.

### Phase 5 — Human-in-the-loop
- Add an `interrupt()` node before any write-action (e.g. `create_ticket`) that pauses the graph and waits for approval via a FastAPI endpoint (`/approve/{run_id}`), then resumes the graph from checkpoint.
- **Learning goal:** LangGraph checkpointing/persistence (needed for interrupt/resume to work at all).

### Phase 6 — Observability with Langfuse
- Wrap the graph with the Langfuse callback handler; tag traces by agent node, tool call, retry count, and human-approval latency.
- Build 2–3 dashboards: retry rate, tool failure rate, human-approval turnaround.
- **Learning goal:** this is what separates "I built an agent" from "I can run one in production."

### Phase 7 — Containerize
- `Dockerfile` (multi-stage, slim base), `docker-compose.yml` for local dev (API + vector DB + Langfuse local, if you self-host it).
- **Learning goal:** production Docker patterns (multi-stage builds, non-root user, healthchecks).

### Phase 8 — Kubernetes (local first)
- Deploy to `kind` or `minikube` first — free, and lets you learn K8s manifests without burning AWS credits.
- `Deployment`, `Service`, `ConfigMap`/`Secret`, `HorizontalPodAutoscaler` (optional, for the resume line).
- **Learning goal:** K8s primitives without cloud cost pressure.

### Phase 9 — AWS free tier deployment
- Given free tier constraints: **ECR** (free tier includes some storage) to host the image, and either:
  - a single **EC2 t2.micro/t3.micro** (free tier eligible) running Docker directly, or
  - **k3s on that same EC2 instance** if you want to show "Kubernetes on AWS" without paying for EKS (EKS control plane is NOT free tier).
- Be upfront in your portfolio write-up that EKS was substituted with k3s-on-EC2 specifically due to free-tier cost — that's a legitimate, honest engineering tradeoff to narrate in interviews.
- **Learning goal:** realistic cloud deployment under real cost constraints — very relatable to interviewers.

### Phase 10 — CI/CD
- GitHub Actions: on push → lint/test → build image → push to ECR → (manual approval gate) → deploy to EC2 via SSH/systemd or `docker compose pull && up -d`.
- **Learning goal:** a CI/CD pipeline that's honest about free-tier limits (no fancy blue/green on a single t3.micro — and that's fine to say out loud).

---

## Production-style folder structure

```
docops-assistant/
├── src/
│   └── docops/
│       ├── api/                  # FastAPI app
│       │   ├── main.py
│       │   ├── routes/
│       │   │   ├── query.py
│       │   │   ├── approve.py
│       │   │   └── health.py
│       │   └── dependencies.py
│       ├── agents/                # LangGraph graph + nodes
│       │   ├── graph.py
│       │   ├── nodes/
│       │   │   ├── router.py
│       │   │   ├── retriever.py
│       │   │   ├── answerer.py
│       │   │   └── verifier.py
│       │   └── state.py
│       ├── rag/
│       │   ├── ingest.py
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   └── vectorstore.py
│       ├── mcp_server/
│       │   ├── server.py
│       │   └── tools/
│       │       ├── search_kb.py
│       │       ├── create_ticket.py
│       │       └── check_status.py
│       ├── mcp_client/
│       │   └── client.py
│       ├── llm/
│       │   └── groq_client.py
│       ├── observability/
│       │   └── langfuse_setup.py
│       ├── core/
│       │   ├── config.py         # pydantic settings, env vars
│       │   └── logging.py
│       └── schemas/               # pydantic models shared across layers
│           ├── query.py
│           └── agent_state.py
├── tests/
│   ├── unit/
│   └── integration/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── overlays/
│       ├── local/
│       └── aws/
├── .github/
│   └── workflows/
│       ├── ci.yaml
│       └── cd.yaml
├── scripts/
│   ├── ingest_docs.sh
│   └── deploy_ec2.sh
├── data/
│   └── raw_docs/                  # sample knowledge base
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

Key production conventions baked in:
- `src/` layout (not a flat repo) so packaging and imports behave correctly.
- Config centralized in `core/config.py` via `pydantic-settings`, never scattered `os.getenv()` calls.
- `agents/state.py` holds a single typed `AgentState` (TypedDict/pydantic) that flows through every LangGraph node — this is the backbone that makes retries and human-in-the-loop resumption possible.
- `k8s/base` + `overlays` (Kustomize pattern) so "local" and "aws" differ only in the overlay, not duplicated manifests.

---

## Suggested pace
Each phase above is realistically 2–5 days of focused work depending on your schedule. Phases 0–3 are the foundation and shouldn't be rushed — everything else builds on that `AgentState` and MCP tool contract being right.

Want to start with Phase 0 + Phase 1 right now? I can generate the actual starter code (ingestion script, vectorstore setup, FastAPI skeleton) for those two phases.
