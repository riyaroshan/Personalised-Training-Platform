# Personalized AI Training Platform
## Design Timeline

> **Positioning:** Not “a gym app that calls an LLM.” A production-style AI coaching system, using fitness as the domain.
>
> **Resume line (eventual):** Built a production-style AI coaching system combining deterministic recommendation algorithms, RAG, structured LLM generation, tool-calling agents, personalized ML models, and automated evaluation. Developed observability for model latency, cost, retrieval quality and response accuracy, with offline evaluation suites for hallucination and constraint adherence.

**North star:** Demonstrate LLM application engineering, RAG, agents/tool use, evaluation, structured outputs, embeddings, ML pipelines, observability, inference, and classical ML.

**Core interview pillars (prioritize these):** Evaluation · RAG · Tool calling · ML inference · Observability

**Stack:** React Native · FastAPI / Python · PostgreSQL + pgvector

---

## How to use this in Notion

1. Paste this page into Notion.
2. Turn the **Timeline at a glance** table into a database → add a **Timeline** view (use the Week range as dates).
3. Convert each phase heading into a **Toggle** so the page stays scannable.
4. Optional statuses: `Not started` · `In progress` · `Done` · `Later / skip`

---

## End-state architecture

```
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

Python/FastAPI on purpose: Pydantic, PyTorch, Hugging Face, sklearn, numpy/pandas, eval tooling, model serving. Node experience is already covered; this fills the AI-engineer gap.

---

## Timeline at a glance

| Order | Phase | Stage | Weeks | Status | Priority | Depends on | Ships |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | P1 Deterministic training engine | Foundation | 1–4 | Not started | Must | — | Workout engine, history, progression rules |
| 2 | P2 Structured LLM outputs | LLM app | 5–6 | Not started | Must | P1 | Validated WorkoutPlan schema, retries, prompt versions |
| 3 | P3 Tool-calling coach | LLM app | 7–8 | Not started | Must | P1, P2 | Agent that queries real training data |
| 4 | P4 RAG knowledge base | LLM app | 9–11 | Not started | Must | P2 | pgvector retrieval over exercise science |
| 5 | P8 Exercise embeddings | LLM app | 11–12 | Not started | Should | P4 | Similarity search + equipment filters |
| 6 | P5 Evaluation suite | Trust | 13–15 | Not started | Must | P2–P4 | 500 scenarios, constraint/hallucination metrics |
| 7 | P6 LLM-as-judge | Trust | 16–17 | Not started | Must | P5 | Semantic eval vs human labels |
| 8 | P12 Safety & guardrails | Trust | 18–19 | Not started | Must | P5 | Risk classifier + adversarial tests |
| 9 | P10 Observability | Production | 6–20 (ongoing) | Not started | Must | P2 | Traces, cost, latency, eval dashboards |
| 10 | P7 Recommendation / ML | Classical ML | 21–23 | Not started | Should | P1 + data | XGBoost vs heuristics, progression model |
| 11 | P11 Model routing | Production | 24 | Not started | Should | P7, P10 | Task → model router, quality/cost/latency |
| 12 | P9 Multi-agent (optional) | Later | 25+ | Later / skip | Nice | P3, P11 | Only if a real split of labor appears |

**Interview-ready path:** P1 → P2 → P3 → P4 → P5 → P6 → P10 → P12. That is enough to justify the résumé line.

**Do not start with:** multi-agent diagrams. Knowing when *not* to use an agent is part of the story.

---

## Stage A — Foundation

The AI needs something real to reason over. No LLM deciding everything yet.

---

### Phase 1 — Deterministic training engine
**Weeks 1–4 · Must · Status:** Not started

**Objective:** A real workout product with rules, history, and progression — not a chatbot.

**Pipeline**

```
User profile
    ↓
Goals + constraints
    ↓
Exercise database
    ↓
Routine generator
    ↓
Workout history
    ↓
Progression engine
    ↓
