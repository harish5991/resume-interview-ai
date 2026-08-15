import re
import hashlib
import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from backend.app.config import settings
from backend.app.schemas.models import (
    ExtractedResume, JobDescriptionAnalysis, GroundedQuestion,
    AnswerEvaluation, ProjectDeepDive, ResumeImprovementItem,
    TopicPreparationItem
)

logger = logging.getLogger("ai_engine")

class QuestionCatalog:
    """Deterministic, highly grounded question templates linked to specific skills, project roles, and difficulty levels."""
    
    SKILL_QUESTIONS = {
        "Python": {
            "Easy": [
                ("What are the key differences between lists and tuples in Python, and when would you prefer one over the other?",
                 "Tests core data structures and mutability understanding.",
                 ["Tuples are immutable; lists are mutable", "Tuples have lower memory overhead", "Tuples can be used as dictionary keys if hashable"]),
                ("How does Python handle memory management and garbage collection?",
                 "Checks awareness of reference counting and cyclic garbage collection in CPython.",
                 ["Reference counting mechanism", "Generational cyclic garbage collector (gc module)", "Memory leaks via circular references"]),
            ],
            "Medium": [
                ("How do Python generators and the `yield` keyword optimize memory in data-heavy pipelines?",
                 "Evaluates understanding of lazy evaluation and generator iterators.",
                 ["Generators yield items one by one instead of loading full list in RAM", "State retention between yield calls", "Memory profiling comparison"]),
                ("Explain how Python decorators work under the hood and provide an example use case like logging or authentication.",
                 "Tests first-class function handling and closure concepts.",
                 ["Functions as first-class objects", "Wrapper function around the original function", "Common use cases: caching, RBAC, execution timing"]),
            ],
            "Hard": [
                ("How does the Global Interpreter Lock (GIL) affect multithreading in CPU-bound vs I/O-bound Python programs?",
                 "Assesses deep concurrency understanding in CPython.",
                 ["GIL prevents multiple native threads from executing Python bytecodes simultaneously", "I/O bound benefits from threading/asyncio", "CPU bound requires multiprocessing"]),
                ("How would you profile and optimize a memory-heavy Python service experiencing latency spikes?",
                 "Tests production observability, profiling tools (cProfile, tracemalloc), and algorithmic efficiency.",
                 ["Profiling with cProfile, line_profiler, tracemalloc", "Vectorization with NumPy/Pandas", "Slot usage in classes, async I/O"]),
            ],
            "Expert": [
                ("How would you architect an async distributed worker queue in Python with graceful failure recovery and backpressure?",
                 "Evaluates production-scale distributed systems design in Python.",
                 ["Celery/RQ/FastStream integration", "Dead-letter queues and exponential backoff", "Prefetch limits and worker starvation handling"]),
            ]
        },
        "FastAPI": {
            "Easy": [
                ("What are the primary benefits of FastAPI compared to traditional frameworks like Flask or Django?",
                 "Evaluates knowledge of modern asynchronous Python frameworks.",
                 ["Native async/await support with Starlette", "Automatic OpenAPI/Swagger docs generation", "Pydantic validation for request/response bodies"]),
            ],
            "Medium": [
                ("How does FastAPI utilize Pydantic models for request validation and serialization?",
                 "Tests data validation, type hints, and API security.",
                 ["Automatic 422 Unprocessable Entity responses for invalid types", "Serialization to JSON", "Nested models and field validators"]),
                ("How do dependency injection and `Depends()` work in FastAPI for database sessions or JWT auth?",
                 "Assesses architectural pattern understanding in FastAPI.",
                 ["Hierarchical dependency resolution", "Yield dependencies for cleanup (closing DB sessions)", "Security scopes and reusable auth middleware"]),
            ],
            "Hard": [
                ("How do you handle background tasks, database connection pooling, and lifecycle events gracefully in FastAPI?",
                 "Tests production reliability and resource management under high throughput.",
                 ["FastAPI Lifespan context managers", "Connection pool configuration with asyncpg/motor", "Async BackgroundTasks vs dedicated Celery queue"]),
            ],
            "Expert": [
                ("How would you design a rate-limiting and token-bucket middleware in FastAPI to protect high-traffic public endpoints?",
                 "Assesses high-throughput API protection and distributed caching.",
                 ["Redis-backed token bucket algorithm", "Client IP / JWT claims identification", "HTTP 429 Too Many Requests with Retry-After header"]),
            ]
        },
        "React": {
            "Easy": [
                ("What is the difference between props and state in React, and how does one-way data flow work?",
                 "Tests foundational component architecture.",
                 ["Props are passed from parent (read-only); state is managed internally", "Unidirectional data flow simplifies debugging", "State updates trigger re-renders"]),
            ],
            "Medium": [
                ("Explain how `useEffect` works, including its dependency array and cleanup function.",
                 "Evaluates lifecycle management and side-effect handling.",
                 ["Runs after render", "Empty array = run once on mount; with dependencies = run when values change", "Cleanup function runs on unmount or before re-run"]),
                ("What are the differences between client-side state (useState/Zustand) and server state (React Query/SWR)?",
                 "Tests modern state management architecture.",
                 ["Server state requires caching, deduplication, invalidation, loading states", "Client UI state is ephemeral", "Minimizing global state pollution"]),
            ],
            "Hard": [
                ("How would you diagnose and prevent unnecessary re-renders in a complex React dashboard with high-frequency data?",
                 "Assesses performance optimization and rendering internals.",
                 ["React DevTools Profiler", "useMemo, useCallback, React.memo usage", "State localization and selector-based subscriptions"]),
            ],
            "Expert": [
                ("How does React 18 Concurrent Mode (Transitions, Suspense, Server Components) improve UI responsiveness under heavy loads?",
                 "Evaluates deep knowledge of modern frontend rendering architecture.",
                 ["Fiber reconciler time-slicing", "useTransition for non-urgent updates", "Streaming SSR with Suspense boundaries"]),
            ]
        },
        "MongoDB": {
            "Easy": [
                ("What is the primary difference between a relational database and a document database like MongoDB?",
                 "Evaluates schema flexibility vs relational integrity understanding.",
                 ["BSON document model vs rigid tabular schemas", "Horizontal scaling capability", "Flexible schema evolution for nested JSON"]),
            ],
            "Medium": [
                ("When would you choose embedding documents versus referencing (linking) documents in MongoDB?",
                 "Tests data modeling and query optimization.",
                 ["Embed for 1-to-1 or 1-to-few relationships accessed together", "Reference for 1-to-many unbounded relationships to avoid 16MB document limit", "Atomicity within a single document"]),
                ("How does the MongoDB Aggregation Pipeline work, and what are common stages like `$match`, `$group`, `$lookup`?",
                 "Assesses multi-stage data processing and analytics capabilities.",
                 ["Pipeline passes documents through transform stages", "$match early for index usage", "$lookup for relational joins", "$group for aggregations"]),
            ],
            "Hard": [
                ("How do compound indexes and index prefixing impact query performance and write latency in MongoDB?",
                 "Assesses indexing strategy and query execution plans.",
                 ["Equality, Sort, Range (ESR) rule", "Index prefixes support subset queries", "Over-indexing increases write amplification"]),
            ],
            "Expert": [
                ("How would you design a sharding key strategy for a multi-tenant MongoDB cluster to avoid hotspotting?",
                 "Assesses large-scale distributed database architecture.",
                 ["Selecting high-cardinality shard key", "Compound shard key with tenantId + hashed field", "Chunk balancing and jumbo chunk avoidance"]),
            ]
        },
        "SQL": {
            "Easy": [
                ("Explain the differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
                 "Evaluates relational algebra and SQL joining fundamentals.",
                 ["INNER JOIN returns matched rows in both", "LEFT JOIN returns all left rows + matching right rows", "NULL handling for unmatched rows"]),
            ],
            "Medium": [
                ("What are database transactions, and how do ACID properties ensure data consistency?",
                 "Tests database reliability principles.",
                 ["Atomicity, Consistency, Isolation, Durability", "Commit and Rollback", "Isolation levels (Read Committed, Repeatable Read, Serializable)"]),
                ("How do indexes work internally in relational databases (B-Tree vs Hash), and when does an index slow down queries?",
                 "Assesses query execution and storage engine internals.",
                 ["B-Tree indexes support range and equality scans", "Index maintenance cost on INSERT/UPDATE/DELETE", "Table scans vs index seek"]),
            ],
            "Hard": [
                ("Explain Window Functions (e.g. `ROW_NUMBER()`, `RANK()`, `PARTITION BY`) and how they differ from `GROUP BY`.",
                 "Evaluates advanced SQL data processing and analytics.",
                 ["Window functions retain individual row identities while computing aggregates", "PARTITION BY creates logical frames", "Running totals and ranking queries"]),
            ],
            "Expert": [
                ("How would you diagnose a query deadlock in PostgreSQL/MySQL and restructure queries to prevent locking contention?",
                 "Assesses production transaction management and concurrency debugging.",
                 ["Lock acquisition order consistency", "Shortening transaction duration", "Row-level locking with SELECT FOR UPDATE SKIP LOCKED"]),
            ]
        },
        "Docker": {
            "Easy": [
                ("What is the difference between a Docker image and a Docker container?",
                 "Tests core containerization concepts.",
                 ["Image is a static read-only template; container is a running instance with a writable layer", "Layered filesystem", "Reproducibility across environments"]),
            ],
            "Medium": [
                ("How do multi-stage Docker builds reduce image size and improve container security?",
                 "Tests production container optimization.",
                 ["Separate build environment with heavy compilers from lean runtime image", "Excludes source build tools and intermediate artifacts", "Reduces vulnerability attack surface"]),
            ],
            "Hard": [
                ("How do Docker networking modes (bridge, host, overlay) work, and how do containers resolve DNS within user-defined networks?",
                 "Assesses container orchestration networking fundamentals.",
                 ["Embedded DNS server in user-defined bridge networks", "Host mode skips network namespace isolation for speed", "Overlay networks for swarm/multi-host communication"]),
            ],
            "Expert": [
                ("How would you secure containerized microservices in production regarding rootless execution, cgroups, and seccomp profiles?",
                 "Assesses container security hardening and Linux namespace isolation.",
                 ["Non-root user in Dockerfile", "Read-only root filesystem", "Dropping Linux capabilities (CAP_DROP ALL)", "cgroups memory/CPU limits"]),
            ]
        }
    }

    BEHAVIORAL_QUESTIONS = [
        ("Tell me about a challenging technical hurdle you faced in one of your projects and how you diagnosed and resolved it.",
         "Project Experience",
         "Evaluates problem-solving methodology, debugging persistence, and ownership.",
         ["Clearly define the problem", "Explain diagnostic steps and tools used", "Describe the solution and measurable outcome", "What you learned"]),
        ("Describe a situation where you had to quickly learn a new framework or technology to deliver a feature under a tight deadline.",
         "Adaptability & Learning",
         "Assesses continuous learning, agility, and time management.",
         ["Context of the project requirement", "Systematic approach to learning (docs, tutorials, prototyping)", "Timely execution and quality delivery"]),
        ("How do you handle disagreements with a peer or team member regarding architectural choices or code reviews?",
         "Collaboration & Teamwork",
         "Tests professional communication, constructive feedback, and ego-free decision making.",
         ["Focus on data, benchmarks, and project requirements rather than personal preferences", "Active listening to alternate viewpoints", "Testing prototypes to decide objectively", "Committing to the final consensus"]),
        ("Tell me about a time when a production feature you built failed or had an unexpected bug. How did you respond?",
         "Accountability & Post-Mortem",
         "Assesses ownership, incident response, and root-cause analysis.",
         ["Immediate mitigation and rollback/hotfix", "Transparent communication with stakeholders", "Blameless post-mortem and adding regression tests"])
    ]

    PROJECT_TEMPLATES = [
        ("In your project '{title}', what was the primary architectural trade-off you made when selecting {tech}?",
         "Project: {title}",
         "Tests architectural justification and practical decision-making in real project contexts.",
         ["Why {tech} was selected over alternatives", "Performance or scalability implications", "Limitations or challenges encountered"]),
        ("How did you ensure data integrity, API validation, and error handling across '{title}'?",
         "Project: {title}",
         "Evaluates production-readiness, robust input validation, and defensive programming.",
         ["Request validation mechanisms", "Global exception handlers and clear HTTP status codes", "Database transaction safety"]),
        ("If '{title}' were to experience a 50x increase in concurrent users, what would be the first bottleneck and how would you scale it?",
         "Project: {title}",
         "Assesses system design, caching, database query optimization, and horizontal scaling.",
         ["Identifying bottlenecks (DB read/write, API compute, memory)", "Introducing caching (Redis) or CDN", "Database indexing and connection pooling", "Horizontal pod autoscaling"]),
        ("Can you walk me through the end-to-end data flow in '{title}' from when a user triggers an action to when data is persisted?",
         "Project: {title}",
         "Tests full-stack clarity and complete mental model of the project implementation.",
         ["Client UI event dispatch", "API request payload & routing", "Business logic execution", "Database query and response formatting"])
    ]


