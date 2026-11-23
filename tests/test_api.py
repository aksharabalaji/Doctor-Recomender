"""
Tests for the Doctor Recommender API.
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient


def _ensure_seed():
    """Run seed script to make sure data files exist."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location(
        "seed_data",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "seed_data.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


@pytest.fixture(scope="module")
def client():
    _ensure_seed()
    from backend.services.engine import get_engine
    import backend.services.engine as eng_mod
    eng_mod._engine = None            # reset singleton
    engine = get_engine()
    engine.build()

    from backend.api.app import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["doctors_loaded"] > 0
    assert body["departments_loaded"] > 0


def test_list_symptoms(client):
    r = client.get("/symptoms")
    assert r.status_code == 200
    syms = r.json()["symptoms"]
    assert isinstance(syms, list)
    assert "chest pain" in syms


def test_list_departments(client):
    r = client.get("/departments")
    assert r.status_code == 200
    assert r.json()["count"] >= 10


def test_list_doctors(client):
    r = client.get("/doctors")
    assert r.status_code == 200
    assert r.json()["count"] > 0


def test_recommend_basic(client):
    r = client.post("/recommend", json={"symptoms": ["chest pain"], "top_n": 3})
    assert r.status_code == 200
    body = r.json()
    assert len(body["departments"]) <= 3
    assert len(body["doctors"]) <= 3
    # Cardiology should feature prominently for chest pain
    dept_names = [d["name"] for d in body["departments"]]
    assert any("Cardiology" in n or "Emergency" in n for n in dept_names)


def test_recommend_multi_symptom(client):
    r = client.post("/recommend", json={"symptoms": ["headache", "dizziness"], "top_n": 5})
    assert r.status_code == 200
    body = r.json()
    assert len(body["departments"]) >= 1
    assert len(body["doctors"]) >= 1


def test_recommend_filter_available(client):
    r = client.post("/recommend", json={
        "symptoms": ["skin rash"],
        "top_n": 10,
        "filter_available": True,
    })
    assert r.status_code == 200
    for doc in r.json()["doctors"]:
        assert doc["available_slots"] > 0


def test_recommend_with_user(client):
    r = client.post("/recommend", json={
        "symptoms": ["fever"],
        "user_id": "U0001",
        "top_n": 3,
    })
    assert r.status_code == 200


def test_recommend_unknown_symptom(client):
    """Unknown symptom should still return results (no crash)."""
    r = client.post("/recommend", json={"symptoms": ["purple zebra flu"]})
    assert r.status_code == 200
    body = r.json()
    assert "departments" in body


def test_recommend_top_n_respected(client):
    for n in [1, 3, 7]:
        r = client.post("/recommend", json={"symptoms": ["cough"], "top_n": n})
        assert r.status_code == 200
        assert len(r.json()["departments"]) <= n
        assert len(r.json()["doctors"]) <= n


def test_feedback_accepted(client):
    r = client.post("/feedback", json={
        "user_id": "U0001",
        "symptom": "chest pain",
        "dept_id": "D001",
        "doc_id":  "DOC001",
        "rating":  5,
        "comment": "Excellent!",
    })
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"


def test_add_doctor(client):
    r = client.post("/doctors", json={
        "name": "Dr. Test Doctor",
        "department_id": "D001",
        "experience_years": 10,
        "rating": 4.5,
        "available_slots": 2,
        "consultation_fee": 700,
        "languages": ["English"],
        "specializations": ["chest pain"],
    })
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "created"
    assert body["doctor"]["id"].startswith("DOC")


def test_add_doctor_invalid_dept(client):
    r = client.post("/doctors", json={
        "name": "Dr. Ghost",
        "department_id": "D999",
        "experience_years": 5,
    })
    assert r.status_code == 404


def test_explanation_present(client):
    r = client.post("/recommend", json={"symptoms": ["back pain"], "top_n": 3})
    assert r.status_code == 200
    body = r.json()
    for dept in body["departments"]:
        assert len(dept["explanation"]) > 10
    for doc in body["doctors"]:
        assert len(doc["explanation"]) > 10


def test_relevance_scores_ordered(client):
    r = client.post("/recommend", json={"symptoms": ["fever", "cough"], "top_n": 5})
    assert r.status_code == 200
    body = r.json()
    dept_scores = [d["relevance_score"] for d in body["departments"]]
    doc_scores  = [d["relevance_score"] for d in body["doctors"]]
    assert dept_scores == sorted(dept_scores, reverse=True)
    assert doc_scores  == sorted(doc_scores,  reverse=True)
