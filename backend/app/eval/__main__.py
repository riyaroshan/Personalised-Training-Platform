from __future__ import annotations

import json

from app.eval.runner import compare_retrievers, public_scorecard, run_suite


def main() -> None:
    card = run_suite()
    payload = public_scorecard(card)
    print("== AI Coach Evaluation Suite ==")
    print(
        json.dumps(
            {
                "cases": payload["cases"],
                "passed": payload["passed"],
                "constraint_adherence": payload["constraint_adherence"],
                "exercise_validity": payload["exercise_validity"],
                "grounded_rate": payload["grounded_rate"],
                "hallucination_rate": payload["hallucination_rate"],
                "avg_latency_ms": payload["avg_latency_ms"],
                "cost_per_request": payload["cost_per_request"],
                "by_family": payload["by_family"],
                "by_variant": payload["by_variant"],
                "failures": payload["failures"],
            },
            indent=2,
        )
    )
    print("\n== Retriever sweep (RAG only) ==")
    sweep = {name: {"pass_rate": item.grounded_rate, "cases": item.cases} for name, item in compare_retrievers().items()}
    print(json.dumps(sweep, indent=2))


if __name__ == "__main__":
    main()
