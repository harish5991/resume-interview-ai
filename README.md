# Resume Interview AI 🎯
> **Grounded, Explainable Resume-to-Interview Questions Generator & Adaptive Mock Interview Platform**

Resume Interview AI is a full-stack web application that solves one of the biggest flaws in existing AI prep tools: **generic, ungrounded questions and unexplained "black-box" scores**.

By parsing candidate resumes (PDF/DOCX) using PyMuPDF and matching them against target Job Descriptions (JDs) via TF-IDF cosine similarity, the application generates **strictly grounded questions** linked to the candidate's actual projects, verified skills, and role expectations. It features an **adaptive mock interview simulator** with real-time 6-axis scoring, speech-to-text recording, duplicate-free question generation, deep-dive project dossiers, and downloadable PDF readiness reports.

---

## 🌟 Key Features

1. **📄 Explainable Resume Text Extraction & Scoring**
   - Extracts text, contact info, categorized skills, work history, projects, and education from PDF and DOCX files.
   - Calculates a multi-dimensional Resume Score (0–100) with category-level breakdowns (Skills, Projects, Experience, Education, Completeness, Relevance) accompanied by natural-language justifications.

2. **🎯 Semantic Resume-to-Job Matching**
   - Calculates candidate-to-job match percentage using TF-IDF vectorization and cosine similarity.
   - Categorizes competencies into **Matching Skills**, **Missing Skills**, and **Partial/Related Skills**.
   - Highlights the most relevant candidate projects and experience tailored to the target role.

3. **💡 Strictly Grounded & Explainable Interview Questions**
   - Every generated question displays:
     - **Question text**
     - **Based On** (e.g., `Project: Resume Interview AI`, `Skill: MongoDB`)
     - **Difficulty** (`Easy`, `Medium`, `Hard`, `Expert`)
     - **Why This Question?** (Clear explainability rationale)
     - **Expected Answer Talking Points & Model Answer Strategy**
   - **Zero Hallucinations**: Questions never invent technologies or companies not in the resume.

4. **🔄 Zero-Duplicate Question Regeneration**
   - Employs question hashing and session-level history tracking so clicking *"Generate Different Questions"* never repeats previously seen questions.

5. **🎙️ Adaptive AI Mock Interview Simulator**
   - Interactive step-by-step interview terminal with **Voice Dictation (Speech-to-Text via Web Speech API)** and text input.
   - Instant **6-Axis Evaluation**:
     1. *Relevance*
     2. *Technical Accuracy*
     3. *Completeness*
     4. *Clarity*
     5. *Confidence*
     6. *Communication*
   - Returns verified strengths, areas for growth, concise model answers, and **adaptive difficulty progression** (e.g., scoring 85+ on Medium automatically elevates the next question to Hard/Expert).

6. **🧩 Skill Gap Analysis & Learning Roadmap**
   - Side-by-side gap visualization with estimated preparation hours, critical concepts to master, and recommended learning resources.

7. **🏛️ Project Deep-Dive & Architecture Dossier**
   - Deep architectural breakdown for candidate projects: Objectives, High-Level Architecture, Database Choice, API Validation, Security, 10x Scalability, Challenges, and 5 Hard Project Questions.

8. **📊 Recharts Readiness Analytics Dashboard**
   - Multi-axis Competency Radar Chart, Score Progression Trendlines, and Difficulty Pass Rate Bar Charts.
   - Priority Weak Topic Detection alerts with targeted remediation.

9. **📑 PDF Interview Readiness Report Export**
   - Downloadable executive PDF generated via ReportLab containing candidate metadata, match breakdown, mock interview transcript, and action plan.

10. **🗂️ Multi-Session Management & Saved Question Bank**
    - Manage multiple interview targets (e.g., "Session 1 — Python Backend", "Session 2 — Full Stack").
    - Pin important questions to a dedicated Saved Questions Bank.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18/19, Vite, Tailwind CSS | High-performance, modular, accessible UI |