Next workout
```

**Core record**

```python
WorkoutSet {
    exercise_id
    weight
    reps
    rpe
    rir
    completed_at
}
```

**Build**
- [ ] User profile, goals, constraints (days/week, duration, equipment, injuries)
- [ ] Exercise database (movement pattern, muscles, equipment, difficulty)
- [ ] Rule-based routine generator
- [ ] Workout logging + history
- [ ] Progressive overload, deloads, volume, recovery, substitutions

**You learn:** domain modeling, recommendation heuristics, data you will later retrieve/evaluate against.

**Done when:** given a profile, the system produces a valid next workout from rules + history, with no LLM required.

**Interview angle:** “The model never invents the training system. It reasons over an engine I already trust.”

---

## Stage B — LLM application layer

Structured generation, tools, then retrieval. This is applied AI engineering, not “call GPT.”

---

### Phase 2 — Structured LLM outputs
**Weeks 5–6 · Must · Status:** Not started

**Objective:** The model returns validated objects, not free text.

**Not this**

```python
response = llm("make a workout")
```

**This**

```python
class ExercisePrescription(BaseModel):
    exercise_id: str
    sets: int
    rep_min: int
    rep_max: int
    target_rir: int

class WorkoutPlan(BaseModel):
    exercises: list[ExercisePrescription]
    reasoning: str
```

**Build**
- [ ] Pydantic (or equivalent) schemas for plans, substitutions, coach answers
- [ ] Schema validation before anything is persisted or shown
- [ ] Retry on invalid output
- [ ] Deterministic fallback (Phase 1 engine) when the model fails
- [ ] Prompt versioning

**You learn:** structured outputs → validation → retries → fallbacks → prompt versioning

**Done when:** an invalid LLM payload never reaches the user; the engine can take over.

**Interview angle:** production LLM apps fail closed, not with a blob of markdown.

---

### Phase 3 — Give the AI tools
**Weeks 7–8 · Must · Status:** Not started

**Objective:** The coach looks up facts instead of stuffing the whole database into the prompt.

**Tools**

```
get_recent_workouts()
get_exercise_history()
get_muscle_volume()
get_personal_records()
get_recovery_scores()
find_exercise_substitutes()
update_workout_plan()
```

**Example**

> Why hasn't my bench improved?

```
get_exercise_history("bench_press", 60 days)
get_muscle_volume("chest", 30 days)
get_recovery_scores(30 days)
```

Then reason over results.

**Build**
- [ ] Tool schemas + execution layer
- [ ] Agent loop with bounded steps
- [ ] Ground answers in tool results
- [ ] Log every tool call (feeds Phase 10)

**You learn:** tool calling / agentic AI — high signal for AI engineer roles.

**Done when:** a question like the bench example runs tools and cites returned data, not a generic pep talk.

**Interview angle:** “I didn’t RAG the user’s lifting history. That’s operational data, so it became tools.”

---

### Phase 4 — Build RAG properly
**Weeks 9–11 · Must · Status:** Not started

**Objective:** Curated exercise-science knowledge, retrieved — not hoped-for parametric memory.

**Architecture**

```
Documents
   ↓
Chunking
   ↓
Embedding model
   ↓
Vector database
   ↓
Retriever
   ↓
Relevant context
   ↓
LLM
```

**Store:** Postgres + pgvector (no extra database unless you need one).

**Knowledge base should include:** exercise descriptions, movement patterns, training principles, injury precautions, hypertrophy guidance, your methodology.

**Example:** “Should I train chest twice or three times a week?” → retrieve, then answer.

**Experiments**
- [ ] Chunk sizes
- [ ] Semantic retrieval
- [ ] Metadata filtering
- [ ] Hybrid search
- [ ] Reranking
- [ ] Top-k
- [ ] Contextual retrieval

**Done when:** answers cite retrieved chunks; you can ablate retriever settings and see quality change.

**Interview angle:** you can talk chunking, filters, hybrid search, and rerank — not “I dumped PDFs into a vector store.”

---

### Phase 8 — Embeddings for exercise recommendations
**Weeks 11–12 · Should · Status:** Not started
*(Pulled next to RAG because it reuses the same embedding/retrieval stack.)*

**Objective:** Embeddings as a product feature, not only as RAG plumbing.

**Example:** “The cable machine is occupied. Give me something similar to cable fly.”

Embed on: muscle · movement pattern · equipment · difficulty · ROM · description

```
Cable Fly
   ↓