class AIEngine:
    @staticmethod
    def _generate_hash(text: str) -> str:
        return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

    @classmethod
    async def generate_questions(
        cls,
        resume: ExtractedResume,
        jd: Optional[JobDescriptionAnalysis] = None,
        difficulty: str = "Medium",
        question_type: str = "Mixed",
        count: int = 5,
        exclude_hashes: Optional[List[str]] = None
    ) -> List[GroundedQuestion]:
        """Generates grounded, explainable questions with strict duplicate prevention."""
        exclude_set = set(exclude_hashes or [])
        generated: List[GroundedQuestion] = []

        # Candidate's extracted entities
        skills = resume.skills if resume.skills else ["Python", "SQL", "React", "FastAPI"]
        projects = resume.projects if resume.projects else [
            type("Proj", (), {"title": "Full-Stack Web App", "technologies": skills[:3], "highlights": ["Built REST APIs"]})()
        ]
        experience = resume.experience if resume.experience else []

        # Target JD skills
        jd_skills = jd.technologies if jd and jd.technologies else []

        # 1. Check if Gemini / LLM is configured
        if settings.GEMINI_API_KEY:
            try:
                llm_questions = await cls._generate_with_gemini(
                    resume=resume,
                    jd=jd,
                    difficulty=difficulty,
                    question_type=question_type,
                    count=count,
                    exclude_hashes=list(exclude_set)
                )
                if llm_questions and len(llm_questions) >= 1:
                    for q in llm_questions:
                        q_hash = cls._generate_hash(q.question)
                        if q_hash not in exclude_set:
                            generated.append(q)
                            exclude_set.add(q_hash)
                    if len(generated) >= count:
                        return generated[:count]
            except Exception as e:
                logger.warning(f"Gemini generation fallback to grounded catalog: {e}")

        # 2. Deterministic Grounded Catalog Generation (Guaranteed grounded & duplicate-free)
        candidate_pool: List[Tuple[str, str, str, str, str, str, List[str], str]] = []

        # (a) Project Based questions
        for p in projects:
            p_tech = p.technologies if p.technologies else skills[:2]
            main_tech = p_tech[0] if p_tech else "Architecture"
            for tmpl, based_tmpl, why, pts in QuestionCatalog.PROJECT_TEMPLATES:
                q_text = tmpl.format(title=p.title, tech=main_tech)
                b_text = based_tmpl.format(title=p.title)
                pts_formatted = [pt.format(tech=main_tech) for pt in pts]
                candidate_pool.append((
                    q_text,
                    b_text,
                    main_tech,
                    difficulty,
                    "Project Based",
                    why,
                    pts_formatted,
                    f"In '{p.title}', we utilized {main_tech} to handle core business logic efficiently with modular separation of concerns."
                ))

        # (b) Technical & Resume Based questions
        for skill in skills:
            skill_catalog = QuestionCatalog.SKILL_QUESTIONS.get(skill)
            if not skill_catalog:
                # Find matching root
                for k, v in QuestionCatalog.SKILL_QUESTIONS.items():
                    if k.lower() in skill.lower() or skill.lower() in k.lower():
                        skill_catalog = v
                        break

            if skill_catalog:
                diff_list = skill_catalog.get(difficulty) or skill_catalog.get("Medium", [])
                for q_text, why, pts in diff_list:
                    candidate_pool.append((
                        q_text,
                        f"Resume Skill: {skill}",
                        skill,
                        difficulty,
                        "Technical",
                        f"Tests in-depth expertise in {skill} listed on your resume.",
                        pts,
                        f"A strong answer should clearly address the core mechanism of {skill} with concrete production examples."
                    ))

        # (c) JD Based questions
        if jd and jd.required_skills:
            for jd_s in jd.required_skills[:4]:
                in_resume = any(jd_s.lower() == s.lower() for s in skills)
                based = f"JD Requirement: {jd_s} (Present in Resume)" if in_resume else f"JD Target Skill: {jd_s} (Job Requirement)"
                candidate_pool.append((
                    f"The target job requires solid experience with {jd_s}. How have you applied {jd_s} in your projects, or how would you ramp up?",
                    based,
                    jd_s,
                    difficulty,
                    "Job Description Based",
                    f"Directly assesses qualification for the key required skill '{jd_s}' in the job description.",
                    [f"Core understanding of {jd_s}", f"Practical project application or learning plan", "Best practices"],
                    f"Explain your hands-on experience or outline your fast learning roadmap for {jd_s}."
                ))

        # (d) Behavioral & Situational
        for q_text, topic, why, pts in QuestionCatalog.BEHAVIORAL_QUESTIONS:
            candidate_pool.append((
                q_text,
                f"Candidate Experience: {topic}",
                "Soft Skills & Communication",
                difficulty,
                "Behavioral",
                why,
                pts,
                "Use the STAR method (Situation, Task, Action, Result) highlighting measurable impact and team collaboration."
            ))

        # Filter by requested question_type if specified and not 'Mixed'
        if question_type != "Mixed":
            type_filtered = [c for c in candidate_pool if c[4].lower() == question_type.lower() or question_type.lower() in c[4].lower()]
            if type_filtered:
                candidate_pool = type_filtered

        # Shuffle candidate pool with deterministic seed variation
        random.shuffle(candidate_pool)

        for item in candidate_pool:
            q_text, based, skill, diff, q_type, why, pts, sample = item
            q_hash = cls._generate_hash(q_text)
            if q_hash not in exclude_set:
                exclude_set.add(q_hash)
                generated.append(GroundedQuestion(
                    question=q_text,
                    based_on=based,
                    skill=skill,
                    difficulty=diff,
                    question_type=q_type,
                    why_this_question=why,
                    expected_answer_points=pts,
                    sample_answer=sample
                ))
            if len(generated) >= count:
                break

        # Fallback if pool exhausted
        if len(generated) < count:
            for i in range(count - len(generated)):
                tech = skills[i % len(skills)] if skills else "Web Development"
                q_text = f"Can you explain a key performance or architectural decision you made when working with {tech}?"
                q_hash = cls._generate_hash(q_text + str(i))
                if q_hash not in exclude_set:
                    exclude_set.add(q_hash)
                    generated.append(GroundedQuestion(
                        question=q_text,
                        based_on=f"Resume Skill: {tech}",
                        skill=tech,
                        difficulty=difficulty,
                        question_type="Technical",
                        why_this_question=f"Tests practical design and trade-off evaluation in {tech}.",
                        expected_answer_points=["Clear problem statement", f"Why {tech} was applied", "Measurable result"],
                        sample_answer="Discuss the technical challenge, solution, and performance outcome."
                    ))

        return generated[:count]

    @classmethod
    async def _generate_with_gemini(
        cls,
        resume: ExtractedResume,
        jd: Optional[JobDescriptionAnalysis],
        difficulty: str,
        question_type: str,
        count: int,
        exclude_hashes: List[str]
    ) -> List[GroundedQuestion]:
        """Calls Google Gemini API for dynamic grounded questions."""
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are a senior technical interviewer. Generate exactly {count} interview questions.

