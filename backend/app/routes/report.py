from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import Response
from backend.app.services.report_service import ReportService
from backend.app.database.db import db_manager

router = APIRouter(prefix="/report", tags=["Report"])

@router.post("/export")
async def export_interview_report(payload: dict = Body(...)):
    session_id = payload.get("session_id", "default")
    
    # Load session or use direct payload
    col_sess = db_manager.get_collection("sessions")
    sess = await col_sess.find_one({"id": session_id})
    
    data = dict(sess) if sess else payload
    
    # Fetch evaluations for session
    col_evals = db_manager.get_collection("evaluations")
    evals = await col_evals.find({"session_id": session_id})
    if evals:
        data["evaluations"] = evals

    try:
        pdf_bytes = ReportService.generate_pdf_report(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Interview_Report_{session_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.get("/presentation-guide")
async def get_presentation_guide_pdf():
    import os
    pdf_path = "/Users/hari/Downloads/project/CTS_Panel_Presentation_Team_Division.pdf"
    if not os.path.exists(pdf_path):
        from generate_presentation_pdf import create_presentation_pdf
        create_presentation_pdf(pdf_path)
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=CTS_Panel_Presentation_Team_Division.pdf"
        }
    )
