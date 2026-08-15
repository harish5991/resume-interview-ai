import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import SessionData
from backend.app.database.db import db_manager

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("", response_model=List[SessionData])
async def list_sessions():
    col = db_manager.get_collection("sessions")
    docs = await col.find({})
    if not docs:
        # Create a default session
        default_sess = SessionData(id="default", name="Default Interview Prep")
        await col.insert_one(default_sess.model_dump())
        return [default_sess]
    return [SessionData(**d) for d in docs]

@router.post("", response_model=SessionData)
async def create_session(payload: dict = Body(...)):
    name = payload.get("name", "New Interview Session")
    new_id = payload.get("id", str(uuid.uuid4()))
    
    session = SessionData(
        id=new_id,
        name=name,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    col = db_manager.get_collection("sessions")
    await col.insert_one(session.model_dump())
    return session

@router.get("/{session_id}", response_model=SessionData)
async def get_session(session_id: str):
    col = db_manager.get_collection("sessions")
    doc = await col.find_one({"id": session_id})
    if not doc:
        # If default requested and doesn't exist, create it
        if session_id == "default":
            default_sess = SessionData(id="default", name="Default Interview Prep")
            await col.insert_one(default_sess.model_dump())
            return default_sess
        raise HTTPException(status_code=404, detail="Session not found.")
    return SessionData(**doc)

@router.put("/{session_id}", response_model=SessionData)
async def update_session(session_id: str, payload: dict = Body(...)):
    col = db_manager.get_collection("sessions")
    existing = await col.find_one({"id": session_id})
    if not existing:
        payload["id"] = session_id
        payload["created_at"] = datetime.now(timezone.utc)
        payload["updated_at"] = datetime.now(timezone.utc)
        await col.insert_one(payload)
        return SessionData(**payload)
    
    payload["updated_at"] = datetime.now(timezone.utc)
    await col.update_one({"id": session_id}, {"$set": payload})
    updated = await col.find_one({"id": session_id})
    return SessionData(**updated)

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    col = db_manager.get_collection("sessions")
    res = await col.delete_one({"id": session_id})
    return {"deleted": True, "message": f"Session {session_id} deleted."}