CANDIDATE RESUME SUMMARY:
Name: {resume.name}
Skills: {', '.join(resume.skills)}
Projects: {', '.join([f"{p.title} ({', '.join(p.technologies)})" for p in resume.projects])}
Experience: {', '.join([f"{e.role} at {e.company}" for e in resume.experience])}

TARGET JOB DESCRIPTION:
Title: {jd.title if jd else "Software Developer"}
Required Skills: {', '.join(jd.required_skills) if jd else "General Tech Stack"}

REQUIREMENTS:
- Difficulty: {difficulty}
- Question Type: {question_type}
- STRICT GROUNDING: Every question MUST be grounded strictly in the candidate's actual projects, skills, or experience from their resume, or target JD. Do NOT invent projects, technologies, or companies not listed above.
- EXPLAINABILITY: Include 'why_this_question' explaining why this question is being asked.
- Output valid JSON only, a list of objects with keys:
  "question": string,
  "based_on": string (e.g. "Project: X" or "Skill: Y"),
  "skill": string,
  "difficulty": "{difficulty}",
  "question_type": "{question_type}",
  "why_this_question": string,
  "expected_answer_points": list of strings,
  "sample_answer": string

JSON Output:"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        results = []
        for item in data:
            results.append(GroundedQuestion(
                question=item.get("question", ""),
                based_on=item.get("based_on", f"Resume Skill: {item.get('skill', 'General')}"),
                skill=item.get("skill", "General"),
                difficulty=item.get("difficulty", difficulty),
                question_type=item.get("question_type", question_type),
                why_this_question=item.get("why_this_question", "Tests core technical domain understanding."),
                expected_answer_points=item.get("expected_answer_points", []),
                sample_answer=item.get("sample_answer", "")
            ))
        return results

    @classmethod
    async def evaluate_answer(
        cls,
        question_id: str,
        question_text: str,
        based_on: str,
        skill: str,
        difficulty: str,
        user_answer: str,
        expected_points: Optional[List[str]] = None
    ) -> AnswerEvaluation:
        """Deep, rigorous evaluation of a candidate's answer across 6 criteria with concepts extraction, STAR analysis, and adaptive follow-up."""
        cleaned_answer = user_answer.strip()
        lower_ans = cleaned_answer.lower()
        words = lower_ans.split()
        word_count = len(words)
        
        # Check for empty or trivial answers
        if word_count < 6:
            pts_str = ", ".join(expected_points[:3]) if expected_points else f"{skill} implementation best practices and trade-offs"
            concrete_model_ans = (
                f"Model response for '{question_text}': In our system, we addressed this by utilizing {skill} with a focus on {pts_str}. "
                f"We established clear architecture boundaries, optimized data handling and query execution, and validated error handling under edge cases. "
                f"This approach provided resilient throughput, minimal processing overhead, and predictable production latency."
            )
            return AnswerEvaluation(
                question_id=question_id,
                overall_score=25,
                relevance_score=30,
                technical_accuracy_score=20,
                completeness_score=15,
                clarity_score=40,
                confidence_score=30,
                communication_score=35,
                verdict_rating="Incomplete / Insufficient",
                concepts_covered=[],
                concepts_missed=expected_points or [f"{skill} core mechanism", "Production trade-offs", "Concrete implementation"],
                strengths=["Submitted an initial response."],
                weaknesses=[
                    "Answer is too short to evaluate technical depth or architectural competence.",
                    "Did not explain why this approach was selected, how it operates, or what trade-offs were considered."
                ],
                improved_answer=concrete_model_ans,
                follow_up_question=f"Can you walk me through a specific code or architecture example where you implemented {skill}?",
                next_recommended_difficulty="Easy",
                feedback_summary="Answer is too brief. Provide a structured response with technical mechanisms and trade-offs.",
                star_feedback={
                    "situation": "Missing — Provide real-world context or problem statement.",
                    "task": "Missing — Specify the technical challenge.",
                    "action": "Missing — Describe the specific tools, algorithms, and design choices.",
                    "result": "Missing — Highlight performance improvements or business outcome."
                }
            )

        # 1. LLM Evaluation (Gemini API / OpenAI) if key is provided
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""You are a Principal Engineer and rigorous technical interviewer at a top tech company.
Evaluate this candidate's interview answer accurately, constructively, and without grade inflation.

