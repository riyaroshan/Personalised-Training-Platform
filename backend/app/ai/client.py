from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
