from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import (
    GroundedQuestion, GenerateQuestionsRequest, ExtractedResume, JobDescriptionAnalysis
)
from backend.app.services.ai_engine import AIEngine
from backend.app.database.db import db_manager

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/generate", response_model=List[GroundedQuestion])
async def generate_questions(req: GenerateQuestionsRequest):
    if not req.resume_data or req.resume_data.validation_status == "REJECTED":
        raise HTTPException(
            status_code=400, 
            detail="A valid, verified resume is required to generate interview questions. Please upload a valid resume."
        )
    
    questions = await AIEngine.generate_questions(
        resume=req.resume_data,
        jd=req.jd_data,
        difficulty=req.difficulty,
        question_type=req.question_type,
        count=req.count,
        exclude_hashes=req.exclude_question_hashes
    )

    # Save to history collection for session with resume_id tracking
    if questions:
        col = db_manager.get_collection("questions_history")
        for q in questions:
            doc = q.model_dump()
            doc["session_id"] = req.session_id
            doc["resume_id"] = req.resume_data.id
            doc["resume_hash"] = getattr(req.resume_data, "resume_hash", None)
            await col.insert_one(doc)

    return questions

@router.post("/regenerate", response_model=List[GroundedQuestion])
async def regenerate_questions(req: GenerateQuestionsRequest):
    """Guarantees new, distinct questions by excluding previous question hashes for this active resume and session."""
    if not req.resume_data or req.resume_data.validation_status == "REJECTED":
        raise HTTPException(
            status_code=400, 
            detail="A valid, verified resume is required to generate interview questions. Please upload a valid resume."
        )

    col = db_manager.get_collection("questions_history")
    query = {"session_id": req.session_id}
    if req.resume_data and req.resume_data.id:
        query["resume_id"] = req.resume_data.id

    previous_docs = await col.find(query)
    prev_hashes = [AIEngine._generate_hash(d.get("question", "")) for d in previous_docs if "question" in d]
    
    all_exclude = list(set(prev_hashes + (req.exclude_question_hashes or [])))

    new_questions = await AIEngine.generate_questions(
        resume=req.resume_data,
        jd=req.jd_data,
        difficulty=req.difficulty,
        question_type=req.question_type,
        count=req.count,
        exclude_hashes=all_exclude
    )

    if new_questions:
        for q in new_questions:
            doc = q.model_dump()
            doc["session_id"] = req.session_id
            doc["resume_id"] = req.resume_data.id
            doc["resume_hash"] = getattr(req.resume_data, "resume_hash", None)
            await col.insert_one(doc)

    return new_questions

@router.post("/bookmark")
async def toggle_bookmark(payload: dict = Body(...)):
    question_dict = payload.get("question")
    session_id = payload.get("session_id", "default")
    if not question_dict or "id" not in question_dict:
        raise HTTPException(status_code=400, detail="Question object is required.")

    col = db_manager.get_collection("saved_questions")
    existing = await col.find_one({"id": question_dict["id"], "session_id": session_id})
    
    if existing:
        await col.delete_one({"id": question_dict["id"], "session_id": session_id})
        return {"bookmarked": False, "message": "Question removed from saved bookmarks."}
    else:
        doc = dict(question_dict)
        doc["session_id"] = session_id
        doc["is_bookmarked"] = True
        await col.insert_one(doc)
        return {"bookmarked": True, "message": "Question saved successfully."}

@router.get("/saved", response_model=List[GroundedQuestion])
async def get_saved_questions(session_id: str = "default"):
    col = db_manager.get_collection("saved_questions")
    saved = await col.find({"session_id": session_id})
    return [GroundedQuestion(**d) for d in saved]
