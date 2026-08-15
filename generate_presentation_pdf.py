#!/usr/bin/env python3
"""
Generate a clean, high-quality 2-Page PDF document for the CTS Panel Presentation Team Division.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = Path("/Users/hari/Downloads/project/CTS_Panel_Presentation_Team_Division.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header banner text
        self.drawString(36, 762, "Resume Interview AI — CTS Panel Project Division")
        self.drawRightString(576, 762, "Confidential / Team Handout")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 756, 576, 756)
        
        # Footer
        self.line(36, 35, 576, 35)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 24, page_text)
        self.drawString(36, 24, "Cognizant (CTS) Project Presentation Guide • 8-Member Team Architecture")
        self.restoreState()

def create_presentation_pdf(output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569')
    )
    
    sec_heading_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1E3A8A')
    )
    
    member_title_style = ParagraphStyle(
        'MemberTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor('#334155')
    )
    
    bold_style = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor('#1E293B')
    )
    
    script_style = ParagraphStyle(
        'ScriptText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#0369A1')
    )
    
    qa_style = ParagraphStyle(
        'QAText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.8,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # Title & Overview Header
    story.append(Paragraph("<b>Resume Interview AI</b> — CTS Panel Project Division & Presentation Guide", title_style))
    story.append(Paragraph("8-Member Full-Stack Architecture Split (4 Core Sections × 2 Members per Section)", subtitle_style))
    story.append(Spacer(1, 6))

    def make_member_box(name_title, role, stack, modules, script, q_text, a_text, bg_color="#F8FAFC", border_color="#CBD5E1"):
        content = []
        content.append(Paragraph(f"<b>{name_title}</b> — <font color='#2563EB'>{role}</font>", member_title_style))
        content.append(Paragraph(f"<b>Tech Stack:</b> {stack}", body_style))
        content.append(Paragraph(f"<b>Modules:</b> {modules}", body_style))
        content.append(Paragraph(f"<b>Speech Script:</b> \"{script}\"", script_style))
        content.append(Paragraph(f"<b>Panel Q:</b> <i>{q_text}</i> <b>Ans:</b> \"{a_text}\"", qa_style))
        
        t = Table([[content]], colWidths=[540])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color)),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
            ('PADDING', (0, 0), (-1, -1), 4.5),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ]))
        return t

    # ---------------- PAGE 1: SECTION 1 & SECTION 2 ----------------
    # Section 1 Header
    story.append(Paragraph("<b>SECTION 1: FRONTEND ARCHITECTURE, UI/UX & VOICE INTEGRATION</b>", sec_heading_style))
    story.append(Spacer(1, 3))
    
    # Member 1
    m1 = make_member_box(
        "MEMBER 1: Frontend Architecture & UI/UX Design Lead",
        "UI Architecture & Component System Engineer",
        "React 19, Vite, Tailwind CSS, Lucide Icons",
        "12 platform views, Sidebar navigation, ScoreRing/Badge/Modal design system, Multi-device responsive layouts.",
        "I was responsible for the core frontend architecture and design system using React 19 and Tailwind CSS. I built the modular layout, interactive gauges, and responsive navigation across all 12 platform views.",
        "How did you structure the component hierarchy for reusability?",
        "We created atomic components in components/common/ like ScoreRing and Badge, ensuring consistent props, visual tokens, and zero-runtime CSS overhead.",
        bg_color="#F0FDF4", border_color="#BBF7D0"
    )
    story.append(m1)
    story.append(Spacer(1, 4))

    # Member 2
    m2 = make_member_box(
        "MEMBER 2: Frontend State Management & Voice UI Engineer",
        "Client State & Speech-to-Text Specialist",
        "React Context API, Web Speech API, Axios Interceptors, sessionStorage",
        "SessionContext global store, Voice dictation in Mock Interview, Live backend health badge (Online/Offline), 502 error handling.",
        "I engineered the frontend state management and browser voice capabilities. I built SessionContext with ephemeral sessionStorage, integrated SpeechRecognition for voice dictation, and added live backend health status monitoring.",
        "How does voice dictation work in the browser?",
        "We hook into window.SpeechRecognition with continuous streaming, appending transcribed text tokens directly to the user's answer state in real-time.",
        bg_color="#F0FDF4", border_color="#BBF7D0"
    )
    story.append(m2)
    story.append(Spacer(1, 7))

    # Section 2 Header
    story.append(Paragraph("<b>SECTION 2: DOCUMENT PROCESSING, NLP & SEMANTIC MATCH ENGINE</b>", sec_heading_style))
    story.append(Spacer(1, 3))

    # Member 3
    m3 = make_member_box(
        "MEMBER 3: Resume Ingestion & Document Parsing Lead",
        "Document Parsing & Resume Scoring Engineer",
        "Python 3.13, PyMuPDF (fitz), Python-docx, Regex Heuristics",
        "PDF & Word text extraction, Section segmentation (Summary/Skills/Experience/Education), 5-factor quality scoring.",
        "I built the resume ingestion and parsing pipeline using PyMuPDF and python-docx. I developed algorithms to extract structured text from resumes, segment key sections, and compute an explainable 5-factor resume quality score.",
        "How do you handle multi-column resumes or unstructured formats?",
        "PyMuPDF extracts raw text blocks preserving reading order, followed by multi-pass regex scanning for standard section headers to segment sections reliably.",
        bg_color="#EFF6FF", border_color="#BFDBFE"
    )
    story.append(m3)
    story.append(Spacer(1, 4))

    # Member 4
    m4 = make_member_box(
        "MEMBER 4: Semantic Matching & Skill Gap Engineer",
        "Job Description Matching & Gap Analysis Specialist",
        "Scikit-learn (TfidfVectorizer, cosine_similarity), NLP Tokenizer",
        "Semantic similarity score calculation, Skill classification (Matched, Missing Gaps, Strengths), Resume improvements engine.",
        "I developed the semantic matching and skill gap engine using Scikit-Learn. I implemented TF-IDF vectorization and Cosine Similarity to calculate match scores and automatically classify technical skills into matched proficiencies, missing gaps, and candidate strengths.",
        "Why choose TF-IDF with Cosine Similarity over large deep learning embeddings?",
        "TF-IDF executes in <50ms with zero API cost/GPU overhead, providing transparent keyword weights so candidates can see exactly which terms influenced their score.",
        bg_color="#EFF6FF", border_color="#BFDBFE"
    )
    story.append(m4)

    # ---------------- PAGE 2: SECTION 3 & SECTION 4 + ORDER TABLE ----------------
    story.append(PageBreak())

    # Section 3 Header
    story.append(Paragraph("<b>SECTION 3: GROUNDED QUESTION GENERATION & MOCK EVALUATION</b>", sec_heading_style))
    story.append(Spacer(1, 3))

    # Member 5
    m5 = make_member_box(
        "MEMBER 5: Grounded Question Generator Lead",
        "Question Generation & Anti-Hallucination Specialist",
        "FastAPI, Google Gemini API / Grounded Deterministic Engine, Pydantic v2",
        "Grounded question engine anchored to candidate projects, Filters (Easy/Med/Hard/Expert, Tech/Behavioral), Zero-duplicate tracking.",
        "I led the Grounded Question Generation engine. I enforced strict algorithmic constraints to ensure every question is anchored to verified candidate projects or target JD requirements, with zero-duplicate history tracking.",
        "How do you prevent the AI from generating generic questions?",
        "Every generation payload passes parsed resume project entities and requires an explicit based_on field linking each question to an identified project or tool.",
        bg_color="#FAF5FF", border_color="#E9D5FF"
    )
    story.append(m5)
    story.append(Spacer(1, 4))

    # Member 6
    m6 = make_member_box(
        "MEMBER 6: Mock Interview & 6-Axis Evaluation Specialist",
        "Answer Evaluation & STAR Diagnostics Engineer",
        "Python, STAR Method Heuristics, Domain Concept Dictionary",
        "6-Axis evaluation matrix (Accuracy/Completeness/Clarity/etc.), STAR diagnostic analyzer, Senior model answers & follow-up questions.",
        "I developed the 6-axis answer evaluation engine and mock interview logic. I built algorithms that extract domain concepts, check for technical anti-patterns, evaluate STAR structure, and formulate senior model answers with interactive follow-ups.",
        "How does the system evaluate technical accuracy without a human interviewer?",
        "We match candidate answers against a domain concept dictionary (e.g. B-Trees for SQL, Event Loop for JS) and penalize misconceptions, returning explicit lists of covered vs missed concepts.",
        bg_color="#FAF5FF", border_color="#E9D5FF"
    )
    story.append(m6)
    story.append(Spacer(1, 7))

    # Section 4 Header
    story.append(Paragraph("<b>SECTION 4: BACKEND INFRASTRUCTURE, DATABASE & REPORTING</b>", sec_heading_style))
    story.append(Spacer(1, 3))

    # Member 7
    m7 = make_member_box(
        "MEMBER 7: REST API & Dual-Database Architect",
        "Backend Architecture & Database Engine Specialist",
        "FastAPI, Motor / PyMongo (MongoDB), AsyncIO, JSON Database Engine",
        "Asynchronous REST routing, Dual-Database manager with automated MongoDB + Local JSON fallback, Session lifecycle APIs.",
        "I architected the FastAPI backend and dual-mode database layer. I designed asynchronous REST endpoints and built a database manager that connects to MongoDB or falls back to an async local JSON database if MongoDB is not present.",
        "How does the system handle database operations asynchronously?",
        "We use Motor for MongoDB and asynchronous file I/O for the local database, allowing queries to run non-blockingly on FastAPI's async event loop without thread pool contention.",
        bg_color="#FFFBEB", border_color="#FDE68A"
    )
    story.append(m7)
    story.append(Spacer(1, 4))

    # Member 8
    m8 = make_member_box(
        "MEMBER 8: Readiness Analytics, PDF Reports & Automation Lead",
        "Analytics Dashboard, PDF Generation & Deployment Engineer",
        "ReportLab, Recharts, Cross-Platform Shell Scripts (run.py, run.bat, run.sh)",
        "Automated ReportLab PDF readiness report export, Readiness analytics charts, 1-click cross-platform launchers for Windows/Mac/Linux.",
        "I engineered the Readiness Analytics dashboard, the ReportLab PDF export engine, and cross-platform automation. I built the automated PDF generator for evaluation reports and created 1-click execution scripts for Windows, Mac, and Linux environments.",
        "How is the PDF generated on the fly?",
        "We use Python's ReportLab library to compile layout flowables, tables, and styled paragraphs into an in-memory binary stream, returning a downloadable PDF in under 100 milliseconds.",
        bg_color="#FFFBEB", border_color="#FDE68A"
    )
    story.append(m8)
    story.append(Spacer(1, 6))

    # Summary Presentation Order Table
    story.append(Paragraph("<b>8-Minute CTS Panel Presentation Order (1 Min per Member)</b>", sec_heading_style))
    story.append(Spacer(1, 2))

    table_data = [
        [Paragraph("<b>#</b>", bold_style), Paragraph("<b>Member</b>", bold_style), Paragraph("<b>Presentation Topic</b>", bold_style), Paragraph("<b>Live Screen / Demo Action</b>", bold_style)],
        ["1", "Member 1", "Introduction & UI Layout System", "Dashboard & Responsive Sidebar Navigation"],
        ["2", "Member 2", "State Management & Voice Dictation", "Live Status Badge & Speech-to-Text Microphone"],
        ["3", "Member 3", "Resume Ingestion & 5-Factor Quality Score", "Upload Resume & Parsed Score Breakdown"],
        ["4", "Member 4", "Semantic Match & Skill Gap Diagnostics", "TF-IDF Match % & Missing vs Matched Skills"],
        ["5", "Member 5", "Grounded Question Generator & Filters", "Generate Filtered Questions Grounded in Resume"],
        ["6", "Member 6", "Mock Interview & 6-Axis Evaluation", "Submit Answer -> 6-Axis Matrix & Model Answer"],
        ["7", "Member 7", "FastAPI Architecture & Dual-Database", "Interactive Swagger Docs (/docs) & DB Engine"],
        ["8", "Member 8", "Readiness Analytics & PDF Report Export", "Analytics Trends & Download PDF Report"],
    ]

    order_table = Table(table_data, colWidths=[20, 70, 210, 240])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(order_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_presentation_pdf(PDF_OUTPUT_PATH)
