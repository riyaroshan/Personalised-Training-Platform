from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from app.ai.client import AgentLLM, AgentTurn
from app.ai.prompts import CURRENT_COACH_PROMPT, get_prompt
from app.ai.schemas import GenerationMeta
from app.ai.tools import (
    TOOL_SCHEMAS,
    ToolContext,
    ToolExecution,
    evidence_from_executions,
    execute_tool,
    resolve_exercise_ids,
)
from app.config import settings
from app.engine.types import Muscle


class CoachReply(BaseModel):
    answer: str
    evidence: list[str] = Field(default_factory=list)


class CoachResult(BaseModel):
    answer: str
    evidence: list[str]
    grounded: bool
    tool_calls: list[dict[str, Any]]
    generation: GenerationMeta
    plan_updated: bool = False


def ask_coach(
    message: str,
    ctx: ToolContext,
    *,
    llm: AgentLLM | None = None,
    max_steps: int | None = None,
) -> CoachResult:
    prompt = get_prompt(CURRENT_COACH_PROMPT)
    budget = max_steps or settings.agent_max_steps
    if llm is None:
        return _heuristic_coach(message, ctx, prompt.id, reason="llm_unavailable")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": prompt.system},
        {"role": "user", "content": message},
    ]
    executions: list[ToolExecution] = []
    tokens_in = 0
    tokens_out = 0
    errors: list[str] = []

    for _step in range(budget):
        try:
            turn = llm.complete(messages, TOOL_SCHEMAS)
        except Exception as exc:
            errors.append(str(exc))
            return _heuristic_coach(message, ctx, prompt.id, reason="llm_failed", errors=errors)
        tokens_in += turn.input_tokens
        tokens_out += turn.output_tokens
        if turn.tool_calls:
            messages.append(_assistant_tool_message(turn))
            for request in turn.tool_calls:
                execution = execute_tool(request.name, request.arguments, ctx)
                executions.append(execution)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": request.id,
                        "content": json.dumps(execution.result, default=str),
                    }
                )
            continue
        if not executions:
            errors.append("ungrounded: model answered without tools")
            return _heuristic_coach(message, ctx, prompt.id, reason="ungrounded", errors=errors)
        reply = _parse_reply(turn.content)
        evidence = evidence_from_executions(executions)
        return CoachResult(
            answer=reply.answer or _compose_answer(message, executions),
            evidence=evidence,
            grounded=True,
            tool_calls=_log(executions),
            generation=GenerationMeta(
                source="llm",
                prompt_version=prompt.id,
                model=turn.model,
                attempts=1,
                input_tokens=tokens_in,
                output_tokens=tokens_out,
                attempt_errors=errors,
            ),
            plan_updated=ctx.persist_plan,
        )

    errors.append("max_steps")
    return _heuristic_coach(message, ctx, prompt.id, reason="max_steps", errors=errors)


def _heuristic_coach(
    message: str,
    ctx: ToolContext,
    prompt_version: str,
    *,
    reason: str,
    errors: list[str] | None = None,
) -> CoachResult:
    executions = [execute_tool(name, arguments, ctx) for name, arguments in _select_tools(message, ctx)]
    evidence = evidence_from_executions(executions)
    return CoachResult(
        answer=_compose_answer(message, executions),
        evidence=evidence,
        grounded=bool(executions),
        tool_calls=_log(executions),
        generation=GenerationMeta(
            source="fallback",
            prompt_version=prompt_version,
            model="heuristic",
            attempts=0 if reason == "llm_unavailable" else 1,
            fallback_reason=reason,
            attempt_errors=errors or [],
        ),
        plan_updated=ctx.persist_plan,
    )


def _select_tools(message: str, ctx: ToolContext) -> list[tuple[str, dict[str, Any]]]:
    text = message.lower()
    calls: list[tuple[str, dict[str, Any]]] = []
    exercise = _mentioned_exercise(text, ctx)
    muscle = _mentioned_muscle(text, exercise)
    if any(token in text for token in ("improv", "stuck", "plateau", "stall", "progress", "bench")):
        if exercise:
            calls.append(("get_exercise_history", {"exercise": exercise, "days": 60}))
        if muscle:
            calls.append(("get_muscle_volume", {"muscle": muscle, "days": 30}))
        calls.append(("get_recovery_scores", {"days": 30}))
        calls.append(("get_recent_workouts", {"limit": 8}))
        if exercise:
            calls.append(("get_personal_records", {"exercise": exercise}))
        return calls
    if any(token in text for token in ("substitut", "instead", "occupied", "swap", "replace")):
        if exercise:
            calls.append(("find_exercise_substitutes", {"exercise": exercise}))
        calls.append(("get_recent_workouts", {"limit": 5}))
        return calls
    if exercise:
        calls.append(("get_exercise_history", {"exercise": exercise, "days": 60}))
        calls.append(("get_personal_records", {"exercise": exercise}))
    if muscle and any(token in text for token in ("volume", "enough", "sets")):
        calls.append(("get_muscle_volume", {"muscle": muscle, "days": 30}))
    calls.append(("get_recent_workouts", {"limit": 8}))
    calls.append(("get_recovery_scores", {"days": 30}))
    return calls