| **Routing & Icons** | React Router v6, Lucide React | Seamless navigation and crisp modern iconography |
| **Charts** | Recharts | Interactive Radar, Line, and Bar visual analytics |
| **Backend API** | Python 3.13, FastAPI, Uvicorn | High-throughput async REST API with Pydantic validation |
| **Document Parsing** | PyMuPDF (`fitz`), `python-docx` | Fast, deterministic PDF and DOCX text extraction |
| **Matching Engine** | `scikit-learn` (TF-IDF), `numpy` | Deterministic cosine similarity and keyword extraction |
| **AI Question Engine** | Google Gemini API (`google-genai`) / Deterministic Grounding Engine | Grounded questions, duplicate prevention, and 6-axis scoring |
| **Database** | MongoDB (Motor/PyMongo) + Persistent JSON Storage Fallback | Dual-mode storage ensuring 100% plug-and-play reliability |
| **PDF Generation** | ReportLab | Executive PDF interview readiness report generation |

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18+ (v22 recommended)
- **Python**: v3.10+ (v3.13 supported)
- *(Optional)* **MongoDB**: Running locally on port 27017 (if not running, the application automatically uses local persistent JSON storage).
- *(Optional)* **Gemini API Key**: For live LLM evaluation (if not set, the built-in deterministic grounding engine operates seamlessly).

---

### Step 1: Clone and Configure Environment

```bash
git clone <repository_url>
cd project

# Copy environment file
cp .env.example .env
```

---

### Step 2: Run the Backend

```bash
# In the project root:
export PYTHONPATH=$(pwd)

# Install backend dependencies (if needed)
pip install fastapi uvicorn pymupdf python-docx pymongo motor reportlab scikit-learn numpy google-genai python-multipart

# Start the FastAPI server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend will be available at: **`http://127.0.0.1:8000`**  
Interactive API Docs (Swagger UI): **`http://127.0.0.1:8000/docs`**

---

### Step 3: Run the Frontend

```bash
# Open a new terminal:
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
The frontend will be available at: **`http://localhost:5173`**

---

## 🧪 Running Tests

Execute the automated test suite verifying all 8 core API subsystems:

```bash
PYTHONPATH=$(pwd) python backend/test_api.py
```

Expected output:
```
✓ Health check verified: {'status': 'healthy', ...}
✓ Sample Resumes and JDs fetched successfully.
✓ Resume scoring & explainable breakdown verified. Score: 78
✓ Semantic matching verified. Match %: 56
✓ Grounded Question Generation & Zero-Duplicate Regeneration verified.
✓ 6-Axis Answer Evaluation & Adaptive Difficulty verified. Score: 65
✓ Analytics dashboard, skill gap, and resume improvements verified.
✓ ReportLab PDF report generation verified (size: 4430 bytes).
Ran 8 tests in 0.039s — OK
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/resume/upload` | Upload PDF/DOCX resume file & extract entities |
| `POST` | `/api/resume/analyze` | Calculate explainable multi-category resume score |
| `GET` | `/api/resume/samples` | Fetch pre-configured verified demo candidate profiles |
| `POST` | `/api/job/analyze` | Parse Job Description into requirements & technologies |
| `GET` | `/api/job/samples` | Fetch sample job descriptions |
| `POST` | `/api/match` | Compute semantic TF-IDF overlap and skill gaps |
| `POST` | `/api/questions/generate` | Generate grounded, explainable interview questions |
| `POST` | `/api/questions/regenerate`| Generate new questions with zero duplicate collisions |
| `POST` | `/api/questions/bookmark` | Toggle question bookmark |
| `GET` | `/api/questions/saved` | Fetch bookmarked questions |
| `POST` | `/api/interview/answer` | Evaluate candidate answer across 6 axes & suggest next difficulty |
| `GET` | `/api/interview/history` | Retrieve transcript of answered mock questions |
| `POST` | `/api/interview/project-deep-dive` | Architectural dossier & 5 hard project questions |
| `POST` | `/api/interview/topics` | Curate Top 10 preparation topics |
| `GET` | `/api/analytics` | Compute readiness score, radar categories, and weak areas |
| `POST` | `/api/analytics/skill-gap`| Generate gap analysis with learning roadmap |
| `POST` | `/api/analytics/improvements` | Generate STAR-format resume bullet improvements |
| `POST` | `/api/report/export` | Generate and download ReportLab PDF report |
| `GET/POST` | `/api/sessions` | Manage independent interview preparation sessions |

