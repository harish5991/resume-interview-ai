import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure root directory in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.schemas.models import ExtractedResume, JobDescriptionAnalysis

class TestResumeInterviewAI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        print("✓ Health check verified:", data)

    def test_02_samples(self):
        res_resumes = self.client.get("/api/resume/samples")
        self.assertEqual(res_resumes.status_code, 200)
        self.assertGreater(len(res_resumes.json()), 0)

        res_jds = self.client.get("/api/job/samples")
        self.assertEqual(res_jds.status_code, 200)
        self.assertGreater(len(res_jds.json()), 0)
        print("✓ Sample Resumes and JDs fetched successfully.")

    def test_03_resume_analysis(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        res = self.client.post("/api/resume/analyze", json=sample_resume)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("score", data)
        self.assertGreaterEqual(data["score"]["overall_score"], 50)
        print("✓ Resume scoring & explainable breakdown verified. Score:", data["score"]["overall_score"])

    def test_04_job_analysis_and_match(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        res = self.client.post("/api/match", json={"resume": sample_resume, "jd": sample_jd})
        self.assertEqual(res.status_code, 200)
        match_data = res.json()
        self.assertIn("match_percentage", match_data)
        self.assertIn("matching_skills", match_data)
        self.assertIn("relevance_explanation", match_data)
        print("✓ Semantic matching verified. Match %:", match_data["match_percentage"])

    def test_05_question_generation_and_deduplication(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        # Generate 5 questions
        gen_res = self.client.post("/api/questions/generate", json={
            "session_id": "test-session",
            "resume_data": sample_resume,
            "jd_data": sample_jd,
            "difficulty": "Medium",
            "question_type": "Mixed",
            "count": 5
        })
        self.assertEqual(gen_res.status_code, 200)
        q_list_1 = gen_res.json()
        self.assertEqual(len(q_list_1), 5)
        
        # Verify grounding on each question
        for q in q_list_1:
            self.assertTrue(len(q["question"]) > 10)
            self.assertTrue(len(q["based_on"]) > 0)
            self.assertTrue(len(q["why_this_question"]) > 0)

        # Regenerate and verify duplicate prevention
        regen_res = self.client.post("/api/questions/regenerate", json={
            "session_id": "test-session",
            "resume_data": sample_resume,
            "jd_data": sample_jd,
            "difficulty": "Medium",
            "question_type": "Mixed",
            "count": 5
        })
        self.assertEqual(regen_res.status_code, 200)
        q_list_2 = regen_res.json()
        self.assertEqual(len(q_list_2), 5)

        q1_texts = set(q["question"] for q in q_list_1)
        q2_texts = set(q["question"] for q in q_list_2)
        overlap = q1_texts.intersection(q2_texts)
        self.assertEqual(len(overlap), 0, f"Detected duplicate questions across regeneration: {overlap}")
        print("✓ Grounded Question Generation & Zero-Duplicate Regeneration verified.")

    def test_06_answer_evaluation(self):
        # 1. Genuine MongoDB answer to MongoDB question
        eval_payload = {
            "session_id": "test-session",
            "question_id": "q-test-1",
            "question_text": "Why did you choose MongoDB for your Resume Interview AI project?",
            "based_on": "Project: Resume Interview AI",
            "skill": "MongoDB",
            "difficulty": "Medium",
            "user_answer": "We chose MongoDB because of its flexible BSON document schema, which allowed us to store complex parsed resumes with nested projects, skills, and experience without rigid schema migrations. We also created compound indexes on user and session IDs for sub-50ms query response times.",
            "expected_points": ["Flexible schema", "BSON documents", "Indexing performance"]
        }

        res = self.client.post("/api/interview/answer", json=eval_payload)
        self.assertEqual(res.status_code, 200)
        eval_data = res.json()
        self.assertGreaterEqual(eval_data["overall_score"], 60)
        self.assertIn("strengths", eval_data)
        self.assertIn("improved_answer", eval_data)
        self.assertIn("next_recommended_difficulty", eval_data)

        # 2. Domain Mismatch: Algorithms/Data Pipeline answer submitted to React question
        mismatch_payload = {
            "session_id": "test-session",
            "question_id": "q-test-react",
            "question_text": "The target job requires solid experience with React. How have you applied React in your projects, or how would you ramp up?",
            "based_on": "JD Target Skill: React (Job Requirement)",
            "skill": "React",
            "difficulty": "Medium",
            "user_answer": "In our architecture, we implemented Algorithms specifically to address Key benefits of Algorithms, Why alternatives fell short, Development speed vs performance. In our processing pipeline, Algorithms handled data ingestion, transformation, and validation with sub-50ms latency. The primary trade-off was balancing memory overhead against execution speed, which we resolved by implementing caching and asynchronous task queues, maintaining 99.9% uptime in production.",
            "expected_points": ["Virtual DOM", "Hooks and lifecycle", "Component modularity"]
        }
        res_mismatch = self.client.post("/api/interview/answer", json=mismatch_payload)
        self.assertEqual(res_mismatch.status_code, 200)
        mismatch_data = res_mismatch.json()
        self.assertLessEqual(mismatch_data["overall_score"], 25)
        self.assertLessEqual(mismatch_data["relevance_score"], 15)
        self.assertEqual(mismatch_data["verdict_rating"], "Off-Topic / Domain Mismatch")
        self.assertEqual(len(mismatch_data["concepts_covered"]), 0)

        # 3. Repeated Sentence / Spam: Copy-pasting looped text on CSS3 question
        spam_payload = {
            "session_id": "test-session",
            "question_id": "q-test-css3",
            "question_text": "Can you explain a key performance or architectural decision you made when working with CSS3?",
            "based_on": "Resume Skill: CSS3",
            "skill": "CSS3",
            "difficulty": "Medium",
            "user_answer": "Describe a situation where you had to quickly learn a new framework or technology to deliver a project feature. " * 8,
            "expected_points": ["CSS Grid and Flexbox", "Critical CSS rendering path", "Hardware accelerated animations"]
        }
        res_spam = self.client.post("/api/interview/answer", json=spam_payload)
        self.assertEqual(res_spam.status_code, 200)
        spam_data = res_spam.json()
        self.assertEqual(spam_data["overall_score"], 0)
        self.assertEqual(spam_data["verdict_rating"], "Irrelevant / Repetitive Input")

        # 4. Genuine CSS3 answer
        css_payload = {
            "session_id": "test-session",
            "question_id": "q-test-css3-good",
            "question_text": "Can you explain a key performance or architectural decision you made when working with CSS3?",
            "based_on": "Resume Skill: CSS3",
            "skill": "CSS3",
            "difficulty": "Medium",
            "user_answer": "When architecting CSS3 in production, I prioritized critical rendering path performance by inlining critical CSS and using content-visibility: auto for offscreen components. We avoided layout thrashing by utilizing hardware-accelerated CSS transforms (transform: translate3d and will-change) for 60 FPS animations instead of JavaScript manipulations, and structured our styles using BEM to prevent specificity wars.",
            "expected_points": ["Critical CSS rendering path", "Hardware accelerated transforms", "CSS architecture (BEM)"]
        }
        res_css = self.client.post("/api/interview/answer", json=css_payload)
        self.assertEqual(res_css.status_code, 200)
        css_data = res_css.json()
        self.assertGreaterEqual(css_data["overall_score"], 70)
        self.assertGreater(len(css_data["concepts_covered"]), 0)

        # 5. Genuine NLP answer (Fixing the main 0-score bug)
        nlp_payload = {
            "session_id": "test-session",
            "question_id": "q-test-nlp",
            "question_text": "How did you use NLP in your project for text processing and skill extraction?",
            "based_on": "Project: Resume Interview AI",
            "skill": "NLP",
            "difficulty": "Medium",
            "user_answer": "In our project, I implemented NLP pipelines using spaCy for tokenization, stopword removal, and Named Entity Recognition (NER) to extract candidate skills and job requirements. We then applied TF-IDF and transformer embeddings with cosine similarity to calculate match percentages.",
            "expected_points": ["Tokenization and stopword removal", "NER for skill extraction", "Embeddings and cosine similarity"]
        }
        res_nlp = self.client.post("/api/interview/answer", json=nlp_payload)
        self.assertEqual(res_nlp.status_code, 200)
        nlp_data = res_nlp.json()
        self.assertGreaterEqual(nlp_data["overall_score"], 70)
        self.assertGreaterEqual(nlp_data["relevance_score"], 65)
        self.assertGreaterEqual(nlp_data["technical_accuracy_score"], 65)
        self.assertIn("strengths", nlp_data)
        self.assertGreater(len(nlp_data["strengths"]), 0)
        self.assertIn("improved_answer", nlp_data)

        # 6. Semicolons and code snippets should NOT trigger gibberish/0-score
        code_payload = {
            "session_id": "test-session",
            "question_id": "q-test-code-semi",
            "question_text": "How do you optimize SQL query execution plans in PostgreSQL?",
            "based_on": "Resume Skill: SQL",
            "skill": "SQL",
            "difficulty": "Medium",
            "user_answer": "I run EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active'; to check for index scans over seq scans. Then I add compound B-tree indexes: CREATE INDEX idx_users ON users(status, created_at);",
            "expected_points": ["EXPLAIN ANALYZE", "B-tree index", "Sequential vs index scan"]
        }
        res_code = self.client.post("/api/interview/answer", json=code_payload)
        self.assertEqual(res_code.status_code, 200)
        code_data = res_code.json()
        self.assertGreaterEqual(code_data["overall_score"], 45)
        self.assertGreaterEqual(code_data["relevance_score"], 45)

        # 7. Empty answer validation
        res_empty = self.client.post("/api/interview/answer", json={
            "session_id": "test-session",
            "question_id": "q-test-empty",
            "question_text": "Explain Python GIL.",
            "skill": "Python",
            "user_answer": "   "
        })
        self.assertEqual(res_empty.status_code, 400)

        # 8. Brief answer gets appropriate feedback and non-zero score
        brief_payload = {
            "session_id": "test-session",
            "question_id": "q-test-brief",
            "question_text": "How does React manage component state?",
            "skill": "React",
            "user_answer": "React manages state using useState hooks and triggers re-renders on state changes.",
            "expected_points": ["useState hook", "Re-rendering"]
        }
        res_brief = self.client.post("/api/interview/answer", json=brief_payload)
        self.assertEqual(res_brief.status_code, 200)
        brief_data = res_brief.json()
        self.assertGreaterEqual(brief_data["overall_score"], 35)
        self.assertGreaterEqual(brief_data["relevance_score"], 45)
        self.assertIn("brief", " ".join(brief_data["weaknesses"]).lower() + brief_data["feedback_summary"].lower())

        print("✓ 6-Axis Answer Evaluation & Domain Mismatch / Spam Detection / NLP verified.")

    def test_07_analytics_and_skill_gap(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        # Skill gap
        gap_res = self.client.post("/api/analytics/skill-gap", json={"resume": sample_resume, "jd": sample_jd})
        self.assertEqual(gap_res.status_code, 200)
        self.assertIn("learning_roadmap", gap_res.json())

        # Improvements
        imp_res = self.client.post("/api/analytics/improvements", json={"resume": sample_resume})
        self.assertEqual(imp_res.status_code, 200)
        self.assertGreater(len(imp_res.json()), 0)

        # Analytics
        ana_res = self.client.get("/api/analytics?session_id=test-session")
        self.assertEqual(ana_res.status_code, 200)
        self.assertIn("interview_readiness_score", ana_res.json())
        print("✓ Analytics dashboard, skill gap, and resume improvements verified.")

    def test_08_pdf_report_export(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        res = self.client.post("/api/report/export", json={
            "session_id": "test-session",
            "resume": sample_resume,
            "jd": sample_jd
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/pdf")
        self.assertGreater(len(res.content), 1000)
        print("✓ ReportLab PDF report generation verified (size:", len(res.content), "bytes).")

    def test_09_final_interview_evaluation(self):
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        # 1. Generate questions
        gen_res = self.client.post("/api/questions/generate", json={
            "session_id": "eval-session",
            "resume_data": sample_resume,
            "jd_data": sample_jd,
            "difficulty": "Medium",
            "count": 3
        })
        self.assertEqual(gen_res.status_code, 200)
        questions = gen_res.json()

        # 2. Submit answers for each question
        evaluations = []
        for q in questions:
            ans_res = self.client.post("/api/interview/answer", json={
                "session_id": "eval-session",
                "question_id": q["id"],
                "question_text": q["question"],
                "based_on": q["based_on"],
                "skill": q["skill"],
                "difficulty": q["difficulty"],
                "user_answer": f"In our project we implemented {q['skill']} for scalable processing and handled memory trade-offs effectively with sub-50ms latency in production.",
                "expected_points": q.get("expected_answer_points", [])
            })
            self.assertEqual(ans_res.status_code, 200)
            evaluations.append(ans_res.json())

        # 3. Call Final Evaluation endpoint
        final_res = self.client.post("/api/interview/final-evaluation", json={
            "session_id": "eval-session",
            "questions": questions,
            "evaluations": evaluations,
            "resume_data": sample_resume,
            "jd_data": sample_jd
        })
        self.assertEqual(final_res.status_code, 200)
        final_data = final_res.json()
        self.assertIn("overall_score", final_data)
        self.assertIn("hiring_verdict", final_data)
        self.assertIn("competency_scores", final_data)
        self.assertIn("per_question_breakdown", final_data)
        self.assertEqual(len(final_data["per_question_breakdown"]), 3)
        print("✓ Final Interview Evaluation synthesis verified. Score:", final_data["overall_score"], "| Verdict:", final_data["hiring_verdict"])

    def test_10_grounding_mysql_10x_scaling(self):
        """Verify MySQL 10x volume scaling answer does NOT hallucinate Redis, Kafka, Celery, Docker, Nginx, HPA."""
        resume_data = {
            "name": "Jordan Lee",
            "email": "jordan@example.com",
            "skills": ["Python", "MySQL", "FastAPI"],
            "projects": [
                {
                    "title": "Inventory Management System",
                    "description": "Built database-backed inventory API with MySQL.",
                    "technologies": ["Python", "MySQL", "FastAPI"],
                    "highlights": ["Designed relational tables and optimized queries"]
                }
            ],
            "experience": []
        }

        gen_res = self.client.post("/api/questions/generate", json={
            "session_id": "grounding-session",
            "resume_data": resume_data,
            "difficulty": "Medium",
            "question_type": "Project Based",
            "count": 5
        })
        self.assertEqual(gen_res.status_code, 200)
        questions = gen_res.json()

        for q in questions:
            self.assertIn("answer_grounding", q)
            self.assertIsNotNone(q["answer_grounding"])
            sample_ans = q["sample_answer"].lower()
            
            # Since Redis, Kafka, Celery, Nginx, Docker, HPA are NOT in the resume,
            # first-person claims of having implemented them must NOT exist.
            if "scale" in q["question"].lower() and "mysql" in q["question"].lower():
                self.assertNotIn("we introduced redis", sample_ans)
                self.assertNotIn("we deployed behind an nginx", sample_ans)
                self.assertNotIn("with horizontal pod autoscaling", sample_ans)
                self.assertNotIn("we decoupled cpu-intensive workloads using asynchronous worker queues (like celery/kafka)", sample_ans)
                print("✓ MySQL 10x volume scaling answer strictly grounded:", q["sample_answer"][:120], "...")

    def test_11_grounding_css3_performance_decision(self):
        """Verify CSS3 performance decision answer does NOT invent BEM, content-visibility, translate3d, will-change, or 40% CLS."""
        resume_data = {
            "name": "Sam Taylor",
            "email": "sam@example.com",
            "skills": ["HTML5", "CSS3", "JavaScript"],
            "projects": [
                {
                    "title": "Portfolio Web App",
                    "description": "Built frontend website using HTML5 and CSS3.",
                    "technologies": ["HTML5", "CSS3", "JavaScript"],
                    "highlights": ["Created responsive grid layouts"]
                }
            ],
            "experience": []
        }

        gen_res = self.client.post("/api/questions/generate", json={
            "session_id": "css3-session",
            "resume_data": resume_data,
            "difficulty": "Medium",
            "question_type": "Technical",
            "count": 5
        })
        self.assertEqual(gen_res.status_code, 200)
        questions = gen_res.json()

        for q in questions:
            self.assertIn("answer_grounding", q)
            if "css3" in q["question"].lower() and "performance" in q["question"].lower():
                sample_ans = q["sample_answer"].lower()
                self.assertNotIn("content-visibility: auto", sample_ans)
                self.assertNotIn("transform: translate3d", sample_ans)
                self.assertNotIn("will-change", sample_ans)
                self.assertNotIn("cumulative layout shift by 40%", sample_ans)
                print("✓ CSS3 performance decision answer strictly grounded without hallucinated metrics:", q["sample_answer"][:120], "...")

    def test_12_grounding_validator_service(self):
        """Directly test GroundingValidator claim validation and auto-rewrite on unsupported tech."""
        from backend.app.services.grounding_validator import GroundingValidator
        from backend.app.schemas.models import ExtractedResume, ProjectItem

        resume = ExtractedResume(
            name="Alex Dev",
            skills=["Python", "FastAPI", "PostgreSQL"],
            projects=[
                ProjectItem(title="API Gateway", description="REST API service", technologies=["Python", "FastAPI"])
            ],
            experience=[]
        )

        unsupported_answer = "In my project, I implemented Redis caching and deployed Kubernetes HPA with Kafka event streaming to reduce latency by 60%."
        grounded_ans, grounding = GroundingValidator.validate_and_ground_answer(
            question_text="How did you scale your system?",
            answer_text=unsupported_answer,
            skill="FastAPI",
            based_on="Project: API Gateway",
            question_type="Technical",
            difficulty="Medium",
            resume=resume
        )

        # Grounding status must indicate revision due to unsupported tech claims
        self.assertEqual(grounding.badge_variant, "warning")
        self.assertTrue(any("redis" in u.lower() for u in grounding.unsupported_claims))
        self.assertTrue(any("kafka" in u.lower() for u in grounding.unsupported_claims))
        self.assertTrue(any("kubernetes" in u.lower() for u in grounding.unsupported_claims))
        
        # Grounded answer must convert to conditional/approach phrasing
        self.assertTrue("approach" in grounded_ans.lower() or "would" in grounded_ans.lower() or "focus" in grounded_ans.lower())
        self.assertNotIn("i implemented redis caching", grounded_ans.lower())
    def test_13_mock_interview_diverse_question_specific_answers(self):
        """Test that 10 consecutive mock interview questions on the same project generate distinct, intent-specific answers."""
        from backend.app.services.diversity_manager import DiversityManager, MockInterviewSessionTracker
        from backend.app.services.intent_classifier import QuestionIntentClassifier, QuestionIntent

        resume_data = {
            "name": "Jordan Dev",
            "skills": ["Python", "FastAPI", "MySQL"],
            "projects": [
                {
                    "title": "Inventory Management Platform",
                    "description": "Engineered automated stock tracking and inventory reconciliation API using Python and MySQL.",
                    "technologies": ["Python", "FastAPI", "MySQL"],
                    "highlights": ["Built RESTful endpoints with FastAPI", "Optimized MySQL relational queries"]
                }
            ],
            "experience": []
        }

        questions_batch = [
            ("Tell me about your Inventory Management Platform project.", QuestionIntent.PROJECT_OVERVIEW),
            ("Why did you choose MySQL for the Inventory Management Platform?", QuestionIntent.WHY_TECHNOLOGY),
            ("What was the biggest technical challenge you faced in the project?", QuestionIntent.CHALLENGE),
            ("How would you improve the system if you had more time?", QuestionIntent.IMPROVEMENT),
            ("How would you scale the Inventory Management Platform for 10x traffic?", QuestionIntent.SCALABILITY),
            ("How did you design the database schema and queries in MySQL?", QuestionIntent.DATABASE),
            ("How did you optimize performance and reduce latency in the API?", QuestionIntent.PERFORMANCE),
            ("Can you walk me through how you debugged a difficult issue in the project?", QuestionIntent.DEBUGGING),
            ("What was your specific role and key contribution to the project?", QuestionIntent.PROJECT_ROLE),
            ("Tell me about a time you had to deliver under a tight deadline on this project.", QuestionIntent.BEHAVIORAL),
        ]

        session_id = "test-diversity-session"
        MockInterviewSessionTracker.clear_session(session_id)

        generated_answers = []
        detected_intents = []
        openings = []

        for q_text, expected_intent in questions_batch:
            res = self.client.post("/api/interview/answer", json={
                "session_id": session_id,
                "question_id": f"q-{len(generated_answers)}",
                "question_text": q_text,
                "based_on": "Project: Inventory Management Platform",
                "skill": "MySQL",
                "difficulty": "Medium",
                "user_answer": "I worked on this project and handled implementation details.",
                "resume_data": resume_data
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()

            model_ans = data.get("improved_answer", "")
            q_intent = data.get("question_intent", "")
            ans_struct = data.get("answer_structure", "")

            self.assertTrue(len(model_ans) > 40, f"Model answer too short for: {q_text}")
            self.assertEqual(q_intent, expected_intent, f"Expected intent {expected_intent}, got {q_intent} for {q_text}")
            self.assertTrue(bool(ans_struct), f"Missing answer structure for {q_text}")

            first_sentence = model_ans.split(".")[0].strip()
            openings.append(first_sentence)
            generated_answers.append(model_ans)
            detected_intents.append(q_intent)

        # 1. Verify pairwise semantic diversity across all 10 answers
        for i in range(len(generated_answers)):
            for j in range(i + 1, len(generated_answers)):
                sim = DiversityManager.calculate_similarity(generated_answers[i], generated_answers[j])
                self.assertLess(sim, 0.65, f"Answers {i} and {j} are too similar (similarity={sim:.2f}):\nAns {i}: {generated_answers[i]}\nAns {j}: {generated_answers[j]}")

        # 2. Verify all 10 detected intents are unique in this suite
        self.assertEqual(len(set(detected_intents)), 10)

        # 3. Verify no consecutive answers share the exact opening sentence
        for i in range(len(openings) - 1):
            self.assertNotEqual(openings[i], openings[i + 1], f"Consecutive identical openings: {openings[i]}")

        # 4. Verify specific intent question keywords exist in answers
        self.assertTrue(any(w in generated_answers[1].lower() for w in ["choose", "select", "driver", "alternative", "fit"]))
        self.assertTrue(any(w in generated_answers[2].lower() for w in ["hurdle", "roadblock", "obstacle", "diagnos", "challenge"]))
        self.assertTrue(any(w in generated_answers[3].lower() for w in ["limitation", "improve", "time", "enhance", "add"]))
        self.assertTrue(any(w in generated_answers[4].lower() for w in ["scale", "scaling", "volume", "bottleneck", "profil", "index"]))

        print(f"✓ 10 distinct Mock Interview questions on same project successfully generated 10 unique, question-specific model answers.")

    def test_14_document_validation_and_non_resume_rejection(self):
        """Test document validation pipeline: accepts valid resumes and strictly rejects non-resume PDFs."""
        import fitz
        from backend.app.services.document_validator import DocumentValidator

        # 1. Test A: Valid Resume PDF
        resume_doc = fitz.open()
        page = resume_doc.new_page()
        page.insert_text((50, 50), """
Alex Chen
San Francisco, CA | alex.chen@example.com | (555) 234-5678 | github.com/alexchen

PROFESSIONAL SUMMARY
Full-Stack Software Engineer with 3+ years experience building web applications with Python, FastAPI, React, and MySQL.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL, HTML5, CSS3
Frameworks: FastAPI, React, Node.js, Django
Databases: PostgreSQL, MySQL, Redis, MongoDB
DevOps: Docker, Git, CI/CD

WORK EXPERIENCE
Software Engineer | CloudScale Systems (2022 - Present)
- Engineered asynchronous REST APIs using FastAPI and MongoDB serving 50k+ daily active users.
- Built real-time analytics dashboard in React with modular state management.

PROJECTS
Inventory Management Platform | Python, FastAPI, MySQL
- Architected REST API backend with MySQL relational storage and automated stock alerts.

EDUCATION
B.S. in Computer Science | University of California, Berkeley (2022)
        """)
        resume_pdf_bytes = resume_doc.tobytes()

        res = self.client.post(
            "/api/resume/upload",
            files={"file": ("Alex_Chen_Resume.pdf", resume_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(res.status_code, 200, f"Expected 200 for valid resume, got {res.status_code}: {res.text}")
        data = res.json()
        self.assertEqual(data.get("validation_status"), "VALID")
        self.assertGreaterEqual(data.get("resume_confidence", 0), 0.70)
        self.assertTrue(bool(data.get("id")))
        self.assertTrue(bool(data.get("resume_hash")))

        # 2. Test B: Academic / Research Paper (Must be rejected)
        paper_doc = fitz.open()
        p_page = paper_doc.new_page()
        p_page.insert_text((50, 50), """
Deep Residual Learning for Image Recognition
Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun

ABSTRACT
Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs.

1. INTRODUCTION
Deep convolutional neural networks have led to a series of breakthroughs for image classification.
Methodology and Materials: We evaluate our representations on the ImageNet 2012 classification dataset.
Figure 1: Training error and test error on CIFAR-10.
Table 1: Error rates on ImageNet validation set.

REFERENCES
[1] Y. LeCun, B. Boser, J. S. Denker, et al. Backpropagation applied to handwritten zip code recognition. Neural Computation, 1989.
[2] A. Krizhevsky, I. Sutskever, and G. E. Hinton. Imagenet classification with deep convolutional neural networks. In NIPS, 2012.
        """)
        paper_pdf_bytes = paper_doc.tobytes()

        res_paper = self.client.post(
            "/api/resume/upload",
            files={"file": ("Deep_Learning_Paper.pdf", paper_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(res_paper.status_code, 422, "Academic paper should be rejected with 422")
        self.assertIn("not a resume", res_paper.text.lower())

        # 3. Test C: Course Certificate (Must be rejected)
        cert_doc = fitz.open()
        c_page = cert_doc.new_page()
        c_page.insert_text((50, 50), """
CERTIFICATE OF COMPLETION
This is to certify that
Alex Chen
has successfully completed the online training course
Full Stack Web Development with React and Python
Certificate ID: CERT-8948291-XY
Verification Code: VERIFY-9821
Authorized Signatory: John Doe, Lead Instructor
Awarded on: March 15, 2024
        """)
        cert_pdf_bytes = cert_doc.tobytes()

        res_cert = self.client.post(
            "/api/resume/upload",
            files={"file": ("Course_Certificate.pdf", cert_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(res_cert.status_code, 422, "Certificate should be rejected with 422")
        self.assertIn("not a resume", res_cert.text.lower())

        # 4. Test D: Project Documentation / Thesis Report (Must be rejected)
        report_doc = fitz.open()
        r_page = report_doc.new_page()
        r_page.insert_text((50, 50), """
A PROJECT REPORT ON
ONLINE INVENTORY MANAGEMENT SYSTEM
Submitted in partial fulfillment of the requirements for the degree of
Bachelor of Technology in Computer Science and Engineering
Department of Computer Science
Academic Year 2023-2024
Under the guidance of: Dr. Robert Vance
TABLE OF CONTENTS
Chapter 1: Introduction
Chapter 2: Literature Survey
Chapter 3: System Requirements Specification (SRS Document)
Chapter 4: Class Diagrams and Data Flow Diagrams
        """)
        report_pdf_bytes = report_doc.tobytes()

        res_report = self.client.post(
            "/api/resume/upload",
            files={"file": ("Project_Report.pdf", report_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(res_report.status_code, 422, "Project report should be rejected with 422")
        self.assertIn("not a resume", res_report.text.lower())

        # 5. Test E: Scanned / Empty PDF (Must be rejected)
        empty_doc = fitz.open()
        empty_doc.new_page()
        empty_bytes = empty_doc.tobytes()

        res_empty = self.client.post(
            "/api/resume/upload",
            files={"file": ("Scanned_Scan.pdf", empty_bytes, "application/pdf")}
        )
        self.assertEqual(res_empty.status_code, 422, "Empty/scanned document should be rejected with 422")
        self.assertIn("text", res_empty.text.lower())

        print("✓ Strict multi-signal document validation verified across Resumes, Papers, Certificates, Reports, and Scanned PDFs.")

    def test_15_active_resume_id_isolation_and_no_context_leakage(self):
        """Test that every valid upload receives a unique ID/hash and question generation strictly isolates context."""
        import fitz

        # Create Resume A (Full Stack: Python, React, MongoDB)
        doc_a = fitz.open()
        p_a = doc_a.new_page()
        p_a.insert_text((50, 50), """
Alice Walker
Email: alice.w@example.com | Phone: (555) 111-2222 | San Francisco, CA

SUMMARY
Frontend Engineer with React and Next.js expertise.

TECHNICAL SKILLS
Languages: JavaScript, TypeScript, HTML, CSS
Frameworks: React, Next.js, Tailwind CSS

EXPERIENCE
Frontend Developer | WebCorp (2022 - 2024)
- Developed responsive web interfaces in React.

EDUCATION
B.S. in Computer Science | Stanford University (2022)
        """)
        bytes_a = doc_a.tobytes()

        # Create Resume B (Backend: Go, Docker, Kubernetes - same filename 'resume.pdf')
        doc_b = fitz.open()
        p_b = doc_b.new_page()
        p_b.insert_text((50, 50), """
Bob Miller
Email: bob.m@example.com | Phone: (555) 333-4444 | Seattle, WA

SUMMARY
Cloud Systems Engineer specializing in Go and Kubernetes infrastructure.

TECHNICAL SKILLS
Languages: Go, Golang, SQL, Bash
DevOps: Docker, Kubernetes, Terraform, AWS

EXPERIENCE
DevOps Engineer | CloudInfra Inc (2021 - Present)
- Managed production Kubernetes clusters and automated CI/CD pipelines.

EDUCATION
B.S. in Software Engineering | University of Washington (2021)
        """)
        bytes_b = doc_b.tobytes()

        # Upload Resume A with filename 'resume.pdf'
        res_a = self.client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", bytes_a, "application/pdf")}
        )
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.json()

        # Upload Resume B with SAME filename 'resume.pdf'
        res_b = self.client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", bytes_b, "application/pdf")}
        )
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.json()

        # 1. Verify different hashes and different IDs despite identical filename
        self.assertNotEqual(data_a["id"], data_b["id"])
        self.assertNotEqual(data_a["resume_hash"], data_b["resume_hash"])

        # 2. Verify questions generated for Resume A contain resume_id = data_a['id']
        q_res_a = self.client.post("/api/questions/generate", json={
            "session_id": "session-a",
            "resume_data": data_a,
            "count": 3
        })
        self.assertEqual(q_res_a.status_code, 200)
        qs_a = q_res_a.json()
        for q in qs_a:
            self.assertEqual(q["resume_id"], data_a["id"])

        # 3. Verify questions generated for Resume B contain resume_id = data_b['id']
        q_res_b = self.client.post("/api/questions/generate", json={
            "session_id": "session-b",
            "resume_data": data_b,
            "count": 3
        })
        self.assertEqual(q_res_b.status_code, 200)
        qs_b = q_res_b.json()
        for q in qs_b:
            self.assertEqual(q["resume_id"], data_b["id"])

        # 4. Verify question content is isolated: Resume B questions must NOT mention React/Next.js
        b_skills_joined = " ".join([q["question"] + " " + q.get("skill", "") for q in qs_b]).lower()
        self.assertNotIn("react", b_skills_joined)

        print("✓ Active Resume ID isolation, SHA content hashing, and zero cross-resume contamination verified.")

    def test_16_clean_analytics_and_zero_hardcoded_defaults(self):
        """Verify analytics endpoint returns 0s and empty lists for empty sessions with zero hardcoded defaults."""
        res = self.client.get("/api/analytics?session_id=brand-new-empty-session")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Must NOT return fake baseline scores
        self.assertEqual(data["interview_readiness_score"], 0)
        self.assertEqual(data["questions_attempted"], 0)
        self.assertEqual(data["correct_answers"], 0)
        self.assertEqual(data["technical_score"], 0)
        self.assertEqual(data["communication_score"], 0)
        self.assertEqual(data["average_interview_score"], 0)

        # Must NOT return hardcoded strings
        topics_str = str(data.get("weak_areas", [])) + str(data.get("strong_areas", []))
        self.assertNotIn("System Design Trade-offs", topics_str)
        self.assertNotIn("Deep Caching & Redis", topics_str)
        self.assertNotIn("Python Core & APIs", topics_str)
        self.assertNotIn("Frontend Component Design", topics_str)
        self.assertEqual(len(data.get("weak_areas", [])), 0)
        self.assertEqual(len(data.get("strong_areas", [])), 0)
        self.assertEqual(len(data.get("score_trends", [])), 0)

        print("✓ Zero hardcoded analytics defaults verified on empty sessions.")

    def test_17_resume_score_and_job_match_analytics(self):
        """Verify end-to-end Resume Score, Job Match Score, session persistence, and Analytics calculation."""
        import uuid
        session_id = f"test-scoring-session-{uuid.uuid4().hex[:6]}"
        self.client.post("/api/interview/history/clear", json={"session_id": session_id})
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        sample_jd = self.client.get("/api/job/samples").json()[0]

        # 1. Analyze Resume Score
        analyze_res = self.client.post("/api/resume/analyze", json=sample_resume)
        self.assertEqual(analyze_res.status_code, 200)
        score_data = analyze_res.json()["score"]
        self.assertGreaterEqual(score_data["overall_score"], 60)
        self.assertGreaterEqual(score_data["skills_score"], 50)
        self.assertGreaterEqual(score_data["projects_score"], 50)
        self.assertGreaterEqual(score_data["completeness_score"], 80)
        self.assertTrue(len(score_data["strengths"]) > 0)
        self.assertTrue(len(score_data["rationale"]) > 0)

        # 2. Persist resume & score to session
        put_res = self.client.put(f"/api/sessions/{session_id}", json={
            "id": session_id,
            "name": "Scoring Test Session",
            "resume": sample_resume,
            "resume_score": score_data,
            "jd": None,
            "match": None
        })
        self.assertEqual(put_res.status_code, 200)

        # 3. Analytics with Resume only (no JD)
        analytics_res_1 = self.client.get(f"/api/analytics?session_id={session_id}")
        self.assertEqual(analytics_res_1.status_code, 200)
        data_1 = analytics_res_1.json()
        self.assertEqual(data_1["resume_score"], score_data["overall_score"])
        self.assertIsNone(data_1["jd_match_percentage"])
        self.assertEqual(data_1["interview_readiness_score"], score_data["overall_score"])
        self.assertGreater(len(data_1["category_performance"]), 0)

        # 4. Perform Job Match
        match_res = self.client.post("/api/match", json={"resume": sample_resume, "jd": sample_jd})
        self.assertEqual(match_res.status_code, 200)
        match_data = match_res.json()
        self.assertGreaterEqual(match_data["match_percentage"], 50)
        self.assertGreater(len(match_data["matching_skills"]), 0)

        # 5. Persist JD and Match to session
        put_res_2 = self.client.put(f"/api/sessions/{session_id}", json={
            "jd": sample_jd,
            "match": match_data
        })
        self.assertEqual(put_res_2.status_code, 200)

        # 6. Analytics with Resume + JD
        analytics_res_2 = self.client.get(f"/api/analytics?session_id={session_id}")
        self.assertEqual(analytics_res_2.status_code, 200)
        data_2 = analytics_res_2.json()
        self.assertEqual(data_2["resume_score"], score_data["overall_score"])
        self.assertEqual(data_2["jd_match_percentage"], match_data["match_percentage"])
        expected_readiness = int((score_data["overall_score"] * 0.5) + (match_data["match_percentage"] * 0.5))
        self.assertEqual(data_2["interview_readiness_score"], expected_readiness)

        # 7. Submit answer and verify combined analytics
        eval_res = self.client.post("/api/interview/answer", json={
            "session_id": session_id,
            "question_id": "q-scoring-1",
            "question_text": "Explain indexing in MongoDB.",
            "based_on": "MongoDB",
            "skill": "MongoDB",
            "difficulty": "Medium",
            "user_answer": "MongoDB uses B-tree indexes to accelerate queries. Compound indexes and explain plans help query optimization.",
            "expected_points": ["B-tree index", "Query acceleration", "Execution plan"],
            "sample_answer": "MongoDB indexes utilize B-trees to drastically reduce query latency.",
            "resume_data": sample_resume,
            "jd_data": sample_jd
        })
        self.assertEqual(eval_res.status_code, 200)

        analytics_res_3 = self.client.get(f"/api/analytics?session_id={session_id}")
        self.assertEqual(analytics_res_3.status_code, 200)
        data_3 = analytics_res_3.json()
        self.assertEqual(data_3["questions_attempted"], 1)
        self.assertGreater(data_3["technical_score"], 0)
        self.assertGreater(data_3["interview_readiness_score"], 0)
        self.assertEqual(len(data_3["score_trends"]), 1)

        print("✓ End-to-end Resume Score, Job Match Score, and Analytics data flow verified.")

    def test_18_session_state_lifecycle_and_clean_startup(self):
        """Verify session state isolation, zero stale data leakage on fresh session, and clean reset."""
        import uuid
        sid_fresh = f"fresh-session-{uuid.uuid4().hex[:8]}"
        sid_a = f"session-a-{uuid.uuid4().hex[:8]}"
        sid_b = f"session-b-{uuid.uuid4().hex[:8]}"

        # 1. Fresh session must return clean empty analytics with 0 readiness and no fallback to other sessions
        fresh_analytics = self.client.get(f"/api/analytics?session_id={sid_fresh}").json()
        self.assertIsNone(fresh_analytics["resume_score"])
        self.assertIsNone(fresh_analytics["jd_match_percentage"])
        self.assertEqual(fresh_analytics["interview_readiness_score"], 0)
        self.assertEqual(fresh_analytics["questions_attempted"], 0)
        self.assertEqual(len(fresh_analytics["weak_areas"]), 0)
        self.assertEqual(len(fresh_analytics["strong_areas"]), 0)
        self.assertEqual(len(fresh_analytics["score_trends"]), 0)

        # 2. Upload resume into Session A
        sample_resume = self.client.get("/api/resume/samples").json()[0]
        put_a = self.client.put(f"/api/sessions/{sid_a}", json={
            "id": sid_a,
            "name": "Session A",
            "resume": sample_resume
        })
        self.assertEqual(put_a.status_code, 200)

        # Session A should show resume score
        analytics_a = self.client.get(f"/api/analytics?session_id={sid_a}").json()
        self.assertIsNotNone(analytics_a["resume_score"])
        self.assertGreater(analytics_a["interview_readiness_score"], 0)

        # 3. Session B must remain completely clean (no leakage from Session A)
        put_b = self.client.put(f"/api/sessions/{sid_b}", json={
            "id": sid_b,
            "name": "Session B",
            "resume": None,
            "resume_score": None,
            "jd": None,
            "match": None,
            "questions": []
        })
        self.assertEqual(put_b.status_code, 200)

        analytics_b = self.client.get(f"/api/analytics?session_id={sid_b}").json()
        self.assertIsNone(analytics_b["resume_score"])
        self.assertIsNone(analytics_b["jd_match_percentage"])
        self.assertEqual(analytics_b["interview_readiness_score"], 0)
        self.assertEqual(analytics_b["questions_attempted"], 0)

        # 4. History isolation
        eval_res = self.client.post("/api/interview/answer", json={
            "session_id": sid_a,
            "question_id": "q-iso-1",
            "question_text": "Describe microservices architecture.",
            "based_on": "Microservices",
            "skill": "Microservices",
            "difficulty": "Medium",
            "user_answer": "Microservices decompose applications into independently deployable loosely coupled services communicating via APIs.",
            "expected_points": ["Independent deployment", "Loose coupling", "API communication"],
            "sample_answer": "Microservices structure applications as discrete autonomous services.",
            "resume_data": sample_resume
        })
        self.assertEqual(eval_res.status_code, 200)

        # Session A has history = 1, Session B has history = 0
        hist_a = self.client.get(f"/api/interview/history?session_id={sid_a}").json()
        hist_b = self.client.get(f"/api/interview/history?session_id={sid_b}").json()
        self.assertEqual(len(hist_a), 1)
        self.assertEqual(len(hist_b), 0)

        # 5. Clear resume in Session A
        clear_res = self.client.put(f"/api/sessions/{sid_a}", json={
            "id": sid_a,
            "resume": None,
            "resume_score": None,
            "jd": None,
            "match": None,
            "questions": []
        })
        self.assertEqual(clear_res.status_code, 200)

        cleared_sess_a = self.client.get(f"/api/sessions/{sid_a}").json()
        self.assertIsNone(cleared_sess_a["resume"])
        self.assertIsNone(cleared_sess_a["resume_score"])

        print("✓ Session lifecycle, state isolation, and clean startup verified.")

    def test_19_invalid_file_uploads_and_error_handling(self):
        """
        Verify that all invalid upload scenarios:
        1. Non-PDF files (TXT, DOCX, PNG, JPG, JSON) -> 400 Bad Request with clear message
        2. Empty files (0 bytes) -> 400 Bad Request
        3. Corrupted PDF files (non-PDF binary stream) -> 400 Bad Request
        4. Scanned / image-only PDFs -> 400 or 422
        5. Unrelated PDFs (academic paper, certificate, project report, invoice, textbook) -> 422 / 400
        6. Password-protected PDFs -> 400 Bad Request
        7. Valid resume PDF after invalid uploads -> 200 OK with parsed data
        8. Consecutive multiple invalid uploads -> all rejected gracefully without 500 errors
        """
        import fitz

        # 1. Non-PDF TXT file
        res_txt = self.client.post(
            "/api/resume/upload",
            files={"file": ("my_resume.txt", b"Software Engineer with Python and React experience", "text/plain")}
        )
        self.assertEqual(res_txt.status_code, 400)
        self.assertIn("Invalid file", res_txt.json()["detail"])

        # 2. Non-PDF DOCX file
        res_docx = self.client.post(
            "/api/resume/upload",
            files={"file": ("resume.docx", b"PK\x03\x04fake docx binary data", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        self.assertEqual(res_docx.status_code, 400)
        self.assertIn("Invalid file", res_docx.json()["detail"])

        # 3. Non-PDF Image file (PNG)
        res_png = self.client.post(
            "/api/resume/upload",
            files={"file": ("resume_screenshot.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png")}
        )
        self.assertEqual(res_png.status_code, 400)
        self.assertIn("Invalid file", res_png.json()["detail"])

        # 4. Empty file (0 bytes)
        res_empty = self.client.post(
            "/api/resume/upload",
            files={"file": ("empty_resume.pdf", b"", "application/pdf")}
        )
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("empty", res_empty.json()["detail"].lower())

        # 5. Corrupted PDF (random garbage bytes with .pdf extension)
        res_corrupt = self.client.post(
            "/api/resume/upload",
            files={"file": ("corrupted.pdf", b"This is not a real PDF file header", "application/pdf")}
        )
        self.assertEqual(res_corrupt.status_code, 400)
        self.assertIn("Invalid file", res_corrupt.json()["detail"])

        # 6. Unrelated PDF: Invoice / Financial Document
        invoice_doc = fitz.open()
        inv_page = invoice_doc.new_page()
        inv_page.insert_text((50, 50), """
TAX INVOICE
Invoice No: INV-2024-00891
Bill To: Acme Global Corporation
GSTIN: 29ABCDE1234F1Z5
Date: 12/04/2024

Items:
1. Enterprise Cloud Subscription - Subtotal: $4,500.00
2. Support & Maintenance - Subtotal: $1,200.00
Total Amount Due: $5,700.00
Payment Receipt: Bank transfer to Account Number 987654321
Transaction ID: TXN-893274921
        """)
        inv_bytes = invoice_doc.tobytes()

        res_inv = self.client.post(
            "/api/resume/upload",
            files={"file": ("Invoice_April2024.pdf", inv_bytes, "application/pdf")}
        )
        self.assertEqual(res_inv.status_code, 422)
        self.assertIn("Invalid file", res_inv.json()["detail"])
        self.assertIn("invoice", res_inv.json()["detail"].lower())

        # 7. Unrelated PDF: Textbook / Reference Manual
        tb_doc = fitz.open()
        tb_page = tb_doc.new_page()
        tb_page.insert_text((50, 50), """
Operating Systems: Principles and Practice
Second Edition
Published by Academic Press
ISBN: 978-0-123456-78-9
All Rights Reserved.

TABLE OF CONTENTS
Chapter 1: Hardware and the Kernel
Chapter 2: Processes and Threads
Chapter 3: Memory Management
Chapter 4: File Systems
Preface: This textbook is designed for an introductory course in operating systems.
        """)
        tb_bytes = tb_doc.tobytes()

        res_tb = self.client.post(
            "/api/resume/upload",
            files={"file": ("Operating_Systems_Textbook.pdf", tb_bytes, "application/pdf")}
        )
        self.assertEqual(res_tb.status_code, 422)
        self.assertIn("Invalid file", res_tb.json()["detail"])

        # 8. Unrelated PDF: Examination Question Paper
        qp_doc = fitz.open()
        qp_page = qp_doc.new_page()
        qp_page.insert_text((50, 50), """
University Examination 2024
Question Paper: Data Structures and Algorithms
Time: 3 Hours | Max Marks: 100
Roll No: __________________

Instructions to candidates:
Answer any five questions. All questions carry equal marks.

Section - A
Q.1 Explain the difference between B-Trees and B+ Trees with suitable diagrams.
Q.2 Write an algorithm for Dijkstra's shortest path finding method.
        """)
        qp_bytes = qp_doc.tobytes()

        res_qp = self.client.post(
            "/api/resume/upload",
            files={"file": ("DSA_Question_Paper.pdf", qp_bytes, "application/pdf")}
        )
        self.assertEqual(res_qp.status_code, 422)
        self.assertIn("Invalid file", res_qp.json()["detail"])

        # 9. Multiple consecutive invalid uploads do not break the server
        for i in range(5):
            res_repeat = self.client.post(
                "/api/resume/upload",
                files={"file": (f"bad_file_{i}.txt", b"random text", "text/plain")}
            )
            self.assertEqual(res_repeat.status_code, 400)

        # 10. Valid resume PDF upload immediately succeeding invalid attempts
        valid_doc = fitz.open()
        v_page = valid_doc.new_page()
        v_page.insert_text((50, 50), """
David Miller
Seattle, WA | david.m@example.com | (555) 987-6543 | linkedin.com/in/davidmiller

PROFESSIONAL SUMMARY
Experienced Software Engineer with 4 years designing distributed Python microservices and React frontends.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Frameworks: FastAPI, Django, React, Node.js
Databases: PostgreSQL, Redis, MongoDB
DevOps: Docker, Git, CI/CD, AWS

WORK EXPERIENCE
Software Engineer | TechCore Systems (2021 - Present)
- Developed asynchronous REST API endpoints using FastAPI and PostgreSQL.
- Optimized Redis caching layer reducing database read load by 60%.

PROJECTS
Event Stream Processing Engine | Python, FastAPI, Redis
- Implemented real-time Kafka consumer and event processing pipeline.

EDUCATION
B.S. in Computer Science | University of Washington (2021)
        """)
        valid_pdf_bytes = valid_doc.tobytes()

        res_valid = self.client.post(
            "/api/resume/upload",
            files={"file": ("David_Miller_Resume.pdf", valid_pdf_bytes, "application/pdf")}
        )
        self.assertEqual(res_valid.status_code, 200)
        valid_data = res_valid.json()
        self.assertEqual(valid_data["validation_status"], "VALID")
        self.assertIn("Python", valid_data["skills"])
        self.assertEqual(valid_data["name"], "David Miller")

        print("✓ All 10 invalid upload and recovery scenarios tested successfully without crashes.")

    def test_20_ephemeral_sessions_clear_and_default_reset(self):
        """Verify that creating custom sessions and calling /reset wipes all custom sessions and returns ONLY default."""
        import uuid
        # 1. Create custom sessions
        sess_1_id = f"custom-session-{uuid.uuid4().hex[:6]}"
        sess_2_id = f"custom-session-{uuid.uuid4().hex[:6]}"
        self.client.post("/api/sessions", json={"id": sess_1_id, "name": "session 1"})
        self.client.post("/api/sessions", json={"id": sess_2_id, "name": "session 2"})

        # Verify they are present
        list_res = self.client.get("/api/sessions").json()
        ids = [s["id"] for s in list_res]
        self.assertIn(sess_1_id, ids)
        self.assertIn(sess_2_id, ids)

        # 2. Trigger reset endpoint (simulating application startup / fresh launch)
        reset_res = self.client.post("/api/sessions/reset")
        self.assertEqual(reset_res.status_code, 200)
        reset_sessions = reset_res.json()

        # 3. Must contain only the default session
        self.assertEqual(len(reset_sessions), 1)
        self.assertEqual(reset_sessions[0]["id"], "default")
        self.assertEqual(reset_sessions[0]["name"], "Default Interview Prep")
        self.assertIsNone(reset_sessions[0]["resume"])

        # 4. Verify subsequent GET /api/sessions also returns only default session
        final_list = self.client.get("/api/sessions").json()
        self.assertEqual(len(final_list), 1)
        self.assertEqual(final_list[0]["id"], "default")
        print("✓ Ephemeral sessions clear and default reset verified.")

    def test_21_independent_evaluation_for_repeated_question_attempts(self):
        """
        Acceptance Test:
        1. Ask Question A.
        2. Submit poor answer -> verify low score.
        3. Repeat Question A.
        4. Submit comprehensive technical answer -> verify independent high score (80+).
        5. Repeat Question A a third time with poor answer -> verify score drops independently.
        6. Switch to Question B -> verify independent evaluation.
        7. Verify history preserves all distinct attempt records without overwriting.
        """
        import uuid
        session_id = f"test-repeat-sess-{uuid.uuid4().hex[:6]}"
        question_a = "How did you use OpenCV in your computer vision or image processing pipeline?"
        question_a_id = "q-opencv-01"

        # 1. Attempt 1: Poor/echo answer to Question A
        attempt_1_id = f"attempt_1_{uuid.uuid4().hex[:6]}"
        ans_1 = self.client.post("/api/interview/answer", json={
            "session_id": session_id,
            "question_id": question_a_id,
            "question_attempt_id": attempt_1_id,
            "question_text": question_a,
            "skill": "OpenCV",
            "difficulty": "Medium",
            "based_on": "Resume Skill: OpenCV",
            "user_answer": "how did you use open CV in your computer version are image processing pipeline submitting"
        })
        self.assertEqual(ans_1.status_code, 200)
        data_1 = ans_1.json()
        self.assertEqual(data_1["question_attempt_id"], attempt_1_id)
        self.assertLessEqual(data_1["overall_score"], 35)

        # 2. Attempt 2: Same Question A with high-quality, comprehensive answer
        attempt_2_id = f"attempt_2_{uuid.uuid4().hex[:6]}"
        ans_2 = self.client.post("/api/interview/answer", json={
            "session_id": session_id,
            "question_id": question_a_id,
            "question_attempt_id": attempt_2_id,
            "question_text": question_a,
            "skill": "OpenCV",
            "difficulty": "Medium",
            "based_on": "Resume Skill: OpenCV",
            "user_answer": (
                "In our computer vision pipeline, we used cv2.VideoCapture for frame ingestion and applied Gaussian blur "
                "and morphological filtering to reduce camera noise. We isolated regions of interest (ROI) to reduce downstream pixel "
                "processing overhead by 50%, and executed contour detection via findContours and bounding rectangles to track objects at steady 30+ FPS."
            )
        })
        self.assertEqual(ans_2.status_code, 200)
        data_2 = ans_2.json()
        self.assertEqual(data_2["question_attempt_id"], attempt_2_id)
        self.assertGreaterEqual(data_2["overall_score"], 80)
        self.assertIn("Exceptional" in data_2["verdict_rating"] or "Strong" in data_2["verdict_rating"], [True])

        # 3. Attempt 3: Same Question A with poor answer again
        attempt_3_id = f"attempt_3_{uuid.uuid4().hex[:6]}"
        ans_3 = self.client.post("/api/interview/answer", json={
            "session_id": session_id,
            "question_id": question_a_id,
            "question_attempt_id": attempt_3_id,
            "question_text": question_a,
            "skill": "OpenCV",
            "difficulty": "Medium",
            "based_on": "Resume Skill: OpenCV",
            "user_answer": "I used it to read images in python."
        })
        self.assertEqual(ans_3.status_code, 200)
        data_3 = ans_3.json()
        self.assertEqual(data_3["question_attempt_id"], attempt_3_id)
        self.assertLessEqual(data_3["overall_score"], 45)

        # 4. Switch to Question B (SQL indexing)
        question_b = "How do B-tree indexes and query execution plans optimize SQL database performance?"
        attempt_b_id = f"attempt_b_{uuid.uuid4().hex[:6]}"
        ans_b = self.client.post("/api/interview/answer", json={
            "session_id": session_id,
            "question_id": "q-sql-02",
            "question_attempt_id": attempt_b_id,
            "question_text": question_b,
            "skill": "SQL",
            "difficulty": "Medium",
            "based_on": "Resume Skill: SQL",
            "user_answer": (
                "In PostgreSQL, we optimize queries by analyzing EXPLAIN ANALYZE execution plans to verify index seeks over sequential scans. "
                "We establish covering B-tree indexes on foreign keys to accelerate relational joins, and configure read committed isolation "
                "to prevent deadlocks while maintaining ACID consistency with sub-20ms query latency."
            )
        })
        self.assertEqual(ans_b.status_code, 200)
        data_b = ans_b.json()
        self.assertEqual(data_b["question_attempt_id"], attempt_b_id)
        self.assertGreaterEqual(data_b["overall_score"], 80)

        # 5. Verify history collection in DB maintains all 4 distinct attempts
        history_res = self.client.get(f"/api/interview/history?session_id={session_id}")
        self.assertEqual(history_res.status_code, 200)
        history = history_res.json()
        self.assertEqual(len(history), 4)

        attempt_ids_in_history = [h.get("question_attempt_id") for h in history]
        self.assertIn(attempt_1_id, attempt_ids_in_history)
        self.assertIn(attempt_2_id, attempt_ids_in_history)
        self.assertIn(attempt_3_id, attempt_ids_in_history)
        self.assertIn(attempt_b_id, attempt_ids_in_history)

        print("✓ Independent evaluation for repeated question attempts and session history verified.")

if __name__ == "__main__":
    unittest.main()



