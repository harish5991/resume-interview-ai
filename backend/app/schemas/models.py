from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
import uuid

class SkillCategory(BaseModel):
    category: str
    skills: List[str]

class ProjectItem(BaseModel):
    title: str
    description: str
    technologies: List[str] = []
    highlights: List[str] = []
    role: Optional[str] = None
    link: Optional[str] = None

class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    location: Optional[str] = None
    responsibilities: List[str] = []
    technologies: List[str] = []

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    grade: Optional[str] = None

class CertificationItem(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None

class ExtractedResume(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    skill_categories: Dict[str, List[str]] = {}
    experience: List[ExperienceItem] = []
    projects: List[ProjectItem] = []
    education: List[EducationItem] = []
    certifications: List[CertificationItem] = []
    achievements: List[str] = []
    raw_text: str = ""
    filename: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResumeScoreBreakdown(BaseModel):
    overall_score: int
    skills_score: int
    projects_score: int
    experience_score: int
    education_score: int
    completeness_score: int
    relevance_score: int
    strengths: List[str] = []
    improvement_areas: List[str] = []
    rationale: str

class JobDescriptionAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Target Job"
    company: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    technologies: List[str] = []
    experience_years: Optional[str] = None
    keywords: List[str] = []
    summary: str = ""
    raw_text: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResumeJobMatch(BaseModel):
    match_percentage: int
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    partial_skills: List[str] = []
    relevant_projects: List[str] = []
    relevant_experience: List[str] = []
    match_summary: str
    relevance_explanation: str
    recommendations: List[str] = []

class GroundedQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    based_on: str  # e.g., "Project: Resume Interview AI", "Experience: Backend Dev at Acme", "Skill: MongoDB"
    skill: str     # e.g., "MongoDB", "FastAPI", "React"
    difficulty: str  # "Easy", "Medium", "Hard", "Expert"
    question_type: str  # "Resume Based", "Technical", "Project Based", "Behavioral", "HR", "Situational", "Job Description Based", "Mixed"
    why_this_question: str  # Explainable rationale
    expected_answer_points: List[str] = []
    sample_answer: Optional[str] = None
    is_bookmarked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GenerateQuestionsRequest(BaseModel):
    session_id: Optional[str] = "default"
    resume_id: Optional[str] = None
    resume_data: Optional[ExtractedResume] = None
    jd_id: Optional[str] = None
    jd_data: Optional[JobDescriptionAnalysis] = None
    difficulty: str = "Medium"
    question_type: str = "Mixed"
    count: int = 5
    exclude_question_hashes: List[str] = []

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "resume" in values and "resume_data" not in values:
                values["resume_data"] = values.get("resume")
            if "jd" in values and "jd_data" not in values:
                values["jd_data"] = values.get("jd")
            if "limit" in values and "count" not in values:
                values["count"] = values.get("limit")
        return values

class AnswerEvaluationRequest(BaseModel):
    session_id: Optional[str] = "default"
    question_id: str
    question_text: str
    based_on: str
    skill: str
    difficulty: str
    user_answer: str
    expected_points: Optional[List[str]] = []

class AnswerEvaluation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    overall_score: int
    relevance_score: int
    technical_accuracy_score: int
    completeness_score: int
    clarity_score: int
    confidence_score: int
    communication_score: int
    verdict_rating: str = "Adequate"
    concepts_covered: List[str] = []
    concepts_missed: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    improved_answer: str
    follow_up_question: Optional[str] = None
    next_recommended_difficulty: str = "Medium"
    feedback_summary: str = ""
    star_feedback: Optional[Dict[str, str]] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LearningRoadmapItem(BaseModel):
    skill: str
    category: str
    importance: str  # "High", "Medium", "Low"
    current_level: str  # "Missing", "Beginner", "Intermediate"
    target_level: str   # "Intermediate", "Advanced"
    estimated_hours: int
    key_topics: List[str] = []
    learning_resources: List[str] = []

class SkillGapAnalysis(BaseModel):
    strong_skills: List[str] = []
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    learning_roadmap: List[LearningRoadmapItem] = []
    summary: str

class ProjectDeepDive(BaseModel):
    project_name: str
    objective: str
    problem_statement: str
    architecture: str
    technologies: List[str] = []
    database_choice: str
    apis_design: str
    challenges_solutions: str
    security_aspects: str
    scalability_notes: str
    testing_strategy: str
    deployment_details: str
    future_improvements: str
    interview_questions: List[GroundedQuestion] = []

class ResumeImprovementItem(BaseModel):
    category: str  # "Impact & Metrics", "Skills", "Keywords", "Projects", "Formatting"
    issue: str
    suggestion: str
    impact_level: str  # "High", "Medium", "Low"
    example_before: Optional[str] = None
    example_after: Optional[str] = None

class TopicPreparationItem(BaseModel):
    topic: str
    importance: str
    why_it_matters: str
    resume_evidence: str
    expected_questions: List[str] = []
    recommended_level: str

class AnalyticsSummary(BaseModel):
    interview_readiness_score: int
    resume_score: int
    jd_match_percentage: int
    average_interview_score: int
    technical_score: int
    communication_score: int
    behavioral_score: int
    questions_attempted: int
    correct_answers: int
    weak_areas: List[Dict[str, Any]] = []
    strong_areas: List[Dict[str, Any]] = []
    score_trends: List[Dict[str, Any]] = []
    category_performance: List[Dict[str, Any]] = []
    difficulty_performance: List[Dict[str, Any]] = []

class SessionData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Session"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resume: Optional[ExtractedResume] = None
    resume_score: Optional[ResumeScoreBreakdown] = None
    jd: Optional[JobDescriptionAnalysis] = None
    match: Optional[ResumeJobMatch] = None
    questions: List[GroundedQuestion] = []
    saved_questions: List[GroundedQuestion] = []
    evaluations: List[AnswerEvaluation] = []
    history: List[Dict[str, Any]] = []
