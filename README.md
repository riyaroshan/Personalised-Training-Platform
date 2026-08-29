# Personalized AI Training Platform

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
