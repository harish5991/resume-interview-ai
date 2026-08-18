import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import (
    AnalyticsSummary, SkillGapAnalysis, ResumeImprovementItem,
    ExtractedResume, JobDescriptionAnalysis
)
from backend.app.services.matcher import JDMatcher
from backend.app.services.parser import ResumeParser
from backend.app.services.ai_engine import AIEngine
from backend.app.database.db import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsSummary)
async def get_analytics(session_id: str = "default"):
    # Pull session data strictly for this session
    col_sess = db_manager.get_collection("sessions")
    sess = await col_sess.find_one({"id": session_id})

    col_evals = db_manager.get_collection("evaluations")
    docs = await col_evals.find({"session_id": session_id})
    
    # If the session has an active resume, filter evaluations to this active resume
    active_resume_id = sess.get("resume", {}).get("id") if sess and sess.get("resume") else None
    if active_resume_id:
        scoped_docs = [d for d in docs if d.get("resume_id") == active_resume_id or not d.get("resume_id")]
    else:
        scoped_docs = docs

    # Deduplicate keeping latest evaluation per unique question
    eval_map = {}
    for d in scoped_docs:
        k = (d.get("question_id") or d.get("question_text", "")).strip()
        if k:
            eval_map[k] = d
    evals = list(eval_map.values())

    logger.info(f"[ANALYTICS_QUERY] Session={session_id}, Active Resume ID={active_resume_id}, Raw Docs={len(docs)}, Scoped Docs={len(scoped_docs)}, Unique Questions Attempted={len(evals)}")
    
    resume_score: Optional[int] = None
    jd_match_pct: Optional[int] = None
    resume_breakdown: Optional[Dict[str, Any]] = None

    if sess:
        if sess.get("resume_score"):
            resume_breakdown = sess["resume_score"]
            resume_score = sess["resume_score"].get("overall_score")
        elif sess.get("resume"):
            try:
                res_obj = ExtractedResume(**sess["resume"])
                jd_obj = JobDescriptionAnalysis(**sess["jd"]) if sess.get("jd") else None
                score_obj = ResumeParser.calculate_score(res_obj, jd_obj)
                resume_breakdown = score_obj.model_dump()
                resume_score = score_obj.overall_score
            except Exception:
                pass

        if sess.get("match"):
            jd_match_pct = sess["match"].get("match_percentage")
        elif sess.get("resume") and sess.get("jd"):
            try:
                res_obj = ExtractedResume(**sess["resume"])
                jd_obj = JobDescriptionAnalysis(**sess["jd"])
                match_obj = JDMatcher.match_resume_and_jd(res_obj, jd_obj)
                jd_match_pct = match_obj.match_percentage
            except Exception:
                pass

    if resume_score is None:
        try:
            col_resumes = db_manager.get_collection("resumes")
            recent_resumes = await col_resumes.find({}, limit=5)
            if recent_resumes:
                latest_resume = recent_resumes[-1]
                res_obj = ExtractedResume(**latest_resume)
                score_obj = ResumeParser.calculate_score(res_obj)
                resume_breakdown = score_obj.model_dump()
                resume_score = score_obj.overall_score
        except Exception:
            pass

    if evals:
        scores = [e.get("overall_score", 0) for e in evals]
        avg_score = int(sum(scores) / len(scores)) if scores else 0
        tech_scores = [e.get("technical_accuracy_score", 0) for e in evals]
        avg_tech = int(sum(tech_scores) / len(tech_scores)) if tech_scores else 0
        comm_scores = [e.get("communication_score", 0) for e in evals]
        avg_comm = int(sum(comm_scores) / len(comm_scores)) if comm_scores else 0
        clarity_scores = [e.get("clarity_score", 0) for e in evals]
        avg_behavioral = int(sum(clarity_scores) / len(clarity_scores)) if clarity_scores else 0
        attempted = len(evals)
        correct = sum(1 for s in scores if s >= 70)
        
        # Trends
        trends = []
        for i, e in enumerate(evals, 1):
            trends.append({
                "attempt": f"Q{i}",
                "score": e.get("overall_score", 0),
                "technical": e.get("technical_accuracy_score", 0),
                "relevance": e.get("relevance_score", 0)
            })

        # Weak vs Strong areas calculated strictly from actual questions attempted
        skill_perf: Dict[str, List[int]] = {}
        for e in evals:
            sk = e.get("skill", "General")
            if sk not in skill_perf:
                skill_perf[sk] = []
            skill_perf[sk].append(e.get("overall_score", 0))

        weak_areas = []
        strong_areas = []
        for sk, scs in skill_perf.items():
            avg_sk = int(sum(scs) / len(scs)) if scs else 0
            if avg_sk < 70:
                weak_areas.append({"topic": sk, "score": avg_sk, "priority": "High" if avg_sk < 60 else "Medium"})
            else:
                strong_areas.append({"topic": sk, "score": avg_sk, "status": "Mastered" if avg_sk >= 85 else "Proficient"})

        # Weighted Interview Readiness Score dynamically normalized over available metrics
        if resume_score is not None and jd_match_pct is not None:
            readiness = int(
                (resume_score * 0.25) +
                (jd_match_pct * 0.25) +
                (avg_tech * 0.25) +
                (avg_comm * 0.15) +
                (avg_behavioral * 0.10)
            )
        elif resume_score is not None:
            readiness = int(
                (resume_score * 0.40) +
                (avg_tech * 0.30) +
                (avg_comm * 0.20) +
                (avg_behavioral * 0.10)
            )
        else:
            readiness = int(
                (avg_tech * 0.50) +
                (avg_comm * 0.30) +
                (avg_behavioral * 0.20)
            )

        category_perf = [
            {"category": "Technical Depth", "score": avg_tech, "fullMark": 100},
            {"category": "Relevance", "score": int(((resume_score or 0) + (jd_match_pct or 0)) / 2) if (resume_score or jd_match_pct) else avg_score, "fullMark": 100},
            {"category": "Communication", "score": avg_comm, "fullMark": 100},
            {"category": "Problem Solving", "score": avg_behavioral, "fullMark": 100},
            {"category": "Completeness", "score": min(100, avg_score + 5) if avg_score > 0 else 0, "fullMark": 100}
        ]

        # Difficulty Performance Breakdown
        diff_scores: Dict[str, List[int]] = {"Easy": [], "Medium": [], "Hard": [], "Expert": []}
        for e in evals:
            diff_level = (e.get("difficulty") or "Medium").strip().capitalize()
            if diff_level not in diff_scores:
                diff_scores[diff_level] = []
            diff_scores[diff_level].append(e.get("overall_score", 0))

        diff_perf = []
        for d in ["Easy", "Medium", "Hard", "Expert"]:
            scs = diff_scores.get(d, [])
            if scs:
                pass_count = sum(1 for s in scs if s >= 70)
                pass_rate = int((pass_count / len(scs)) * 100)
                avg_diff_score = int(sum(scs) / len(scs))
            else:
                pass_rate = 0
                avg_diff_score = 0
            diff_perf.append({
                "difficulty": d,
                "passRate": pass_rate,
                "avgScore": avg_diff_score
            })
    else:
        # No mock interviews completed yet
        avg_score = 0
        avg_tech = 0
        avg_comm = 0
        avg_behavioral = 0
        attempted = 0
        correct = 0
        trends = []
        weak_areas = []
        strong_areas = []
        diff_perf = []

        if resume_score is not None and jd_match_pct is not None:
            readiness = int((resume_score * 0.5) + (jd_match_pct * 0.5))
        elif resume_score is not None:
            readiness = int(resume_score)
        elif jd_match_pct is not None:
            readiness = int(jd_match_pct)
        else:
            readiness = 0

        if resume_score is not None or jd_match_pct is not None:
            rb = resume_breakdown or {}
            skills_val = rb.get("skills_score", resume_score or 75)
            proj_val = rb.get("projects_score", resume_score or 70)
            comp_val = rb.get("completeness_score", 80)
            rel_val = jd_match_pct if jd_match_pct is not None else rb.get("relevance_score", 75)

            category_perf = [
                {"category": "Technical Depth", "score": skills_val, "fullMark": 100},
                {"category": "Relevance", "score": rel_val, "fullMark": 100},
                {"category": "Communication", "score": comp_val, "fullMark": 100},
                {"category": "Problem Solving", "score": proj_val, "fullMark": 100},
                {"category": "Completeness", "score": comp_val, "fullMark": 100}
            ]
        else:
            category_perf = []

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
