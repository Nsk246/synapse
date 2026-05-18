# Synapse

> Real-time semantic observability for multi-agent LLM pipelines.

Synapse intercepts meaning drift at agent handoff boundaries — before it becomes a silent production failure.

## The problem

Multi-agent systems (LangGraph, CrewAI, etc.) suffer from **semantic drift**: an agent outputs structurally valid JSON that completely misrepresents the intent passed by the previous node. Standard observability tools (LangSmith, Langfuse) record this after the fact. Synapse blocks it at the boundary.

## How it works

Each handoff passes through a two-phase middleware:

1. **Schema Gate** — Pydantic structural validator. Blocks malformed output.
2. **Semantic Drift Validator** — all-MiniLM-L6-v2 cosine similarity check. Blocks meaning loss.

If cosine similarity < threshold (default 0.85), the edge halts and surfaces a forensics panel.

## Stack

- **Backend**: FastAPI, LangGraph, Pydantic, sentence-transformers
- **Frontend**: Next.js 14, React Flow v12, Tailwind CSS, Zustand
- **Transport**: WebSockets (9-event discriminated schema)

## Pipeline

Query Planner -> Web Researcher -> Evidence Analyst -> Report Writer

## Getting started

cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
