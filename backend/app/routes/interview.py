import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import (
    AnswerEvaluation, AnswerEvaluationRequest, ExtractedResume, 
    JobDescriptionAnalysis, ProjectDeepDive, TopicPreparationItem,
    FinalInterviewEvaluation, FinalInterviewEvaluationRequest
)
from backend.app.services.ai_engine import AIEngine
from backend.app.services.diversity_manager import MockInterviewSessionTracker
from backend.app.database.db import db_manager

router = APIRouter(prefix="/interview", tags=["Mock Interview"])

@router.post("/answer", response_model=AnswerEvaluation)
async def evaluate_interview_answer(req: AnswerEvaluationRequest):
    if not req.user_answer or not req.user_answer.strip():
        raise HTTPException(status_code=400, detail="Answer text cannot be empty.")

    attempt_id = req.question_attempt_id or f"attempt_{uuid.uuid4().hex[:12]}"

    evaluation = await AIEngine.evaluate_answer(
        question_id=req.question_id,
        question_text=req.question_text,
        based_on=req.based_on,
        skill=req.skill,
        difficulty=req.difficulty,
        user_answer=req.user_answer,
        expected_points=req.expected_points,
        sample_answer=req.sample_answer,
        session_id=req.session_id or "default",
        resume_data=req.resume_data,
        jd_data=req.jd_data,
        question_intent=req.question_intent,
        question_attempt_id=attempt_id
    )

    # Save to evaluations collection
    col = db_manager.get_collection("evaluations")
    doc = evaluation.model_dump()
    doc["session_id"] = req.session_id or "default"
    doc["question_attempt_id"] = attempt_id
    doc["resume_id"] = req.resume_data.id if req.resume_data else None
    doc["resume_hash"] = getattr(req.resume_data, "resume_hash", None) if req.resume_data else None
    doc["question_text"] = req.question_text
    doc["user_answer"] = req.user_answer
    doc["skill"] = req.skill
    doc["difficulty"] = req.difficulty
    doc["based_on"] = req.based_on
    doc["expected_points"] = req.expected_points
    await col.insert_one(doc)

    return evaluation

@router.post("/final-evaluation", response_model=FinalInterviewEvaluation)
async def evaluate_full_interview(req: FinalInterviewEvaluationRequest):
    evaluations = req.evaluations
    questions = req.questions

    # If evaluations not sent directly in request, fetch from database for this session
    if not evaluations and req.session_id:
        col = db_manager.get_collection("evaluations")
        docs = await col.find({"session_id": req.session_id})
        # Deduplicate evaluations, keeping latest per question_attempt_id / question_id
        eval_map = {}
        for d in docs:
            k = d.get("question_attempt_id") or d.get("question_id") or d.get("question_text")
            eval_map[k] = AnswerEvaluation(**d)
        evaluations = list(eval_map.values())

    final_eval = await AIEngine.generate_final_interview_evaluation(
        questions=questions,
        evaluations=evaluations,
        resume=req.resume_data,
        jd=req.jd_data
    )

    # Save final evaluation record
    col_final = db_manager.get_collection("final_evaluations")
    doc = final_eval.model_dump()
    doc["session_id"] = req.session_id
    doc["resume_id"] = req.resume_data.id if req.resume_data else None
    doc["resume_hash"] = getattr(req.resume_data, "resume_hash", None) if req.resume_data else None
    await col_final.insert_one(doc)

    return final_eval

@router.get("/history")
async def get_interview_history(session_id: str = "default"):
    col = db_manager.get_collection("evaluations")
    docs = await col.find({"session_id": session_id})
    
    # Deduplicate keeping the latest evaluation per unique question
    eval_map = {}
    for d in docs:
        k = d.get("question_id") or d.get("question_text")
        eval_map[k] = d
    return list(eval_map.values())

@router.delete("/history")
async def clear_interview_history(session_id: str = "default"):
    col = db_manager.get_collection("evaluations")
    col_qh = db_manager.get_collection("questions_history")
    await col.delete_many({"session_id": session_id})
    await col_qh.delete_many({"session_id": session_id})
    MockInterviewSessionTracker.clear_session(session_id)
    return {"message": "Question history and evaluations cleared for session", "session_id": session_id}

@router.post("/history/clear")
async def clear_interview_history_post(payload: dict = Body(default={})):
    session_id = payload.get("session_id", "default")
    col = db_manager.get_collection("evaluations")
    col_qh = db_manager.get_collection("questions_history")
    await col.delete_many({"session_id": session_id})
    await col_qh.delete_many({"session_id": session_id})
    MockInterviewSessionTracker.clear_session(session_id)
    return {"message": "Question history and evaluations cleared for session", "session_id": session_id}

@router.post("/project-deep-dive", response_model=ProjectDeepDive)
async def get_project_deep_dive(payload: dict = Body(...)):
    title = payload.get("title", "Highlighted Project")
    technologies = payload.get("technologies", ["Python", "FastAPI", "React", "MongoDB"])
    description = payload.get("description", "")
    
    deep_dive = AIEngine.generate_project_deep_dive(title, technologies, description)
    return deep_dive

@router.post("/topics", response_model=List[TopicPreparationItem])
async def get_preparation_topics(payload: dict = Body(...)):
    resume_dict = payload.get("resume")
    jd_dict = payload.get("jd")

    if not resume_dict:
        raise HTTPException(status_code=400, detail="Resume data is required.")

    resume = ExtractedResume(**resume_dict)
    jd = JobDescriptionAnalysis(**jd_dict) if jd_dict else None
    
    topics = AIEngine.generate_preparation_topics(resume, jd)
    return topics

