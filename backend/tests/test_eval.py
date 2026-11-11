from app.eval.runner import compare_retrievers, public_scorecard, run_suite
from app.eval.scenarios import plan_scenarios, rag_scenarios
from app.rag.index import KnowledgeIndex


def test_gold_plan_and_engine_beats_naive() -> None:
    card = run_suite(include_naive=True)
    gold = next(item for item in card.results if item.id == "plan.gold_beginner_no_bb" and item.variant == "engine")
    naive = next(item for item in card.results if item.id == "plan.gold_beginner_no_bb" and item.variant == "naive")
    assert gold.passed
    assert gold.checks["no_barbell"]
    assert gold.checks["duration"]
    assert gold.checks["days"]
    assert not naive.passed
    assert card.by_variant["engine"]["pass_rate"] > card.by_variant["naive"]["pass_rate"]


def test_chest_frequency_rag_is_grounded() -> None:
    card = run_suite(include_naive=False)
    row = next(item for item in card.results if item.id == "rag.chest_frequency")
    assert row.passed
    assert "hypertrophy_frequency" in row.detail["cited"]


def test_coach_bench_uses_tools() -> None:
    card = run_suite(include_naive=False)
    row = next(item for item in card.results if item.id == "coach.bench_plateau")
    assert row.passed
    assert row.checks["grounded"]


def test_scorecard_has_interview_metrics() -> None:
    payload = public_scorecard(run_suite())
    for key in (
        "constraint_adherence",
        "exercise_validity",
        "grounded_rate",
        "hallucination_rate",
        "avg_latency_ms",
        "cost_per_request",
    ):
        assert key in payload
    assert payload["constraint_adherence"] >= 0.8
    assert payload["exercise_validity"] == 1.0


def test_retriever_ablation_changes_quality() -> None:
    index = KnowledgeIndex()
    cards = compare_retrievers(index)
    default = cards["hybrid_rerank"]
    filtered = cards["injury_filter"]
    chest_default = next(item for item in default.results if item.id == "rag.chest_frequency")
    chest_filtered = next(item for item in filtered.results if item.id == "rag.chest_frequency")
    assert chest_default.checks["retrieved_expected"]
    assert not chest_filtered.checks["retrieved_expected"]
    assert default.grounded_rate > filtered.grounded_rate


def test_eval_http_scorecard() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/v1/eval/scorecard?include_naive=false")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["constraint_adherence"] == 1.0
    assert "failures" in body
    assert "results" not in body


def test_suite_has_labeled_scenarios() -> None:
    assert len(plan_scenarios()) >= 20
    assert len(rag_scenarios()) >= 8
