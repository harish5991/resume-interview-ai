from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import (
    AnalyticsSummary, SkillGapAnalysis, ResumeImprovementItem,
    ExtractedResume, JobDescriptionAnalysis
)
from backend.app.services.matcher import JDMatcher
from backend.app.services.ai_engine import AIEngine
from backend.app.database.db import db_manager

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsSummary)
async def get_analytics(session_id: str = "default"):
    col_evals = db_manager.get_collection("evaluations")
    evals = await col_evals.find({"session_id": session_id})
    if not evals and session_id != "default":
        evals = await col_evals.find({"session_id": "default"})

    # Pull latest session data if present
    col_sess = db_manager.get_collection("sessions")
    sess = await col_sess.find_one({"id": session_id})
    
    resume_score = 82
    jd_match_pct = 75
    if sess:
        if sess.get("resume_score"):
            resume_score = sess["resume_score"].get("overall_score", 82)
        if sess.get("match"):
            jd_match_pct = sess["match"].get("match_percentage", 75)

    if evals:
        scores = [e.get("overall_score", 75) for e in evals]
        avg_score = int(sum(scores) / len(scores))
        tech_scores = [e.get("technical_accuracy_score", 75) for e in evals]
        avg_tech = int(sum(tech_scores) / len(tech_scores))
        comm_scores = [e.get("communication_score", 80) for e in evals]
        avg_comm = int(sum(comm_scores) / len(comm_scores))
        clarity_scores = [e.get("clarity_score", 78) for e in evals]
        avg_behavioral = int(sum(clarity_scores) / len(clarity_scores))
        attempted = len(evals)
        correct = sum(1 for s in scores if s >= 70)
        
        # Trends
        trends = []
        for i, e in enumerate(evals, 1):
            trends.append({
                "attempt": f"Q{i}",
                "score": e.get("overall_score", 70),
                "technical": e.get("technical_accuracy_score", 70),
                "relevance": e.get("relevance_score", 70)
            })

        # Weak vs Strong areas
        skill_perf: Dict[str, List[int]] = {}
        for e in evals:
            sk = e.get("skill", "General")
            if sk not in skill_perf:
                skill_perf[sk] = []
            skill_perf[sk].append(e.get("overall_score", 70))

        weak_areas = []
        strong_areas = []
        for sk, scs in skill_perf.items():
            avg_sk = int(sum(scs) / len(scs))
            if avg_sk < 70:
                weak_areas.append({"topic": sk, "score": avg_sk, "priority": "High" if avg_sk < 60 else "Medium"})
            else:
                strong_areas.append({"topic": sk, "score": avg_sk, "status": "Mastered" if avg_sk >= 85 else "Proficient"})

    else:
        # Default baseline for empty session
        avg_score = 80
        avg_tech = 78
        avg_comm = 82
        avg_behavioral = 80
        attempted = 0
        correct = 0
        trends = [
            {"attempt": "Baseline", "score": 75, "technical": 72, "relevance": 78}
        ]
        weak_areas = [
            {"topic": "System Design Trade-offs", "score": 62, "priority": "Medium"},
            {"topic": "Deep Caching & Redis", "score": 58, "priority": "High"}
        ]
        strong_areas = [
            {"topic": "Python Core & APIs", "score": 88, "status": "Mastered"},
            {"topic": "Frontend Component Design", "score": 84, "status": "Proficient"}
        ]

    # Weighted Interview Readiness Score
    readiness = int(
        (resume_score * 0.25) +
        (jd_match_pct * 0.25) +
        (avg_tech * 0.25) +
        (avg_comm * 0.15) +
        (avg_behavioral * 0.10)
    )

    category_perf = [
        {"category": "Technical Depth", "score": avg_tech, "fullMark": 100},
        {"category": "Relevance", "score": int((resume_score + jd_match_pct) / 2), "fullMark": 100},
        {"category": "Communication", "score": avg_comm, "fullMark": 100},
        {"category": "Problem Solving", "score": avg_behavioral, "fullMark": 100},
        {"category": "Completeness", "score": min(100, avg_score + 5), "fullMark": 100}
    ]

    diff_perf = [
        {"difficulty": "Easy", "passRate": 92, "avgScore": 88},
        {"difficulty": "Medium", "passRate": 80, "avgScore": 79},
        {"difficulty": "Hard", "passRate": 68, "avgScore": 69},
        {"difficulty": "Expert", "passRate": 55, "avgScore": 58}
    ]

    return AnalyticsSummary(
        interview_readiness_score=readiness,
        resume_score=resume_score,
        jd_match_percentage=jd_match_pct,
        average_interview_score=avg_score,
        technical_score=avg_tech,
        communication_score=avg_comm,
        behavioral_score=avg_behavioral,
        questions_attempted=attempted,
        correct_answers=correct,
        weak_areas=weak_areas,
        strong_areas=strong_areas,
        score_trends=trends,
        category_performance=category_perf,
        difficulty_performance=diff_perf
    )

@router.post("/skill-gap", response_model=SkillGapAnalysis)
async def get_skill_gap(payload: dict = Body(...)):
    resume_dict = payload.get("resume")
    jd_dict = payload.get("jd")

    if not resume_dict or not jd_dict:
        raise HTTPException(status_code=400, detail="Both resume and job description are required for skill gap analysis.")

    resume = ExtractedResume(**resume_dict)
    jd = JobDescriptionAnalysis(**jd_dict)

    gap = JDMatcher.generate_skill_gap(resume, jd)
    return gap

@router.post("/improvements", response_model=List[ResumeImprovementItem])
async def get_resume_improvements(payload: dict = Body(...)):
    resume_dict = payload.get("resume")
    if not resume_dict:
        raise HTTPException(status_code=400, detail="Resume data is required.")

    resume = ExtractedResume(**resume_dict)
    improvements = AIEngine.generate_resume_improvements(resume)
    return improvements
