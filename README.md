# Resume Interview AI 🎯

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF.svg?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Grounded, Explainable Resume-to-Interview Question Generator & Adaptive Mock Interview Platform**

</div>

---

## 📌 Executive Summary

**Resume Interview AI** is an intelligent, full-stack career readiness platform designed to solve the critical flaws of conventional AI interview prep tools: **generic, ungrounded questions and unexplained "black-box" scores**.

By parsing candidate resumes (PDF/DOCX) using high-precision document extraction and aligning them against target Job Descriptions (JDs) via TF-IDF cosine similarity, the application generates **strictly grounded questions** tied directly to verified projects, technical skills, and role requirements. The platform provides an **adaptive mock interview simulator** with real-time 6-axis answer scoring, voice dictation, duplicate-free question regeneration, system architecture deep-dives, skill gap roadmaps, and downloadable ReportLab PDF readiness reports.

---

## 🌟 Key Features & Innovations

### 1. 📄 Explainable Resume Text Extraction & 6-Category Scoring
- **Multi-Format Ingestion**: Parses PDF and DOCX files using PyMuPDF (`fitz`) and `python-docx` with contact, skill, project, work experience, and education extraction.
- **Explainable Multi-Dimensional Score (0–100)**: Evaluates resumes across 6 key categories:
  - *Skills Breadth & Depth* (25%)
  - *Project Complexity & Verifiability* (25%)
  - *Work Experience & Impact* (20%)
  - *Education & Certifications* (10%)
  - *Structural Completeness* (10%)
  - *Relevance to Technical Standards* (10%)
- **Natural Language Rationale**: Delivers actionable feedback and strength/gap justifications for every category score.

### 2. 🎯 Semantic Resume-to-Job Matching
- **Deterministic TF-IDF & Cosine Similarity Engine**: Mathematically measures semantic alignment between candidate experience and job descriptions.
- **Categorized Competency Breakdown**:
  - ✅ **Matching Skills**: Verified overlap between resume and target role.
  - ❌ **Missing Skills**: Core requirements absent from the candidate profile.
  - ⚠️ **Partial / Related Skills**: Transferable competencies requiring domain adaptation.
- **Project Tailoring**: Highlights the candidate's most relevant past projects tailored to the target job description.

### 3. 💡 Strictly Grounded & Explainable Interview Questions
- **Zero-Hallucination Guarantee**: Employs an anti-hallucination `grounding_validator` ensuring questions only reference verified projects, tools, and experiences in the resume.
- **Rich Question Anatomy**:
  - **Question Text**: Targeted technical, behavioral, or architectural prompt.
  - **Based On**: Explicit anchor point (e.g., `Project: Resume Interview AI`, `Skill: MongoDB`).
  - **Difficulty Level**: `Easy`, `Medium`, `Hard`, or `Expert`.
  - **Why This Question?**: Clear explainability rationale linking the JD requirement to the resume item.
  - **Expected Answer Talking Points & Model Strategy**: Guideposts for a structured candidate response.

### 4. 🔄 Zero-Duplicate Question Regeneration Engine
- **Session-Tracked Question Hashing**: Uses SHA-256 content hashing and session-level history tracking.
- Clicking *"Generate Different Questions"* guarantees 100% fresh questions without repeating previously seen prompts within the same session.

### 5. 🎙️ Adaptive AI Mock Interview Simulator
- **Dual-Input Modality**: Supports typed text and hands-free **Voice Dictation (Speech-to-Text via the Web Speech API)**.
- **Real-Time 6-Axis Evaluation**:
  1. *Relevance* (0–100) — Alignment with the core question prompt.
  2. *Technical Accuracy* (0–100) — Precision of concepts, algorithms, and tooling.
  3. *Completeness* (0–100) — Thoroughness in covering all required aspects.
  4. *Clarity* (0–100) — Logical organization and conciseness.
  5. *Confidence* (0–100) — Assertive, authoritative communication style.
  6. *Communication* (0–100) — Structure, vocabulary, and readability.
- **Dynamic Difficulty Progression**: Scoring 85+ on Medium automatically adapts subsequent questions to Hard/Expert; scores below 50 gently scale down to reinforce foundational concepts.

