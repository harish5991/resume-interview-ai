# 👥 Project Contribution & Architecture Ledger

> **Project Name**: Resume Interview AI 🎯  
> **Repository**: [harish5991/resume-interview-ai](https://github.com/harish5991/resume-interview-ai)  
> **Evaluation**: Cognizant (CTS) Hackathon  
> **Team Structure**: 8 Specialized Engineering Roles (4 Architectural Sections × 2 Members)

---

## 🏛️ Section 1: Frontend Architecture, UI/UX & Voice Integration

### Member 1: Bhanusree Varikuntla
- **GitHub**: [`@bhanusreevarikuntla`](https://github.com/bhanusreevarikuntla)
- **Role**: Frontend Architecture & UI/UX Design Lead
- **Specialization**: UI Architecture & Atomic Design System Specialist
- **Tech Stack**: React 19, Vite, Tailwind CSS, Lucide Icons, ErrorBoundary
- **Specific Responsibilities**:
  - Engineered the single-page application core structure, responsive layouts, and navigation hierarchy across all 12 platform views.
  - Built the reusable atomic component system in `frontend/src/components/common/` (`ScoreRing`, `Badge`, `Modal`, `Toast`, `ErrorBoundary`).
  - Designed the master sidebar navigation, header layout, and multi-device responsive breakpoints.
- **Key Files & Directories**:
  - `frontend/src/App.jsx`
  - `frontend/src/components/layout/Sidebar.jsx`
  - `frontend/src/components/layout/Header.jsx`
  - `frontend/src/components/common/ScoreRing.jsx`
  - `frontend/src/components/common/Badge.jsx`
  - `frontend/src/components/common/ErrorBoundary.jsx`
  - `frontend/src/pages/Home.jsx`
- **Assigned Feature Branch**: `feat/ui-accessibility-and-tooltips`

---

### Member 2: Chapala Keerthana
- **GitHub**: [`@chapala-keerthana09`](https://github.com/chapala-keerthana09)
- **Role**: Frontend State & Voice UI Engineer
- **Specialization**: Client State & Speech-to-Text Specialist
- **Tech Stack**: React Context API, Web Speech API (`webkitSpeechRecognition`), Axios Interceptors, `sessionStorage`
- **Specific Responsibilities**:
  - Engineered the `SessionContext` global state store with ephemeral `sessionStorage` synchronization across browser refreshes.
  - Integrated browser-native Speech-to-Text for real-time candidate voice dictation during adaptive mock interviews.
  - Built live backend health status monitoring (Online/Offline indicator) and Axios HTTP client error handling.
- **Key Files & Directories**:
  - `frontend/src/context/SessionContext.jsx`
  - `frontend/src/services/api.js`
  - `frontend/src/pages/MockInterview.jsx` (Voice dictation hooks and microphone controls)
- **Assigned Feature Branch**: `feat/voice-dictation-visualizer`

---

## 🔬 Section 2: Document Processing, NLP & Semantic Match Engine

### Member 3: Harish
- **GitHub**: [`@harish5991`](https://github.com/harish5991)
- **Role**: Resume Ingestion & Validation Lead
- **Specialization**: Document Parsing, Resume Validation & Quality Scoring Specialist
- **Tech Stack**: Python 3.11/3.13, PyMuPDF (`fitz`), `python-docx`, DocumentValidator, Regex Heuristics
- **Specific Responsibilities**:
  - Developed the high-precision resume ingestion pipeline extracting structured text from PDF and Word documents.
  - Built the `DocumentValidator` to detect and reject non-resumes, academic papers, research articles, and certificates.
  - Engineered multi-pass regex section segmenter and an explainable 7-factor resume quality scoring algorithm (0–100).
- **Key Files & Directories**:
  - `backend/app/services/parser.py`
  - `backend/app/services/document_validator.py`
  - `backend/app/routes/resume.py`
- **Assigned Feature Branch**: `feat/parser-certification-heuristics`

---

### Member 4: Venaganti Akshitha
- **GitHub**: [`@VenagantiAkshitha`](https://github.com/VenagantiAkshitha)
- **Role**: Semantic Matching Engineer
- **Specialization**: Job Description Match & Gap Analysis Specialist
- **Tech Stack**: Scikit-learn (`TfidfVectorizer`, `cosine_similarity`), NLP Tokenizer
- **Specific Responsibilities**:
  - Implemented the deterministic TF-IDF cosine similarity engine between candidate resumes and job descriptions.
  - Built automated competency taxonomy classification (Matched Skills, Critical Missing Gaps, Candidate Strengths).
  - Developed the 4-week structured learning roadmap generator and STAR-method resume bullet point optimizer.
- **Key Files & Directories**:
  - `backend/app/services/matcher.py`
  - `frontend/src/pages/JobMatch.jsx`
  - `frontend/src/pages/SkillGap.jsx`
  - `frontend/src/pages/ResumeImprovement.jsx`
- **Assigned Feature Branch**: `feat/skill-gap-learning-resources`

---

## 🧠 Section 3: Grounded Question Generation & Mock Evaluation

### Member 5: Shivani Bashaboina
- **GitHub**: [`@ShivaniBashaboina`](https://github.com/ShivaniBashaboina)
- **Role**: Question Generator & Diversity Lead
- **Specialization**: Grounded Generation, Anti-Hallucination & Diversity Specialist
- **Tech Stack**: FastAPI, Google Gemini API / Grounded Catalog, `GroundingValidator`, `DiversityManager`, MD5/SHA-256 Hashing, Pydantic v2
- **Specific Responsibilities**:
  - Engineered the grounded question generation engine strictly anchored to candidate projects and target JD requirements.
  - Built the `GroundingValidator` anti-hallucination blocker ensuring questions never invent unverified technologies.
  - Implemented zero-duplicate SHA-256 session tracking and the 23-archetype question diversity rotation engine.
- **Key Files & Directories**:
  - `backend/app/services/ai_engine.py`
  - `backend/app/services/grounding_validator.py`
  - `backend/app/services/diversity_manager.py`
  - `backend/app/routes/questions.py`
  - `frontend/src/pages/GenerateQuestions.jsx`
- **Assigned Feature Branch**: `feat/diversity-archetype-expansions`

---

### Member 6: Gajapuram Bhavya Sri
- **GitHub**: [`@bhavyasri0331`](https://github.com/bhavyasri0331)
- **Role**: Mock Evaluation & STAR Specialist
- **Specialization**: Answer Evaluation, Intent Classifier & STAR Diagnostics Engineer
- **Tech Stack**: Python, `QuestionIntentClassifier`, Domain Concept Dictionary, STAR Method Heuristics
- **Specific Responsibilities**:
  - Developed the real-time 6-axis candidate answer scoring engine (Technical Accuracy, Relevance, Completeness, Clarity, Confidence, Communication).
  - Built domain concept extraction and misconception penalty detection algorithms.
  - Engineered STAR diagnostic feedback analyzer, senior model answer synthesis, and dynamic adaptive difficulty scaling.
- **Key Files & Directories**:
  - `backend/app/services/intent_classifier.py`
  - `backend/app/routes/interview.py`
  - `frontend/src/pages/MockInterview.jsx` (Evaluation & feedback matrix)
  - `frontend/src/pages/ProjectDeepDive.jsx`
- **Assigned Feature Branch**: `feat/star-diagnostic-metric-scoring`

---

## ⚡ Section 4: Backend Infrastructure, Database & Reporting

### Member 7: Vanjari Shiva
- **GitHub**: [`@Shivakrishna6805`](https://github.com/Shivakrishna6805)
- **Role**: REST API & Database Architect
- **Specialization**: Backend Architecture & Dual-Database Specialist
- **Tech Stack**: FastAPI, Motor (`AsyncIOMotorClient`), PyMongo, `asyncio.Lock`, LocalJsonCollection, Pydantic v2
- **Specific Responsibilities**:
  - Designed the asynchronous REST routing architecture, middleware CORS policies, and request/response validation contracts.
  - Engineered the dual-mode storage engine with seamless automatic fallback from MongoDB to async Local JSON storage.
  - Implemented session persistence, thread-safe asynchronous file locking, and ephemeral session cleanup APIs.
- **Key Files & Directories**:
  - `backend/app/main.py`
  - `backend/app/database/db.py`
  - `backend/app/config.py`
  - `backend/app/schemas/models.py`
  - `backend/app/routes/sessions.py`
- **Assigned Feature Branch**: `feat/db-latency-benchmarking`

---

### Member 8: Nithin
- **GitHub**: [`@nithin4518`](https://github.com/nithin4518)
- **Role**: Readiness Analytics & PDF Lead
- **Specialization**: Analytics Dashboard, PDF Engine & Automation Engineer
- **Tech Stack**: ReportLab, Recharts, Cross-Platform Launchers (`run.py`, `run.bat`, `run.sh`), Automated Test Suite
- **Specific Responsibilities**:
  - Built the automated ReportLab in-memory PDF engine generating downloadable executive interview readiness reports in <100ms.
  - Engineered the interactive Recharts analytics dashboard (competency radar, score trendlines, weak-area remediation alerts).
  - Authored cross-platform 1-click execution scripts (`run.py`, `run.bat`, `run.sh`) and the automated API testing suite (`test_api.py`).
- **Key Files & Directories**:
  - `backend/app/services/report_service.py`
  - `backend/app/routes/report.py`
  - `backend/app/routes/analytics.py`
  - `frontend/src/pages/AnalyticsDashboard.jsx`
  - `backend/test_api.py`
  - `run.py`, `run.bat`, `run.sh`
- **Assigned Feature Branch**: `feat/pdf-report-styling-enhancement`

---

## 📊 Summary Contribution Matrix

| Member Name | GitHub Handle | Section | Primary Contribution |
| :--- | :--- | :--- | :--- |
| **Bhanusree Varikuntla** | [`@bhanusreevarikuntla`](https://github.com/bhanusreevarikuntla) | Section 1 | Frontend SPA architecture, navigation & atomic design system |
| **Chapala Keerthana** | [`@chapala-keerthana09`](https://github.com/chapala-keerthana09) | Section 1 | Global `SessionContext` store & Web Speech API voice dictation |
| **Harish** | [`@harish5991`](https://github.com/harish5991) | Section 2 | PyMuPDF/docx resume parsing & 7-factor explainable scoring |
| **Venaganti Akshitha** | [`@VenagantiAkshitha`](https://github.com/VenagantiAkshitha) | Section 2 | TF-IDF semantic job matching & skill gap roadmap generator |
| **Shivani Bashaboina** | [`@ShivaniBashaboina`](https://github.com/ShivaniBashaboina) | Section 3 | Grounded question generator, anti-hallucination & deduplication |
| **Gajapuram Bhavya Sri** | [`@bhavyasri0331`](https://github.com/bhavyasri0331) | Section 3 | 6-Axis mock answer scoring, domain concepts & STAR feedback |
| **Vanjari Shiva** | [`@Shivakrishna6805`](https://github.com/Shivakrishna6805) | Section 4 | FastAPI async architecture & dual MongoDB/JSON fallback engine |
| **Nithin** | [`@nithin4518`](https://github.com/nithin4518) | Section 4 | ReportLab PDF engine, Recharts dashboard & automation launchers |
