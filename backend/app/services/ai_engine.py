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
                 ["Tuples are immutable; lists are mutable", "Tuples have lower memory overhead", "Tuples can be used as dictionary keys if hashable"],
                 "Lists are mutable sequences suitable for collections that change, whereas tuples are immutable and memory-efficient. I prefer tuples for fixed data schemas, dictionary keys, and function return values to ensure data integrity."),
                ("How does Python handle memory management and garbage collection?",
                 "Checks awareness of reference counting and cyclic garbage collection in CPython.",
                 ["Reference counting mechanism", "Generational cyclic garbage collector (gc module)", "Memory leaks via circular references"],
                 "Python manages memory primarily through reference counting, where an object's memory is deallocated when its reference count drops to zero. To handle circular references, CPython uses a generational cyclic garbage collector that periodically traverses object graphs."),
            ],
            "Medium": [
                ("How do Python generators and the `yield` keyword optimize memory in data-heavy pipelines?",
                 "Evaluates understanding of lazy evaluation and generator iterators.",
                 ["Generators yield items one by one instead of loading full list in RAM", "State retention between yield calls", "Memory profiling comparison"],
                 "Generators produce items on-demand using the `yield` keyword rather than loading the entire dataset into memory at once. In data pipelines, this lazy evaluation allows processing multi-gigabyte files with a constant memory footprint."),
                ("Explain how Python decorators work under the hood and provide an example use case like logging or authentication.",
                 "Tests first-class function handling and closure concepts.",
                 ["Functions as first-class objects", "Wrapper function around the original function", "Common use cases: caching, RBAC, execution timing"],
                 "Decorators are higher-order functions that take a function as an argument and return an extended wrapper function using closures. I commonly use decorators for cross-cutting concerns like measuring execution time, enforcing role-based access control, and route authentication."),
            ],
            "Hard": [
                ("How does the Global Interpreter Lock (GIL) affect multithreading in CPU-bound vs I/O-bound Python programs?",
                 "Assesses deep concurrency understanding in CPython.",
                 ["GIL prevents multiple native threads from executing Python bytecodes simultaneously", "I/O bound benefits from threading/asyncio", "CPU bound requires multiprocessing"],
                 "The GIL ensures only one native thread executes Python bytecode at a time. For I/O-bound programs, threads release the GIL during network or disk waits, making threading or `asyncio` effective. For CPU-bound tasks, we bypass the GIL using multiprocessing or native C-extensions like NumPy."),
            ]
        },
        "YOLO": {
            "Easy": [
                ("What is YOLOv8 and why would you use it for real-time object detection?",
                 "Evaluates understanding of single-shot computer vision models.",
                 ["Anchor-free detection architecture", "Fast real-time inference with high mAP", "Pre-trained on COCO dataset"],
                 "YOLOv8 is an anchor-free object detection model used to detect and classify objects in real time. I used it because it delivers high accuracy (mAP) with fast inference speeds, making it ideal for live video feeds and traffic monitoring."),
            ],
            "Medium": [
                ("What is the difference between YOLO's single-shot approach and two-stage detectors like Faster R-CNN?",
                 "Tests architectural knowledge of deep learning vision models.",
                 ["Single pass bounding box regression vs region proposal network", "Inference latency comparison", "Speed vs small-object localization trade-offs"],
                 "YOLO performs bounding box regression and classification in a single forward pass across the image grid, achieving real-time inference (>30 FPS). Two-stage detectors like Faster R-CNN first generate region proposals and then classify them, which is slightly more accurate for small objects but significantly slower."),
            ],
            "Hard": [
                ("How do you optimize YOLOv8 inference for production deployment on edge or GPU devices?",
                 "Assesses model export, quantization, and TensorRT acceleration.",
                 ["ONNX and TensorRT export", "FP16 / INT8 quantization", "Batch inference and Non-Maximum Suppression (NMS) tuning"],
                 "We export the trained PyTorch YOLO model to ONNX, optimize the compute graph with TensorRT for INT8/FP16 quantization, and adjust IoU thresholds in Non-Maximum Suppression (NMS) to eliminate redundant boxes while minimizing GPU latency.")
            ]
        },
        "OpenCV": {
            "Easy": [
                ("How did you use OpenCV in your computer vision or image processing pipeline?",
                 "Tests core OpenCV frame processing operations.",
                 ["Frame capture from video stream", "Color conversion and thresholding", "Drawing bounding boxes and tracking IDs"],
                 "I used OpenCV for video stream ingestion (`cv2.VideoCapture`), frame-by-frame preprocessing (grayscale conversion and Gaussian blurring), and drawing real-time bounding boxes and vehicle count statistics on processed frames."),
            ],
            "Medium": [
                ("How do Region of Interest (ROI) masking and morphological operations improve video processing performance in OpenCV?",
                 "Evaluates practical computer vision optimization techniques.",
                 ["Cropping computational frame area", "Morphological opening/closing for noise removal", "Frame skipping and threaded I/O"],
                 "By applying an ROI mask to crop only the active traffic lanes, we reduce the number of pixels passed to downstream inference by over 50%. We also apply morphological transformations to remove sensor noise and isolate moving contours.")
            ]
        },
        "FastAPI": {
            "Easy": [
                ("What are the primary benefits of FastAPI compared to traditional frameworks like Flask or Django?",
                 "Evaluates knowledge of modern asynchronous Python frameworks.",
                 ["Native async/await support with Starlette", "Automatic OpenAPI/Swagger docs generation", "Pydantic validation for request/response bodies"],
                 "FastAPI provides native asynchronous support built on Starlette and Uvicorn, automatic interactive OpenAPI/Swagger documentation, and robust request/response validation using Pydantic type annotations."),
            ],
            "Medium": [
                ("How does FastAPI utilize Pydantic models for request validation and serialization?",
                 "Tests data validation, type hints, and API security.",
                 ["Automatic 422 Unprocessable Entity responses for invalid types", "Serialization to JSON", "Nested models and field validators"],
                 "FastAPI parses incoming JSON bodies against defined Pydantic schemas. If fields are missing or have incorrect data types, it automatically returns structured 422 Unprocessable Entity responses before executing the route handler."),
            ]
        },
        "React": {
            "Easy": [
                ("What is the difference between props and state in React, and how does one-way data flow work?",
                 "Tests foundational component architecture.",
                 ["Props are passed from parent (read-only); state is managed internally", "Unidirectional data flow simplifies debugging", "State updates trigger re-renders"],
                 "Props are immutable data passed down from parent to child components, whereas state is mutable local data managed within a component. React enforces unidirectional data flow, making state changes predictable and easier to debug."),
            ],
            "Medium": [
                ("Explain how `useEffect` works, including its dependency array and cleanup function.",
                 "Evaluates lifecycle management and side-effect handling.",
                 ["Runs after render", "Empty array = run once on mount; with dependencies = run when values change", "Cleanup function runs on unmount or before re-run"],
                 "`useEffect` performs side-effects such as API fetching or event subscriptions. An empty dependency array runs the effect once on mount, specified variables trigger re-execution when changed, and the returned cleanup function cancels subscriptions or timers on unmount."),
            ]
        },
        "MongoDB": {
            "Easy": [
                ("What is the primary difference between a relational database and a document database like MongoDB?",
                 "Evaluates schema flexibility vs relational integrity understanding.",
                 ["BSON document model vs rigid tabular schemas", "Horizontal scaling capability", "Flexible schema evolution for nested JSON"],
                 "MongoDB stores data as flexible, hierarchical BSON documents with dynamic schemas, whereas relational databases use rigid tables and columns. MongoDB excels at horizontal scaling and storing nested JSON entities without complex joins."),
            ]
        },
        "SQL": {
            "Easy": [
                ("Explain the differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
                 "Evaluates relational algebra and SQL joining fundamentals.",
                 ["INNER JOIN returns matched rows in both", "LEFT JOIN returns all left rows + matching right rows", "NULL handling for unmatched rows"],
                 "An `INNER JOIN` returns only rows that have matching values in both tables. A `LEFT JOIN` returns all records from the left table along with matching rows from the right table (filling unmatched fields with NULL), and a `FULL OUTER JOIN` returns all records when there is a match in either table."),
            ]
        },
        "Docker": {
            "Easy": [
                ("What is the difference between a Docker image and a Docker container?",
                 "Tests core containerization concepts.",
                 ["Image is a static read-only template; container is a running instance with a writable layer", "Layered filesystem", "Reproducibility across environments"],
                 "A Docker image is an immutable, read-only template containing the application code, runtime, libraries, and dependencies. A Docker container is a runnable, isolated instance of that image with a thin writable layer on top."),
            ]
        }
    }

    BEHAVIORAL_QUESTIONS = [
        ("Tell me about a challenging technical hurdle you faced in one of your projects and how you diagnosed and resolved it.",
         "Project Experience",
         "Evaluates problem-solving methodology, debugging persistence, and ownership.",
         ["Clearly define the problem", "Explain diagnostic steps and tools used", "Describe the solution and measurable outcome", "What you learned"],
         "In my project, we experienced severe frame drops during live camera feeds. I profiled CPU bottlenecks using cProfile and OpenCV timers, identified that frame conversions were blocking the main thread, and resolved it by offloading video decoding to a background worker thread, restoring steady 30 FPS inference."),
        ("Describe a situation where you had to quickly learn a new framework or technology to deliver a project feature.",
         "Adaptability & Learning",
         "Assesses continuous learning, agility, and time management.",
         ["Context of the project requirement", "Systematic approach to learning (docs, tutorials, prototyping)", "Timely execution and quality delivery"],
         "When our team needed to deploy a real-time object detection model, I quickly learned the YOLOv8 Python API and ONNX runtime within three days through documentation and rapid prototyping, successfully integrating vehicle detection into our production pipeline ahead of schedule.")
    ]

    PROJECT_TEMPLATES = [
        ("What is {tech} and why did you choose it in your '{title}' project?",
         "Project: {title}",
         "Tests core technology selection, architectural trade-offs, and practical application in your project.",
         ["Core mechanism and role of {tech}", "Why {tech} was selected over alternatives", "Performance, accuracy, or throughput advantage", "Production outcome in '{title}'"],
         "In '{title}', {tech} served as the primary technology for core processing and workflow execution. We chose {tech} over alternative options because it provides superior execution speed, native async/parallel support, and an extensive ecosystem of production-grade tools. In our pipeline, {tech} handled request ingestion, data transformation, and core execution with sub-50ms latency. The key trade-off was managing memory overhead under concurrent load, which we solved by introducing connection pooling and caching, ensuring '{title}' operated smoothly with high reliability."),
        ("How did you use {tech} in your '{title}' project?",
         "Project: {title}",
         "Evaluates hands-on implementation details, pipeline design, and framework usage.",
         ["Pipeline and architecture integration", "Data flow and frame/request processing", "Validation and output handling", "Error recovery"],
         "In '{title}', I integrated {tech} to drive the end-to-end processing pipeline. Specifically, it ingested incoming raw data, executed data sanitization and feature extraction, and processed the core business logic before persisting results. To ensure production reliability, I implemented structured validation with schema models, automated logging, and decoupled compute-heavy tasks into background worker threads, maintaining steady throughput and low API response times."),
        ("What was the primary architectural trade-off you made in '{title}' when selecting {tech}?",
         "Project: {title}",
         "Tests architectural justification, engineering trade-offs, and decision making in real projects.",
         ["Why {tech} was selected over alternatives", "Performance or scalability implications", "Limitations or challenges encountered", "Mitigation strategy"],
         "When building '{title}', the main architectural trade-off was balancing developer velocity with low-latency execution. Selecting {tech} gave us rapid prototyping capabilities and well-tested libraries, but required careful tuning of concurrency and memory usage. We addressed this by profiling hot paths with runtime analyzers, adding an in-memory caching layer for repetitive queries, and strictly isolating resource-heavy operations to avoid blocking the main thread."),
        ("If '{title}' were to experience a 10x increase in volume, how would you scale your {tech} implementation?",
         "Project: {title}",
         "Assesses system design, caching, database query optimization, and horizontal scaling.",
         ["Identifying bottlenecks (DB read/write, API compute, memory)", "Introducing caching (Redis) or CDN", "Database indexing and connection pooling", "Horizontal pod autoscaling"],
         "To scale {tech} for 10x traffic in '{title}', I would execute a three-tier optimization strategy: First, introduce Redis caching for high-frequency read operations to eliminate redundant compute overhead. Second, decouple CPU-intensive workloads using asynchronous worker queues (like Celery/Kafka) with backpressure controls. Third, containerize the application with Docker and deploy behind an Nginx reverse proxy with horizontal pod autoscaling (HPA) based on CPU and memory thresholds.")
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
            for tmpl, based_tmpl, why, pts, sample_tmpl in QuestionCatalog.PROJECT_TEMPLATES:
                q_text = tmpl.format(title=p.title, tech=main_tech)
                b_text = based_tmpl.format(title=p.title)
                pts_formatted = [pt.format(title=p.title, tech=main_tech) for pt in pts]
                sample_formatted = sample_tmpl.format(title=p.title, tech=main_tech)
                candidate_pool.append((
                    q_text,
                    b_text,
                    main_tech,
                    difficulty,
                    "Project Based",
                    why,
                    pts_formatted,
                    sample_formatted
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
                for entry in diff_list:
                    q_text = entry[0]
                    why = entry[1]
                    pts = entry[2]
                    sample = entry[3] if len(entry) > 3 else f"A strong answer for {skill} covers {pts[0]} and practical trade-offs."
                    candidate_pool.append((
                        q_text,
                        f"Resume Skill: {skill}",
                        skill,
                        difficulty,
                        "Technical",
                        why,
                        pts,
                        sample
                    ))

        # (c) JD Based questions
        if jd and jd.required_skills:
            for jd_s in jd.required_skills[:4]:
                in_resume = any(jd_s.lower() == s.lower() for s in skills)
                based = f"JD Requirement: {jd_s} (Present in Resume)" if in_resume else f"JD Target Skill: {jd_s} (Job Requirement)"
                jd_sample = f"To address {jd_s}, I explain core principles, highlight past hands-on implementation, and describe best practices for production reliability."
                candidate_pool.append((
                    f"The target job requires solid experience with {jd_s}. How have you applied {jd_s} in your projects, or how would you ramp up?",
                    based,
                    jd_s,
                    difficulty,
                    "Job Description Based",
                    f"Directly assesses qualification for the key required skill '{jd_s}' in the job description.",
                    [f"Core understanding of {jd_s}", f"Practical project application or learning plan", "Best practices"],
                    jd_sample
                ))

        # (d) Behavioral & Situational
        for q_text, topic, why, pts, sample in QuestionCatalog.BEHAVIORAL_QUESTIONS:
            candidate_pool.append((
                q_text,
                f"Candidate Experience: {topic}",
                "Soft Skills & Communication",
                difficulty,
                "Behavioral",
                why,
                pts,
                sample
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
        """Calls Google Gemini API for dynamic grounded questions with comprehensive interviewer-caliber suggested answers."""
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are a Principal Software Engineer and hiring manager at a top technology company.
Generate exactly {count} interview questions with comprehensive, senior-engineer caliber suggested answers.

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
- DETAILED SUGGESTED ANSWERS: Every 'sample_answer' MUST be a thorough, high-caliber, multi-sentence model answer (4-6 sentences) formatted exactly as an interviewer expects to hear:
  1. Core Concept/Definition: Direct technical explanation of the tool, mechanism, or principle.
  2. Implementation Context: How it is practically applied in the project/workflow with specific libraries or APIs.
  3. Architecture & Trade-offs: Why it was chosen over alternatives and what performance/scaling trade-offs were evaluated.
  4. Measurable Result: Quantifiable impact (e.g. latency, throughput, reliability, metrics).

Output valid JSON only, a list of objects with keys:
  "question": string,
  "based_on": string (e.g. "Project: X" or "Skill: Y"),
  "skill": string,
  "difficulty": "{difficulty}",
  "question_type": "{question_type}",
  "why_this_question": string,
  "expected_answer_points": list of strings (3-4 bullet points),
  "sample_answer": string (thorough, detailed model response)

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
        
        # Check for empty or trivial answers (strict 0 score)
        if word_count < 4 or len(cleaned_answer) == 0:
            pts_str = ", ".join(expected_points[:3]) if expected_points else f"{skill} core mechanisms and architecture trade-offs"
            concrete_model_ans = (
                f"In our architecture, we implemented {skill} specifically to address {pts_str}. "
                f"In our processing pipeline, {skill} handled data ingestion, transformation, and validation with sub-50ms latency. "
                f"The primary trade-off was balancing memory overhead against execution speed, which we resolved by implementing caching and asynchronous task queues, maintaining 99.9% uptime in production."
            )
            return AnswerEvaluation(
                question_id=question_id,
                overall_score=0,
                relevance_score=0,
                technical_accuracy_score=0,
                completeness_score=0,
                clarity_score=0,
                confidence_score=0,
                communication_score=0,
                verdict_rating="No Answer Provided",
                concepts_covered=[],
                concepts_missed=expected_points or [f"{skill} core mechanism", "Production trade-offs", "Concrete implementation"],
                strengths=["No technical response was submitted."],
                weaknesses=[
                    f"No answer was entered for this question on {skill}.",
                    "Type or dictate your technical explanation to receive a criteria evaluation."
                ],
                improved_answer=concrete_model_ans,
                follow_up_question=f"Can you walk me through a specific code or architecture example where you implemented {skill}?",
                next_recommended_difficulty="Easy",
                feedback_summary="No answer was provided (0/100). Review the suggested model answer below to prepare.",
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

STRICT ZERO-SCORE POLICY:
- If the candidate's answer is empty, random gibberish, off-topic words, jokes, or completely irrelevant to the question asked about '{skill}', you MUST score overall_score=0 and ALL 6 sub-scores=0 with verdict 'Irrelevant / Random Input'.
- If the candidate provided a genuine, relevant technical explanation, evaluate fairly on technical accuracy, completeness, and clarity (scores 50-95).
- Every 'improved_answer' MUST be a realistic, senior-engineer first-person spoken response (4-6 sentences) answering the question directly as spoken in an interview.

INTERVIEW CONTEXT:
Question: "{question_text}"
Grounding Context: {based_on}
Target Domain/Skill: {skill}
Difficulty Level: {difficulty}
Expected Key Points: {', '.join(expected_points) if expected_points else 'Standard production best practices, mechanics, trade-offs'}

CANDIDATE ANSWER:
"{cleaned_answer}"

REQUIRED JSON OUTPUT FORMAT:
{{
  "overall_score": int (0-100),
  "relevance_score": int (0-100),
  "technical_accuracy_score": int (0-100),
  "completeness_score": int (0-100),
  "clarity_score": int (0-100),
  "confidence_score": int (0-100),
  "communication_score": int (0-100),
  "verdict_rating": "Exceptional" | "Strong Technical Answer" | "Adequate with Gaps" | "Needs Technical Depth" | "Irrelevant / Random Input" | "No Answer Provided",
  "concepts_covered": ["List of 2-4 specific technical concepts the candidate correctly mentioned"],
  "concepts_missed": ["List of 2-4 critical technical concepts or trade-offs the candidate omitted"],
  "strengths": ["2-3 specific, evidence-based strengths of their answer"],
  "weaknesses": ["2-3 actionable, technical points where the answer fell short"],
  "improved_answer": "A detailed, first-person senior-engineer response (4-6 sentences) directly answering the question with mechanisms, choices, and measurable results.",
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
                raw_overall = int(data.get("overall_score", 0))
                verdict = data.get("verdict_rating", "Needs Technical Depth")

                # If LLM classified as irrelevant/random or gave trivial score, clamp all to 0
                if raw_overall <= 20 or "irrelevant" in verdict.lower() or "random" in verdict.lower():
                    raw_overall = 0
                    rel_s = 0
                    tech_s = 0
                    comp_s = 0
                    clar_s = 0
                    conf_s = 0
                    comm_s = 0
                    verdict = "Irrelevant / Random Input"
                else:
                    rel_s = int(data.get("relevance_score", 0))
                    tech_s = int(data.get("technical_accuracy_score", 0))
                    comp_s = int(data.get("completeness_score", 0))
                    clar_s = int(data.get("clarity_score", 0))
                    conf_s = int(data.get("confidence_score", 0))
                    comm_s = int(data.get("communication_score", 0))

                return AnswerEvaluation(
                    question_id=question_id,
                    overall_score=raw_overall,
                    relevance_score=rel_s,
                    technical_accuracy_score=tech_s,
                    completeness_score=comp_s,
                    clarity_score=clar_s,
                    confidence_score=conf_s,
                    communication_score=comm_s,
                    verdict_rating=verdict,
                    concepts_covered=data.get("concepts_covered", []),
                    concepts_missed=data.get("concepts_missed", []),
                    strengths=data.get("strengths", ["Clear technical terminology."]),
                    weaknesses=data.get("weaknesses", ["Expand on trade-offs and quantifiable impact."]),
                    improved_answer=data.get("improved_answer", f"In our project, we utilized {skill} to optimize core business logic and maintain high throughput."),
                    follow_up_question=data.get("follow_up_question", f"How would you optimize this approach under heavy concurrent load?"),
                    next_recommended_difficulty=data.get("next_recommended_difficulty", "Medium"),
                    feedback_summary=data.get("feedback_summary", "Evaluation complete."),
                    star_feedback=data.get("star_feedback")
                )
            except Exception as e:
                logger.warning(f"Gemini evaluation fallback to advanced deterministic engine: {e}")

        # 2. Advanced Deterministic Semantic Evaluation Engine
        # Domain concept dictionaries
        DOMAIN_CONCEPTS = {
            "yolo": {
                "keywords": ["yolo", "yolov8", "bounding", "anchor", "detection", "inference", "onnx", "tensorrt", "map", "nms", "coco", "fp16", "fps", "latency", "real-time", "video"],
                "core_terms": ["Anchor-free Architecture", "Real-Time Inference Latency", "TensorRT / ONNX Optimization", "Non-Maximum Suppression (NMS)", "Single-Shot Object Detection"]
            },
            "opencv": {
                "keywords": ["opencv", "cv2", "frame", "videocapture", "grayscale", "blur", "roi", "mask", "threshold", "contour", "morphology", "image", "pipeline", "fps"],
                "core_terms": ["Frame Ingestion (`cv2.VideoCapture`)", "Region of Interest (ROI) Masking", "Morphological Filtering", "Contour & Bounding Box Rendering", "Image Preprocessing Pipeline"]
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
            "mongodb": {
                "keywords": ["bson", "document", "schema", "embed", "reference", "index", "aggregation", "pipeline", "sharding", "replica", "wiredtiger", "16mb", "collection", "nosql", "query", "latency"],
                "core_terms": ["BSON Document Model", "Compound Indexing", "Embedding vs Referencing", "Aggregation Pipeline", "16MB Document Limit", "Horizontal Scalability"]
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

        # Check for technical relevance
        q_words = [w for w in question_text.lower().replace("?", "").replace("'", "").replace('"', '').split() if len(w) > 3 and w not in {"what", "how", "why", "when", "which", "your", "project", "used", "using", "with"}]
        q_matches = sum(1 for qw in q_words if qw in lower_ans)
        
        tech_hits = 0
        if matched_domain:
            tech_hits = sum(1 for kw in matched_domain["keywords"] if kw in lower_ans)
        else:
            generic_tech = {"latency", "async", "cache", "throughput", "schema", "optimize", "indexing", "payload", "query", "thread", "api", "database", "pipeline", "memory", "function"}
            tech_hits = sum(1 for w in words if w in generic_tech)

        relevance_triggers = [skill.lower(), "because", "project", "approach", "implementation", "architecture", "choice"]
        rel_matches = sum(1 for rt in relevance_triggers if rt in lower_ans)

        # STRICT GIBBERISH / OFF-TOPIC / RANDOM CHECK (Score 0)
        is_off_topic = (tech_hits == 0 and q_matches == 0 and rel_matches == 0) or (tech_hits == 0 and word_count < 12) or (q_matches == 0 and rel_matches == 0)

        if is_off_topic:
            pts_str = ", ".join(expected_points[:3]) if expected_points else f"{skill} implementation details and trade-offs"
            concrete_model_ans = (
                f"In our architecture, we selected {skill} to address {pts_str}. "
                f"In our pipeline, {skill} handled the core execution logic with high throughput and low latency. "
                f"The key architectural trade-off was balancing memory overhead with developer velocity, which we solved through caching and asynchronous worker queues."
            )
            return AnswerEvaluation(
                question_id=question_id,
                overall_score=0,
                relevance_score=0,
                technical_accuracy_score=0,
                completeness_score=0,
                clarity_score=0,
                confidence_score=0,
                communication_score=0,
                verdict_rating="Irrelevant / Random Input",
                concepts_covered=[],
                concepts_missed=expected_points or [f"{skill} core mechanism", "Production trade-offs", "Concrete implementation"],
                strengths=["Submitted text, but no relevant technical content was identified."],
                weaknesses=[
                    f"The submitted answer does not discuss {skill} or address the question asked.",
                    "Ensure you explain the core mechanism, implementation choices, and practical trade-offs."
                ],
                improved_answer=concrete_model_ans,
                follow_up_question=f"Can you explain how {skill} works under the hood in a production environment?",
                next_recommended_difficulty="Easy",
                feedback_summary=f"The answer provided was off-topic, random, or lacked technical substance regarding {skill} (Scored 0/100).",
                star_feedback={
                    "situation": "Missing — Provide real-world context.",
                    "task": "Missing — Specify technical requirement.",
                    "action": "Missing — Describe concrete tools and implementation.",
                    "result": "Missing — Include measurable outcome."
                }
            )

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
            for pt in (expected_points or ["Core Mechanism", "Trade-offs", "Production Implementation"]):
                pt_words = [w for w in pt.lower().split() if len(w) > 3]
                if any(pw in lower_ans for pw in pt_words):
                    concepts_covered.append(pt)
                else:
                    concepts_missed.append(pt)

        # 1. Relevance Score
        relevance_score = min(96, max(45, 50 + (rel_matches * 10) + (q_matches * 8) + min(20, word_count // 4)))

        # 2. Technical Accuracy Score
        penalty = 0
        if "tuple is mutable" in lower_ans or "tuples are mutable" in lower_ans:
            penalty += 25
        if "mongodb is relational" in lower_ans or "mongodb foreign key" in lower_ans:
            penalty += 20
        if "useeffect runs before" in lower_ans:
            penalty += 20

        technical_accuracy = min(96, max(40, (55 + (tech_hits * 10)) - penalty))

        # 3. Completeness Score (Problem + Action + Result + Trade-offs)
        has_causal = any(c in lower_ans for c in ["because", "in order to", "which allowed", "so that", "leading to", "due to", "trade-off"])
        has_metric = bool(re.search(r'\d+%|\d+ms|\d+x|\$\d+|\d+\s*(?:users|sec|seconds|records|queries|fps)', lower_ans))
        has_tradeoff = any(t in lower_ans for t in ["trade-off", "tradeoff", "downside", "limitation", "alternative", "however", "instead of", "compared to"])
        
        comp_base = 45 + (15 if has_causal else 0) + (15 if has_metric else 0) + (15 if has_tradeoff else 0) + min(15, word_count // 6)
        completeness = min(95, max(40, comp_base))

        # 4. Clarity Score
        has_paragraphs_or_sentences = lower_ans.count(".") >= 2 or lower_ans.count("\n") >= 1
        clarity = 88 if has_paragraphs_or_sentences and word_count >= 30 else (75 if word_count >= 18 else 60)

        # 5. Confidence Score
        hesitations = ["maybe", "i think", "i guess", "probably", "not really sure", "sort of", "kind of", "i don't know"]
        hesitation_count = sum(1 for h in hesitations if h in lower_ans)
        confidence = max(45, 90 - (hesitation_count * 15))

        # 6. Communication Score
        comm_words = ["specifically", "architected", "implemented", "optimized", "ensured", "mitigated", "structured", "decoupled"]
        comm_hits = sum(1 for cw in comm_words if cw in lower_ans)
        communication = min(95, max(55, 68 + (comm_hits * 7) + (8 if has_paragraphs_or_sentences else 0)))

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
            strengths.append(f"Correctly addressed core mechanisms: {', '.join(concepts_covered[:3])}.")
        if has_causal:
            strengths.append("Provided clear causal reasoning explaining the rationale behind design choices.")
        if has_metric:
            strengths.append("Supported assertions with concrete metrics and impact.")
        if not strengths:
            strengths.append(f"Addressed the core prompt regarding {skill}.")

        # Construct specific weaknesses
        weaknesses = []
        if concepts_missed:
            weaknesses.append(f"Missed discussing core architectural points: {', '.join(concepts_missed[:2])}.")
        if not has_tradeoff:
            weaknesses.append("Did not evaluate design trade-offs, potential drawbacks, or evaluated alternatives.")
        if not has_metric:
            weaknesses.append("Lacks quantifiable outcomes (e.g. latency reduction, query throughput, memory savings, FPS).")
        if hesitation_count > 0:
            weaknesses.append("Tone contains speculative phrasing ('I think', 'maybe'). State technical decisions assertively.")

        # Senior model answer
        if matched_domain:
            terms_str = ", ".join(matched_domain["core_terms"][:3])
            improved = (
                f"In our architecture, we selected {skill} to leverage {terms_str}. "
                f"This decoupled data persistence from synchronous request bottlenecks, allowing our services to scale independently. "
                f"We established indexing and query projection, mitigating throughput bottlenecks and reducing p99 latency to <50ms. "
                f"The key trade-off was accepting eventual consistency in exchange for high availability and horizontal partition tolerance."
            )
        else:
            improved = (
                f"In our system, we applied {skill} specifically to address performance, reliability, and scalability requirements. "
                f"We structured the implementation with clear separation of concerns, strictly validated inputs with schema models, and cached hot read paths. "
                f"This reduced compute overhead by ~40% while maintaining resilience and low latency under high concurrency spikes."
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