### 6. 🏛️ Project Deep-Dive & Architecture Dossier
- Comprehensive architectural breakdowns for candidate projects:
  - **High-Level System Architecture & Component Interactions**
  - **Database Choice & Data Modeling Trade-offs**
  - **API Contract Validation & Error Handling**
  - **Security & Authentication Posture**
  - **10x Scalability Strategy & Bottleneck Mitigation**
  - **5 Hard Project Defense Questions** with deep technical expected responses.

### 7. 🧩 Skill Gap Analysis & 4-Week Study Roadmap
- Side-by-side competency gap visualization.
- Curates estimated learning hours, foundational concepts, best-practice methodologies, and recommended learning resources for every missing technology.

### 8. ✍️ STAR-Format Resume Improvement Generator
- Transforms passive resume bullet points into high-impact **STAR-method** (Situation, Task, Action, Result) accomplishments with quantified metrics.

### 9. 📊 Visual Analytics & Competency Radar
- **Recharts Analytics Dashboard**:
  - Multi-Axis Competency Radar Chart.
  - Mock Interview Score Progression Trendline.
  - Difficulty Pass Rate Bar Chart.
  - Priority Weak Topic Alerts with remediation advice.

### 10. 📑 ReportLab PDF Readiness Report
- One-click executive PDF export summarizing candidate metadata, resume score breakdown, JD match percentage, interview transcript, and personalized readiness recommendations.

### 11. 💾 Dual-Mode Storage Architecture
- **Automatic Fallback Engine**: Connects to **MongoDB** if available; seamlessly falls back to a **Local Persistent JSON Storage Engine** if MongoDB is absent. Requires zero database setup to run out of the box!

---

## 🛠️ Technology Stack

| Layer | Technologies & Libraries | Key Responsibilities |
| :--- | :--- | :--- |
| **Frontend UI** | React 18/19, Vite, Tailwind CSS | Responsive, accessible, high-performance user interface |
| **Icons & Visuals** | Lucide React, Recharts | Modern UI iconography and dynamic interactive analytics |
| **Voice & Audio** | Web Speech API | Real-time speech-to-text dictation for mock interviews |
| **Backend Framework** | Python 3.10–3.13, FastAPI, Uvicorn | High-throughput async REST API with Pydantic v2 validation |
| **Document Parsing** | PyMuPDF (`fitz`), `python-docx` | Fast, deterministic text and entity extraction from PDFs & DOCX |
| **NLP & Matching** | `scikit-learn` (TF-IDF), `numpy` | Deterministic cosine similarity and keyword extraction |
| **AI Question Engine** | Google Gemini API (`google-genai`) / Grounded Fallback Engine | Contextual question generation, 6-axis scoring, deduplication |
| **Database & Persistence** | MongoDB (Motor/PyMongo) + Persistent JSON Fallback | Dual-mode storage ensuring 100% plug-and-play reliability |
| **Reporting & Export** | ReportLab | Generation of downloadable executive PDF readiness reports |

---

## 🔄 System Architecture & Workflow

```mermaid
flowchart TD
    subgraph Client ["Frontend (React + Vite + Tailwind CSS)"]
        UI[User Interface / Navigation]
        Voice[Web Speech API Voice Dictation]
        Charts[Recharts Analytics Dashboard]
    end

    subgraph API ["Backend API (FastAPI + Uvicorn)"]
        Routes[FastAPI Routers]
        Parser[PyMuPDF / docx Parser]
        Matcher[TF-IDF Matching Engine]
        AIEngine[Grounded Question & Evaluation Engine]
        Report[ReportLab PDF Generator]
    end

    subgraph Storage ["Dual-Mode Data Layer"]
        DBRouter{MongoDB Available?}
        MongoDB[(MongoDB Motor Engine)]
        JSONDB[(Local Persistent JSON Storage)]
    end

    UI -->|Upload Resume / Input JD| Routes
    Routes --> Parser
    Parser --> Matcher
    Matcher --> AIEngine
    Voice -->|Transcribed Audio| Routes
    AIEngine --> Routes
    Routes --> Report
    Routes --> DBRouter
    DBRouter -->|Yes| MongoDB
    DBRouter -->|No| JSONDB
    Routes --> Charts
```

