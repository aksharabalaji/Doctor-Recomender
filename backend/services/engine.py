"""
Recommendation engine.

Two-stage pipeline
──────────────────
Stage 1 – Content-based filtering
  • TF-IDF over (symptom → department/doctor tags)
  • Cosine similarity between query and item vectors

Stage 2 – Collaborative-signal re-ranking
  • Build a simple user–department interaction matrix
  • For known users, boost departments that similar users preferred
  • For new users, fall back to pure content score

Final score = α * content_score + β * collab_score + γ * availability_score + δ * rating_score
"""

from __future__ import annotations
import json, os, logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import joblib

logger = logging.getLogger(__name__)

DATA_DIR   = Path(__file__).parent.parent / "data"
MODEL_DIR  = Path(__file__).parent.parent / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

ALPHA  = 0.45   # content weight
BETA   = 0.20   # collaborative weight
GAMMA  = 0.15   # availability weight
DELTA  = 0.20   # rating weight


class RecommendationEngine:
    """Stateful engine – call .build() once, then .recommend() per request."""

    def __init__(self):
        self.doctors: list[dict]      = []
        self.departments: list[dict]  = []
        self.symptom_map: dict        = {}
        self.interactions: pd.DataFrame = pd.DataFrame()

        self._dept_vectorizer: Optional[TfidfVectorizer] = None
        self._doc_vectorizer:  Optional[TfidfVectorizer] = None
        self._dept_matrix = None   # (n_depts  × vocab)
        self._doc_matrix  = None   # (n_docs   × vocab)

        # Collaborative: user × department rating matrix
        self._user_dept_matrix: Optional[pd.DataFrame] = None
        self._scaler = MinMaxScaler()
        self._model_version = "1.0.0"

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_data(self):
        self.departments  = json.loads((DATA_DIR / "departments.json").read_text())
        self.doctors      = json.loads((DATA_DIR / "doctors.json").read_text())
        self.symptom_map  = json.loads((DATA_DIR / "symptom_map.json").read_text())
        ipath = DATA_DIR / "interactions.json"
        if ipath.exists():
            self.interactions = pd.DataFrame(json.loads(ipath.read_text()))
        logger.info("Data loaded: %d depts | %d doctors | %d interactions",
                    len(self.departments), len(self.doctors), len(self.interactions))

    # ── Model building ────────────────────────────────────────────────────────

    def build(self):
        """Train / re-train the engine from current data files."""
        self.load_data()
        self._build_content_vectors()
        self._build_collab_matrix()
        self._save_artifacts()
        logger.info("Engine built (version %s)", self._model_version)

    def _doc_text(self, d: dict) -> str:
        parts = [d["department_name"]] + d.get("specializations", [])
        return " ".join(parts).lower()

    def _dept_text(self, dept: dict) -> str:
        related = [sym for sym, dids in self.symptom_map.items() if dept["id"] in dids]
        return (dept["name"] + " " + dept["description"] + " " + " ".join(related)).lower()

    def _build_content_vectors(self):
        dept_corpus = [self._dept_text(d) for d in self.departments]
        doc_corpus  = [self._doc_text(d)  for d in self.doctors]

        self._dept_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self._doc_vectorizer  = TfidfVectorizer(ngram_range=(1, 2), min_df=1)

        self._dept_matrix = self._dept_vectorizer.fit_transform(dept_corpus)
        self._doc_matrix  = self._doc_vectorizer.fit_transform(doc_corpus)

    def _build_collab_matrix(self):
        if self.interactions.empty:
            return
        # Average rating per (user, dept)
        pivot = (
            self.interactions
            .groupby(["user_id", "dept_id"])["rating"]
            .mean()
            .unstack(fill_value=0)
        )
        self._user_dept_matrix = pivot

    def _save_artifacts(self):
        joblib.dump(self._dept_vectorizer, MODEL_DIR / "dept_vectorizer.pkl")
        joblib.dump(self._doc_vectorizer,  MODEL_DIR / "doc_vectorizer.pkl")
        joblib.dump(self._dept_matrix,     MODEL_DIR / "dept_matrix.pkl")
        joblib.dump(self._doc_matrix,      MODEL_DIR / "doc_matrix.pkl")
        if self._user_dept_matrix is not None:
            self._user_dept_matrix.to_pickle(MODEL_DIR / "user_dept_matrix.pkl")

    def load_artifacts(self):
        """Load pre-trained artefacts (faster startup)."""
        self.load_data()
        try:
            self._dept_vectorizer = joblib.load(MODEL_DIR / "dept_vectorizer.pkl")
            self._doc_vectorizer  = joblib.load(MODEL_DIR / "doc_vectorizer.pkl")
            self._dept_matrix     = joblib.load(MODEL_DIR / "dept_matrix.pkl")
            self._doc_matrix      = joblib.load(MODEL_DIR / "doc_matrix.pkl")
            upath = MODEL_DIR / "user_dept_matrix.pkl"
            if upath.exists():
                self._user_dept_matrix = pd.read_pickle(upath)
            logger.info("Artifacts loaded from disk")
        except FileNotFoundError:
            logger.warning("No pre-built artifacts found – building now")
            self.build()

    # ── Recommendation core ───────────────────────────────────────────────────

    def recommend(
        self,
        symptoms: list[str],
        user_id: Optional[str] = None,
        top_n: int = 5,
        filter_available: bool = False,
    ) -> tuple[list[dict], list[dict]]:
        """
        Returns (dept_results, doctor_results) each sorted by final score.
        """
        query = " ".join(symptoms)

        dept_results = self._score_departments(query, symptoms, user_id, top_n)
        doc_results  = self._score_doctors(query, symptoms, user_id, top_n, filter_available)

        return dept_results, doc_results

    # ── Department scoring ────────────────────────────────────────────────────

    def _score_departments(
        self,
        query: str,
        symptoms: list[str],
        user_id: Optional[str],
        top_n: int,
    ) -> list[dict]:
        # Content similarity
        q_vec = self._dept_vectorizer.transform([query])
        content_scores = cosine_similarity(q_vec, self._dept_matrix).flatten()

        # Collaborative boost
        collab_scores = np.zeros(len(self.departments))
        if user_id and self._user_dept_matrix is not None:
            collab_scores = self._collab_dept_scores(user_id)

        # Availability / wait-time (lower wait = higher score)
        max_wait = max(d["avg_wait_min"] for d in self.departments) or 1
        avail_scores = np.array(
            [1 - (d["avg_wait_min"] / max_wait) for d in self.departments]
        )

        # Composite
        final = (
            ALPHA * content_scores
            + BETA  * collab_scores
            + GAMMA * avail_scores
        )

        dept_ids_with_score = sorted(
            enumerate(final), key=lambda x: x[1], reverse=True
        )[:top_n]

        results = []
        for idx, score in dept_ids_with_score:
            dept = dict(self.departments[idx])
            matched = [s for s in symptoms if dept["id"] in self.symptom_map.get(s, [])]
            dept["relevance_score"] = round(float(score), 4)
            dept["matched_symptoms"] = matched
            dept["explanation"] = self._explain_dept(dept, matched, score)
            results.append(dept)
        return results

    def _collab_dept_scores(self, user_id: str) -> np.ndarray:
        scores = np.zeros(len(self.departments))
        if user_id not in self._user_dept_matrix.index:
            return scores
        user_vec = self._user_dept_matrix.loc[user_id].values.reshape(1, -1)
        all_vecs = self._user_dept_matrix.values
        sims = cosine_similarity(user_vec, all_vecs).flatten()
        # Top-5 similar users
        top_idx = np.argsort(sims)[::-1][1:6]
        similar_ratings = self._user_dept_matrix.iloc[top_idx].mean(axis=0)
        for i, dept in enumerate(self.departments):
            scores[i] = similar_ratings.get(dept["id"], 0) / 5.0
        return scores

    # ── Doctor scoring ────────────────────────────────────────────────────────

    def _score_doctors(
        self,
        query: str,
        symptoms: list[str],
        user_id: Optional[str],
        top_n: int,
        filter_available: bool,
    ) -> list[dict]:
        doctors = self.doctors
        if filter_available:
            doctors = [d for d in doctors if d["available_slots"] > 0]
        if not doctors:
            return []

        # Rebuild doc matrix for filtered set
        corpus = [self._doc_text(d) for d in doctors]
        doc_mat = self._doc_vectorizer.transform(corpus)

        q_vec = self._doc_vectorizer.transform([query])
        content_scores = cosine_similarity(q_vec, doc_mat).flatten()

        # Availability score
        max_slots = max((d["available_slots"] for d in doctors), default=1) or 1
        avail_scores = np.array([d["available_slots"] / max_slots for d in doctors])

        # Rating score
        rating_scores = np.array([d["rating"] / 5.0 for d in doctors])

        # Composite
        final = (
            ALPHA * content_scores
            + GAMMA * avail_scores
            + DELTA * rating_scores
        )

        top_idx = np.argsort(final)[::-1][:top_n]
        results = []
        for idx in top_idx:
            doc  = dict(doctors[idx])
            score = float(final[idx])
            doc["relevance_score"] = round(score, 4)
            doc["explanation"] = self._explain_doc(doc, symptoms, score)
            results.append(doc)
        return results

    # ── Explanation helpers ───────────────────────────────────────────────────

    def _explain_dept(self, dept: dict, matched: list[str], score: float) -> str:
        if matched:
            return (
                f"{dept['name']} is recommended because it commonly treats "
                f"{', '.join(matched)}. Average wait time is {dept['avg_wait_min']} min."
            )
        return (
            f"{dept['name']} may be relevant based on your symptom profile. "
            f"Average wait time: {dept['avg_wait_min']} min."
        )

    def _explain_doc(self, doc: dict, symptoms: list[str], score: float) -> str:
        matched_specs = [s for s in symptoms if s in doc.get("specializations", [])]
        parts = [f"Dr. {doc['name'].replace('Dr. ', '')} specialises in {doc['department_name']}"]
        if matched_specs:
            parts.append(f"with experience in {', '.join(matched_specs)}")
        parts.append(
            f"({doc['experience_years']} yrs exp, ★ {doc['rating']}, "
            f"{doc['available_slots']} slot(s) open)"
        )
        return " ".join(parts) + "."

    # ── Feedback ingestion ────────────────────────────────────────────────────

    def record_feedback(self, feedback: dict):
        """Append one feedback row and incrementally update collab matrix."""
        ipath = DATA_DIR / "interactions.json"
        existing = json.loads(ipath.read_text()) if ipath.exists() else []
        existing.append(feedback)
        ipath.write_text(json.dumps(existing, indent=2))
        # Refresh collab matrix in memory
        self.interactions = pd.DataFrame(existing)
        self._build_collab_matrix()

    # ── Doctor ingestion ──────────────────────────────────────────────────────

    def add_doctor(self, doc: dict) -> dict:
        import uuid
        doc["id"] = f"DOC{str(uuid.uuid4())[:6].upper()}"
        self.doctors.append(doc)
        dpath = DATA_DIR / "doctors.json"
        dpath.write_text(json.dumps(self.doctors, indent=2))
        # Re-build doc vectors
        self._build_content_vectors()
        return doc

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def model_version(self) -> str:
        return self._model_version


# Singleton
_engine: Optional[RecommendationEngine] = None

def get_engine() -> RecommendationEngine:
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
        _engine.load_artifacts()
    return _engine
