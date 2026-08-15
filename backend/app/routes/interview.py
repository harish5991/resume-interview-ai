from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import (
    AnswerEvaluation, AnswerEvaluationRequest, ExtractedResume, 
    JobDescriptionAnalysis, ProjectDeepDive, TopicPreparationItem
)
from backend.app.services.ai_engine import AIEngine
from backend.app.database.db import db_manager

router = APIRouter(prefix="/interview", tags=["Mock Interview"])

@router.post("/answer", response_model=AnswerEvaluation)
async def evaluate_interview_answer(req: AnswerEvaluationRequest):
    if not req.user_answer or not req.user_answer.strip():
        raise HTTPException(status_code=400, detail="Answer text cannot be empty.")

    evaluation = await AIEngine.evaluate_answer(
        question_id=req.question_id,
        question_text=req.question_text,
        based_on=req.based_on,
        skill=req.skill,
        difficulty=req.difficulty,
        user_answer=req.user_answer,
        expected_points=req.expected_points
    )

    # Save to evaluations collection
    col = db_manager.get_collection("evaluations")
    doc = evaluation.model_dump()
    doc["session_id"] = req.session_id
    doc["question_text"] = req.question_text
    doc["user_answer"] = req.user_answer
    doc["skill"] = req.skill
    doc["difficulty"] = req.difficulty
    await col.insert_one(doc)

    return evaluation

@router.get("/history")
async def get_interview_history(session_id: str = "default"):
    col = db_manager.get_collection("evaluations")
    docs = await col.find({"session_id": session_id})
    return docs

@router.delete("/history")
async def clear_interview_history(session_id: str = "default"):
    col = db_manager.get_collection("evaluations")
    col_qh = db_manager.get_collection("questions_history")
    await col.delete_many({"session_id": session_id})
    await col_qh.delete_many({"session_id": session_id})
    if session_id == "default":
        await col.delete_many({})
        await col_qh.delete_many({})
    return {"message": "Question history and evaluations cleared for session", "session_id": session_id}

@router.post("/history/clear")
async def clear_interview_history_post(payload: dict = Body(default={})):
    session_id = payload.get("session_id", "default")
    col = db_manager.get_collection("evaluations")
    col_qh = db_manager.get_collection("questions_history")
    await col.delete_many({"session_id": session_id})
    await col_qh.delete_many({"session_id": session_id})
    if session_id == "default":
        await col.delete_many({})
        await col_qh.delete_many({})
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
