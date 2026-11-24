# 🏥 MediMatch – AI-Powered Doctor & Department Recommender System

<p align="center">
  <b>An intelligent healthcare recommendation platform that connects patients with suitable medical departments and doctors based on their symptoms, availability, and preferences.</b>
</p>

<p align="center">
  <a href="https://medimatch-frontend-e96m.onrender.com">🌐 Live Demo</a> •
  <a href="https://github.com/aksharabalaji/Doctor-Recomender">📂 GitHub Repository</a>
</p>

---

## 🌟 Project Overview

**MediMatch** is an AI/ML-based healthcare recommendation system designed to simplify the process of finding suitable doctors and medical departments.

Users can enter their symptoms, and the system analyzes the information to recommend relevant medical departments and doctors.

The application uses Machine Learning techniques, recommendation algorithms, and doctor availability information to provide personalized and relevant recommendations through an interactive web interface.

MediMatch aims to make healthcare navigation easier, faster, and more accessible.

## 🎯 Objectives

- Recommend suitable medical departments based on patient symptoms.
- Identify relevant doctors using intelligent recommendation algorithms.
- Consider doctor availability while generating recommendations.
- Provide personalized recommendations using user interaction data.
- Improve healthcare accessibility through a user-friendly platform.
- Provide an interactive analytics and feedback system.

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 Symptom-Based Search | Enter symptoms to find suitable doctors and departments. |
| 🤖 AI/ML Recommendations | Uses TF-IDF and recommendation techniques to identify relevant matches. |
| 🏥 Department Recommendation | Suggests appropriate medical departments. |
| 👨‍⚕️ Doctor Recommendation | Ranks doctors based on relevance and other available information. |
| 📅 Availability Filtering | Filter doctors based on their availability. |
| 🎯 Top-N Recommendations | Customize the number of recommended doctors. |
| 👤 Personalized Results | Supports optional user-based recommendations. |
| ⭐ Feedback System | Allows users to provide feedback. |
| ➕ Add Doctor | Provides an interface to add doctor information. |
| 📊 Analytics Dashboard | Displays recommendation-related analytics. |

## 🛠️ Technology Stack

### Programming Language
- Python

### Frontend
- Streamlit

### Backend
- FastAPI
- REST API

### Machine Learning & Data Processing
- Scikit-learn
- Pandas
- NumPy
- TF-IDF
- Recommendation Algorithms

### Deployment
- Render

### Development Tools
- Visual Studio Code
- Git
- GitHub

## 🧠 How MediMatch Works

```text
        PATIENT
           |
           ▼
    Enter Symptoms
           |
           ▼
     Data Processing
           |
           ▼
   Machine Learning Engine
           |
           ▼
   Department Recommendation
           |
           ▼
    Doctor Ranking System
           |
           ▼
   Availability Filtering
           |
           ▼
  Personalized Recommendations
           |
           ▼
     DISPLAY RESULTS
```

## ⚙️ Recommendation Methodology

MediMatch combines different recommendation techniques to generate relevant results.

**1. TF-IDF (Term Frequency–Inverse Document Frequency)**

- Processes symptom-related information.
- Identifies relevant keywords.
- Helps determine similarity between symptoms and medical departments.

**2. Content-Based Recommendation**

- Matches patient symptoms with relevant doctor and department information.
- Uses available doctor details to rank relevant results.

**3. Collaborative Filtering**

- Uses available user interaction information to support personalized recommendations.

**4. Availability-Based Filtering**

- Considers doctor availability.
- Allows users to filter out unavailable doctors.

## 📂 Project Structure

```text
Doctor-Recomender/
│
├── frontend/
│   └── app.py
│
├── backend/
│   ├── main.py
│   ├── engine.py
│   ├── schemas.py
│   └── seed_data.py
│
├── data/
│   ├── doctors.json
│   ├── departments.json
│   ├── symptom_map.json
│   └── interactions.json
│
├── requirements.txt
├── README.md
└── .gitignore
```

*Note: Adjust the folder names above if your actual repository structure differs.*

## 🚀 Live Application

Experience MediMatch here:

🌐 **[Launch MediMatch – Live Application](https://medimatch-frontend-e96m.onrender.com)**

The application is deployed using Render.

## 💻 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aksharabalaji/Doctor-Recomender.git
```

### 2. Navigate to the Project

```bash
cd Doctor-Recomender
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the FastAPI Backend

```bash
python -m uvicorn main:app --reload
```

The backend should be accessible at:

```text
http://127.0.0.1:8000
```

### 6. Start the Streamlit Frontend

Open another terminal and execute:

```bash
python -m streamlit run frontend/app.py
```

Open the local application in your browser:

```text
http://localhost:8501
```

*Ensure that the backend entry point and API URL match your local project configuration.*

## 🔮 Future Enhancements

- Integration with real hospital databases.
- Online doctor appointment booking.
- AI-powered healthcare chatbot.
- Multilingual support.
- Hospital and clinic recommendations.
- Advanced patient analytics.
- Improved recommendation accuracy using larger datasets.

## ⚠️ Disclaimer

MediMatch is an educational and decision-support project. It is not a substitute for professional medical advice, diagnosis, or treatment. Recommendations should not be considered medical diagnoses.

## 👩‍💻 Developer

**Akshara Balaji**

B.E. Computer Science and Engineering – Cyber Security

**Areas of Interest:**
- Artificial Intelligence & Machine Learning
- Python Development
- Healthcare Technology
- Data Science

## ⭐ Support

If you find this project interesting or useful, consider giving this repository a ⭐ on GitHub!

Your support motivates further development and innovation.

---

<p align="center">
  <b>Built with ❤️ using Python, Machine Learning and FastAPI.</b>
</p>
