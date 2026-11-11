from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel

from app.ai.schemas import LLMWorkoutPlan
from app.config import settings


class LLMParseError(Exception):
    pass


@dataclass
class ParseResult:
    parsed: LLMWorkoutPlan
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class StructuredLLM(Protocol):
    model: str

    def parse(self, messages: list[dict[str, str]]) -> ParseResult: ...


class OpenAIStructuredLLM:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=api_key)

    def parse(self, messages: list[dict[str, str]]) -> ParseResult:
        completion = self._parse(messages)
        choice = completion.choices[0].message
        if getattr(choice, "refusal", None):
            raise LLMParseError(f"model refused: {choice.refusal}")
        parsed = getattr(choice, "parsed", None)
        if parsed is None:
            raise LLMParseError("model returned no parsed WorkoutPlan")
        usage = getattr(completion, "usage", None)
        return ParseResult(
            parsed=parsed,
            model=self.model,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    def _parse(self, messages: list[dict[str, str]]):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "response_format": LLMWorkoutPlan,
            "temperature": 0.2,
        }
        completions = self._client.chat.completions
        if hasattr(completions, "parse"):
            return completions.parse(**kwargs)
        return self._client.beta.chat.completions.parse(**kwargs)


@dataclass
class ToolRequest:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class AgentTurn:
    content: str | None = None
    tool_calls: list[ToolRequest] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class AgentLLM(Protocol):
    model: str

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AgentTurn: ...


class OpenAIAgentLLM:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=api_key)

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AgentTurn:
        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=0.2,
        )
        choice = completion.choices[0].message
        usage = getattr(completion, "usage", None)
        calls: list[ToolRequest] = []
        for item in getattr(choice, "tool_calls", None) or []:
            raw_args = item.function.arguments or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            calls.append(ToolRequest(id=item.id, name=item.function.name, arguments=arguments))
        return AgentTurn(
            content=choice.content,
            tool_calls=calls,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            model=self.model,
        )


class FakeAgentLLM:
    def __init__(self, turns: list[dict[str, Any]], model: str = "fake-agent"):
        self.model = model
        self._turns = list(turns)
        self.calls: list[list[dict[str, Any]]] = []

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AgentTurn:
        self.calls.append(messages)
        if not self._turns:
            raise LLMParseError("FakeAgentLLM has no remaining turns")
        item = self._turns.pop(0)
        calls = [
            ToolRequest(
                id=f"call_{index}",
                name=row["name"],
                arguments=row.get("arguments") or {},
            )
            for index, row in enumerate(item.get("tool_calls") or [])
        ]
        return AgentTurn(
            content=item.get("content"),
            tool_calls=calls,
            input_tokens=8,
            output_tokens=24,
            model=self.model,
        )


class FakeLLM:
    def __init__(self, responses: list[LLMWorkoutPlan | BaseModel | Exception], model: str = "fake"):
        self.model = model
        self._responses = list(responses)
        self.calls: list[list[dict[str, str]]] = []

    def parse(self, messages: list[dict[str, str]]) -> ParseResult:
        self.calls.append(messages)
        if not self._responses:
            raise LLMParseError("FakeLLM has no remaining responses")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        if not isinstance(item, LLMWorkoutPlan):
            item = LLMWorkoutPlan.model_validate(item)
        return ParseResult(parsed=item, model=self.model, input_tokens=12, output_tokens=48)


def build_llm() -> StructuredLLM | None:
    key = (settings.openai_api_key or "").strip()
    if not key:
        return None
    return OpenAIStructuredLLM(api_key=key, model=settings.llm_model)


def build_agent_llm() -> AgentLLM | None:
    key = (settings.openai_api_key or "").strip()
    if not key:
        return None
    return OpenAIAgentLLM(api_key=key, model=settings.llm_model)