---

## 🏗️ Project Architecture

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app setup, CORS, route mounting
│   │   ├── config.py            # Settings and .env configuration
│   │   ├── database/
│   │   │   └── db.py            # MongoDB + Persistent JSON Storage engine
│   │   ├── schemas/
│   │   │   └── models.py        # Pydantic v2 models and data contracts
│   │   ├── services/
│   │   │   ├── parser.py        # PyMuPDF/docx extractor & scoring logic
│   │   │   ├── matcher.py       # TF-IDF cosine matching & skill gap engine
│   │   │   ├── ai_engine.py     # Grounded questions, evaluator & deduplication
│   │   │   └── report_service.py# ReportLab PDF report generation
│   │   └── routes/
│   │       ├── resume.py        # Resume upload & analysis routes
│   │       ├── job.py           # Job description routes
│   │       ├── match.py         # Semantic matching routes
│   │       ├── questions.py     # Question generator & bookmark routes
│   │       ├── interview.py     # Adaptive mock interview routes
│   │       ├── analytics.py     # Analytics & skill gap routes
│   │       ├── report.py        # PDF report export route
│   │       └── sessions.py      # Multi-session management routes
│   └── test_api.py              # Automated backend test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # ScoreRing, Badge, Toast, Modal
│   │   │   └── layout/          # Sidebar, Header
│   │   ├── context/             # SessionContext (state & sample management)
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── ResumeAnalysis.jsx
│   │   │   ├── JobMatch.jsx
│   │   │   ├── GenerateQuestions.jsx
│   │   │   ├── MockInterview.jsx
│   │   │   ├── SkillGap.jsx
│   │   │   ├── ProjectDeepDive.jsx
│   │   │   ├── PreparationMode.jsx
│   │   │   ├── ResumeImprovement.jsx
│   │   │   ├── AnalyticsDashboard.jsx
│   │   │   ├── SavedQuestions.jsx
│   │   │   └── QuestionHistory.jsx
│   │   ├── services/            # Axios API client
│   │   ├── App.jsx              # Routing & Layout
│   │   └── main.jsx             # Entry point
│   ├── tailwind.config.js       # Custom design tokens & styling
│   └── vite.config.js           # Vite configuration & backend proxy
│
├── PROJECT_EXPLANATION.md       # Plain-language guide for viva/interviews
├── README.md                    # Main documentation
└── .env.example                 # Environment template
```

---

## 🛡️ Differentiators Summary

| Feature | Generic ChatGPT Wrapper | Resume Interview AI |
| :--- | :--- | :--- |
| **Question Grounding** | Inappropriate or hallucinated questions | Strictly linked to actual resume projects and skills |
| **Explainability** | Black-box output with no rationale | Shows *"Why this question?"* and evaluation breakdown |
| **Mock Interview** | Static text chat | Adaptive difficulty scaling based on candidate answer depth |
| **Answer Scoring** | Single arbitrary score | 6-Axis Evaluation (Relevance, Tech Accuracy, Completeness, Clarity, Confidence, Communication) |
| **Deduplication** | Repeated questions on reload | Strict hash-tracked zero-duplicate regeneration engine |
| **Readiness Report** | None | Downloadable ReportLab executive PDF |

---

## 📄 License
MIT License. Built for seamless interview demonstration, academic showcases, and hackathons.
