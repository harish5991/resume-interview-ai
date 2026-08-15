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
        eval_payload = {
            "session_id": "test-session",
            "question_id": "q-test-1",
            "question_text": "Why did you choose MongoDB for your Resume Interview AI project?",
            "based_on": "Project: Resume Interview AI",
            "skill": "MongoDB",
            "difficulty": "Medium",
            "user_answer": "We chose MongoDB because of its flexible BSON document schema, which allowed us to store complex parsed resumes with nested projects, skills, and experience without rigid schema migrations. We also created indexes on user and session IDs for sub-50ms query response times.",
            "expected_points": ["Flexible schema", "BSON documents", "Indexing performance"]
        }

        res = self.client.post("/api/interview/answer", json=eval_payload)
        self.assertEqual(res.status_code, 200)
        eval_data = res.json()
        self.assertGreaterEqual(eval_data["overall_score"], 60)
        self.assertIn("strengths", eval_data)
        self.assertIn("improved_answer", eval_data)
        self.assertIn("next_recommended_difficulty", eval_data)
        print("✓ 6-Axis Answer Evaluation & Adaptive Difficulty verified. Score:", eval_data["overall_score"])

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

if __name__ == "__main__":
    unittest.main()
