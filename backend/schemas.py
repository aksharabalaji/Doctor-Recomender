"""Pydantic v2 schemas for request / response validation."""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# ── Inbound ──────────────────────────────────────────────────────────────────

class SymptomRequest(BaseModel):
    symptoms: list[str] = Field(..., min_length=1, description="One or more symptom strings")
    user_id: Optional[str] = Field(None, description="Optional user ID for personalised ranking")
    top_n: int = Field(5, ge=1, le=20, description="Number of results to return")
    filter_available: bool = Field(False, description="Only return doctors with open slots")

    @field_validator("symptoms", mode="before")
    @classmethod
    def lower_strip(cls, v):
        return [s.strip().lower() for s in v]


class FeedbackRequest(BaseModel):
    user_id: str
    symptom: str
    dept_id: str
    doc_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class DoctorIngestion(BaseModel):
    """Used when adding a new doctor via the API."""
    name: str
    department_id: str
    experience_years: int = Field(..., ge=0)
    rating: float = Field(4.0, ge=0.0, le=5.0)
    total_reviews: int = 0
    available_slots: int = 0
    consultation_fee: int = 500
    languages: list[str] = ["English"]
    specializations: list[str] = []


# ── Outbound ─────────────────────────────────────────────────────────────────

class DepartmentResult(BaseModel):
    id: str
    name: str
    description: str
    avg_wait_min: int
    relevance_score: float
    matched_symptoms: list[str]
    explanation: str


class DoctorResult(BaseModel):
    id: str
    name: str
    department_id: str
    department_name: str
    experience_years: int
    rating: float
    total_reviews: int
    available_slots: int
    consultation_fee: int
    languages: list[str]
    specializations: list[str]
    relevance_score: float
    explanation: str


class RecommendationResponse(BaseModel):
    query_symptoms: list[str]
    departments: list[DepartmentResult]
    doctors: list[DoctorResult]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackResponse(BaseModel):
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    model_version: str
    doctors_loaded: int
    departments_loaded: int
