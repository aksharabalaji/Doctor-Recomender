"""
Seed script – generates synthetic doctors, departments, and interactions.
Run once: python scripts/seed_data.py
"""
import json, random, os
from datetime import datetime, timedelta

random.seed(42)

DEPARTMENTS = [
    {"id": "D001", "name": "Cardiology",       "description": "Heart and cardiovascular system",        "avg_wait_min": 20},
    {"id": "D002", "name": "Neurology",         "description": "Brain, spine, and nervous system",       "avg_wait_min": 30},
    {"id": "D003", "name": "Orthopedics",       "description": "Bones, joints, and muscles",             "avg_wait_min": 25},
    {"id": "D004", "name": "Gastroenterology",  "description": "Digestive system and stomach",           "avg_wait_min": 35},
    {"id": "D005", "name": "Dermatology",       "description": "Skin, hair, and nails",                  "avg_wait_min": 15},
    {"id": "D006", "name": "Pulmonology",       "description": "Lungs and respiratory tract",            "avg_wait_min": 20},
    {"id": "D007", "name": "Endocrinology",     "description": "Hormones, diabetes, thyroid",            "avg_wait_min": 40},
    {"id": "D008", "name": "Ophthalmology",     "description": "Eyes and vision",                        "avg_wait_min": 15},
    {"id": "D009", "name": "ENT",               "description": "Ear, nose, and throat",                  "avg_wait_min": 20},
    {"id": "D010", "name": "Psychiatry",        "description": "Mental health and behavioural disorders","avg_wait_min": 45},
    {"id": "D011", "name": "General Medicine",  "description": "General adult illnesses and check-ups",  "avg_wait_min": 10},
    {"id": "D012", "name": "Emergency",         "description": "Acute and emergency care",               "avg_wait_min": 5},
]

SYMPTOM_DEPT_MAP = {
    "chest pain":         ["D001", "D012", "D006"],
    "shortness of breath":["D006", "D001", "D012"],
    "headache":           ["D002", "D011", "D009"],
    "dizziness":          ["D002", "D001", "D009"],
    "back pain":          ["D003", "D011"],
    "knee pain":          ["D003"],
    "abdominal pain":     ["D004", "D012", "D011"],
    "nausea":             ["D004", "D011"],
    "skin rash":          ["D005"],
    "acne":               ["D005"],
    "cough":              ["D006", "D009", "D011"],
    "fatigue":            ["D007", "D011", "D010"],
    "weight gain":        ["D007", "D011"],
    "blurred vision":     ["D008", "D007"],
    "eye pain":           ["D008", "D012"],
    "ear pain":           ["D009"],
    "sore throat":        ["D009", "D011"],
    "anxiety":            ["D010"],
    "depression":         ["D010"],
    "fever":              ["D011", "D012"],
    "cold":               ["D011", "D009"],
    "diabetes symptoms":  ["D007"],
    "heart palpitations": ["D001"],
    "joint swelling":     ["D003"],
    "hair loss":          ["D005", "D007"],
}

first_names = ["Arjun","Priya","Vikram","Meera","Rahul","Ananya","Suresh","Kavitha","Deepak","Lakshmi",
               "Sanjay","Nisha","Amit","Pooja","Ravi","Divya","Kiran","Smita","Ajay","Geeta"]
last_names  = ["Sharma","Patel","Kumar","Singh","Iyer","Nair","Reddy","Gupta","Verma","Joshi",
               "Mehta","Das","Choudhury","Pillai","Rao","Bhat","Menon","Desai","Shah","Agarwal"]

def rand_name(): return f"Dr. {random.choice(first_names)} {random.choice(last_names)}"

DOCTORS = []
doc_id = 1
for dept in DEPARTMENTS:
    count = random.randint(2, 4)
    for _ in range(count):
        exp = random.randint(3, 25)
        DOCTORS.append({
            "id": f"DOC{doc_id:03d}",
            "name": rand_name(),
            "department_id": dept["id"],
            "department_name": dept["name"],
            "experience_years": exp,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "total_reviews": random.randint(20, 300),
            "available_slots": random.randint(0, 8),
            "consultation_fee": random.choice([300, 500, 700, 900, 1200]),
            "languages": random.sample(["English","Tamil","Hindi","Telugu","Kannada"], k=random.randint(1,3)),
            "specializations": [],
        })
        doc_id += 1

# Attach specializations from symptom map
for sym, dept_ids in SYMPTOM_DEPT_MAP.items():
    for doc in DOCTORS:
        if doc["department_id"] in dept_ids and random.random() > 0.4:
            doc["specializations"].append(sym)

# Synthetic interaction history (user_id -> list of {symptom, chosen_dept, chosen_doc, rating})
USERS = [f"U{i:04d}" for i in range(1, 201)]
INTERACTIONS = []
all_symptoms = list(SYMPTOM_DEPT_MAP.keys())
for _ in range(1500):
    user = random.choice(USERS)
    symptom = random.choice(all_symptoms)
    dept_ids = SYMPTOM_DEPT_MAP[symptom]
    dept_id  = random.choice(dept_ids)
    docs_in_dept = [d for d in DOCTORS if d["department_id"] == dept_id]
    if not docs_in_dept:
        continue
    doc = random.choice(docs_in_dept)
    INTERACTIONS.append({
        "user_id":    user,
        "symptom":    symptom,
        "dept_id":    dept_id,
        "doc_id":     doc["id"],
        "rating":     random.randint(1, 5),
        "timestamp":  (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
    })

out = "backend/data"
os.makedirs(out, exist_ok=True)
json.dump(DEPARTMENTS,    open(f"{out}/departments.json",  "w"), indent=2)
json.dump(DOCTORS,        open(f"{out}/doctors.json",      "w"), indent=2)
json.dump(INTERACTIONS,   open(f"{out}/interactions.json", "w"), indent=2)
json.dump(SYMPTOM_DEPT_MAP, open(f"{out}/symptom_map.json","w"), indent=2)

print(f"✅  {len(DEPARTMENTS)} departments | {len(DOCTORS)} doctors | {len(INTERACTIONS)} interactions")
print("Saved to backend/data/")
