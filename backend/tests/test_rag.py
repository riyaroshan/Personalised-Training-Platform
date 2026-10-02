from app.engine.types import Equipment, Goal, TrainingAge, UserConstraints
from app.rag.answer import ablate, answer_question
from app.rag.exercises import similar_exercises
from app.rag.index import KnowledgeIndex
from app.rag.retrieve import RetrieverConfig


CHEST_QUESTION = "Should I train chest twice or three times a week?"


def test_chest_frequency_retrieves_and_cites_source() -> None:
    index = KnowledgeIndex()
    result = answer_question(CHEST_QUESTION, index=index)
    ids = [item.document_id for item in result.citations]
    assert "hypertrophy_frequency" in ids
    assert result.citations
    assert "[hypertrophy_frequency]" in result.answer
    assert "twice" in result.answer.lower()


def test_metadata_filter_excludes_hypertrophy_docs() -> None:
    index = KnowledgeIndex()
    injury = index.search(CHEST_QUESTION, RetrieverConfig(topic="injury", top_k=5, hybrid=True))
    ids = {hit.chunk.document_id for hit in injury}
    assert "hypertrophy_frequency" not in ids
    assert ids <= {"injury_shoulder", "injury_knee"}


def test_ablation_changes_ranking() -> None:
    index = KnowledgeIndex()
    reports = ablate(CHEST_QUESTION, index=index)
    by_topic = next(item for item in reports if item["settings"]["topic"] == "injury")
    default = next(
        item
        for item in reports
        if item["settings"]["hybrid"] and item["settings"]["rerank"] and item["settings"]["topic"] is None
        and item["settings"]["chunk_size"] == 80
        and item["settings"]["contextual"] is True
    )
    assert "hypertrophy_frequency" in default["top_document_ids"]
    assert "hypertrophy_frequency" not in by_topic["top_document_ids"]


def test_embedding_substitutes_respect_dumbbell_filter() -> None:
    constraints = UserConstraints(
        days_per_week=3,
        max_duration_minutes=45,
        available_equipment=[Equipment.DUMBBELL],
        injuries=[],
        goal=Goal.HYPERTROPHY,
        training_age=TrainingAge.BEGINNER,
    )
    matches = similar_exercises("cable_fly", constraints, limit=5)
    assert matches
    ids = [exercise.id for exercise, _ in matches]
    assert "db_fly" in ids
    assert "pec_deck" not in ids
    assert all("dumbbell" in [eq.value for eq in exercise.equipment] for exercise, _ in matches)
