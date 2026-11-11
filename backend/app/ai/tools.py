from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.engine.catalog import Catalog
from app.engine.substitutions import find_substitutes
from app.engine.types import Muscle, UserConstraints, WorkoutPlan, WorkoutSetLog
from app.engine.volume import logged_sets_by_muscle


@dataclass
class WorkoutSnapshot:
    id: str
    label: str
    day_index: int
    started_at: datetime
    completed_at: datetime | None
    exercise_ids: list[str]
    set_count: int


@dataclass
class ToolContext:
    catalog: Catalog
    constraints: UserConstraints
    history: list[WorkoutSetLog]
    workouts: list[WorkoutSnapshot]
    current_plan: WorkoutPlan | None
    sessions_completed: int
    now: datetime
    updated_plan: WorkoutPlan | None = None
    persist_plan: bool = False


@dataclass
class ToolExecution:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    ok: bool = True


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_workouts",
            "description": "Return the athlete's most recent logged workout sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_history",
            "description": "Load logged sets for an exercise (name or id) over a lookback window, with e1RM trend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise": {"type": "string"},
                    "days": {"type": "integer", "minimum": 7, "maximum": 180, "default": 60},
                },
                "required": ["exercise"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_muscle_volume",
            "description": "Count hard sets logged for a muscle over a lookback window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "muscle": {"type": "string"},
                    "days": {"type": "integer", "minimum": 7, "maximum": 90, "default": 30},
                },
                "required": ["muscle"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_personal_records",
            "description": "Best estimated 1RM and heaviest set per exercise from the log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recovery_scores",
            "description": "Heuristic recovery from session frequency, RPE, and RIR. Not HRV or sleep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "minimum": 7, "maximum": 90, "default": 30},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_exercise_substitutes",
            "description": "Rule-based substitutes that respect equipment and injuries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 8, "default": 5},
                },
                "required": ["exercise"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_workout_plan",
            "description": "Replace an exercise in the current plan with another catalog exercise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "replace_exercise_id": {"type": "string"},
                    "with_exercise_id": {"type": "string"},
                    "day_index": {"type": "integer", "minimum": 0, "maximum": 6},
                },
                "required": ["replace_exercise_id", "with_exercise_id"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any], ctx: ToolContext) -> ToolExecution:
    handlers = {
        "get_recent_workouts": _recent_workouts,
        "get_exercise_history": _exercise_history,
        "get_muscle_volume": _muscle_volume,
        "get_personal_records": _personal_records,
        "get_recovery_scores": _recovery_scores,
        "find_exercise_substitutes": _substitutes,
        "update_workout_plan": _update_plan,
    }
    handler = handlers.get(name)
    if handler is None:
        return ToolExecution(name=name, arguments=arguments, result={"error": f"unknown tool {name}"}, ok=False)
    try:
        result = handler(arguments, ctx)
        return ToolExecution(name=name, arguments=arguments, result=result, ok="error" not in result)
    except Exception as exc:
        return ToolExecution(name=name, arguments=arguments, result={"error": str(exc)}, ok=False)


def resolve_exercise_ids(query: str, catalog: Catalog) -> list[str]:
    needle = query.strip().lower().replace(" ", "_")
    if not needle:
        return []
    if needle in catalog.by_id:
        return [needle]
    matches: list[str] = []
    for exercise in catalog.exercises:
        haystack = f"{exercise.id} {exercise.name.lower().replace(' ', '_')}"
        if needle in haystack:
            if needle == "bench" and "dip" in exercise.id:
                continue
            matches.append(exercise.id)
    return matches


def evidence_from_executions(executions: list[ToolExecution]) -> list[str]:
    lines: list[str] = []
    for item in executions:
        if not item.ok:
            lines.append(f"{item.name}: {item.result.get('error', 'failed')}")
            continue
        payload = item.result
        if item.name == "get_exercise_history":
            lines.append(
                f"{item.name}: {payload.get('set_count', 0)} sets over {payload.get('days')}d; "
                f"trend={payload.get('trend')}; latest_e1rm={payload.get('latest_e1rm_kg')}; "
                f"best_e1rm={payload.get('best_e1rm_kg')}"
            )
        elif item.name == "get_muscle_volume":
            lines.append(
                f"{item.name}: {payload.get('muscle')} {payload.get('hard_sets')} hard sets in {payload.get('days')}d"
            )
        elif item.name == "get_recovery_scores":
            lines.append(
                f"{item.name}: status={payload.get('status')} score={payload.get('score')} "
                f"avg_rpe={payload.get('avg_rpe')} avg_rir={payload.get('avg_rir')}"
            )
        elif item.name == "get_recent_workouts":
            lines.append(f"{item.name}: {payload.get('count', 0)} recent sessions")
        elif item.name == "get_personal_records":
            records = payload.get("records") or []
            top = records[0] if records else None
            if top:
                lines.append(
                    f"{item.name}: {top['exercise_id']} best {top['best_weight_kg']}kg x {top['best_reps']}"
                )
            else:
                lines.append(f"{item.name}: no records")
        elif item.name == "find_exercise_substitutes":
            names = [row["exercise_id"] for row in payload.get("substitutes", [])[:3]]
            lines.append(f"{item.name}: {payload.get('exercise_id')} -> {names}")
        elif item.name == "update_workout_plan":
            lines.append(
                f"{item.name}: replaced {payload.get('replaced')} with {payload.get('with')} on day {payload.get('day_index')}"
            )
        else:
            lines.append(f"{item.name}: ok")
    return lines


