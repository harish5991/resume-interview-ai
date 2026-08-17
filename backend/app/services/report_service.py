import io
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ReportService:
    @staticmethod
    def generate_pdf_report(
        session_data: Dict[str, Any]
    ) -> bytes:
        if not REPORTLAB_AVAILABLE:
            # Fallback simple printable document
            candidate_name = session_data.get("resume", {}).get("name", "Candidate") if isinstance(session_data.get("resume"), dict) else "Candidate"
            return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n% Plain Text Fallback for {candidate_name}\n".encode("utf-8")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_LEFT
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#64748B")
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        badge_style = ParagraphStyle(
            'Badge',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#2563EB")
        )

        elements = []

        # Header
        candidate_name = session_data.get("resume", {}).get("name", "Candidate") if isinstance(session_data.get("resume"), dict) else getattr(session_data.get("resume"), "name", "Candidate")
        job_title = session_data.get("jd", {}).get("title", "Target Role") if isinstance(session_data.get("jd"), dict) else getattr(session_data.get("jd"), "title", "Target Role")
        
        elements.append(Paragraph("Resume Interview AI — Comprehensive Report", title_style))
        elements.append(Paragraph(f"Candidate: <b>{candidate_name}</b> | Target Position: <b>{job_title}</b> | Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y')}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E2E8F0"), spaceAfter=14))

        # Metrics Summary Table
        resume_score_val = None
        if isinstance(session_data.get("resume_score"), dict):
            resume_score_val = session_data["resume_score"].get("overall_score")
        elif session_data.get("resume"):
            try:
                score_obj = ResumeParser.calculate_score(ExtractedResume(**session_data["resume"]))
                resume_score_val = score_obj.overall_score
            except Exception:
                pass

        jd_match_val = None
        if isinstance(session_data.get("match"), dict):
            jd_match_val = session_data["match"].get("match_percentage")
        
        evaluations = session_data.get("evaluations", [])
        avg_interview_val = int(sum(e.get("overall_score", 0) if isinstance(e, dict) else getattr(e, "overall_score", 0) for e in evaluations) / len(evaluations)) if evaluations else None

        if resume_score_val is not None and jd_match_val is not None and avg_interview_val is not None:
            readiness = int((resume_score_val * 0.3) + (jd_match_val * 0.3) + (avg_interview_val * 0.4))
        elif resume_score_val is not None and jd_match_val is not None:
            readiness = int((resume_score_val * 0.5) + (jd_match_val * 0.5))
        elif resume_score_val is not None:
            readiness = int(resume_score_val)
        else:
            readiness = avg_interview_val or 0

        resume_disp = f"{resume_score_val}/100" if resume_score_val is not None else "—"
        jd_disp = f"{jd_match_val}%" if jd_match_val is not None else "—"
        avg_disp = f"{avg_interview_val}/100" if avg_interview_val is not None else "—"

        metrics_data = [
            [
                Paragraph("<b>Interview Readiness</b>", body_style),
                Paragraph("<b>Resume Quality</b>", body_style),
                Paragraph("<b>Job Match</b>", body_style),
                Paragraph("<b>Mock Interview Avg</b>", body_style)
            ],
            [
                Paragraph(f"<font size=16 color='#2563EB'><b>{readiness}%</b></font>", body_style),
                Paragraph(f"<font size=16 color='#059669'><b>{resume_disp}</b></font>", body_style),
                Paragraph(f"<font size=16 color='#D97706'><b>{jd_disp}</b></font>", body_style),
                Paragraph(f"<font size=16 color='#7C3AED'><b>{avg_disp}</b></font>", body_style)
            ]
        ]

        
        t_metrics = Table(metrics_data, colWidths=[130, 130, 130, 130])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_metrics)
        elements.append(Spacer(1, 14))

        # Section 1: Resume & Job Analysis
        elements.append(Paragraph("1. Skills & Job Fit Analysis", section_heading))
        
        match_obj = session_data.get("match", {})
        matching_skills = match_obj.get("matching_skills", []) if isinstance(match_obj, dict) else getattr(match_obj, "matching_skills", [])
        missing_skills = match_obj.get("missing_skills", []) if isinstance(match_obj, dict) else getattr(match_obj, "missing_skills", [])
        
        analysis_data = [
            [
                Paragraph("<b>Matching Core Skills:</b>", body_style),
                Paragraph(", ".join(matching_skills[:8]) or "Python, SQL, React, APIs", body_style)
            ],
            [
                Paragraph("<b>Identified Skill Gaps:</b>", body_style),
                Paragraph(", ".join(missing_skills[:6]) or "None identified", body_style)
            ],
            [
                Paragraph("<b>Match Rationale:</b>", body_style),
                Paragraph(match_obj.get("relevance_explanation", "Strong foundational alignment with core stack.") if isinstance(match_obj, dict) else getattr(match_obj, "relevance_explanation", "Strong foundational alignment."), body_style)
            ]
        ]
        t_analysis = Table(analysis_data, colWidths=[140, 380])
        t_analysis.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#F1F5F9")),
        ]))
        elements.append(t_analysis)
        elements.append(Spacer(1, 12))

        # Section 2: Mock Interview Transcript & Feedback
        elements.append(Paragraph("2. Mock Interview Transcript & Evaluation", section_heading))
        
        if evaluations:
            for idx, ev in enumerate(evaluations[:5], 1):
                if isinstance(ev, dict):
                    ev_dict = ev
                elif hasattr(ev, "model_dump"):
                    ev_dict = ev.model_dump()
                elif hasattr(ev, "dict"):
                    ev_dict = ev.dict()
                else:
                    ev_dict = {}
                q_text = ev_dict.get("question_text", f"Question {idx}")
                score = ev_dict.get("overall_score", 80)
                strengths = ev_dict.get("strengths", [])
                weaknesses = ev_dict.get("weaknesses", [])
                improved = ev_dict.get("improved_answer", "")

                q_block = [
                    [Paragraph(f"<b>Q{idx}: {q_text}</b>", body_style), Paragraph(f"<b>Score: {score}/100</b>", badge_style)],
                    [Paragraph(f"<b>Strengths:</b> {'; '.join(strengths)}", body_style), ""],
                    [Paragraph(f"<b>Areas for Growth:</b> {'; '.join(weaknesses)}", body_style), ""],
                    [Paragraph(f"<b>Model Answer:</b> {improved}", body_style), ""]
                ]
                t_q = Table(q_block, colWidths=[420, 100])
                t_q.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                    ('SPAN', (0,1), (1,1)),
                    ('SPAN', (0,2), (1,2)),
                    ('SPAN', (0,3), (1,3)),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ]))
                elements.append(t_q)
                elements.append(Spacer(1, 8))
        else:
            elements.append(Paragraph("No mock interview answers recorded in this session yet. Complete questions in the 'Mock Interview' tab to see detailed evaluations here.", body_style))

        elements.append(Spacer(1, 10))

        # Section 3: Recommended Action Plan
        elements.append(Paragraph("3. Recommended Preparation Action Plan", section_heading))
        recs = [
            "1. Review STAR-format technical stories for your primary projects with quantitative metrics.",
            "2. Practice explaining database indexing, query optimization, and scaling trade-offs.",
            f"3. Ramp up on missing target skills: {', '.join(missing_skills[:3]) if missing_skills else 'Advanced system design and microservices'}.",
            "4. Run a 10-question timed adaptive mock interview to refine answer clarity under time constraints."
        ]
        for r in recs:
            elements.append(Paragraph(r, body_style))
        def _draw_page_decorations(canvas, d):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748B"))
            canvas.drawString(36, 20, "Resume Interview AI — Official CTS Candidate Readiness Dossier")
            canvas.drawRightString(576, 20, f"Page {d.page}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=_draw_page_decorations, onLaterPages=_draw_page_decorations)
        buffer.seek(0)
        return buffer.getvalue()

# ReportLab PDF Layout & Footer Engine - Nithin
