from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_user_and_generate_plan() -> None:
    created = client.post(
        "/v1/users",
        json={
            "name": "Riya",
            "days_per_week": 3,
            "max_duration_minutes": 45,
            "available_equipment": [
                "dumbbell",
                "cable",
                "machine",
                "bodyweight",
                "kettlebell",
                "band",
            ],
            "goal": "hypertrophy",
            "training_age": "beginner",
        },
    )
    assert created.status_code == 200, created.text
    user_id = created.json()["id"]

    plan = client.post(f"/v1/users/{user_id}/plan")
    assert plan.status_code == 200, plan.text
    body = plan.json()
    assert body["violations"] == []
    assert len(body["plan"]["days"]) == 3
    assert all(day["estimated_minutes"] <= 45 for day in body["plan"]["days"])

    workout = client.post(f"/v1/users/{user_id}/workouts", json={"day_index": 0})
    assert workout.status_code == 200, workout.text
    first_exercise = body["plan"]["days"][0]["exercises"][0]["exercise_id"]
    logged = client.post(
        f"/v1/workouts/{workout.json()['id']}/sets",
        json={
            "exercise_id": first_exercise,
            "set_index": 0,
            "weight_kg": 16,
            "reps": 10,
            "rpe": 7,
            "rir": 2,
        },
    )
    assert logged.status_code == 200, logged.text
