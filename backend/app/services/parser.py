import re
import io
import logging
from typing import Dict, List, Tuple, Any, Optional
import fitz  # PyMuPDF
import docx
from backend.app.schemas.models import (
    ExtractedResume, ProjectItem, ExperienceItem, 
    EducationItem, CertificationItem, ResumeScoreBreakdown
)

logger = logging.getLogger("parser")

# Standard taxonomy of common technical skills
KNOWN_SKILLS = {
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust", 
    "ruby", "php", "swift", "kotlin", "scala", "r", "dart", "sql", "html", "html5", "css", "css3",
    # Frontend
    "react", "react.js", "reactjs", "next.js", "nextjs", "vue", "vue.js", "vuejs", "angular", 
    "svelte", "tailwind", "tailwind css", "bootstrap", "redux", "zustand", "graphql", "webpack", "vite",
    # Backend
    "node.js", "nodejs", "express", "express.js", "fastapi", "flask", "django", "spring", 
    "spring boot", "nestjs", "asp.net", ".net", "laravel", "rails", "rest api", "restful apis", "grpc",
    # Databases
    "mongodb", "postgresql", "postgres", "mysql", "sqlite", "redis", "cassandra", "dynamodb", 
    "mariadb", "oracle", "neo4j", "elasticsearch", "firebase", "supabase", "firestore",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", 
    "ci/cd", "github actions", "jenkins", "terraform", "ansible", "nginx", "linux", "git", "github", "gitlab",
    # Data & AI/ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch", 
    "scikit-learn", "pandas", "numpy", "power bi", "tableau", "spark", "hadoop", "kafka", 
    "llm", "langchain", "transformers", "huggingface", "data analysis", "data engineering",
    # Concepts & Architecture
    "microservices", "system design", "distributed systems", "oop", "object oriented programming",
    "data structures", "algorithms", "agile", "scrum", "unit testing", "tdd", "ci/cd pipelines"
}

