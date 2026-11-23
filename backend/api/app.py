
"""
FastAPI backend for MediMatch - Doctor Recommender.
Run: uvicorn backend.api.app:app --reload
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.services.engine import get_engine
from backend.schemas import (
    SymptomRequest,
    FeedbackRequest,
    DoctorIngestion,
    RecommendationResponse,
    FeedbackResponse,
    HealthResponse,
)

app = FastAPI(
    title="MediMatch - Doctor Recommender API",
    description="AI-based doctor and department recommendation system",
    version="1.0.0",
)

# Allow the Streamlit frontend to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_recommendation_engine():
    """Get the initialized recommendation engine."""
    try:
        return get_engine()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation engine initialization failed: {exc}",
        )


@app.get("/")
def home():
    return {
        "message": "Welcome to MediMatch Doctor Recommender API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    engine = get_recommendation_engine()

    return {
        "status": "ok",
        "model_version": engine.model_version,
        "doctors_loaded": len(engine.doctors),
        "departments_loaded": len(engine.departments),
    }


@app.get("/symptoms")
def list_symptoms():
    engine = get_recommendation_engine()

    symptoms = sorted(engine.symptom_map.keys())

    return {
        "count": len(symptoms),
        "symptoms": symptoms,
    }


@app.get("/departments")
def list_departments():
    engine = get_recommendation_engine()

    return {
        "count": len(engine.departments),
        "departments": engine.departments,
    }


@app.get("/doctors")
def list_doctors():
    engine = get_recommendation_engine()

    return {
        "count": len(engine.doctors),
        "doctors": engine.doctors,
    }


@app.post("/recommend", response_model=RecommendationResponse)
def recommend_doctors(request: SymptomRequest):
    engine = get_recommendation_engine()

    try:
        departments, doctors = engine.recommend(
            symptoms=request.symptoms,
            user_id=request.user_id,
            top_n=request.top_n,
            filter_available=request.filter_available,
        )

        return {
            "query_symptoms": request.symptoms,
            "departments": departments,
            "doctors": doctors,
            "generated_at": datetime.now(timezone.utc),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {exc}",
        )


@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest):
    engine = get_recommendation_engine()

    feedback = request.model_dump()
    feedback["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        engine.record_feedback(feedback)

        return {
            "status": "accepted",
            "message": "Feedback submitted successfully",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Feedback submission failed: {exc}",
        )


@app.post("/doctors", status_code=201)
def add_doctor(request: DoctorIngestion):
    engine = get_recommendation_engine()

    department = next(
        (
            dept
            for dept in engine.departments
            if dept["id"] == request.department_id
        ),
        None,
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found",
        )

    doctor_data = request.model_dump()
    doctor_data["department_name"] = department["name"]

    try:
        doctor = engine.add_doctor(doctor_data)

        return {
            "status": "created",
            "doctor": doctor,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Doctor registration failed: {exc}",
        )
