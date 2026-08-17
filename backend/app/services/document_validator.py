import re
import hashlib
import io
import logging
from typing import Dict, List, Tuple, Any, Optional
import fitz  # PyMuPDF
import docx
from backend.app.schemas.models import DocumentValidationResult

logger = logging.getLogger("document_validator")

class DocumentValidator:
    """Strictly validates whether an uploaded document is a genuine resume/CV before parsing or question generation."""

    # Positive section headers and markers commonly found in resumes
    POSITIVE_MARKERS: Dict[str, Dict[str, Any]] = {
        "contact_info": {
            "patterns": [
                re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),  # Email
                re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'), # Phone
                re.compile(r'\b(?:linkedin\.com/in/|github\.com/|portfolio|leetcode\.com)\b', re.I),
            ],
            "weight": 0.20,
            "label": "Contact Information (Email / Phone / Profiles)"
        },
        "skills_section": {
            "patterns": [
                re.compile(r'\b(?:technical\s+skills|skills\s*(?:&|and)\s*abilities|core\s+competencies|programming\s+languages|technologies|tools\s*&?\s*frameworks|areas\s+of\s+expertise)\b', re.I),
                re.compile(r'\b(?:python|javascript|typescript|java|react|fastapi|sql|docker|git|c\+\+|node\.js|html5?|css3?)\b', re.I)
            ],
            "weight": 0.25,
            "label": "Skills & Technical Competencies"
        },
        "experience_section": {
            "patterns": [
                re.compile(r'\b(?:work\s+experience|professional\s+experience|employment\s+history|experience|internships?|work\s+history)\b', re.I),
                re.compile(r'\b(?:software\s+engineer|developer|intern|lead|consultant|analyst|manager|specialist)\b', re.I),
                re.compile(r'\b(?:20\d\d\s*[-–—]\s*(?:present|current|20\d\d)|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b\s*20\d\d)', re.I)
            ],
            "weight": 0.25,
            "label": "Work Experience / Employment History"
        },
        "projects_section": {
            "patterns": [
                re.compile(r'\b(?:personal\s+projects|academic\s+projects|key\s+projects|technical\s+projects|projects\s*(?:undertaken)?)\b', re.I),
                re.compile(r'\b(?:built|developed|engineered|implemented|designed|architected)\b.*?\b(?:using|with|via|in)\b', re.I)
            ],
            "weight": 0.20,
            "label": "Projects & Implementations"
        },
        "education_section": {
            "patterns": [
                re.compile(r'\b(?:education|academic\s+background|qualifications|academic\s+credentials)\b', re.I),
                re.compile(r'\b(?:bachelor|master|b\.tech|b\.e|b\.s|m\.s|m\.tech|ph\.d|degree|diploma|university|college|gpa|cgpa)\b', re.I)
            ],
            "weight": 0.15,
            "label": "Education & Degrees"
        },
        "summary_section": {
            "patterns": [
                re.compile(r'\b(?:professional\s+summary|career\s+objective|summary|about\s+me|profile|objective)\b', re.I)
            ],
            "weight": 0.10,
            "label": "Professional Summary / Objective"
        },
        "certifications_section": {
            "patterns": [
                re.compile(r'\b(?:certifications?|licenses?|achievements?|honors?|awards?|publications?)\b', re.I)
            ],
            "weight": 0.05,
            "label": "Certifications & Achievements"
        }
    }

    # Negative document indicators that identify non-resume documents
    NEGATIVE_DOCUMENT_PATTERNS: Dict[str, Dict[str, Any]] = {
        "ACADEMIC_PAPER": {
            "patterns": [
                re.compile(r'\b(?:abstract\b.*?\bintroduction\b)', re.I | re.DOTALL),
                re.compile(r'\b(?:literature\s+review|methodology\s+and\s+materials|experimental\s+results|conclusions?\s+and\s+future\s+work)\b', re.I),
                re.compile(r'\b(?:ieee\s+transactions|arxiv:\d+|doi:\s*10\.\d+|proceedings\s+of\s+the\b|et\s+al\.)\b', re.I),
                re.compile(r'\b(?:fig\.\s*\d+|figure\s*\d+:|table\s*\d+:|references\s*\n\s*\[1\])\b', re.I)
            ],
            "penalty": 0.60,
            "label": "Academic / Research Paper"
        },
        "CERTIFICATE": {
            "patterns": [
                re.compile(r'\b(?:certificate\s+of\s+(?:completion|achievement|excellence|appreciation|participation))\b', re.I),
                re.compile(r'\b(?:this\s+is\s+to\s+certify\s+that|has\s+successfully\s+completed\s+the\s+(?:course|program|training))\b', re.I),
                re.compile(r'\b(?:certificate\s+(?:id|number|no)|verification\s+code|authorized\s+signat(?:ure|ory)|instructor\s+signature)\b', re.I),
                re.compile(r'\b(?:awarded\s+to\s+[A-Za-z\s]+on\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d+))\b', re.I)
            ],
            "penalty": 0.70,
            "label": "Course / Training Certificate"
        },
        "PROJECT_REPORT": {
            "patterns": [
                re.compile(r'\b(?:submitted\s+in\s+partial\s+fulfillment\s+of\s+the\s+requirements?)\b', re.I),
                re.compile(r'\b(?:table\s+of\s+contents|chapter\s+1|chapter\s+2|literature\s+survey|system\s+requirements?\s+specification|srs\s+document)\b', re.I),
                re.compile(r'\b(?:under\s+the\s+guidance\s+of|supervised\s+by|academic\s+year\s*20\d\d[-–]\d\d|department\s+of\s+[A-Za-z\s]+engineering)\b', re.I)
            ],
            "penalty": 0.60,
            "label": "Academic Project Report / Thesis"
        },
        "INVOICE_OR_FINANCIAL": {
            "patterns": [
                re.compile(r'\b(?:tax\s+invoice|bill\s+to:|invoice\s+(?:number|no|#)|total\s+amount|subtotal|payment\s+receipt|gstin|balance\s+due)\b', re.I),
                re.compile(r'\b(?:bank\s+statement|account\s+number|transaction\s+id|debit\s+amount|credit\s+amount)\b', re.I)
            ],
            "penalty": 0.80,
            "label": "Invoice / Financial Document"
        },
        "QUESTION_PAPER": {
            "patterns": [
                re.compile(r'\b(?:question\s+paper|time:\s*3\s*hours?|maximum\s+marks|max\s+marks:\s*\d+|answer\s+any\s+(?:five|all)\s+questions?)\b', re.I),
                re.compile(r'\b(?:section\s*[-–]\s*[a-c]|roll\s+no:|instructions?\s+to\s+candidates?|q\.?\s*no\.\s*\d+)\b', re.I)
            ],
            "penalty": 0.80,
            "label": "Examination Question Paper"
        },
        "TEXTBOOK_OR_MANUAL": {
            "patterns": [
                re.compile(r'\b(?:textbook|table\s+of\s+contents|chapter\s+\d+|isbn\s*(?:-1[03]:)?\s*[\d-]{10,}|published\s+by|all\s+rights\s+reserved|preface|glossary\s+of\s+terms)\b', re.I),
                re.compile(r'\b(?:instructor(?:\'s)?\s+(?:guide|manual)|solution\s+manual|first\s+edition|second\s+edition|third\s+edition)\b', re.I)
            ],
            "penalty": 0.70,
            "label": "Textbook / Reference Manual"
        },
        "GENERIC_DOC": {
            "patterns": [
                re.compile(r'\b(?:privacy\s+policy|terms\s+(?:and|&)\s+conditions|all\s+rights\s+reserved|user\s+manual|installation\s+guide)\b', re.I)
            ],
            "penalty": 0.50,
            "label": "General Documentation / Brochure"
        }
    }

    @classmethod
    def calculate_file_hash(cls, content_bytes: bytes) -> str:
        """Computes SHA-256 hash of the binary file content."""
        return hashlib.sha256(content_bytes).hexdigest()

    @classmethod
    def extract_text(cls, content_bytes: bytes, ext: str) -> Tuple[str, Optional[str]]:
        """Safely extracts raw text from PDF bytes and detects encryption or corruption."""
        text = ""
        error = None

        if not content_bytes or len(content_bytes) == 0:
            return "", "Invalid file. The uploaded file is empty. Please upload a valid resume PDF."

        if ext != ".pdf":
            return "", f"Invalid file format '{ext}'. Only PDF resumes (.pdf) are accepted. Please upload a valid resume PDF."

        # Verify PDF header magic bytes
        if b"%PDF-" not in content_bytes[:1024]:
            return "", "Invalid file. The uploaded file is corrupted or not a valid PDF document. Please upload a valid resume PDF."

        try:
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            if doc.is_encrypted:
                return "", "Invalid file. Password-protected PDFs cannot be parsed. Please upload an unprotected resume PDF."
            
            for page in doc:
                text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
            return "", f"Invalid file. Corrupted or unreadable PDF document. Please upload a valid resume PDF."

        return text.strip(), error

    @classmethod
    def validate_and_classify(cls, content_bytes: bytes, filename: str, ext: str) -> DocumentValidationResult:
        """
        Runs comprehensive multi-signal classification on document bytes and extracted text.
        Rejects non-resumes, scanned/empty documents, certificates, papers, textbooks, and invoices.
        """
        file_hash = cls.calculate_file_hash(content_bytes)
        raw_text, extract_error = cls.extract_text(content_bytes, ext.lower())

        if extract_error:
            return DocumentValidationResult(
                is_resume=False,
                confidence=0.0,
                validation_status="REJECTED",
                document_type="PROTECTED_OR_CORRUPT",
                file_hash=file_hash,
                word_count=0,
                error=extract_error
            )

        words = raw_text.split()
        word_count = len(words)

        # 1. Scanned / Empty document check
        if word_count < 35 or len(raw_text) < 140:
            return DocumentValidationResult(
                is_resume=False,
                confidence=0.05,
                validation_status="REJECTED",
                document_type="SCANNED_OR_EMPTY",
                file_hash=file_hash,
                word_count=word_count,
                error="Invalid file. We couldn't extract readable text from this PDF. Scanned or image-only documents are not supported. Please upload a text-based resume PDF."
            )

        # 2. Check Positive Resume Signals
        positive_score = 0.0
        positive_signals: List[str] = []
        matched_sections: set = set()

        for section_key, config in cls.POSITIVE_MARKERS.items():
            section_matched = False
            for pattern in config["patterns"]:
                if pattern.search(raw_text):
                    section_matched = True
                    break
            if section_matched:
                positive_score += config["weight"]
                positive_signals.append(config["label"])
                matched_sections.add(section_key)

        # 3. Check Negative Document Signals
        negative_penalty = 0.0
        negative_signals: List[str] = []
        detected_non_resume_type: Optional[str] = None

        for doc_type, config in cls.NEGATIVE_DOCUMENT_PATTERNS.items():
            matches_for_type = 0
            for pattern in config["patterns"]:
                if pattern.search(raw_text):
                    matches_for_type += 1

            if matches_for_type >= 2:
                # Strong negative detection
                negative_penalty += config["penalty"]
                negative_signals.append(f"Strong match for {config['label']} ({matches_for_type} patterns)")
                detected_non_resume_type = doc_type
            elif matches_for_type == 1:
                negative_penalty += config["penalty"] * 0.4
                negative_signals.append(f"Partial match for {config['label']}")
                if not detected_non_resume_type:
                    detected_non_resume_type = doc_type

        # 4. Calculate Final Confidence Score
        # Max positive score possible = 1.20, normalize to 1.0
        normalized_positive = min(1.0, positive_score)
        final_confidence = max(0.0, min(1.0, normalized_positive - negative_penalty))

        # Core required sections: (Skills OR Experience OR Projects) AND (Education OR Contact OR Summary)
        has_technical_core = any(s in matched_sections for s in ["skills_section", "projects_section", "experience_section"])
        has_identity_core = any(s in matched_sections for s in ["contact_info", "education_section", "summary_section"])
        primary_section_count = len(matched_sections)

        # 5. Final Classification Verdict
        is_resume = False
        validation_status = "REJECTED"
        doc_type_verdict = "RESUME" if not detected_non_resume_type else detected_non_resume_type
        error_msg = None

        if final_confidence >= 0.65 and has_technical_core and primary_section_count >= 3:
            is_resume = True
            validation_status = "VALID"
            doc_type_verdict = "RESUME"

        elif final_confidence >= 0.50 and has_technical_core and has_identity_core and not detected_non_resume_type:
            is_resume = True
            validation_status = "VALID"
            doc_type_verdict = "RESUME"

        else:
            is_resume = False
            validation_status = "REJECTED"
            if detected_non_resume_type:
                label_name = cls.NEGATIVE_DOCUMENT_PATTERNS.get(detected_non_resume_type, {}).get("label", "non-resume document")
                error_msg = f"Invalid file. This document appears to be a {label_name}, not a resume or CV. Please upload a valid resume PDF containing your education, skills, projects, or work experience."
            else:
                error_msg = "Invalid file. This document doesn't appear to be a resume or CV. Please upload a valid resume PDF containing your education, skills, projects, or work experience."

        return DocumentValidationResult(
            is_resume=is_resume,
            confidence=round(final_confidence, 2),
            validation_status=validation_status,
            document_type=doc_type_verdict,
            file_hash=file_hash,
            word_count=word_count,
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            error=error_msg
        )