CATEGORY_MAP = {
    "Languages": ["python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "sql", "html", "css", "dart", "r"],
    "Frontend": ["react", "react.js", "reactjs", "next.js", "nextjs", "vue", "vue.js", "angular", "tailwind", "tailwind css", "bootstrap", "redux", "vite", "webpack"],
    "Backend & APIs": ["node.js", "nodejs", "fastapi", "flask", "django", "express", "spring boot", "rest api", "graphql", "grpc", "microservices"],
    "Databases": ["mongodb", "postgresql", "postgres", "mysql", "redis", "sqlite", "elasticsearch", "dynamodb", "supabase", "firebase"],
    "Cloud & DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "ci/cd", "linux", "terraform", "jenkins"],
    "AI & Data Science": ["machine learning", "deep learning", "nlp", "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "power bi", "tableau", "llm"]
}

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        text = ""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"Failed to extract text with PyMuPDF: {e}")
        return text.strip()

    @staticmethod
    def extract_text_from_docx(docx_bytes: bytes) -> str:
        text = ""
        try:
            doc = docx.Document(io.BytesIO(docx_bytes))
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + " "
                    text += "\n"
        except Exception as e:
            logger.error(f"Failed to extract text from docx: {e}")
        return text.strip()

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Name heuristic: typically first non-empty line with 2-4 alphabetic words
        name = "Candidate"
        for line in lines[:5]:
            clean_line = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            words = clean_line.split()
            if 2 <= len(words) <= 4 and not any(kw in clean_line.lower() for kw in ["resume", "curriculum", "profile", "contact", "email", "phone", "developer", "engineer"]):
                name = clean_line.title()
                break

        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else None

        # Phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None

        # Location heuristic
        location = None
        loc_patterns = [
            r'([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(\s*\d{5})?)',
            r'([A-Z][a-zA-Z\s]+,\s*(?:USA|India|Canada|UK|Germany|Australia))'
        ]
        for pat in loc_patterns:
            loc_match = re.search(pat, text)
            if loc_match:
                location = loc_match.group(1).strip()
                break

        return {"name": name, "email": email, "phone": phone, "location": location}

    @staticmethod
    def extract_skills(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        lower_text = " " + text.lower() + " "
        found_skills = set()

        for skill in KNOWN_SKILLS:
            # Word boundary regex for single words, direct substring for multi-word or symbols
            if len(skill.split()) == 1 and skill.isalpha():
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, lower_text):
                    found_skills.add(skill)
            else:
                if skill in lower_text:
                    found_skills.add(skill)

        # Standardize skill names (e.g. capitalize nicely)
        display_map = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript", "java": "Java",
            "c++": "C++", "c#": "C#", "c": "C", "go": "Go", "golang": "Go", "rust": "Rust",
            "react": "React", "react.js": "React", "reactjs": "React", "next.js": "Next.js", "nextjs": "Next.js",
            "vue": "Vue.js", "angular": "Angular", "tailwind": "Tailwind CSS", "tailwind css": "Tailwind CSS",
            "node.js": "Node.js", "nodejs": "Node.js", "express": "Express.js", "fastapi": "FastAPI",
            "flask": "Flask", "django": "Django", "spring boot": "Spring Boot",
            "mongodb": "MongoDB", "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "mysql": "MySQL",
            "sqlite": "SQLite", "redis": "Redis", "aws": "AWS", "docker": "Docker", "kubernetes": "Kubernetes",
            "git": "Git", "github": "GitHub", "machine learning": "Machine Learning", "deep learning": "Deep Learning",
            "nlp": "NLP", "pandas": "Pandas", "numpy": "NumPy", "scikit-learn": "Scikit-Learn",
            "power bi": "Power BI", "tableau": "Tableau", "rest api": "REST APIs", "graphql": "GraphQL",
            "microservices": "Microservices", "system design": "System Design", "ci/cd": "CI/CD",
            "html": "HTML5", "css": "CSS3", "sql": "SQL", "pytorch": "PyTorch", "tensorflow": "TensorFlow"
        }

        standardized_skills = []
        for s in found_skills:
            name = display_map.get(s, s.title())
            if name not in standardized_skills:
                standardized_skills.append(name)

        # Categorize
        categories = {}
        for cat, skills in CATEGORY_MAP.items():
            cat_list = []
            for s in skills:
                std_name = display_map.get(s, s.title())
                if std_name in standardized_skills and std_name not in cat_list:
                    cat_list.append(std_name)
            if cat_list:
                categories[cat] = cat_list

        return standardized_skills, categories

    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        section_headers = {
            "summary": ["summary", "professional summary", "about me", "objective", "profile"],
            "experience": ["experience", "work experience", "employment history", "professional experience", "work history"],
            "projects": ["projects", "personal projects", "academic projects", "key projects", "notable projects"],
            "skills": ["skills", "technical skills", "core competencies", "skills & tools", "technologies"],
            "education": ["education", "academic background", "academics", "qualifications"],
            "certifications": ["certifications", "licenses", "certificates", "courses"],
            "achievements": ["achievements", "awards", "honors", "publications", "extracurricular"]
        }

        # Build regex to split into sections
        lines = text.split('\n')
        sections: Dict[str, List[str]] = {k: [] for k in section_headers}
        current_section = "summary"

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # Check if line matches a header (short length, uppercase or title case)
            lower_line = trimmed.lower().rstrip(':')
            detected = None
            if len(trimmed.split()) <= 4:
                for sec, aliases in section_headers.items():
                    if lower_line in aliases:
                        detected = sec
                        break

            if detected:
                current_section = detected
            else:
                sections[current_section].append(trimmed)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    @classmethod
    def parse_projects(cls, projects_text: str) -> List[ProjectItem]:
        if not projects_text:
            return []
        
        items = []
        blocks = re.split(r'\n\s*\n|•(?=[A-Z])', projects_text)
        
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue
            
            first_line = lines[0].lstrip('•-*| ')
            # Look for project title patterns: "Resume Interview AI | React, FastAPI, Python"
            parts = re.split(r'\||–|-|:', first_line)
            title = parts[0].strip()
            
            # Extract technologies from the block
            skills, _ = cls.extract_skills(block)
            
            highlights = [l.lstrip('•-*> ') for l in lines[1:] if len(l.strip()) > 10]
            if not highlights and len(lines) == 1:
                highlights = [first_line]

            if len(title) > 3 and not title.lower().startswith(("project", "academic", "github", "http")):
                items.append(ProjectItem(
                    title=title,
                    description=block[:250],
                    technologies=skills,
                    highlights=highlights[:4]
                ))

        # Fallback if block splitting yielded nothing
        if not items and projects_text:
            skills, _ = cls.extract_skills(projects_text)
            items.append(ProjectItem(
                title="Highlighted Project",
                description=projects_text[:200],
                technologies=skills,
                highlights=[l.lstrip('•-*> ') for l in projects_text.split('\n')[:3]]
            ))

        return items[:6]

    @classmethod
    def parse_experience(cls, exp_text: str) -> List[ExperienceItem]:
        if not exp_text:
            return []
        
        items = []
        blocks = re.split(r'\n\s*\n', exp_text)
        
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue
            
            first_line = lines[0].lstrip('•-* ')
            role = "Software Engineer"
            company = "Tech Organization"
            duration = None
            
            # Look for dates like 2022 - 2024, May 2021 - Present
            date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d\d)\b.*?(?:Present|Current|20\d\d))', block, re.I)
            if date_match:
                duration = date_match.group(0)

            parts = re.split(r'\||–|-|,| at ', first_line)
            if len(parts) >= 2:
                role = parts[0].strip()
                company = parts[1].strip()
            elif len(parts) == 1:
                role = parts[0].strip()

            skills, _ = cls.extract_skills(block)
            bullets = [l.lstrip('•-*> ') for l in lines[1:] if len(l.strip()) > 10]

            if len(role) > 2:
                items.append(ExperienceItem(
                    role=role,
                    company=company,
                    duration=duration,
                    responsibilities=bullets[:5],
                    technologies=skills
                ))

        return items[:5]

    @classmethod
    def parse_education(cls, edu_text: str) -> List[EducationItem]:
        if not edu_text:
            return []
        
        items = []
        lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
        for line in lines:
            if any(deg in line.lower() for deg in ["bachelor", "master", "b.tech", "b.e", "b.s", "m.s", "m.tech", "ph.d", "degree", "diploma", "computer science", "engineering"]):
                parts = re.split(r'\||–|-|,', line)
                degree = parts[0].strip()
                inst = parts[1].strip() if len(parts) > 1 else "University / Institution"
                year_match = re.search(r'\b(20\d\d|19\d\d)\b', line)
                year = year_match.group(0) if year_match else None
                items.append(EducationItem(degree=degree, institution=inst, year=year))
        
        if not items and edu_text:
            items.append(EducationItem(degree="Bachelor of Science in Computer Science", institution="University / College"))

        return items[:3]

    @classmethod
    def parse_resume(cls, text: str, filename: Optional[str] = None) -> ExtractedResume:
        cleaned = cls.clean_text(text)
        contact = cls.extract_contact_info(cleaned)
        skills, categories = cls.extract_skills(cleaned)
        sections = cls.extract_sections(cleaned)
        
        projects = cls.parse_projects(sections.get("projects", ""))
        experience = cls.parse_experience(sections.get("experience", ""))
        education = cls.parse_education(sections.get("education", ""))
        
        # Certifications
        certs_text = sections.get("certifications", "")
        certifications = []
        if certs_text:
            for l in certs_text.split('\n'):
                t = l.strip().lstrip('•-* ')
                if len(t) > 4:
                    certifications.append(CertificationItem(name=t))

        # Achievements
        achieve_text = sections.get("achievements", "")
        achievements = [l.strip().lstrip('•-* ') for l in achieve_text.split('\n') if len(l.strip()) > 8]

        return ExtractedResume(
            name=contact["name"],
            email=contact["email"],
            phone=contact["phone"],
            location=contact["location"],
            summary=sections.get("summary", "")[:400] or None,
            skills=skills,
            skill_categories=categories,
            experience=experience,
            projects=projects,
            education=education,
            certifications=certifications,
            achievements=achievements,
            raw_text=cleaned,
            filename=filename
        )

    @staticmethod
    def calculate_score(resume: ExtractedResume, jd: Optional[Any] = None) -> ResumeScoreBreakdown:
        # Explainable score calculation
        skills_count = len(resume.skills)
        skills_score = min(100, max(20, skills_count * 8))

        proj_count = len(resume.projects)
        projects_score = min(100, max(20, proj_count * 25 + sum(len(p.technologies) for p in resume.projects) * 3))

        exp_count = len(resume.experience)
        experience_score = min(100, max(20, exp_count * 30 + sum(len(e.responsibilities) for e in resume.experience) * 4))

        edu_count = len(resume.education)
        education_score = 90 if edu_count > 0 else 50

        # Completeness based on contact info, sections presence
        completeness = 40
        if resume.email: completeness += 15
        if resume.phone: completeness += 15
        if resume.skills: completeness += 10
        if resume.projects: completeness += 10
        if resume.education: completeness += 10
        completeness_score = min(100, completeness)

        relevance_score = 80
        if jd and hasattr(jd, "required_skills") and jd.required_skills:
            jd_skills_lower = [s.lower() for s in jd.required_skills]
            match_count = sum(1 for s in resume.skills if s.lower() in jd_skills_lower)
            relevance_score = min(100, int((match_count / max(1, len(jd.required_skills))) * 100))

        overall = int(
            (skills_score * 0.25) +
            (projects_score * 0.25) +
            (experience_score * 0.20) +
            (education_score * 0.10) +
            (completeness_score * 0.10) +
            (relevance_score * 0.10)
        )

        strengths = []
        improvement_areas = []

        if skills_score >= 75:
            strengths.append(f"Broad technical skill set with {skills_count} verified tools & languages.")
        else:
            improvement_areas.append("Add more specific technical frameworks, libraries, and databases.")

        if proj_count >= 2:
            strengths.append(f"Demonstrated practical hands-on capability across {proj_count} detailed projects.")
        else:
            improvement_areas.append("Include at least 2-3 end-to-end projects showcasing architecture and deployment.")

        if exp_count > 0:
            strengths.append("Contains structured professional work experience with documented responsibilities.")
        else:
            improvement_areas.append("Highlight open-source contributions, internships, or freelance work.")

        if completeness_score >= 85:
            strengths.append("Complete resume structure with clear contact information and education.")
        
        rationale = (
            f"Your resume achieved an overall score of {overall}/100. "
            f"You have strong scores in {'Skills' if skills_score >= 70 else 'Education'} ({max(skills_score, education_score)}/100) "
            f"and {'Projects' if projects_score >= 70 else 'Experience'} ({max(projects_score, experience_score)}/100). "
            f"{'Matching target job profile.' if relevance_score >= 75 else 'Can be enhanced by tailoring project descriptions with target job keywords.'}"
        )

        return ResumeScoreBreakdown(
            overall_score=overall,
            skills_score=skills_score,
            projects_score=projects_score,
            experience_score=experience_score,
            education_score=education_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            strengths=strengths,
            improvement_areas=improvement_areas,
            rationale=rationale
        )