---

## 📂 Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry, CORS, and router registration
│   │   ├── config.py                   # Environment settings and application configuration
│   │   ├── database/
│   │   │   └── db.py                   # Dual-mode storage engine (MongoDB + Persistent JSON Fallback)
│   │   ├── schemas/
│   │   │   └── models.py               # Pydantic v2 data models and request/response contracts
│   │   ├── services/
│   │   │   ├── parser.py               # PyMuPDF/docx extractor & 6-category scoring engine
│   │   │   ├── matcher.py              # TF-IDF cosine matching & skill gap engine
│   │   │   ├── ai_engine.py            # Grounded questions, 6-axis evaluation & deduplication
│   │   │   ├── diversity_manager.py    # Topic distribution and difficulty balance manager
│   │   │   ├── document_validator.py   # Document structure and file security validation
│   │   │   ├── grounding_validator.py  # Anti-hallucination resume entity cross-checker
│   │   │   ├── intent_classifier.py    # Question intent & technical topic classification
│   │   │   └── report_service.py       # ReportLab PDF interview readiness report generator
│   │   └── routes/
│   │       ├── resume.py               # Resume upload, entity extraction & scoring endpoints
│   │       ├── job.py                  # Job description parsing & sample JD endpoints
│   │       ├── match.py                # Semantic resume-to-job matching endpoints
│   │       ├── questions.py            # Grounded question generation & bookmark endpoints
│   │       ├── interview.py            # Adaptive mock interview & 6-axis evaluation endpoints
│   │       ├── analytics.py            # Readiness analytics, skill gap & bullet improvement endpoints
│   │       ├── report.py               # PDF readiness report download endpoint
│   │       └── sessions.py             # Multi-session management & state endpoints
│   ├── data/                           # Local persistent JSON data storage directory
│   ├── test_api.py                     # Automated unit and integration test suite
│   └── requirements.txt                # Python backend dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/                 # ScoreRing, Badge, Toast, Modal, ErrorBoundary
│   │   │   └── layout/                 # Sidebar, Header, Navigation
│   │   ├── context/
│   │   │   └── SessionContext.jsx      # Global session state, history & sample data manager
│   │   ├── pages/
│   │   │   ├── Home.jsx                # Landing page & quick workflow kickstart
│   │   │   ├── ResumeAnalysis.jsx      # Resume upload, parsing & explainable scoring
│   │   │   ├── JobMatch.jsx            # JD matching, competency gaps & project alignment
│   │   │   ├── GenerateQuestions.jsx   # Grounded questions, explainability & deduplication
│   │   │   ├── MockInterview.jsx       # Adaptive mock interview with voice input & 6-axis scoring
│   │   │   ├── SkillGap.jsx            # In-depth skill gaps & 4-week study roadmap
│   │   │   ├── ProjectDeepDive.jsx     # Architectural dossiers & 5 hard project questions
│   │   │   ├── PreparationMode.jsx     # Curated top 10 interview preparation topics
│   │   │   ├── ResumeImprovement.jsx   # STAR-format bullet point rewriter
│   │   │   ├── AnalyticsDashboard.jsx  # Recharts competency radar & readiness metrics
│   │   │   ├── SavedQuestions.jsx      # Bookmarked questions collection
│   │   │   └── QuestionHistory.jsx     # Mock interview transcripts and score history
│   │   ├── services/
│   │   │   └── api.js                  # Axios HTTP client configuration & backend API endpoints
│   │   ├── App.jsx                     # Route definitions and layout structure
│   │   └── main.jsx                    # React application entry point
│   ├── tailwind.config.js              # Tailwind CSS theme, colors, and typography settings
│   ├── vite.config.js                  # Vite bundler configuration & backend API proxy
│   └── package.json                    # Frontend dependencies and scripts
│
├── .env.example                        # Environment variables template
├── requirements.txt                    # Root Python dependencies definition
├── run.py                              # Cross-platform Python launcher script
├── run.bat                             # Windows 1-click batch launcher
├── run.sh                              # macOS / Linux 1-click bash launcher
├── SETUP_GUIDE.md                      # Comprehensive multi-IDE execution guide
└── README.md                           # Main project documentation
```

---

## 🚀 Quick Start & Execution

### Prerequisites
- **Python**: Version 3.10 or higher (`python --version` or `python3 --version`)
- **Node.js**: Version 18 or higher (`node --version` and `npm --version`)
- *(Optional)* **Gemini API Key**: For live LLM evaluation (the deterministic engine runs automatically if omitted).
- *(Optional)* **MongoDB**: Local or remote instance (automatically uses local JSON storage if absent).

---

### Option A: 1-Command Universal Launcher (Recommended)

From the project root directory:

**Windows**:
```cmd
run.bat
```
*or*
```cmd
python run.py
```

**macOS / Linux**:
```bash
./run.sh
```
*or*
```bash
python3 run.py
```

> **The launcher automatically:**
> 1. Installs any missing Python packages from `requirements.txt`.
> 2. Runs `npm install` in `frontend/` if `node_modules` is missing.
> 3. Starts the FastAPI backend (`http://127.0.0.1:8000`) and React frontend (`http://localhost:5174`) concurrently.
> 4. Provides clean shutdown on `Ctrl+C`.