def _mentioned_exercise(text: str, ctx: ToolContext) -> str | None:
    for exercise in ctx.catalog.exercises:
        if exercise.id.replace("_", " ") in text or exercise.name.lower() in text:
            return exercise.id
    aliases = {
        "bench": "bench",
        "squat": "squat",
        "deadlift": "deadlift",
        "row": "row",
        "fly": "fly",
        "press": "press",
        "curl": "curl",
        "pull up": "pull",
        "pullup": "pull",
    }
    for alias, query in aliases.items():
        if alias in text:
            ids = resolve_exercise_ids(query, ctx.catalog)
            if ids:
                return query
    return None


def _mentioned_muscle(text: str, exercise: str | None) -> str | None:
    for muscle in Muscle:
        if muscle.value.replace("_", " ") in text or muscle.value in text:
            return muscle.value
    mapping = {
        "bench": "chest",
        "fly": "chest",
        "squat": "quads",
        "deadlift": "hamstrings",
        "row": "upper_back",
        "pull": "lats",
    }
    if exercise:
        for key, muscle in mapping.items():
            if key in exercise:
                return muscle
    if "bench" in text:
        return "chest"
    return None


def _compose_answer(message: str, executions: list[ToolExecution]) -> str:
    by_name = {item.name: item.result for item in executions if item.ok}
    history = by_name.get("get_exercise_history") or {}
    volume = by_name.get("get_muscle_volume") or {}
    recovery = by_name.get("get_recovery_scores") or {}
    parts = ["Answer grounded in logged training data, not generic coaching."]
    if history:
        parts.append(
            f"History for {history.get('query')}: {history.get('set_count', 0)} sets across "
            f"{history.get('sessions', 0)} sessions in {history.get('days')} days. "
            f"Estimated 1RM trend is {history.get('trend')} "
            f"(first {history.get('first_e1rm_kg')} kg, latest {history.get('latest_e1rm_kg')} kg)."
        )
        if history.get("trend") == "declining":
            parts.append(
                "Load/rep performance dropped in the log, so this is not a missing-motivation problem."
            )
        elif history.get("trend") == "flat":
            parts.append("Performance is roughly unchanged; look at volume and recovery before adding load.")
        elif history.get("set_count", 0) == 0:
            parts.append("There is no logged work for that lift in the window, so progress cannot be judged yet.")
    if volume:
        parts.append(
            f"Chest/muscle volume: {volume.get('hard_sets')} hard sets on {volume.get('muscle')} "
            f"in {volume.get('days')} days."
        )
    if recovery:
        parts.append(
            f"Recovery heuristic is {recovery.get('status')} (score {recovery.get('score')}). "
            f"{recovery.get('notes')}"
        )
    substitutes = by_name.get("find_exercise_substitutes")
    if substitutes:
        names = [row["name"] for row in substitutes.get("substitutes", [])[:3]]
        parts.append(f"Eligible substitutes for {substitutes.get('exercise_id')}: {', '.join(names) or 'none'}.")
    if len(parts) == 1:
        parts.append("Tools ran, but the log does not contain enough detail for a stronger claim.")
    return " ".join(parts)


def _parse_reply(content: str | None) -> CoachReply:
    if not content or not content.strip():
        return CoachReply(answer="")
    text = content.strip()
    try:
        return CoachReply.model_validate(json.loads(text))
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return CoachReply.model_validate(json.loads(match.group(0)))
            except Exception:
                pass
        return CoachReply(answer=text)


def _assistant_tool_message(turn: AgentTurn) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": turn.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in turn.tool_calls
        ],
    }


def _log(executions: list[ToolExecution]) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "arguments": item.arguments,
            "ok": item.ok,
            "result": _compact(item.result),
        }
        for item in executions
    ]


def _compact(result: dict[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    if "sets" in payload and isinstance(payload["sets"], list) and len(payload["sets"]) > 8:
        payload["sets"] = payload["sets"][-8:]
    if "plan" in payload:
        payload = {key: value for key, value in payload.items() if key != "plan"}
        payload["plan_updated"] = True
    return payload
