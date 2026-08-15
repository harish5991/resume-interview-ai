from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import JobDescriptionAnalysis
from backend.app.services.matcher import JDMatcher
from backend.app.database.db import db_manager

router = APIRouter(prefix="/job", tags=["Job Description"])

SAMPLE_JDS = [
    {
        "id": "jd-fullstack",
        "title": "Full Stack Engineer (React, Python & Cloud)",
        "company": "NextGen Technologies",
        "experience_years": "2-4+ years",
        "required_skills": ["Python", "FastAPI", "React", "TypeScript", "MongoDB", "PostgreSQL", "Docker", "REST APIs"],
        "preferred_skills": ["AWS", "Redis", "CI/CD", "Tailwind CSS", "Microservices"],
        "responsibilities": [
            "Design and build responsive frontend user interfaces using React and modern CSS.",
            "Architect robust RESTful APIs in Python (FastAPI/Django) and manage database schema migrations.",
            "Write comprehensive automated unit and integration tests.",
            "Collaborate with product and design teams in an agile environment."
        ],
        "technologies": ["Python", "FastAPI", "React", "TypeScript", "MongoDB", "PostgreSQL", "Docker", "REST APIs", "AWS", "Redis", "CI/CD"],
        "keywords": ["FastAPI", "React", "Python", "MongoDB", "REST APIs", "Docker", "TypeScript", "PostgreSQL", "Agile"],
        "summary": "Seeking a talented Full Stack Developer to build modern cloud applications using React, Python, and MongoDB.",
        "raw_text": "Full Stack Engineer (React, Python & Cloud) at NextGen Technologies\nLocation: Remote / Hybrid\nExperience: 2-4+ years\n\nJob Summary:\nWe are looking for a passionate Full Stack Engineer proficient in React and Python/FastAPI to design, build, and maintain high-performance web applications.\n\nRequired Qualifications:\n• Strong proficiency with Python and modern web frameworks like FastAPI or Django\n• Hands-on experience building frontend web applications with React and TypeScript\n• Solid understanding of SQL (PostgreSQL) and NoSQL (MongoDB) databases\n• Experience with REST APIs, containerization using Docker, and Git\n\nPreferred Qualifications:\n• Experience with AWS cloud infrastructure and Redis caching\n• Familiarity with CI/CD automation pipelines and Tailwind CSS\n\nResponsibilities:\n• Develop modular web components in React and clean REST endpoints in FastAPI\n• Optimize database query performance and maintain data integrity\n• Participate in code reviews and agile sprints"
    },
    {
        "id": "jd-data-analyst",
        "title": "Data Analyst & Business Intelligence Specialist",
        "company": "Insight Analytics Corp",
        "experience_years": "1-3+ years",
        "required_skills": ["Python", "SQL", "Power BI", "Tableau", "Pandas", "Data Analysis"],
        "preferred_skills": ["PostgreSQL", "Scikit-Learn", "Machine Learning", "Excel"],
        "responsibilities": [
            "Build interactive dashboards and KPI reports in Power BI and Tableau.",
            "Write complex SQL queries and data transformation scripts in Python (Pandas/NumPy).",
            "Perform statistical analysis to identify trends and operational bottlenecks.",
            "Present actionable findings to executive stakeholders."
        ],
        "technologies": ["Python", "SQL", "Power BI", "Tableau", "Pandas", "PostgreSQL", "Data Analysis"],
        "keywords": ["SQL", "Power BI", "Tableau", "Python", "Pandas", "Dashboards", "Metrics", "Analytics"],
        "summary": "Join our analytics team to build data pipelines, interactive dashboards in Power BI and Tableau, and deliver business insights.",
        "raw_text": "Data Analyst & Business Intelligence Specialist at Insight Analytics Corp\nExperience: 1-3+ years\n\nRequirements:\n• Strong proficiency in SQL for extracting and aggregating complex datasets\n• Proven experience creating dashboards with Power BI and Tableau\n• Working knowledge of Python and Pandas for data manipulation\n• Excellent communication skills for presenting analytical findings\n\nResponsibilities:\n• Create automated reporting dashboards for business leadership\n• Identify patterns and KPI trends using statistical analysis"
    }
]

@router.get("/samples")
async def get_sample_jds():
    return SAMPLE_JDS

@router.post("/analyze", response_model=JobDescriptionAnalysis)
async def analyze_job(payload: dict = Body(...)):
    text = payload.get("text", "")
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Please provide a valid job description text (minimum 10 characters).")
    
    analysis = JDMatcher.analyze_job_description(text)
    
    col = db_manager.get_collection("job_descriptions")
    await col.insert_one(analysis.model_dump())

    return analysis
