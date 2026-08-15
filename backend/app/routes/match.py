from fastapi import APIRouter, HTTPException, Body
from backend.app.schemas.models import ExtractedResume, JobDescriptionAnalysis, ResumeJobMatch
from backend.app.services.matcher import JDMatcher

router = APIRouter(prefix="/match", tags=["Matching"])

@router.post("", response_model=ResumeJobMatch)
async def match_resume_and_job(payload: dict = Body(...)):
    resume_dict = payload.get("resume")
    jd_dict = payload.get("jd")

    if not resume_dict:
        raise HTTPException(status_code=400, detail="Resume data is required for matching.")
    if not jd_dict:
        raise HTTPException(status_code=400, detail="Job Description data is required for matching.")

    try:
        resume = ExtractedResume(**resume_dict)
        jd = JobDescriptionAnalysis(**jd_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid resume or job data structure: {str(e)}")

    match_result = JDMatcher.match_resume_and_jd(resume, jd)
    return match_result
