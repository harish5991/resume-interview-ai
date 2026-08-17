import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from backend.app.schemas.models import (
    ExtractedResume, JobDescriptionAnalysis, AnswerGrounding, ClaimValidationResult
)
from backend.app.services.intent_classifier import QuestionIntentClassifier, QuestionIntent

logger = logging.getLogger("grounding_validator")

class GroundingValidator:
    """Strict anti-hallucination and claim validation engine for resume-grounded interview answers."""

    # Common external technologies that AI models tend to hallucinate into candidate answers
    HIGH_RISK_TECHNOLOGIES = {
        "redis", "kafka", "celery", "kubernetes", "k8s", "hpa", "horizontal pod autoscaling",
        "nginx", "docker", "bem", "content-visibility", "translate3d", "will-change",
        "aws", "gcp", "azure", "graphql", "elasticsearch", "rabbitmq", "ansible",
        "terraform", "helm", "istio", "prometheus", "grafana", "microservices",
        "event-driven", "grpc", "ci/cd", "jenkins", "gitlab ci", "github actions"
    }

    # First-person implementation claim patterns
    FIRST_PERSON_CLAIM_PATTERNS = [
        re.compile(r'\bi\s+(?:implemented|built|engineered|architected|deployed|integrated|used|optimized|configured|designed|scaled|introduced)\b', re.IGNORECASE),
        re.compile(r'\bwe\s+(?:implemented|built|engineered|architected|deployed|integrated|used|optimized|configured|designed|scaled|introduced)\b', re.IGNORECASE),
        re.compile(r'\bin\s+my\s+(?:production|project|experience|role|team|architecture)\b', re.IGNORECASE),
        re.compile(r'\bmy\s+implementation\b', re.IGNORECASE),
        re.compile(r'\breducing\s+[\w\s]+\s+by\s+\d+%', re.IGNORECASE),
        re.compile(r'\bachieving\s+\d+\s*(?:fps|ms|%|users|req)', re.IGNORECASE),
    ]

    @classmethod
    def extract_evidence_context(cls, resume: Optional[ExtractedResume]) -> Dict[str, Any]:
        """Extracts and normalizes all verified facts from the candidate's resume."""
        if not resume:
            return {
                "skills_set": set(),
                "skills_list": [],
                "projects_map": {},
                "experience_map": {},
                "raw_text_lower": "",
                "evidence_items": []
            }

        skills_list = [s.strip() for s in (resume.skills or []) if s.strip()]
        skills_set = {s.lower() for s in skills_list}

        projects_map = {}
        for p in (resume.projects or []):
            p_title = p.title.strip() if p.title else "Project"
            p_techs = [t.strip() for t in (p.technologies or []) if t.strip()]
            p_highlights = [h.strip() for h in (p.highlights or []) if h.strip()]
            projects_map[p_title.lower()] = {
                "title": p_title,
                "technologies": p_techs,
                "tech_set": {t.lower() for t in p_techs},
                "highlights": p_highlights,
                "description": p.description or ""
            }
            for t in p_techs:
                skills_set.add(t.lower())

        experience_map = {}
        for e in (resume.experience or []):
            comp = e.company.strip() if e.company else "Company"
            role = e.role.strip() if e.role else "Role"
            e_techs = [t.strip() for t in (e.technologies or []) if t.strip()]
            e_resp = [r.strip() for r in (e.responsibilities or []) if r.strip()]
            experience_map[comp.lower()] = {
                "company": comp,
                "role": role,
                "technologies": e_techs,
                "tech_set": {t.lower() for t in e_techs},
                "responsibilities": e_resp
            }
            for t in e_techs:
                skills_set.add(t.lower())

        raw_text_parts = [
            getattr(resume, "raw_text", "") or "",
            getattr(resume, "summary", "") or "",
            " ".join(skills_list),
            " ".join([p["description"] for p in projects_map.values()]),
            " ".join([e["company"] + " " + e["role"] for e in experience_map.values()])
        ]
        raw_text_lower = " ".join(raw_text_parts).lower()

        # Build list of evidence items for display
        evidence_items = []
        for s in skills_list[:6]:
            evidence_items.append(f"Skill: {s}")
        for p_title, p_data in list(projects_map.items())[:3]:
            tech_str = f" ({', '.join(p_data['technologies'][:2])})" if p_data['technologies'] else ""
            evidence_items.append(f"Project: {p_data['title']}{tech_str}")
        for comp, exp_data in list(experience_map.items())[:2]:
            evidence_items.append(f"Experience: {exp_data['role']} at {exp_data['company']}")

        return {
            "skills_set": skills_set,
            "skills_list": skills_list,
            "projects_map": projects_map,
            "experience_map": experience_map,
            "raw_text_lower": raw_text_lower,
            "evidence_items": evidence_items
        }

    @classmethod
    def is_technology_verified(cls, tech: str, evidence: Dict[str, Any]) -> bool:
        """Checks if a technology is explicitly mentioned in candidate's resume."""
        tech_lower = tech.lower().strip()
        if not tech_lower:
            return True

        if tech_lower in evidence["skills_set"]:
            return True

        # Check in project technologies or experience technologies
        for p in evidence["projects_map"].values():
            if tech_lower in p["tech_set"] or any(tech_lower in t.lower() for t in p["technologies"]):
                return True
        for e in evidence["experience_map"].values():
            if tech_lower in e["tech_set"] or any(tech_lower in t.lower() for t in e["technologies"]):
                return True

        # Check substring in raw resume text with word boundary
        pattern = r'\b' + re.escape(tech_lower) + r'\b'
        if re.search(pattern, evidence["raw_text_lower"]):
            return True

        return False

    @classmethod
    def classify_question_type(cls, question_text: str, question_type: str, based_on: str) -> str:
        """Categorizes the question into a clear grounding strategy type."""
        q_lower = question_text.lower()
        b_lower = based_on.lower()

        if any(w in q_lower for w in ["10x", "if you were to", "how would you scale", "how would you design", "hypothetical", "imagine", "scenario"]):
            return "Hypothetical / Technical"
        if "project:" in b_lower or "project based" in question_type.lower() or "in your project" in q_lower:
            return "Direct Experience"
        if "experience:" in b_lower or "behavioral" in question_type.lower() or "tell me about a time" in q_lower:
            return "Behavioral / Project"
        if "what is" in q_lower or "difference between" in q_lower or "explain how" in q_lower:
            return "Conceptual / Knowledge"
        return "Hypothetical / Technical"

    @classmethod
    def validate_and_ground_answer(
        cls,
        question_text: str,
        answer_text: str,
        skill: str,
        based_on: str,
        question_type: str,
        difficulty: str,
        resume: Optional[ExtractedResume],
        jd: Optional[JobDescriptionAnalysis] = None
    ) -> Tuple[str, AnswerGrounding]:
        """
        Validates the answer for hallucinated experience, ensures conditional framing for hypotheticals,
        and rewrites any unsupported candidate experience claims.
        """
        evidence = cls.extract_evidence_context(resume)
        answer_type = cls.classify_question_type(question_text, question_type, based_on)

        cleaned_answer = answer_text.strip() if answer_text else ""
        claims_validation: List[ClaimValidationResult] = []
        unsupported_claims: List[str] = []
        evidence_used: List[str] = []

        # 1. Detect relevant evidence used
        skill_verified = cls.is_technology_verified(skill, evidence)
        if skill_verified and skill:
            evidence_used.append(f"Skill: {skill}")

        for p_name, p_data in evidence["projects_map"].items():
            if p_data["title"].lower() in question_text.lower() or p_data["title"].lower() in based_on.lower() or p_data["title"].lower() in cleaned_answer.lower():
                evidence_used.append(f"Project: {p_data['title']}")

        for comp, exp_data in evidence["experience_map"].items():
            if exp_data["company"].lower() in question_text.lower() or exp_data["company"].lower() in based_on.lower() or exp_data["company"].lower() in cleaned_answer.lower():
                evidence_used.append(f"Experience: {exp_data['role']} at {exp_data['company']}")

        if not evidence_used and skill:
            evidence_used.append(f"Topic: {skill}")

        # 2. Check for high-risk unverified technology claims in the answer
        needs_rewrite = False
        rewrite_reasons = []

        # Check for first-person experience assertions with unverified technologies
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_answer) if s.strip()]
        for sent in sentences:
            has_first_person = any(p.search(sent) for p in cls.FIRST_PERSON_CLAIM_PATTERNS)
            found_unverified_techs = []

            for tech in cls.HIGH_RISK_TECHNOLOGIES:
                # Check if tech is mentioned in this sentence
                if re.search(r'\b' + re.escape(tech) + r'\b', sent, re.IGNORECASE):
                    if not cls.is_technology_verified(tech, evidence):
                        found_unverified_techs.append(tech)

            if found_unverified_techs:
                if has_first_person:
                    # Direct hallucination of experience!
                    for t in found_unverified_techs:
                        unsupported_claims.append(f"Claimed past implementation of '{t}' without resume evidence")
                        claims_validation.append(ClaimValidationResult(
                            claim=f"Implemented {t}",
                            status="UNSUPPORTED",
                            evidence=None
                        ))
                    needs_rewrite = True
                    rewrite_reasons.append(f"Unsupported implementation claims: {', '.join(found_unverified_techs)}")
                else:
                    # Mentioned conditionally or hypothetically
                    for t in found_unverified_techs:
                        claims_validation.append(ClaimValidationResult(
                            claim=f"Suggested {t} as a technical consideration",
                            status="HYPOTHETICAL",
                            evidence="General technical recommendation"
                        ))

        # 3. Classify specific Question Intent and Answer Structure
        detected_intent, answer_structure = QuestionIntentClassifier.classify(question_text, question_type, based_on)

        is_10x_scale_q = bool(re.search(r'\b10x\b', question_text, re.IGNORECASE))
        is_css3_decision_q = bool(re.search(r'\b(css|css3)\b', question_text, re.IGNORECASE) and re.search(r'\b(decision|architectural|performance|optimization)\b', question_text, re.IGNORECASE))

        # 4. Apply strict rewriting if needed
        final_answer = cleaned_answer
        caution_note: Optional[str] = None
        status = "Resume Supported"
        badge_variant = "success"

        if is_10x_scale_q:
            # Enforce: Approach -> Technical reasoning -> Candidate connection (NO unverified Redis/Kafka/HPA assertions)
            status = "Resume Grounded"
            badge_variant = "info"
            answer_type = "Hypothetical / Technical"
            detected_intent = QuestionIntent.SCALABILITY
            caution_note = "Technical recommendations are framed conditionally to reflect honest scaling principles."

            # Structure answer cleanly
            tech_target = skill if skill and skill != "Technical" else "the system"
            final_answer = (
                f"For a 10x increase in volume, my approach would focus on isolating bottlenecks through proactive profiling and metrics. "
                f"I would first inspect slow database queries and execution plans to optimize indexing and eliminate full table scans. "
                f"Next, I would introduce connection pooling, review read-heavy access patterns to evaluate in-memory caching where applicable, "
                f"and configure read replicas if database reads become saturated. "
                f"Since my background includes working with {tech_target}, I would apply these scaling optimizations incrementally based on measured production constraints."
            )

        elif is_css3_decision_q and not any(k in evidence["raw_text_lower"] for k in ["bem", "content-visibility", "translate3d", "will-change"]):
            # Specific CSS3 performance question with only CSS3 on resume
            status = "Resume Grounded"
            badge_variant = "info"
            answer_type = "Conceptual / Knowledge"
            detected_intent = QuestionIntent.TECHNICAL_DECISION
            caution_note = "Scoped to avoid fabricating unverified CSS optimization projects while detailing solid styling practices."

            final_answer = (
                f"My resume highlights experience with CSS3, although it does not detail a standalone CSS performance refactor project. "
                f"If asked about this in an interview, I would explain that I approach CSS architecture by maintaining low selector specificity to minimize browser style recalculations, "
                f"using 'box-sizing: border-box' across components for predictable sizing, and structuring modular classes for reusability. "
                f"To prevent expensive layout reflows and repaints, I focus on animating composited properties like transform and opacity, "
                f"and test rendering performance using browser DevTools."
            )

        elif needs_rewrite:
            # Sanitize and rewrite into honest conditional response
            status = "Needs Caution"
            badge_variant = "warning"
            caution_note = f"Answer was revised to remove unverified claims ({'; '.join(rewrite_reasons)}) and framed conditionally."
            
            tech_target = skill if skill and skill != "Technical" else "this technology"
            final_answer = (
                f"When working with {tech_target}, my approach centers on understanding core mechanics and applying appropriate design patterns. "
                f"I would assess system requirements, ensure structured data validation, and optimize execution paths based on workload demands. "
                f"Based on the competencies listed in my resume, I would evaluate practical trade-offs and collaborate with the engineering team to implement reliable, maintainable solutions."
            )

        elif answer_type == "Hypothetical / Technical":
            status = "Resume Grounded"
            badge_variant = "info"
            caution_note = "Technical recommendations are hypothetical"

        grounding = AnswerGrounding(
            status=status,
            badge_variant=badge_variant,
            answer_type=answer_type,
            question_intent=detected_intent,
            answer_structure=answer_structure,
            evidence_used=evidence_used,
            unsupported_claims=unsupported_claims,
            caution_note=caution_note,
            claims_validation=claims_validation
        )

        return final_answer, grounding