INTERVIEW CONTEXT:
Question: "{question_text}"
Grounding Context: {based_on}
Target Domain/Skill: {skill}
Difficulty Level: {difficulty}
Expected Key Points: {', '.join(expected_points) if expected_points else 'Standard production best practices, mechanics, trade-offs'}

CANDIDATE ANSWER:
"{cleaned_answer}"

EVALUATION RUBRIC:
1. Relevance (0-100): Did the candidate directly address what was asked?
2. Technical Accuracy (0-100): Are the technical mechanisms, terminology, and system behaviors correct?
3. Completeness (0-100): Did they cover the 'Why', 'How', and trade-offs?
4. Clarity (0-100): Is the structure logical, concise, and easy to follow?
5. Confidence (0-100): Is the tone assertive, professional, and free of excessive hedging?
6. Communication (0-100): Professional vocabulary and clarity of explanation.

REQUIRED JSON OUTPUT FORMAT:
{{
  "overall_score": int (0-100),
  "relevance_score": int (0-100),
  "technical_accuracy_score": int (0-100),
  "completeness_score": int (0-100),
  "clarity_score": int (0-100),
  "confidence_score": int (0-100),
  "communication_score": int (0-100),
  "verdict_rating": "Exceptional" | "Strong Technical Answer" | "Adequate with Gaps" | "Needs Technical Depth" | "Incomplete",
  "concepts_covered": ["List of 2-4 specific technical concepts the candidate correctly mentioned"],
  "concepts_missed": ["List of 2-4 critical technical concepts or trade-offs the candidate omitted"],
  "strengths": ["2-3 specific, evidence-based strengths of their answer"],
  "weaknesses": ["2-3 actionable, technical points where the answer fell short"],
  "improved_answer": "A concise, senior-engineer caliber ideal answer (3-5 sentences) showcasing deep domain mastery.",
  "follow_up_question": "A sharp, realistic follow-up question the interviewer would ask next.",
  "next_recommended_difficulty": "Easy" | "Medium" | "Hard" | "Expert",
  "feedback_summary": "1-2 sentence concise executive summary of the evaluation.",
  "star_feedback": {{
    "situation": "Brief assessment of context provided",
    "task": "Brief assessment of challenge stated",
    "action": "Brief assessment of technical implementation described",
    "result": "Brief assessment of outcome or metrics highlighted"
  }}
}}"""

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.split("```json")[1].split("```")[0].strip()
                elif text.startswith("```"):
                    text = text.split("```")[1].split("```")[0].strip()

                data = json.loads(text)
                return AnswerEvaluation(
                    question_id=question_id,
                    overall_score=int(data.get("overall_score", 75)),
                    relevance_score=int(data.get("relevance_score", 75)),
                    technical_accuracy_score=int(data.get("technical_accuracy_score", 75)),
                    completeness_score=int(data.get("completeness_score", 70)),
                    clarity_score=int(data.get("clarity_score", 80)),
                    confidence_score=int(data.get("confidence_score", 75)),
                    communication_score=int(data.get("communication_score", 80)),
                    verdict_rating=data.get("verdict_rating", "Adequate with Gaps"),
                    concepts_covered=data.get("concepts_covered", []),
                    concepts_missed=data.get("concepts_missed", []),
                    strengths=data.get("strengths", ["Clear explanation of fundamental concepts."]),
                    weaknesses=data.get("weaknesses", ["Could add more depth on trade-offs and scaling."]),
                    improved_answer=data.get("improved_answer", f"A strong answer directly addresses why {skill} was selected, the underlying mechanism, and measurable outcome."),
                    follow_up_question=data.get("follow_up_question", f"How would you optimize this approach under heavy concurrent load?"),
                    next_recommended_difficulty=data.get("next_recommended_difficulty", "Medium"),
                    feedback_summary=data.get("feedback_summary", "Good attempt with clear technical understanding."),
                    star_feedback=data.get("star_feedback")
                )
            except Exception as e:
                logger.warning(f"Gemini evaluation fallback to advanced deterministic engine: {e}")

        # 2. Advanced Deterministic Semantic Evaluation Engine
        # Domain concept dictionaries
        DOMAIN_CONCEPTS = {
            "mongodb": {
                "keywords": ["bson", "document", "schema", "embed", "reference", "index", "aggregation", "pipeline", "sharding", "replica", "wiredtiger", "16mb", "collection", "nosql", "query", "latency"],
                "core_terms": ["BSON Document Model", "Compound Indexing", "Embedding vs Referencing", "Aggregation Pipeline", "16MB Document Limit", "Horizontal Scalability"]
            },
            "python": {
                "keywords": ["gil", "thread", "async", "generator", "yield", "decorator", "closure", "immutable", "tuple", "list", "memory", "reference count", "garbage collection", "cprofile", "typing"],
                "core_terms": ["Reference Counting & GC", "Global Interpreter Lock (GIL)", "Lazy Generator Evaluation", "Decorator Closures", "Object Mutability"]
            },
            "fastapi": {
                "keywords": ["pydantic", "validation", "async", "await", "depends", "dependency", "openapi", "swagger", "starlette", "lifespan", "middleware", "background task", "status code", "endpoint"],
                "core_terms": ["Pydantic Data Validation", "Dependency Injection (`Depends`)", "Asynchronous Event Loop", "OpenAPI Specification", "Lifespan Context Management"]
            },
            "react": {
                "keywords": ["props", "state", "useeffect", "usememo", "usecallback", "re-render", "virtual dom", "fiber", "reconciliation", "hooks", "component", "cleanup", "zustand", "context"],
                "core_terms": ["Unidirectional Data Flow", "Lifecycle & Cleanup in `useEffect`", "Virtual DOM Reconciliation", "Memoization & Render Optimization", "State Localization"]
            },
            "sql": {
                "keywords": ["acid", "transaction", "join", "index", "b-tree", "isolation", "deadlock", "foreign key", "normalization", "partition", "window function", "postgres", "mysql", "query plan"],
                "core_terms": ["ACID Guarantees", "Index Seek vs Scan", "Transaction Isolation Levels", "Relational JOIN Mechanics", "Window Analytics Functions"]
            },
            "docker": {
                "keywords": ["image", "container", "layer", "multi-stage", "build", "network", "bridge", "host", "cgroups", "namespace", "daemon", "dockerfile", "volume", "rootless"],
                "core_terms": ["Layered Filesystem Caching", "Multi-stage Image Optimization", "Container Network Namespaces", "Resource Isolation via cgroups", "Non-root Security Hardening"]
            }
        }

        # Find matching domain
        matched_domain = None
        for dom_key in DOMAIN_CONCEPTS:
            if dom_key in skill.lower() or dom_key in question_text.lower():
                matched_domain = DOMAIN_CONCEPTS[dom_key]
                break

        # Analyze covered vs missed concepts
        concepts_covered = []
        concepts_missed = []
        if matched_domain:
            for term in matched_domain["core_terms"]:
                term_words = [w for w in term.lower().replace("`", "").replace("(", "").replace(")", "").split() if len(w) > 3]
                if any(tw in lower_ans for tw in term_words):
                    concepts_covered.append(term)
                else:
                    concepts_missed.append(term)
        else:
            # Heuristic concepts based on expected_points
            for pt in (expected_points or ["Core Mechanism", "Trade-offs", "Production Implementation"]):
                pt_words = [w for w in pt.lower().split() if len(w) > 3]
                if any(pw in lower_ans for pw in pt_words):
                    concepts_covered.append(pt)
                else:
                    concepts_missed.append(pt)

        # 1. Relevance Score
        relevance_triggers = [skill.lower(), "because", "project", "approach", "implementation", "architecture", "choice"]
        rel_matches = sum(1 for rt in relevance_triggers if rt in lower_ans)
        relevance_score = min(96, max(35, 45 + (rel_matches * 10) + min(25, word_count // 4)))

        # 2. Technical Accuracy Score
        tech_hits = 0
        if matched_domain:
            tech_hits = sum(1 for kw in matched_domain["keywords"] if kw in lower_ans)
        else:
            tech_hits = sum(1 for w in words if w in {"latency", "async", "cache", "throughput", "schema", "optimize", "indexing", "payload", "query", "thread", "api"})
        
        # Check negative assertions / common misconceptions
        penalty = 0
        if "tuple is mutable" in lower_ans or "tuples are mutable" in lower_ans:
            penalty += 25
        if "mongodb is relational" in lower_ans or "mongodb foreign key" in lower_ans:
            penalty += 20
        if "useeffect runs before" in lower_ans:
            penalty += 20

        technical_accuracy = min(96, max(30, (50 + (tech_hits * 8)) - penalty))

        # 3. Completeness Score (Problem + Action + Result + Trade-offs)
        has_causal = any(c in lower_ans for c in ["because", "in order to", "which allowed", "so that", "leading to", "due to", "trade-off"])
        has_metric = bool(re.search(r'\d+%|\d+ms|\d+x|\$\d+|\d+\s*(?:users|sec|seconds|records|queries)', lower_ans))
        has_tradeoff = any(t in lower_ans for t in ["trade-off", "tradeoff", "downside", "limitation", "alternative", "however", "instead of", "compared to"])
        
        comp_base = 40 + (15 if has_causal else 0) + (15 if has_metric else 0) + (15 if has_tradeoff else 0) + min(15, word_count // 6)
        completeness = min(95, max(35, comp_base))

        # 4. Clarity Score
        has_paragraphs_or_sentences = lower_ans.count(".") >= 2 or lower_ans.count("\n") >= 1
        clarity = 88 if has_paragraphs_or_sentences and word_count >= 30 else (72 if word_count >= 18 else 55)

        # 5. Confidence Score
        hesitations = ["maybe", "i think", "i guess", "probably", "not really sure", "sort of", "kind of", "i don't know"]
        hesitation_count = sum(1 for h in hesitations if h in lower_ans)
        confidence = max(40, 90 - (hesitation_count * 15))

        # 6. Communication Score
        comm_words = ["specifically", "architected", "implemented", "optimized", "ensured", "mitigated", "structured", "decoupled"]
        comm_hits = sum(1 for cw in comm_words if cw in lower_ans)
        communication = min(95, max(50, 65 + (comm_hits * 7) + (10 if has_paragraphs_or_sentences else 0)))

        # Weighted Overall Score
        overall = int(
            (relevance_score * 0.25) +
            (technical_accuracy * 0.25) +
            (completeness * 0.20) +
            (clarity * 0.10) +
            (confidence * 0.10) +
            (communication * 0.10)
        )

        # Verdict rating
        if overall >= 85:
            verdict = "Exceptional Technical Mastery"
            next_diff = "Hard" if difficulty in ["Easy", "Medium"] else "Expert"
        elif overall >= 75:
            verdict = "Strong Technical Answer"
            next_diff = "Hard" if difficulty == "Medium" else difficulty
        elif overall >= 60:
            verdict = "Adequate with Gaps"
            next_diff = difficulty
        elif overall >= 45:
            verdict = "Needs Technical Depth"
            next_diff = "Medium" if difficulty in ["Hard", "Expert"] else "Easy"
        else:
            verdict = "Incomplete / Insufficient"
            next_diff = "Easy"

        # Construct specific strengths
        strengths = []
        if concepts_covered:
            strengths.append(f"Correctly identified key mechanisms: {', '.join(concepts_covered[:3])}.")
        if has_causal:
            strengths.append("Provided clear causal reasoning explaining the rationale behind design choices.")
        if has_metric:
            strengths.append("Supported assertions with concrete impact metrics / numbers.")
        if not strengths:
            strengths.append(f"Directly addressed the prompt regarding {skill}.")

        # Construct specific weaknesses
        weaknesses = []
        if concepts_missed:
            weaknesses.append(f"Missed discussing core architectural points: {', '.join(concepts_missed[:2])}.")
        if not has_tradeoff:
            weaknesses.append("Did not evaluate design trade-offs, potential drawbacks, or evaluated alternatives.")
        if not has_metric:
            weaknesses.append("Lacks quantifiable outcomes (e.g. latency reduction, query throughput, memory savings).")
        if hesitation_count > 0:
            weaknesses.append("Tone contains speculative phrasing ('I think', 'maybe'). State technical decisions assertively.")

        # Senior model answer
        if matched_domain:
            terms_str = ", ".join(matched_domain["core_terms"][:3])
            improved = (
                f"A senior engineer response for '{question_text}': We selected {skill} to leverage {terms_str}. "
                f"In our architecture, this decoupled data persistence from synchronous request bottlenecks. "
                f"We established compound indexing and query projection, mitigating potential 16MB document boundary issues and reducing p99 latency to <50ms. "
                f"The key trade-off was accepting eventual consistency in exchange for horizontal partition tolerance."
            )
        else:
            improved = (
                f"A senior engineer response for '{question_text}': In our system, we applied {skill} specifically to address performance and scalability constraints. "
                f"We structured the implementation with clear separation of concerns, strictly validated inputs, and cached hot read paths. "
                f"This reduced execution overhead by ~40% while maintaining resilience against high concurrency spikes."
            )

        # Follow-up question
        follow_up = f"If this {skill} implementation encountered a 20x spike in concurrent requests, where would the first bottleneck emerge and how would you resolve it?"

        star_fb = {
            "situation": "Clearly stated system background." if word_count >= 30 else "Brief context; could frame problem scale more clearly.",
            "task": "Target technical goal was addressed." if relevance_score >= 70 else "Goal statement could be sharper.",
            "action": f"Mentioned concrete actions with {skill}." if tech_hits >= 2 else f"Expand on the exact implementation mechanisms of {skill}.",
            "result": "Quantified impact included." if has_metric else "Missing quantitative metrics (e.g., latency, throughput, % improvement)."
        }

        return AnswerEvaluation(
            question_id=question_id,
            overall_score=overall,
            relevance_score=relevance_score,
            technical_accuracy_score=technical_accuracy,
            completeness_score=completeness,
            clarity_score=clarity,
            confidence_score=confidence,
            communication_score=communication,
            verdict_rating=verdict,
            concepts_covered=concepts_covered[:4],
            concepts_missed=concepts_missed[:4],
            strengths=strengths,
            weaknesses=weaknesses,
            improved_answer=improved,
            follow_up_question=follow_up,
            next_recommended_difficulty=next_diff,
            feedback_summary=f"Scored {overall}/100 ({verdict}). {'Demonstrated solid grasp of technical mechanisms.' if overall >= 75 else 'Review the missed concepts and incorporate trade-offs and metrics.'}",
            star_feedback=star_fb
        )

    @classmethod
    def generate_project_deep_dive(cls, project_title: str, technologies: List[str], description: str) -> ProjectDeepDive:
        tech_list = technologies or ["Python", "FastAPI", "React", "MongoDB"]
        main_tech = tech_list[0] if tech_list else "Full Stack"
        db_tech = next((t for t in tech_list if t.lower() in ["mongodb", "postgresql", "mysql", "redis", "sqlite"]), "MongoDB / PostgreSQL")

        questions = [
            GroundedQuestion(
                question=f"Why did you choose {main_tech} for '{project_title}', and what other alternatives did you evaluate?",
                based_on=f"Project: {project_title}",
                skill=main_tech,
                difficulty="Medium",
                question_type="Project Based",
                why_this_question="Tests trade-off analysis and technical decision making in real systems.",
                expected_answer_points=[f"Key benefits of {main_tech}", "Why alternatives fell short", "Development speed vs performance"],
                sample_answer=f"We selected {main_tech} due to its high developer ergonomics, strong async ecosystem, and rapid API prototyping capabilities."
            ),
            GroundedQuestion(
                question=f"How is the data model designed in {db_tech} for '{project_title}', and how did you prevent performance bottlenecks?",
                based_on=f"Project: {project_title}",
                skill=db_tech,
                difficulty="Hard",
                question_type="Project Based",
                why_this_question="Evaluates database indexing, schema design, and query optimization.",
                expected_answer_points=["Document/Relational schema layout", "Indexing strategy for frequent queries", "Connection pooling"],
                sample_answer="We established indexes on foreign keys/lookup IDs and implemented pagination to avoid unbounded data retrieval."
            ),
            GroundedQuestion(
                question=f"What was the most challenging bug or architectural bottleneck you encountered in '{project_title}' and how did you resolve it?",
                based_on=f"Project: {project_title}",
                skill="System Architecture",
                difficulty="Hard",
                question_type="Project Based",
                why_this_question="Assesses debugging persistence, root-cause analysis, and incident resolution.",
                expected_answer_points=["Symptom and reproduction", "Profiling/logging methodology", "Root cause and permanent fix"],
                sample_answer="Walk through a concrete latency or state synchronization issue, how you profiled it, and the refactoring applied."
            ),
            GroundedQuestion(
                question=f"How did you implement security, authentication, and input validation in '{project_title}'?",
                based_on=f"Project: {project_title}",
                skill="Security & Validation",
                difficulty="Medium",
                question_type="Project Based",
                why_this_question="Checks secure coding practices, CORS, JWT handling, and input sanitization.",
                expected_answer_points=["JWT/Session auth", "Pydantic/Schema validation", "CORS policy and rate limiting"],
                sample_answer="All incoming payloads are strictly validated using schema models, and stateful endpoints require signed JWT bearer tokens."
            ),
            GroundedQuestion(
                question=f"If '{project_title}' needed to handle 10,000 requests per second, what changes would you introduce in caching and infrastructure?",
                based_on=f"Project: {project_title}",
                skill="Scalability",
                difficulty="Expert",
                question_type="Project Based",
                why_this_question="Tests horizontal scalability, distributed caching, and microservices readiness.",
                expected_answer_points=["Redis caching layer", "Load balancing with Nginx/k8s", "Database read replicas", "Asynchronous worker queues"],
                sample_answer="Introduce Redis for caching hot reads, decouple compute with background worker queues (Celery), and scale stateless backend instances behind a reverse proxy."
            )
        ]

        return ProjectDeepDive(
            project_name=project_title,
            objective=f"Develop a robust, user-centric application solving core workflow automation using {', '.join(tech_list[:3])}.",
            problem_statement=description[:250] if description else f"Providing seamless and responsive operations with real-time feedback for users.",
            architecture=f"Client-Server architecture with modular {tech_list[0] if tech_list else 'modern'} frontend communicating via RESTful APIs to an asynchronous Python backend, backed by {db_tech}.",
            technologies=tech_list,
            database_choice=f"Utilized {db_tech} for flexible schema management, high-throughput writes, and rapid iteration during development.",
            apis_design="RESTful JSON APIs adhering to standard HTTP verbs, structured error payloads, and Pydantic request/response validation.",
            challenges_solutions="Managing asynchronous state consistency and preventing query latency spikes by adding targeted indexing.",
            security_aspects="Token-based authentication, strict CORS origins, environment variable separation for secrets, and input sanitization.",
            scalability_notes="Stateless application design allowing horizontal container scaling across Docker/Kubernetes pods.",
            testing_strategy="Unit testing of core utility functions and end-to-end API integration tests verifying valid and error boundary conditions.",
            deployment_details="Containerized via Docker, automated CI/CD pipeline via GitHub Actions for testing and deployment.",
            future_improvements="Integrating real-time WebSocket notifications, advanced caching with Redis, and AI-driven automated recommendations.",
            interview_questions=questions
        )

    @classmethod
    def generate_resume_improvements(cls, resume: ExtractedResume) -> List[ResumeImprovementItem]:
        improvements: List[ResumeImprovementItem] = []

        # Check project descriptions for metrics
        has_metrics = any(re.search(r'\d+%|\d+x|\$\d+|\d+\s*(?:users|ms|seconds|hours)', p.description or "") for p in resume.projects)
        if not has_metrics:
            improvements.append(ResumeImprovementItem(
                category="Impact & Metrics",
                issue="Projects lack quantifiable results and business impact metrics.",
                suggestion="Use the Google X-Y-Z formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
                impact_level="High",
                example_before="Built an API that processes user resumes and generates questions.",
                example_after="Architected an async FastAPI service processing 500+ resumes with <200ms latency, improving preparation speed by 40%."
            ))

        # Check action verbs
        weak_verbs = ["worked on", "helped with", "responsible for", "handled"]
        has_weak = any(any(v in (p.description or "").lower() for v in weak_verbs) for p in resume.projects)
        if has_weak or len(resume.projects) > 0:
            improvements.append(ResumeImprovementItem(
                category="Action Verbs",
                issue="Avoid passive phrases like 'worked on' or 'helped with'.",
                suggestion="Begin bullet points with strong power action verbs like 'Architected', 'Engineered', 'Optimized', 'Deployed'.",
                impact_level="Medium",
                example_before="Worked on the database integration and frontend UI.",
                example_after="Engineered responsive React interface and optimized MongoDB aggregation pipelines reducing load times by 35%."
            ))

        # Check skills grouping
        if len(resume.skills) < 8:
            improvements.append(ResumeImprovementItem(
                category="Skills Section",
                issue="Technical skill inventory could be more comprehensive.",
                suggestion="Explicitly list Languages, Frontend, Backend, Databases, Cloud & DevOps, and Testing tools in categorized groupings.",
                impact_level="High",
                example_before="Skills: Python, React, Database",
                example_after="Languages: Python, JavaScript, TypeScript | Backend: FastAPI, Node.js | Databases: MongoDB, PostgreSQL | DevOps: Docker, Git"
            ))

        # Check achievements
        if not resume.achievements:
            improvements.append(ResumeImprovementItem(
                category="Achievements & Leadership",
                issue="Missing a dedicated achievements or extracurricular leadership section.",
                suggestion="Highlight hackathons, open-source pull requests, certifications, or academic honors.",
                impact_level="Medium",
                example_before="No achievements section listed.",
                example_after="Finalist in University Hackathon 2024 (Top 5 of 120 teams) | Published open-source React component with 200+ GitHub stars."
            ))

        return improvements

    @classmethod
    def generate_preparation_topics(cls, resume: ExtractedResume, jd: Optional[JobDescriptionAnalysis] = None) -> List[TopicPreparationItem]:
        topics: List[TopicPreparationItem] = []
        skills = resume.skills if resume.skills else ["Python", "SQL", "React", "MongoDB", "FastAPI"]
        
        for s in skills[:8]:
            topics.append(TopicPreparationItem(
                topic=f"{s} Core Architecture & Internals",
                importance="High",
                why_it_matters=f"Frequently examined in live interviews to verify deep hands-on expertise beyond basic syntax.",
                resume_evidence=f"Featured prominently in your skills and project implementations.",
                expected_questions=[
                    f"How does {s} manage concurrency / memory?",
                    f"What are the common pitfalls and performance trade-offs in {s}?",
                    f"Explain a production scenario where you debugged an issue in {s}."
                ],
                recommended_level="Intermediate to Advanced"
            ))

        # Add System Design and Behavioral
        topics.append(TopicPreparationItem(
            topic="System Design & Scalability",
            importance="High",
            why_it_matters="Crucial for demonstrating engineering maturity, caching strategy, and database scaling.",
            resume_evidence=f"Demonstrated across your project architectures: {', '.join([p.title for p in resume.projects[:2]]) or 'Web applications'}.",
            expected_questions=[
                "How would you design a rate limiter or URL shortener?",
                "How do you ensure zero data loss during high database write traffic?",
                "When should you decouple monolithic services into microservices?"
            ],
            recommended_level="Intermediate"
        ))

        topics.append(TopicPreparationItem(
            topic="Behavioral & STAR Method Communication",
            importance="Medium",
            why_it_matters="Assesses culture fit, conflict resolution, ownership, and cross-functional teamwork.",
            resume_evidence="Evaluated across your past work experience and team project collaborations.",
            expected_questions=[
                "Tell me about a time you resolved a major production bug.",
                "How do you handle scope changes or tight release deadlines?",
                "Describe a situation where you convinced a team to adopt a better tech stack."
            ],
            recommended_level="All Candidates"
        ))

        return topics[:10]