def _recent_workouts(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    limit = int(arguments.get("limit") or 8)
    rows = []
    for workout in sorted(ctx.workouts, key=lambda item: _aware(item.started_at), reverse=True)[:limit]:
        rows.append(
            {
                "id": workout.id,
                "label": workout.label,
                "day_index": workout.day_index,
                "started_at": _iso(workout.started_at),
                "completed_at": _iso(workout.completed_at) if workout.completed_at else None,
                "set_count": workout.set_count,
                "exercises": workout.exercise_ids,
            }
        )
    return {"count": len(rows), "workouts": rows}


def _exercise_history(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    query = str(arguments.get("exercise") or "")
    days = int(arguments.get("days") or 60)
    ids = resolve_exercise_ids(query, ctx.catalog)
    if not ids:
        return {"error": f"no exercise matched {query!r}", "query": query}
    cutoff = ctx.now - timedelta(days=days)
    rows = [entry for entry in ctx.history if entry.exercise_id in ids and _aware(entry.completed_at) >= cutoff]
    rows.sort(key=lambda item: _aware(item.completed_at))
    e1rms = [_e1rm(entry) for entry in rows if entry.weight_kg]
    latest = _session_best_e1rm(rows[-1:]) if rows else None
    # compare first vs last session (by date)
    sessions = _group_sessions(rows)
    first_best = _session_best_e1rm(sessions[0]) if sessions else None
    last_best = _session_best_e1rm(sessions[-1]) if sessions else None
    trend = "no_data"
    if first_best and last_best:
        if last_best > first_best * 1.03:
            trend = "improving"
        elif last_best < first_best * 0.97:
            trend = "declining"
        else:
            trend = "flat"
    return {
        "query": query,
        "matched_exercise_ids": ids,
        "days": days,
        "set_count": len(rows),
        "sessions": len(sessions),
        "best_e1rm_kg": round(max(e1rms), 1) if e1rms else None,
        "latest_e1rm_kg": round(last_best, 1) if last_best else None,
        "first_e1rm_kg": round(first_best, 1) if first_best else None,
        "trend": trend,
        "sets": [
            {
                "exercise_id": entry.exercise_id,
                "weight_kg": entry.weight_kg,
                "reps": entry.reps,
                "rpe": entry.rpe,
                "rir": entry.rir,
                "completed_at": _iso(entry.completed_at),
            }
            for entry in rows[-24:]
        ],
    }


def _muscle_volume(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    raw = str(arguments.get("muscle") or "").strip().lower()
    days = int(arguments.get("days") or 30)
    try:
        muscle = Muscle(raw)
    except ValueError:
        return {"error": f"unknown muscle {raw!r}"}
    volume = logged_sets_by_muscle(ctx.history, ctx.catalog, days=days, now=ctx.now)
    cutoff = ctx.now - timedelta(days=days)
    by_exercise: dict[str, int] = {}
    for entry in ctx.history:
        if _aware(entry.completed_at) < cutoff:
            continue
        exercise = ctx.catalog.get(entry.exercise_id)
        if muscle in exercise.primary_muscles:
            by_exercise[entry.exercise_id] = by_exercise.get(entry.exercise_id, 0) + 1
    return {
        "muscle": muscle.value,
        "days": days,
        "hard_sets": volume.get(muscle, 0),
        "exercises": by_exercise,
    }


def _personal_records(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    query = arguments.get("exercise")
    allowed = resolve_exercise_ids(str(query), ctx.catalog) if query else None
    if query and not allowed:
        return {"error": f"no exercise matched {query!r}", "records": []}
    best: dict[str, dict[str, Any]] = {}
    for entry in ctx.history:
        if allowed is not None and entry.exercise_id not in allowed:
            continue
        if not entry.weight_kg:
            continue
        e1rm = _e1rm(entry)
        current = best.get(entry.exercise_id)
        if current is None or e1rm > current["best_e1rm_kg"]:
            best[entry.exercise_id] = {
                "exercise_id": entry.exercise_id,
                "name": ctx.catalog.get(entry.exercise_id).name,
                "best_weight_kg": entry.weight_kg,
                "best_reps": entry.reps,
                "best_e1rm_kg": round(e1rm, 1),
                "at": _iso(entry.completed_at),
            }
    records = sorted(best.values(), key=lambda row: row["best_e1rm_kg"], reverse=True)
    return {"records": records}


def _recovery_scores(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    days = int(arguments.get("days") or 30)
    cutoff = ctx.now - timedelta(days=days)
    recent = [entry for entry in ctx.history if _aware(entry.completed_at) >= cutoff]
    session_days = {_aware(entry.completed_at).date() for entry in recent}
    rpes = [entry.rpe for entry in recent if entry.rpe is not None]
    rirs = [entry.rir for entry in recent if entry.rir is not None]
    avg_rpe = round(sum(rpes) / len(rpes), 2) if rpes else None
    avg_rir = round(sum(rirs) / len(rirs), 2) if rirs else None
    sessions = len(session_days)
    sessions_per_week = round(sessions / max(days / 7, 1), 2)
    last = max((_aware(entry.completed_at) for entry in recent), default=None)
    days_since = (ctx.now - last).days if last else None
    score = 0.7
    notes = []
    if avg_rpe is not None and avg_rpe >= 8.5:
        score -= 0.2
        notes.append("Average RPE is high.")
    if avg_rir is not None and avg_rir <= 0.5:
        score -= 0.2
        notes.append("Sets are often taken near failure.")
    if sessions_per_week >= 5:
        score -= 0.1
        notes.append("Session frequency is high for recovery.")
    if days_since is not None and days_since >= 6:
        score -= 0.05
        notes.append("Last session was several days ago.")
    score = round(min(max(score, 0.05), 1.0), 2)
    if score >= 0.65:
        status = "good"
    elif score >= 0.45:
        status = "ok"
    else:
        status = "poor"
    if not notes:
        notes.append("No strong fatigue flags in the log.")
    return {
        "days": days,
        "sessions": sessions,
        "sessions_per_week": sessions_per_week,
        "avg_rpe": avg_rpe,
        "avg_rir": avg_rir,
        "days_since_last_session": days_since,
        "score": score,
        "status": status,
        "notes": " ".join(notes),
    }


def _substitutes(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    query = str(arguments.get("exercise") or "")
    limit = int(arguments.get("limit") or 5)
    ids = resolve_exercise_ids(query, ctx.catalog)
    if not ids:
        return {"error": f"no exercise matched {query!r}"}
    exercise_id = ids[0]
    matches = find_substitutes(exercise_id, ctx.constraints, ctx.catalog, limit=limit)
    return {
        "exercise_id": exercise_id,
        "substitutes": [
            {
                "exercise_id": exercise.id,
                "name": exercise.name,
                "score": score,
                "equipment": [item.value for item in exercise.equipment],
            }
            for exercise, score in matches
        ],
    }


def _update_plan(arguments: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    if ctx.current_plan is None:
        return {"error": "no current plan"}
    source_id = str(arguments["replace_exercise_id"])
    target_id = str(arguments["with_exercise_id"])
    if source_id not in ctx.catalog.by_id:
        return {"error": f"unknown exercise {source_id}"}
    if target_id not in ctx.catalog.by_id:
        return {"error": f"unknown exercise {target_id}"}
    eligible_ids = {exercise.id for exercise in ctx.catalog.eligible(ctx.constraints)}
    if target_id not in eligible_ids:
        return {"error": f"{target_id} is not eligible for this athlete"}
    day_index = arguments.get("day_index")
    replaced = False
    days = []
    for day in ctx.current_plan.days:
        exercises = []
        for prescription in day.exercises:
            next_id = prescription.exercise_id
            if next_id == source_id and (day_index is None or day.day_index == day_index):
                next_id = target_id
                replaced = True
            exercises.append(prescription.model_copy(update={"exercise_id": next_id}))
        days.append(day.model_copy(update={"exercises": exercises}))
    if not replaced:
        return {"error": f"{source_id} is not on the current plan"}
    plan = ctx.current_plan.model_copy(update={"days": days})
    ctx.current_plan = plan
    ctx.updated_plan = plan
    ctx.persist_plan = True
    return {
        "replaced": source_id,
        "with": target_id,
        "day_index": day_index,
        "plan": plan.model_dump(mode="json"),
    }


def _group_sessions(rows: list[WorkoutSetLog]) -> list[list[WorkoutSetLog]]:
    grouped: dict[Any, list[WorkoutSetLog]] = {}
    order: list[Any] = []
    for entry in rows:
        key = _aware(entry.completed_at).date()
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(entry)
    return [grouped[key] for key in order]


def _session_best_e1rm(rows: list[WorkoutSetLog]) -> float | None:
    values = [_e1rm(entry) for entry in rows if entry.weight_kg]
    return max(values) if values else None


def _e1rm(entry: WorkoutSetLog) -> float:
    return float(entry.weight_kg) * (1 + entry.reps / 30)


def _iso(stamp: datetime) -> str:
    return _aware(stamp).isoformat()


def _aware(stamp: datetime) -> datetime:
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=UTC)
    return stamp