---

### Option B: Manual Step-by-Step Setup

#### 1. Configure Environment
```bash
cp .env.example .env
```

#### 2. Start the Backend Server
```bash
# 1. (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Launch the FastAPI server
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`

#### 3. Start the Frontend Server
```bash
# Open a new terminal window:
cd frontend

# 1. Install dependencies
npm install

# 2. Start the Vite development server
npm run dev
```
- **Frontend App**: `http://localhost:5174` (or `http://localhost:5173`)

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive automated test suite verifying all core API routes, parsing algorithms, grounding mechanisms, deduplication logic, and ReportLab PDF rendering.

```bash
# Run tests from the project root:
PYTHONPATH=$(pwd) python3 backend/test_api.py
```

### Verified Test Assertions:
```
✓ Health check verified: {'status': 'healthy', 'database': '...'}
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

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and active database engine mode |
| `POST` | `/api/resume/upload` | Upload PDF/DOCX file and extract structured entities |
| `POST` | `/api/resume/analyze` | Calculate explainable 6-category resume score and rationale |
| `GET` | `/api/resume/samples` | Retrieve pre-configured demo candidate resumes |
| `POST` | `/api/job/analyze` | Parse Job Description into requirements and tech taxonomy |
| `GET` | `/api/job/samples` | Retrieve pre-configured demo Job Descriptions |
| `POST` | `/api/match` | Compute TF-IDF match score, matching/missing skills, and project fit |
| `POST` | `/api/questions/generate` | Generate grounded, explainable interview questions |
| `POST` | `/api/questions/regenerate` | Regenerate questions with guaranteed zero duplicate collisions |
| `POST` | `/api/questions/bookmark` | Bookmark / unbookmark a specific question |
| `GET` | `/api/questions/saved` | Fetch all bookmarked questions for the active session |
| `POST` | `/api/interview/answer` | Evaluate candidate response across 6 axes and adapt difficulty |
| `GET` | `/api/interview/history` | Retrieve full mock interview question-and-answer transcripts |
| `POST` | `/api/interview/project-deep-dive` | Generate architectural project dossier and 5 hard questions |
| `POST` | `/api/interview/topics` | Curate Top 10 preparation topics based on resume & JD |
| `GET` | `/api/analytics` | Compute readiness score, radar categories, and weak areas |
| `POST` | `/api/analytics/skill-gap` | Generate side-by-side gap analysis and 4-week study roadmap |
| `POST` | `/api/analytics/improvements` | Generate STAR-format resume bullet point optimizations |
| `POST` | `/api/report/export` | Generate and download ReportLab PDF Interview Readiness Report |
| `GET` | `/api/sessions` | List all saved preparation sessions |
| `POST` | `/api/sessions` | Create or update a preparation session |

---

## 👥 Team Architecture & Contribution Matrix

| Team Member | GitHub Handle | Core Specialization & Architecture Role | Primary Owned Modules & Source Files |
| :--- | :--- | :--- | :--- |
| **Bhanusree Varikuntla** | [`@bhanusreevarikuntla`](https://github.com/bhanusreevarikuntla) | **Frontend UI/UX Architecture Lead** | `frontend/src/App.jsx`, `frontend/src/components/layout/`, `components/common/`, `Home.jsx` |
| **Chapala Keerthana** | [`@chapala-keerthana09`](https://github.com/chapala-keerthana09) | **Frontend State & Voice UI Engineer** | `frontend/src/context/SessionContext.jsx`, `frontend/src/services/api.js`, `MockInterview.jsx` (Voice Dictation) |
| **Harish** | [`@harish5991`](https://github.com/harish5991) | **Resume Ingestion & Validation Lead** | `backend/app/services/parser.py`, `document_validator.py`, `backend/app/routes/resume.py` |
| **Venaganti Akshitha** | [`@VenagantiAkshitha`](https://github.com/VenagantiAkshitha) | **Semantic Matching & Skill Gap Specialist** | `backend/app/services/matcher.py`, `JobMatch.jsx`, `SkillGap.jsx`, `ResumeImprovement.jsx` |
| **Shivani Bashaboina** | [`@ShivaniBashaboina`](https://github.com/ShivaniBashaboina) | **Grounded Question Generator & Diversity Lead** | `backend/app/services/ai_engine.py`, `grounding_validator.py`, `diversity_manager.py`, `routes/questions.py` |
| **Gajapuram Bhavya Sri** | [`@bhavyasri0331`](https://github.com/bhavyasri0331) | **Mock Evaluation & STAR Specialist** | `backend/app/services/intent_classifier.py`, `backend/app/routes/interview.py`, `MockInterview.jsx`, `ProjectDeepDive.jsx` |
| **Vanjari Shiva** | [`@Shivakrishna6805`](https://github.com/Shivakrishna6805) | **REST API & Dual-Database Architect** | `backend/app/main.py`, `backend/app/database/db.py`, `backend/app/schemas/models.py`, `sessions.py` |
| **Nithin** | [`@nithin4518`](https://github.com/nithin4518) | **Readiness Analytics, PDF & Automation Lead** | `backend/app/services/report_service.py`, `backend/app/routes/report.py`, `AnalyticsDashboard.jsx`, `test_api.py`, `run.py` |

> 📖 **Comprehensive Breakdown**: For detailed file ownership, technical responsibilities, architecture proofs, and commit lineages for each member, see [**`CONTRIBUTIONS.md`**](CONTRIBUTIONS.md).

---

## 🛡️ Differentiators vs. Generic AI Wrappers

| Feature Matrix | Generic ChatGPT Wrapper | Resume Interview AI 🎯 |
| :--- | :--- | :--- |
| **Question Grounding** | Frequent hallucinations; invents technologies | **Strict Grounding Validator** tied to verified resume entities |
| **Score Explainability** | Black-box single numeric score | **6-Category Breakdown** with natural language justifications |
| **Mock Interview Experience** | Static back-and-forth chat | **Adaptive Difficulty Engine** with real-time level scaling |
| **Answer Evaluation** | Surface-level summary | **6-Axis Evaluation**: Relevance, Tech Accuracy, Completeness, Clarity, Confidence, Communication |
| **Input Modalities** | Typed text only | **Text + Web Speech API Voice Dictation** |
| **Question Deduplication** | High rate of repeated questions | **SHA-256 Hash Engine** guaranteeing zero duplicate regeneration |
| **System Architecture Defense** | None | **Project Deep-Dive Dossier** with 10x scalability & security analysis |
| **Offline / DB Resilience** | Hard failure if DB drops | **Dual-Mode Persistence** (MongoDB + Local JSON Fallback) |
| **Readiness Deliverable** | None | **ReportLab Executive PDF Export** |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Built for enterprise interview preparation, academic defense showcases, and competitive hackathons.
