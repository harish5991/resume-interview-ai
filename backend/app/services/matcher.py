import re
import math
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.schemas.models import (
    ExtractedResume, JobDescriptionAnalysis, ResumeJobMatch,
    SkillGapAnalysis, LearningRoadmapItem
)
from backend.app.services.parser import ResumeParser, KNOWN_SKILLS

class JDMatcher:
    @staticmethod
    def analyze_job_description(text: str) -> JobDescriptionAnalysis:
        cleaned = ResumeParser.clean_text(text)
        lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
        
        # Title heuristic: look in first 3 lines
        title = "Software Engineer"
        for line in lines[:3]:
            if any(w in line.lower() for w in ["engineer", "developer", "architect", "analyst", "manager", "scientist", "specialist"]):
                title = line.split('-')[0].split('|')[0].strip()
                break

        # Company heuristic
        company = None
        for line in lines[:5]:
            if "at " in line.lower() or "company:" in line.lower():
                company = line.split("at ")[-1].split("company:")[-1].strip()
                break

        # Extract skills
        skills, _ = ResumeParser.extract_skills(cleaned)
        
        # Segment into required vs preferred
        lower = cleaned.lower()
        req_section = ""
        pref_section = ""
        
        if "preferred" in lower or "nice to have" in lower or "plus" in lower:
            parts = re.split(r'preferred|nice to have|good to have|bonus points', lower)
            req_section = parts[0]
            pref_section = parts[1] if len(parts) > 1 else ""
        else:
            req_section = lower

        req_skills, _ = ResumeParser.extract_skills(req_section)
        pref_skills, _ = ResumeParser.extract_skills(pref_section) if pref_section else ([], {})

        # Extract years of experience requirement
        exp_match = re.search(r'(\d+[\+]?\s*(?:to\s*\d+)?\s*(?:years|yrs)\b.*?(?:experience|exp))', cleaned, re.I)
        experience_years = exp_match.group(0) if exp_match else "1-3+ years"

        # Responsibilities
        resp_lines = []
        for line in lines:
            if line.startswith(('•', '-', '*', '1.', '2.', '3.')) and len(line) > 15:
                resp_lines.append(line.lstrip('•-*0123456789. '))

        # Top keywords (TF-IDF or frequency)
        words = re.findall(r'\b[a-zA-Z]{3,15}\b', cleaned.lower())
        stopwords = {"with", "and", "the", "for", "you", "our", "team", "will", "are", "have", "must", "work", "that", "this", "from", "your", "skills", "experience", "role", "years", "working", "using", "ability"}
        freq = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1
        keywords = [k.capitalize() for k, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:12]]

        return JobDescriptionAnalysis(
            title=title,
            company=company,
            required_skills=req_skills or skills[:8],
            preferred_skills=pref_skills or skills[8:12],
            responsibilities=resp_lines[:6],
            technologies=skills,
            experience_years=experience_years,
            keywords=keywords,
            summary=cleaned[:350],
            raw_text=cleaned
        )

    @classmethod
    def match_resume_and_jd(cls, resume: ExtractedResume, jd: JobDescriptionAnalysis) -> ResumeJobMatch:
        resume_skills_lower = {s.lower(): s for s in resume.skills}
        jd_skills_lower = {s.lower(): s for s in jd.technologies or jd.required_skills}

        matching = []
        missing = []
        for s_low, s_orig in jd_skills_lower.items():
            if s_low in resume_skills_lower:
                matching.append(s_orig)
            else:
                missing.append(s_orig)

        # Related/Partial skills (e.g. if JD has TypeScript and resume has JavaScript, or React vs Next.js)
        partial = []
        related_pairs = [
            ({"javascript", "typescript"}, "JavaScript / TypeScript ecosystem"),
            ({"react", "next.js", "vue", "angular"}, "Modern Frontend SPA Frameworks"),
            ({"sql", "postgresql", "mysql", "mongodb"}, "Database Management"),
            ({"docker", "kubernetes", "aws", "gcp"}, "Cloud & Containerization"),
            ({"fastapi", "flask", "django", "express", "node.js"}, "Backend API Development")
        ]
        for pair_set, label in related_pairs:
            res_has = any(s.lower() in resume_skills_lower for s in pair_set)
            jd_wants = any(s.lower() in jd_skills_lower for s in pair_set)
            if res_has and jd_wants and label not in partial:
                partial.append(label)

        # Cosine Similarity between Resume text and JD text
        corpus = [resume.raw_text, jd.raw_text]
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
            sim_score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception:
            sim_score = 0.5

        # Weighted calculation
        skill_ratio = len(matching) / max(1, len(jd_skills_lower)) if jd_skills_lower else 0.7
        semantic_score = sim_score * 100
        skill_score = skill_ratio * 100

        # Match % is weighted average of Skill overlap (65%) and Semantic TF-IDF similarity (35%)
        final_match_pct = int(min(100, max(25, (skill_score * 0.65) + (semantic_score * 0.35))))

        # Identify relevant projects
        relevant_projects = []
        for p in resume.projects:
            p_text = f"{p.title} {' '.join(p.technologies)} {' '.join(p.highlights)}".lower()
            if any(s.lower() in p_text for s in jd.required_skills) or any(k.lower() in p_text for k in jd.keywords[:6]):
                relevant_projects.append(f"{p.title} (covers {', '.join([s for s in p.technologies if s.lower() in jd_skills_lower][:3]) or 'relevant tech'})")

        if not relevant_projects and resume.projects:
            relevant_projects.append(f"{resume.projects[0].title} (demonstrates full-stack development lifecycle)")

        # Relevant experience
        relevant_exp = []
        for exp in resume.experience:
            e_text = f"{exp.role} {exp.company} {' '.join(exp.technologies)} {' '.join(exp.responsibilities)}".lower()
            if any(s.lower() in e_text for s in jd.required_skills):
                relevant_exp.append(f"{exp.role} at {exp.company}")

        # Summary & Explainable Rationale
        match_summary = (
            f"Candidate profile matches {final_match_pct}% of the '{jd.title}' requirements. "
            f"You possess {len(matching)} matching core skills including {', '.join(matching[:4]) or 'fundamental concepts'}. "
            f"{f'Missing {len(missing)} skills: ' + ', '.join(missing[:3]) if missing else 'Exceptional skill overlap!'}"
        )

        relevance_explanation = (
            f"The match score combines direct technical skill overlap ({int(skill_score)}%) with textual TF-IDF semantic relevance ({int(semantic_score)}%). "
            f"Your background with {', '.join(matching[:3]) if matching else 'your current stack'} aligns well with key responsibilities in the target role."
        )

        recommendations = []
        if missing:
            recommendations.append(f"Familiarize yourself with {', '.join(missing[:3])} fundamentals before the interview.")
        if len(relevant_projects) < 2:
            recommendations.append("Tailor your project descriptions to emphasize database architecture and scalability.")
        recommendations.append("Prepare STAR (Situation, Task, Action, Result) answers for your primary project.")

        return ResumeJobMatch(
            match_percentage=final_match_pct,
            matching_skills=matching,
            missing_skills=missing,
            partial_skills=partial,
            relevant_projects=relevant_projects,
            relevant_experience=relevant_exp,
            match_summary=match_summary,
            relevance_explanation=relevance_explanation,
            recommendations=recommendations
        )

    @classmethod
    def generate_skill_gap(cls, resume: ExtractedResume, jd: JobDescriptionAnalysis) -> SkillGapAnalysis:
        match_res = cls.match_resume_and_jd(resume, jd)
        strong = [s for s in resume.skills if s in match_res.matching_skills]
        
        roadmap: List[LearningRoadmapItem] = []
        for missing in match_res.missing_skills:
            # Estimate importance
            is_req = missing.lower() in [s.lower() for s in jd.required_skills]
            importance = "High" if is_req else "Medium"
            
            # Map topics
            topics = [f"{missing} Core Fundamentals", f"Integrating {missing} in Real-world Projects", f"Common {missing} Interview Questions & Best Practices"]
            resources = [f"Official {missing} Documentation", f"Interactive {missing} Crash Course (FreeCodeCamp/YouTube)", f"Building a Mini CRUD/Service using {missing}"]
            
            roadmap.append(LearningRoadmapItem(
                skill=missing,
                category="Target Job Requirement",
                importance=importance,
                current_level="Missing",
                target_level="Intermediate",
                estimated_hours=6 if importance == "High" else 4,
                key_topics=topics,
                learning_resources=resources
            ))

        summary = (
            f"Skill gap analysis identified {len(strong)} strong matching skills and {len(match_res.missing_skills)} missing skills. "
            f"Focusing on the high-importance skills ({', '.join([item.skill for item in roadmap if item.importance == 'High'][:3]) or 'all key skills'}) "
            f"will bridge the requirement gap quickly."
        )

        return SkillGapAnalysis(
            strong_skills=strong,
            matching_skills=match_res.matching_skills,
            missing_skills=match_res.missing_skills,
            learning_roadmap=roadmap,
            summary=summary
        )
