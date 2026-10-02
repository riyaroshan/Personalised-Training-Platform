# Personalized AI Training Platform

Fun little personal project for myself where I learn  LLM application engineering, RAG, agents/tool use, evaluation, structured outputs, embeddings, ML pipelines while also creating an app I'd like to use to track my workouts. Will take 10 phases to complete.

Phase 1: deterministic workout engine.
Phase 2: structured LLM plans with validation, retries, and engine fallback.

## Run

```bash
cd backend
uv sync
uv run pytest
uv run python scripts/demo.py
uv run uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Copy `backend/.env.example` to `backend/.env` and set `OPENAI_API_KEY` to use the model. Without a key, `POST /v1/users/{id}/plan/ai` still returns a valid plan from the engine (`generation.source = "fallback"`).

## Try it

Create a user, then either:

- `POST /v1/users/{id}/plan` — rules only (`generation.source = "engine"`)
- `POST /v1/users/{id}/plan/ai` — LLM structured output, validated; falls back to the engine if the model is missing or invalid

## What exists

- Exercise catalog, routine generator, logging, progression
- Structured `WorkoutPlan` generation, prompt version `workout_plan.v1`, retries, fallback
- RAG over a curated exercise-science knowledge base (chunking, hybrid retrieval, rerank, citations)
- Exercise embeddings for “something like X” with equipment filters

## RAG

```bash
# docs: POST /v1/rag/query
# ablate retriever settings: GET /v1/rag/ablate
# similar exercises: POST /v1/exercises/similar
```

Example: `{"question": "Should I train chest twice or three times a week?"}`

Default embeddings are local hashing so RAG works without an embedding API. Set `EMBEDDING_PROVIDER=openai` if you want OpenAI embeddings. With `DATABASE_URL` pointing at Postgres, chunks are also written to pgvector (`docker compose up -d`).


## Proposed Structure
```text
                 React Native
                      │
                      ▼
                 API Gateway
                      │
              FastAPI / Python
                      │
       ┌──────────────┼───────────────┐
       │              │               │
       ▼              ▼               ▼
 Workout Engine   AI Orchestrator   Analytics
       │              │
       │       ┌──────┼──────────┐
       │       ▼      ▼          ▼
       │      LLM   Retriever   Tools
       │              │
       │            pgvector
       │
       ▼
   PostgreSQL
       │
       ▼
Training / Feature Pipeline
       │
       ▼
Prediction Model
```
