"""
Streamlit UI for the Doctor / Department Recommender.
Run: streamlit run frontend/app.py
Expects FastAPI backend at http://localhost:8000
"""

import streamlit as st
import requests, json
from datetime import datetime

import os

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MediMatch – Doctor Recommender",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

.hero {
    background: linear-gradient(135deg, #0f4c81 0%, #1a7abf 60%, #4db6e6 100%);
    padding: 2.5rem 2rem 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero h1 { color: white; margin: 0 0 .4rem; font-size: 2.2rem; }
.hero p  { margin: 0; opacity: .85; font-size: 1.05rem; }

.card {
    background: white;
    border: 1px solid #e8eef5;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: .9rem;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
    transition: box-shadow .2s;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }

.badge {
    display: inline-block;
    background: #e8f4ff;
    color: #0f4c81;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: .78rem;
    font-weight: 600;
    margin: 2px;
}
.badge-green { background: #e6f9f0; color: #0d7a4e; }
.badge-orange { background: #fff3e0; color: #b85c00; }

.score-bar-bg {
    background: #e8eef5;
    border-radius: 10px;
    height: 8px;
    overflow: hidden;
}
.score-bar-fill {
    background: linear-gradient(90deg,#1a7abf,#4db6e6);
    height: 8px;
    border-radius: 10px;
}
.star { color: #f4b400; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/hospital.png", width=60)
    st.markdown("## ⚙️ Settings")

    top_n = st.slider("Top N results", 1, 10, 5)
    filter_avail = st.toggle("Only show available doctors", value=False)
    user_id = st.text_input("User ID (optional, for personalised results)", placeholder="e.g. U0042")

    st.divider()
    st.markdown("### 📋 All Symptoms")
    try:
        syms = requests.get(f"{API}/symptoms", timeout=4).json()["symptoms"]
        st.write(", ".join(syms))
    except Exception:
        st.warning("Backend offline – start FastAPI first")

    st.divider()
    st.markdown("### 🏢 Departments")
    try:
        depts = requests.get(f"{API}/departments", timeout=4).json()["departments"]
        for d in depts:
            st.markdown(f"**{d['id']}** – {d['name']}")
    except Exception:
        pass

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🏥 MediMatch</h1>
  <p>Describe your symptoms and we'll match you with the right department and doctor.</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_search, tab_feedback, tab_add_doc, tab_analytics = st.tabs(
    ["🔍 Find a Doctor", "⭐ Give Feedback", "➕ Add Doctor", "📊 Analytics"]
)

# ════════════════════════════════════════════════════════════════════════════ #
#  TAB 1 – FIND A DOCTOR
# ════════════════════════════════════════════════════════════════════════════ #
with tab_search:
    col_inp, col_info = st.columns([2, 1])

    with col_inp:
        st.subheader("Describe your symptoms")
        symptoms_input = st.text_area(
            "Enter symptoms (comma-separated)",
            placeholder="e.g. chest pain, shortness of breath",
            height=80,
        )

        # Quick picks
        st.markdown("**Quick picks:**")
        quick_cols = st.columns(4)
        quick_opts = ["fever", "headache", "back pain", "cough", "skin rash",
                      "anxiety", "blurred vision", "abdominal pain"]
        selected_quick: list[str] = []
        for i, sym in enumerate(quick_opts):
            if quick_cols[i % 4].checkbox(sym, key=f"q_{sym}"):
                selected_quick.append(sym)

        search_btn = st.button("🔍 Find Match", type="primary", use_container_width=True)

    with col_info:
        st.markdown("#### How it works")
        st.markdown("""
1. Enter or select **symptoms**
2. Engine scores departments via **TF-IDF + collaborative filtering**
3. Doctors ranked by **content + availability + rating**
4. Each result includes an **explanation note**
        """)

    if search_btn:
        raw = [s.strip().lower() for s in symptoms_input.split(",") if s.strip()]
        all_syms = raw + selected_quick
        all_syms = list(dict.fromkeys(all_syms))   # deduplicate, preserve order

        if not all_syms:
            st.warning("Please enter at least one symptom.")
        else:
            with st.spinner("Finding best matches…"):
                try:
                    resp = requests.post(
                        f"{API}/recommend",
                        json={
                            "symptoms": all_syms,
                            "user_id": user_id or None,
                            "top_n": top_n,
                            "filter_available": filter_avail,
                        },
                        timeout=10,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    st.error(f"API error: {exc}")
                    st.stop()

            st.success(f"Results for: **{', '.join(data['query_symptoms'])}**")

            dept_col, doc_col = st.columns(2)

            with dept_col:
                st.markdown("### 🏢 Departments")
                for dept in data["departments"]:
                    pct = int(dept["relevance_score"] * 100)
                    matched = " ".join(
                        f'<span class="badge">{s}</span>' for s in dept["matched_symptoms"]
                    ) or '<span class="badge badge-orange">general match</span>'
                    st.markdown(f"""
<div class="card">
  <b style="font-size:1.05rem">{dept['name']}</b>
  &nbsp;<span style="color:#888;font-size:.85rem">avg wait {dept['avg_wait_min']} min</span><br>
  <div class="score-bar-bg" style="margin:.5rem 0">
    <div class="score-bar-fill" style="width:{pct}%"></div>
  </div>
  <small style="color:#555">{dept['description']}</small><br>
  <div style="margin:.4rem 0">{matched}</div>
  <small style="color:#0f4c81">💡 {dept['explanation']}</small>
</div>""", unsafe_allow_html=True)

            with doc_col:
                st.markdown("### 👨‍⚕️ Doctors")
                for doc in data["doctors"]:
                    pct   = int(doc["relevance_score"] * 100)
                    stars = "⭐" * round(doc["rating"])
                    slots = doc["available_slots"]
                    slot_badge = (
                        f'<span class="badge badge-green">{slots} slot(s) open</span>'
                        if slots > 0
                        else '<span class="badge badge-orange">no slots</span>'
                    )
                    fee = f"₹{doc['consultation_fee']}"
                    langs = " ".join(f'<span class="badge">{l}</span>' for l in doc["languages"])
                    st.markdown(f"""
<div class="card">
  <b style="font-size:1.05rem">{doc['name']}</b>
  &nbsp;{slot_badge}<br>
  <span style="color:#555;font-size:.85rem">{doc['department_name']} · {doc['experience_years']} yrs · {fee}</span><br>
  <div class="score-bar-bg" style="margin:.5rem 0">
    <div class="score-bar-fill" style="width:{pct}%"></div>
  </div>
  <span class="star">{stars}</span>
  <span style="color:#888;font-size:.82rem">({doc['rating']}/5 · {doc['total_reviews']} reviews)</span><br>
  <div style="margin:.3rem 0">{langs}</div>
  <small style="color:#0f4c81">💡 {doc['explanation']}</small>
</div>""", unsafe_allow_html=True)

            # Store last result for feedback tab
            st.session_state["last_result"] = data

# ════════════════════════════════════════════════════════════════════════════ #
#  TAB 2 – FEEDBACK
# ════════════════════════════════════════════════════════════════════════════ #
with tab_feedback:
    st.subheader("Rate your experience")
    st.markdown("Your feedback improves future recommendations.")

    last = st.session_state.get("last_result", {})

    with st.form("feedback_form"):
        fb_user    = st.text_input("User ID", value=user_id or "")
        fb_symptom = st.text_input(
            "Symptom", value=(last.get("query_symptoms") or [""])[0]
        )

        dept_options = [f"{d['id']} – {d['name']}" for d in (last.get("departments") or [])]
        doc_options  = [f"{d['id']} – {d['name']}" for d in (last.get("doctors") or [])]

        fb_dept   = st.selectbox("Department visited", dept_options or ["(no recent results)"])
        fb_doc    = st.selectbox("Doctor visited",     doc_options  or ["(no recent results)"])
        fb_rating = st.slider("Rating", 1, 5, 4)
        fb_comment = st.text_area("Comments (optional)", height=60)

        submitted = st.form_submit_button("Submit Feedback", type="primary")
        if submitted:
            if not fb_user or not fb_symptom:
                st.error("User ID and symptom are required.")
            else:
                dept_id_val = fb_dept.split(" – ")[0] if " – " in fb_dept else fb_dept
                doc_id_val  = fb_doc.split(" – ")[0]  if " – " in fb_doc  else fb_doc
                try:
                    r = requests.post(f"{API}/feedback", json={
                        "user_id": fb_user,
                        "symptom": fb_symptom,
                        "dept_id": dept_id_val,
                        "doc_id":  doc_id_val,
                        "rating":  fb_rating,
                        "comment": fb_comment,
                    }, timeout=6)
                    r.raise_for_status()
                    st.success("✅ Feedback submitted! Thank you.")
                except Exception as exc:
                    st.error(f"Submission failed: {exc}")

# ════════════════════════════════════════════════════════════════════════════ #
#  TAB 3 – ADD DOCTOR
# ════════════════════════════════════════════════════════════════════════════ #
with tab_add_doc:
    st.subheader("Add a New Doctor")
    try:
        dept_list = requests.get(f"{API}/departments", timeout=4).json()["departments"]
        dept_map  = {f"{d['id']} – {d['name']}": d["id"] for d in dept_list}
    except Exception:
        dept_map = {}

    with st.form("add_doctor_form"):
        ad_name    = st.text_input("Full name (without Dr.)", placeholder="Anjali Mehta")
        ad_dept    = st.selectbox("Department", list(dept_map.keys()) or ["(offline)"])
        ad_exp     = st.number_input("Experience (years)", 0, 60, 5)
        ad_rating  = st.slider("Initial rating", 1.0, 5.0, 4.0, step=0.1)
        ad_slots   = st.number_input("Available slots today", 0, 20, 3)
        ad_fee     = st.number_input("Consultation fee (₹)", 100, 5000, 500, step=100)
        ad_langs   = st.multiselect("Languages", ["English","Tamil","Hindi","Telugu","Kannada","Malayalam"], default=["English"])
        ad_specs   = st.multiselect("Specialisations (symptoms)", sorted(
            requests.get(f"{API}/symptoms", timeout=4).json()["symptoms"]
            if dept_map else []
        ))

        submitted_doc = st.form_submit_button("Add Doctor", type="primary")
        if submitted_doc:
            if not ad_name or not ad_dept:
                st.error("Name and department are required.")
            else:
                try:
                    r = requests.post(f"{API}/doctors", json={
                        "name":             f"Dr. {ad_name}",
                        "department_id":    dept_map.get(ad_dept, ad_dept),
                        "experience_years": int(ad_exp),
                        "rating":           float(ad_rating),
                        "available_slots":  int(ad_slots),
                        "consultation_fee": int(ad_fee),
                        "languages":        ad_langs,
                        "specializations":  ad_specs,
                    }, timeout=10)
                    r.raise_for_status()
                    st.success(f"✅ Doctor added: {r.json()['doctor']['id']}")
                except Exception as exc:
                    st.error(f"Failed: {exc}")

# ════════════════════════════════════════════════════════════════════════════ #
#  TAB 4 – ANALYTICS
# ════════════════════════════════════════════════════════════════════════════ #
with tab_analytics:
    st.subheader("System Analytics")
    try:
        import plotly.express as px

        docs  = requests.get(f"{API}/doctors",     timeout=4).json()["doctors"]
        depts = requests.get(f"{API}/departments", timeout=4).json()["departments"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Doctors",     len(docs))
        c2.metric("Departments",       len(depts))
        c3.metric("Available Doctors", sum(1 for d in docs if d["available_slots"] > 0))

        import pandas as pd
        df = pd.DataFrame(docs)

        st.markdown("#### Doctors per Department")
        count_df = df.groupby("department_name").size().reset_index(name="count").sort_values("count", ascending=False)
        fig1 = px.bar(count_df, x="department_name", y="count",
                      color="count", color_continuous_scale="Blues",
                      labels={"department_name": "Department", "count": "# Doctors"})
        fig1.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_tickangle=-30, margin=dict(t=20))
        st.plotly_chart(fig1, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Rating Distribution")
            fig2 = px.histogram(df, x="rating", nbins=15, color_discrete_sequence=["#1a7abf"])
            fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=20))
            st.plotly_chart(fig2, use_container_width=True)

        with col_b:
            st.markdown("#### Availability (slots open)")
            avail_df = df.groupby("department_name")["available_slots"].sum().reset_index()
            avail_df.columns = ["Department", "Slots"]
            fig3 = px.pie(avail_df, values="Slots", names="Department",
                          color_discrete_sequence=px.colors.sequential.Blues_r)
            fig3.update_layout(margin=dict(t=20))
            st.plotly_chart(fig3, use_container_width=True)

    except Exception as exc:
        st.info(f"Analytics unavailable – ensure the backend is running. ({exc})")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center style='color:#aaa;font-size:.8rem'>MediMatch · Doctor & Department Recommender · "
    f"Built with FastAPI + scikit-learn + Streamlit · {datetime.now().year}</center>",
    unsafe_allow_html=True,
)
