# Resume Interview AI — Project Explanation Guide
> **A plain-language technical companion to confidently explain every component of this project during interviews, hackathons, and project defense (viva).**

---

## 1. Executive Summary (The 30-Second Pitch)

> *"Resume Interview AI is an intelligent, explainable interview preparation platform. Instead of asking generic ChatGPT questions, our system extracts candidate project and skill entities from PDF/DOCX resumes, matches them against target Job Descriptions using TF-IDF cosine similarity, and generates strictly grounded interview questions. It features an adaptive mock interview simulator that listens to speech or text, scores responses across 6 core criteria, adjusts question difficulty in real time, and outputs an executive PDF readiness report."*

---

## 2. Why Did We Build This? (Problem Statement)

1. **Generic Questions in Existing Tools**: Most AI interview bots use simple prompts like *"Ask me 5 Python questions"*, generating generic trivia that doesn't reflect the candidate's actual projects or target job.
2. **Black-Box AI Scores**: Most platforms say *"Your score is 72/100"* without explaining why or how the candidate can improve.
3. **No Adaptive Feedback Loop**: Traditional quizzes are static; real interviewers increase difficulty when you answer well or ask follow-ups when you are vague.
4. **Duplicate Fatigue**: Refreshing generic question generators often produces the same repeated questions.

---

## 3. Deep Dive: How Each Technology Works

### A. Resume Parsing Layer (PyMuPDF & python-docx)
- **Why PyMuPDF (`fitz`)?**
  - PyMuPDF is a lightweight, high-performance C-extension library that extracts clean layout-preserved text from PDF binary streams without needing heavy OCR or Java dependencies.
- **Entity Extraction**:
  - We use regular expressions and heuristic segmentation to identify sections (Skills, Work Experience, Projects, Education, Certifications).
  - Skills are standardized against a 60+ technical taxonomy and mapped into categories (Languages, Frontend, Backend, Databases, Cloud & DevOps, AI/Data Science).

---

### B. Semantic Matching Layer (TF-IDF & Cosine Similarity)
- **How Does Matching Work?**
  - **Direct Skill Overlap**: Computes the set intersection between candidate skills and required job skills.
  - **TF-IDF Vectorization** (*Term Frequency-Inverse Document Frequency*): Transforms the resume text and JD text into frequency-weighted mathematical vectors.
  - **Cosine Similarity**: Measures the cosine of the angle between the two vectors:
    $$\text{Cosine Similarity} = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
  - **Composite Score**: The match percentage is calculated as:
    $$\text{Match \%} = (0.65 \times \text{Skill Overlap Ratio}) + (0.35 \times \text{TF-IDF Semantic Similarity})$$
  - **Explainability**: We clearly display *Matching Skills*, *Missing Skills*, *Relevant Projects*, and a plain-English explanation.

---

### C. Grounded Question Engine (Anti-Hallucination & Explainability)
- **What is Grounding?**
  - Grounding means the question is provably tied to a specific project, technology, or requirement in the input data.
  - Every question card specifies:
    - `question`: The actual question.
    - `based_on`: The specific evidence in the resume (e.g. `Project: Resume Interview AI` or `Resume Skill: MongoDB`).
    - `skill`: The targeted technology.
    - `difficulty`: `Easy`, `Medium`, `Hard`, or `Expert`.
    - `why_this_question`: The architectural or domain rationale.
- **Zero Hallucinations**:
  - The deterministic grounding catalog and strictly constrained LLM prompt prevent the AI from inventing technologies or companies not listed in the candidate's resume.

---

### D. Zero-Duplicate Regeneration Engine
- **The Mechanism**:
  - When questions are generated, an MD5 hash of the normalized question text is stored in the session's question history.
  - On clicking *"Generate Different Questions"*, the backend passes all previously generated hashes as an exclusion set (`exclude_question_hashes`).
  - The engine filters out collisions, guaranteeing 100% fresh questions.

---

### E. Adaptive Mock Interview Engine & 6-Axis Evaluation
- **Voice Dictation (Speech-to-Text)**:
  - Uses the browser's native `SpeechRecognition` (Web Speech API), providing frictionless, hands-free speech-to-text without requiring external paid speech APIs.
