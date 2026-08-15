import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.app.schemas.models import ExtractedResume, ResumeScoreBreakdown
from backend.app.services.parser import ResumeParser
from backend.app.database.db import db_manager

router = APIRouter(prefix="/resume", tags=["Resume"])

SAMPLE_RESUMES = [
    {
        "id": "sample-fullstack",
        "title": "Alex Chen — Full Stack Developer (React & Python)",
        "name": "Alex Chen",
        "email": "alex.chen@example.com",
        "phone": "+1 (555) 234-5678",
        "location": "San Francisco, CA",
        "summary": "Full Stack Software Engineer with 3+ years experience building scalable web applications using React, Python, FastAPI, and MongoDB.",
        "skills": ["Python", "JavaScript", "TypeScript", "React", "FastAPI", "Node.js", "MongoDB", "PostgreSQL", "Docker", "Git", "REST APIs", "Tailwind CSS"],
        "skill_categories": {
            "Languages": ["Python", "JavaScript", "TypeScript"],
            "Frontend": ["React", "Tailwind CSS"],
            "Backend & APIs": ["FastAPI", "Node.js", "REST APIs"],
            "Databases": ["MongoDB", "PostgreSQL"],
            "Cloud & DevOps": ["Docker", "Git"]
        },
        "experience": [
            {
                "role": "Full Stack Engineer",
                "company": "CloudScale Systems",
                "duration": "2022 - Present",
                "location": "San Francisco, CA",
                "responsibilities": [
                    "Engineered asynchronous REST APIs using FastAPI and MongoDB serving 50k+ daily active users.",
                    "Built real-time dashboard in React with modular state management and responsive styling.",
                    "Containerized microservices using Docker and implemented CI/CD deployment pipelines."
                ],
                "technologies": ["Python", "FastAPI", "React", "MongoDB", "Docker"]
            }
        ],
        "projects": [
            {
                "title": "Resume Interview AI",
                "description": "An AI-powered interview preparation platform that analyzes candidate resumes and generates grounded, explainable questions with adaptive mock interview scoring.",
                "technologies": ["Python", "FastAPI", "React", "MongoDB", "Tailwind CSS"],
                "highlights": [
                    "Implemented TF-IDF cosine matching and PyMuPDF text extraction pipeline.",
                    "Designed 6-axis answer evaluation system with dynamic difficulty scaling.",
                    "Built clean responsive frontend with Recharts analytics and PDF report export."
                ]
            },
            {
                "title": "Distributed Task Queue",
                "description": "High-throughput asynchronous job processing system with Redis-backed message broker and worker pooling.",
                "technologies": ["Python", "Redis", "Docker", "PostgreSQL"],
                "highlights": [
                    "Handled 10k messages/minute with automatic retry and dead-letter queue recovery.",
                    "Implemented token-bucket rate limiting middleware to prevent worker starvation."
                ]
            }
        ],
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "University of California, Berkeley",
                "year": "2022"
            }
        ],
        "certifications": [
            {"name": "AWS Certified Solutions Architect — Associate"}
        ],
        "achievements": [
            "1st Place Winner at Berkeley AI Hackathon 2023",
            "Published open-source React component with 400+ GitHub stars"
        ],
        "raw_text": "Alex Chen\nFull Stack Software Engineer\nalex.chen@example.com | San Francisco, CA\n\nSKILLS\nLanguages: Python, JavaScript, TypeScript\nFrontend: React, Tailwind CSS\nBackend: FastAPI, Node.js, REST APIs\nDatabases: MongoDB, PostgreSQL\nDevOps: Docker, Git\n\nEXPERIENCE\nFull Stack Engineer | CloudScale Systems (2022 - Present)\n• Engineered asynchronous REST APIs using FastAPI and MongoDB serving 50k+ daily active users.\n• Built real-time dashboard in React with modular state management.\n• Containerized microservices using Docker and CI/CD pipelines.\n\nPROJECTS\nResume Interview AI | Python, FastAPI, React, MongoDB\n• Implemented TF-IDF cosine matching and PyMuPDF text extraction pipeline.\n• Designed 6-axis answer evaluation system with dynamic difficulty scaling.\n• Built clean responsive frontend with Recharts analytics and PDF report export.\n\nDistributed Task Queue | Python, Redis, Docker, PostgreSQL\n• Handled 10k messages/minute with automatic retry and dead-letter queue recovery.\n\nEDUCATION\nB.S. in Computer Science | UC Berkeley (2022)"
    },
    {
        "id": "sample-backend",
        "title": "Samantha Ray — Python & Backend Systems Engineer",
        "name": "Samantha Ray",
        "email": "samantha.ray@example.com",
        "phone": "+1 (555) 890-1234",
        "location": "Austin, TX",
        "summary": "Backend Software Engineer specializing in distributed Python services, SQL optimization, Redis caching, and microservices architecture.",
        "skills": ["Python", "FastAPI", "Django", "SQL", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Kafka", "Microservices", "CI/CD"],
        "skill_categories": {
            "Languages": ["Python", "SQL"],
            "Backend & APIs": ["FastAPI", "Django", "Microservices"],
            "Databases": ["PostgreSQL", "Redis"],
            "Cloud & DevOps": ["Docker", "Kubernetes", "AWS", "Kafka", "CI/CD"]
        },
        "experience": [
            {
                "role": "Backend Engineer",
                "company": "Apex Data Corp",
                "duration": "2021 - 2024",
                "location": "Austin, TX",
                "responsibilities": [
                    "Architected high-throughput data ingestion pipelines using Kafka and Python.",
                    "Optimized complex PostgreSQL relational queries reducing p99 latency from 450ms to 60ms.",
                    "Maintained 99.95% API uptime across Kubernetes clusters on AWS."
                ],
                "technologies": ["Python", "PostgreSQL", "Kafka", "Docker", "AWS"]
            }
        ],
        "projects": [
            {
                "title": "Real-time Event Ingestion Service",
                "description": "Event-driven microservice streaming financial transactions with deduplication and partitioned PostgreSQL storage.",
                "technologies": ["Python", "FastAPI", "Kafka", "PostgreSQL", "Redis"],
                "highlights": [
                    "Processed 25,000 events/second using asynchronous connection pools and Redis caches.",
                    "Wrote automated pytest test suites achieving 92% code coverage."
                ]
            }
        ],
        "education": [
            {
                "degree": "B.Tech in Information Technology",
                "institution": "Texas Tech University",
                "year": "2021"
            }
        ],
        "certifications": [
            {"name": "HashiCorp Certified Terraform Associate"}
        ],
        "achievements": [
            "Delivered zero-downtime database migration for 10M+ user records"
        ],
        "raw_text": "Samantha Ray\nBackend Software Engineer\nsamantha.ray@example.com | Austin, TX\n\nSKILLS: Python, FastAPI, Django, SQL, PostgreSQL, Redis, Docker, Kubernetes, AWS, Kafka, Microservices\n\nEXPERIENCE:\nBackend Engineer at Apex Data Corp (2021 - 2024)\n• Architected high-throughput data ingestion pipelines using Kafka and Python.\n• Optimized complex PostgreSQL queries reducing p99 latency by 85%.\n\nPROJECTS:\nReal-time Event Ingestion Service | Python, FastAPI, Kafka, PostgreSQL\n• Processed 25,000 events/second with async connection pooling.\n\nEDUCATION:\nB.Tech in Information Technology, Texas Tech University (2021)"
    }
]

@router.get("/samples")
async def get_sample_resumes():
    return SAMPLE_RESUMES

@router.post("/upload", response_model=ExtractedResume)
async def upload_resume(file: UploadFile = File(...)):
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported.")
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    
    extracted_text = ""
    if ext == ".pdf":
        extracted_text = ResumeParser.extract_text_from_pdf(content)
    elif ext == ".docx":
        extracted_text = ResumeParser.extract_text_from_docx(content)
    elif ext == ".txt":
        extracted_text = content.decode("utf-8", errors="ignore")

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="Unable to extract text from the file. Please ensure the document is not an image-only scan or encrypted."
        )

    parsed = ResumeParser.parse_resume(extracted_text, filename=filename)
    
    # Save to database collection
    col = db_manager.get_collection("resumes")
    await col.insert_one(parsed.model_dump())

    return parsed

@router.post("/analyze")
async def analyze_resume(resume_data: ExtractedResume):
    score = ResumeParser.calculate_score(resume_data)
    return {
        "resume": resume_data,
        "score": score
    }