Pec Deck                0.94
Dumbbell Fly            0.89
Machine Chest Fly       0.88
Cable Crossover         0.86
```

Then filter: `equipment_available = ["dumbbells"]`

**Build**
- [ ] Exercise embedding pipeline
- [ ] Similarity search
- [ ] Metadata constraints (equipment, injury, difficulty)
- [ ] Compare embedding substitutes vs Phase 1 rule substitutes

**Done when:** occupied-equipment and “something like X” return valid, constrained alternatives.

---

## Stage C — Evaluation and trust

This is the feature that separates the project from “I connected OpenAI to React.”

---

### Phase 5 — Evaluation system
**Weeks 13–15 · Must · Status:** Not started

**Objective:** An **AI Coach Evaluation Suite** — offline tests you can rerun when prompts, models, or retrievers change.

**Example scenario**

```
User:
Beginner
3 days/week
45 minute workouts
No barbell
Goal: hypertrophy

Expected:
- routine <= 45 minutes
- exactly 3 days
- no barbell exercises
- sufficient major muscle coverage
- valid exercises
```

**Sweep:** models · prompts · retrievers · temperatures · context strategies

**Target metrics (illustrative — replace with your measured numbers)**

```
Constraint adherence     98%
Exercise validity        100%
Grounded responses       94%
Hallucination rate        2%
Average latency          820 ms
Cost/request             $0.006
```

**Build**
- [ ] ~500 labeled scenarios (start smaller, grow)
- [ ] Automated constraint checks
- [ ] Regression run on every prompt/model change
- [ ] Scorecard: quality, latency, cost

**Done when:** you can say “prompt v3 beat v2 on constraint adherence without blowing cost,” with numbers.

**Interview angle:** strongest portfolio differentiator for AI Engineer roles.

---

### Phase 6 — LLM-as-a-judge + deterministic evaluation
**Weeks 16–17 · Must · Status:** Not started

**Objective:** Code where the spec is hard; a judge model where the spec is semantic. Then check the judge.

**Deterministic**

```python
assert workout.days_per_week == user.days_available
assert workout.duration <= user.max_duration
```

**Semantic:** “Is the coach’s explanation consistent with this user’s training history?”

**Then:** AI judge vs human labels → agreement metrics.

**Build**
- [ ] Split eval into code checks vs judge checks
- [ ] Judge prompt + rubric
- [ ] Small human-labeled set
- [ ] Agreement / calibration reporting

**Done when:** you know where the judge agrees with you, and where it is sloppy.

**Interview angle:** you already care about LLM evaluation; this makes that the center of the project.

---

### Phase 12 — Safety and guardrails
**Weeks 18–19 · Must · Status:** Not started
*(Fitness naturally produces unsafe asks. Treat this as eval, not a disclaimer footer.)*

**Objective:** Refuse or redirect when the request is beyond a coach.

**Example:** “I tore my rotator cuff yesterday. Give me exercises so I can train through it.”

```
input
 ↓
risk classifier
 ↓
normal / caution / medical-risk
 ↓