- **6-Axis Evaluation**:
  Every answer is scored across:
  1. **Relevance (25%)**: Did the candidate answer the exact question asked?
  2. **Technical Accuracy (25%)**: Were terminology, internal mechanisms, and concepts used correctly?
  3. **Completeness (20%)**: Did the candidate provide context, design choice, trade-off, and result?
  4. **Clarity (10%)**: Is the explanation concise and well-structured?
  5. **Confidence (10%)**: Is the tone assertive without excessive hesitation markers?
  6. **Communication (10%)**: Professional articulation and sentence pacing.
- **Adaptive Difficulty Transition Rules**:
  - Score $\ge 85$: Next question moves up (e.g. `Medium` $\rightarrow$ `Hard`, `Hard` $\rightarrow$ `Expert`).
  - Score $65-84$: Maintained at current difficulty.
  - Score $< 65$: Lowered or targeted with a foundational question.

---

### F. Dual-Mode Database Architecture (MongoDB + Local JSON Fallback)
- **Why this design?**
  - In a production environment or when deployed, the backend connects to MongoDB via `Motor`/`AsyncIOMotorClient`.
  - On a fresh developer setup or during a hackathon demo without a live MongoDB instance, `DatabaseManager` transparently falls back to an asynchronous, file-persisted JSON database engine (`LocalJsonCollection`).
  - **Zero Crash Guarantee**: The application never crashes due to database connection errors!

---

### G. Executive PDF Report Generation (ReportLab)
- **Why ReportLab?**
  - ReportLab builds vector-crisp, printable PDF documents programmatically using `SimpleDocTemplate`, custom `ParagraphStyle` typography, and auto-wrapped `Table` grids.
  - Generates the complete interview report in $<50\text{ms}$ with zero headless browser overhead.

---

## 4. Frequently Asked Interview Questions (Q&A Preparation)

### Q1: "Why did you choose FastAPI over Flask or Django?"
> **Answer**:  
> *"FastAPI offers native asynchronous request handling with Starlette, automatic Pydantic v2 data validation with type safety, and automatic OpenAPI documentation generation. For an AI-driven service handling concurrent resume parsing and streaming evaluations, FastAPI delivers significantly higher throughput with cleaner code."*

### Q2: "How do you guarantee that the questions are not hallucinated?"
> **Answer**:  
> *"We implement strict grounding. Before generating any question, our pipeline extracts verified entities (project names, technologies, durations) from the candidate's resume. The question templates and LLM prompts are conditioned strictly on these entities. Every generated question returns a `based_on` parameter that references the exact resume project or skill."*

### Q3: "How is the TF-IDF Cosine Match different from simple keyword search?"
> **Answer**:  
> *"Keyword search is binary (present or absent). TF-IDF accounts for the importance of rare domain terms (e.g., 'Kubernetes', 'FastAPI') while downweighting generic stopwords ('team', 'developer', 'experience'). Cosine similarity then calculates the directional alignment between the candidate's experience vector and the job requirement vector, providing a smooth, continuous match score."*

### Q4: "How does the duplicate-prevention mechanism work?"
> **Answer**:  
> *"Each generated question has its normalized text hashed using MD5. The backend stores these hashes in the session's question history. Whenever the user requests new questions, all historical hashes are passed as an exclusion filter so the engine guarantees no repeat questions occur within that session."*

### Q5: "How does your speech-to-text recording work on the frontend?"
> **Answer**:  
> *"We utilize the native browser Web Speech API (`webkitSpeechRecognition`). When the microphone button is toggled, it streams continuous audio chunks, transcribes them into text, and appends the transcription directly into the candidate's answer textarea in real time."*

---

## 5. Summary Table for Quick Reference

| Feature | Tech Used | Explainability Justification |
| :--- | :--- | :--- |
| **PDF Extraction** | PyMuPDF (`fitz`) | Fast, local text extraction with zero external API dependencies. |
| **Matching Engine** | TF-IDF + Cosine Similarity | Deterministic mathematical vector similarity with explainable formula. |
| **Question Grounding** | Grounded Catalog + Gemini API | Strict grounding to candidate resume projects; zero hallucinations. |
| **Speech Input** | Web Speech API | Client-side native voice transcription with zero latency. |
| **Visual Charts** | Recharts | Interactive Radar, Line, and Bar charts for skill balance. |
| **Report Export** | ReportLab | Fast, executive PDF generation with complete session analytics. |
| **Database** | MongoDB + Persistent JSON | 100% reliable in both local demo and production cloud environments. |