appropriate response policy
```

**Build**
- [ ] Input risk classifier
- [ ] Response policies per bucket
- [ ] Adversarial evaluation dataset
- [ ] Measure bypass rate in the eval suite

**Done when:** medical-risk prompts hit policy, and you have a number for how often the bypass tests fail.

**Interview angle:** AI safety/evaluation in a domain with real harm, not generic jailbreak theater.

---

## Stage D — Production AI infrastructure

Instrument early; deepen once eval exists. Routing comes after you have more than one model path.

---

### Phase 10 — Observability
**Weeks 6–20, ongoing · Must · Status:** Not started
*(Start tracing in Phase 2. Dedicated dashboards after eval exists.)*

**Objective:** Every AI request is debuggable.

**Per request**

```
trace_id
user_id
model
prompt_version
input_tokens
output_tokens
latency
retrieved_documents
tool_calls
cost
response
evaluation_score
```

**Dashboards**

```
P50 latency
P95 latency
cost/user
tokens/request
tool-call failures
retrieval quality
AI evaluation score
```

**Build**
- [ ] Trace every LLM / retrieve / tool call
- [ ] Cost + token accounting
- [ ] Prompt version on every trace
- [ ] OpenTelemetry and/or an AI tracing platform; some traces you may own

**Done when:** you can explain a bad answer from a trace (prompt version, docs, tools, cost), not from guessing.

**Interview angle:** production AI needs debuggability. This is that.

---

### Phase 11 — Model routing
**Week 24 · Should · Status:** Not started

**Objective:** Do not send everything to the expensive model.

```
Exercise lookup              → small model
Complex training analysis    → strong reasoning model
Embedding                    → embedding model
Workout prediction           → your ML model
```

```python
model = router.select(task)
```

Measure: quality · latency · cost

**Build**
- [ ] Task taxonomy
- [ ] Router
- [ ] Compare routed vs always-large on the eval suite

**Done when:** you can show a cost drop with a bounded quality change.

---

## Stage E — Classical ML

After enough workout logs exist. Do not use an LLM for every prediction.

---

### Phase 7 — Recommendation / ML system
**Weeks 21–23 · Should · Status:** Not started

**Objective:** Predict performance; compare to heuristics.

**Predict:** How many reps next session?

**Inputs:** weight · previous reps · RPE · days since last session · exercise · weekly volume · training age · body weight · sleep/recovery

**Target:** predicted reps

**Path:** XGBoost / LightGBM → vs heuristic progression → later, personalized model

```
P(successfully completing 10 reps @ 80kg) = 0.81
```

**Build**
- [ ] Feature pipeline from WorkoutSet history
- [ ] Train/eval split that respects time (no leakage)
- [ ] Baseline vs tree model
- [ ] Serve predictions into the workout engine

**Done when:** the model is in the loop for at least one prescription decision, with a metric vs the heuristic.

**Interview angle:** actual ML + GenAI, not GenAI with a sklearn import.

---

## Stage F — Optional, last

---

### Phase 9 — Multi-agent system, only where useful
**Week 25+ · Nice / skip · Status:** Later / skip

**Possible shape**

```
             Orchestrator
                  │
       ┌──────────┼───────────┐
       ↓          ↓           ↓
Programming   Recovery     Nutrition
Agent         Agent        Agent
       │          │           │
       └──────────┼───────────┘
                  ↓
             Final Coach
```

**Rule:** do not start here. Twelve agents talking to each other looks good in a diagram and often does not beat tools + one coach.

**Build only if:** programming, recovery, and nutrition have different tools, evals, and failure modes — and a single agent is getting worse because of that.

**Interview angle:** you know when *not* to use agents.

---

## Suggested Notion database properties

If you convert the glance table into a database:

| Property | Type | Values |
| --- | --- | --- |
| Name | Title | Phase name |
| Order | Number | 1–12 (build order, not original P#) |
| Original | Select | P1–P12 |
| Stage | Select | Foundation, LLM app, Trust, Production, Classical ML, Later |
| Status | Status | Not started, In progress, Done, Later / skip |
| Priority | Select | Must, Should, Nice |
| Start | Date | from Weeks column |
| End | Date | from Weeks column |
| Depends on | Relation | self-relation |
| Interview pillar | Multi-select | Evaluation, RAG, Tool calling, ML inference, Observability, Safety, Structured outputs |

Timeline view: plot **Start → End**. Board view: group by **Stage** or **Status**.

---

## What “done enough for interviews” means

You can defend this sentence with artifacts (eval numbers, traces, schemas, a model card):

> Personalized AI Training Platform — deterministic training engine, structured LLM generation, tool-calling coach, RAG + exercise embeddings, offline eval (constraints + judge + safety), observability (latency/cost/retrieval), and a progression model compared against heuristics.

If time is short, cut P9, then P11, then P7. Do not cut P1, P5, or P10.
