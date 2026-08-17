import re
import collections
from typing import List, Dict, Any, Optional, Tuple, Set
from backend.app.schemas.models import ExtractedResume, JobDescriptionAnalysis
from backend.app.services.intent_classifier import QuestionIntent, QuestionIntentClassifier, INTENT_STRUCTURE_MAP

class MockInterviewSessionTracker:
    """Tracks mock interview question history, previous answers, and used patterns to prevent repetitive answers."""
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_session(cls, session_id: str = "default") -> Dict[str, Any]:
        if session_id not in cls._sessions:
            cls._sessions[session_id] = {
                "questions": [],
                "answers": [],
                "intents": [],
                "used_openings": [],
                "used_topics": [],
                "used_examples": []
            }
        return cls._sessions[session_id]

    @classmethod
    def record_entry(cls, session_id: str, question: str, answer: str, intent: str, opening: str, topic: str):
        sess = cls.get_session(session_id)
        sess["questions"].append(question)
        sess["answers"].append(answer)
        sess["intents"].append(intent)
        sess["used_openings"].append(opening)
        if topic and topic not in sess["used_topics"]:
            sess["used_topics"].append(topic)

    @classmethod
    def clear_session(cls, session_id: str = "default"):
        if session_id in cls._sessions:
            del cls._sessions[session_id]

class DiversityManager:
    """Manages question-specific answer synthesis, anti-repetition guards, and semantic relevance validation."""

    OPENING_TEMPLATES: Dict[str, List[str]] = {
        QuestionIntent.PROJECT_OVERVIEW: [
            "{title} is designed to solve the problem of {goal}. At a high level, it operates by {mechanism}.",
            "The primary objective behind {title} was creating a reliable system for {goal}. In this architecture, {tech} drives the core workflows.",
            "I built {title} to streamline {goal}. The application coordinates request handling, data validation, and result delivery.",
        ],
        QuestionIntent.PROJECT_ROLE: [
            "My primary responsibility in {title} was owning the core processing pipeline and {tech} integration.",
            "In {title}, I focused hands-on on designing the API architecture, data models, and backend workflow execution.",
            "I led the implementation of the core service layers in {title}, specifically structuring clean validation boundaries and service modularity."
        ],
        QuestionIntent.WHY_TECHNOLOGY: [
            "We selected {tech} over alternative options primarily because our workload required {driver}.",
            "When evaluating the architecture for {title}, {tech} stood out as the best fit due to {driver}.",
            "The primary reason I chose {tech} was its strong developer ecosystem, clean abstractions, and direct support for {driver}."
        ],
        QuestionIntent.CHALLENGE: [
            "The most significant technical hurdle we faced in {title} occurred when {obstacle}.",
            "During development of {title}, a major roadblock emerged around {obstacle}.",
            "A challenging problem we had to diagnose in {title} was {obstacle} under high-load conditions."
        ],
        QuestionIntent.PROBLEM_SOLVING: [
            "When tackling {problem}, my methodology was to isolate the root cause by inspecting execution metrics and trace logs.",
            "To resolve {problem}, I broke down the workflow into verifiable units and profiled the latency of each layer.",
            "I addressed {problem} systematically by writing targeted test cases to reproduce the anomaly and verifying edge cases defensively."
        ],
        QuestionIntent.SCALABILITY: [
            "For a 10x volume increase in {title}, my strategy focuses on diagnosing bottlenecks before introducing architectural complexity.",
            "To scale {title} under heavy concurrent traffic, I would first profile query execution plans and database access patterns.",
            "Scaling {title} effectively requires a layered approach: optimizing data access hot-paths, connection pooling, and in-memory caching."
        ],
        QuestionIntent.IMPROVEMENT: [
            "If I had additional time to iterate on {title}, the primary limitation I would address is {limitation}.",
            "Looking at {title} in retrospect, the highest-impact enhancement would be refactoring {limitation}.",
            "An architectural area where I would evolve {title} is upgrading {limitation} to improve throughput and maintainability."
        ],
        QuestionIntent.TECHNICAL_DECISION: [
            "A key architectural decision in {title} was choosing {tech} to enforce structured data flow and separation of concerns.",
            "When designing {title}, we decided to decouple compute-heavy operations from the primary request-response cycle.",
            "We made a deliberate technical decision in {title} to prioritize maintainability and fast iteration speed by using {tech}."
        ],
        QuestionIntent.DATABASE: [
            "For the data layer in {title}, we structured the schema around our primary access patterns to minimize unnecessary joins.",
            "In our database design for {title}, we established appropriate indexing on high-cardinality search columns to ensure O(log N) lookups.",
            "We managed database reliability in {title} by defining clear relational constraints, schema migrations, and connection pooling."
        ],
        QuestionIntent.PERFORMANCE: [
            "To optimize performance in {title}, I profiled execution times using runtime timers and eliminated redundant compute overhead.",
            "We addressed performance bottlenecks in {title} by reducing serialization costs and optimizing hot query paths.",
            "Performance tuning in {title} centered on reducing I/O waits and batching database operations."
        ],
        QuestionIntent.DEBUGGING: [
            "When diagnosing issues in {title}, I rely on structured logging and step-by-step reproduction in an isolated test environment.",
            "To troubleshoot subtle defects in {title}, I inspect boundary data values and trace API payloads across layer transitions.",
            "My debugging workflow involves formulating a hypothesis, checking system metrics, and verifying the fix with automated regression tests."
        ],
        QuestionIntent.BEHAVIORAL: [
            "In that situation, our team was managing competing priorities under tight delivery constraints.",
            "When faced with that scenario, I established clear milestone expectations and maintained transparent communication across the team.",
            "I approached that circumstance by breaking down requirements into manageable sprints and proactively mitigating risks."
        ],
        QuestionIntent.CONCEPTUAL: [
            "At its core, {tech} operates on the principle of {mechanism}.",
            "{tech} is designed to provide {mechanism}, making it especially valuable for production systems requiring reliability.",
            "The fundamental concept behind {tech} centers on {mechanism} and predictable state management."
        ]
    }

    @staticmethod
    def calculate_similarity(text_a: str, text_b: str) -> float:
        """Calculates token Jaccard and 2-gram overlap similarity between two text strings."""
        if not text_a or not text_b:
            return 0.0

        words_a = set(re.findall(r'\b\w{3,}\b', text_a.lower()))
        words_b = set(re.findall(r'\b\w{3,}\b', text_b.lower()))
        if not words_a or not words_b:
            return 0.0

        word_jaccard = len(words_a & words_b) / len(words_a | words_b)

        # 2-gram overlap
        tokens_a = re.findall(r'\b\w+\b', text_a.lower())
        tokens_b = re.findall(r'\b\w+\b', text_b.lower())
        grams_a = set(zip(tokens_a[:-1], tokens_a[1:])) if len(tokens_a) > 1 else set()
        grams_b = set(zip(tokens_b[:-1], tokens_b[1:])) if len(tokens_b) > 1 else set()

        gram_jaccard = (len(grams_a & grams_b) / len(grams_a | grams_b)) if (grams_a or grams_b) else 0.0
        return 0.5 * word_jaccard + 0.5 * gram_jaccard

    @classmethod
    def check_relevance(cls, question: str, intent: str, answer: str) -> str:
        """
        Validates whether the generated answer directly addresses the intent and question keywords.
        Returns: 'RELEVANT', 'PARTIALLY_RELEVANT', 'IRRELEVANT'
        """
        ans_lower = answer.lower()
        q_lower = question.lower()

        # Intent specific keyword expectations
        intent_expectations = {
            QuestionIntent.WHY_TECHNOLOGY: ["choose", "select", "because", "alternative", "requirement", "trade-off", "fit", "benefit"],
            QuestionIntent.CHALLENGE: ["challenge", "hurdle", "obstacle", "difficult", "diagnos", "issue", "bottleneck", "resolve"],
            QuestionIntent.SCALABILITY: ["scale", "scaling", "volume", "bottleneck", "index", "profil", "replica", "traffic", "caching"],
            QuestionIntent.IMPROVEMENT: ["improve", "limitation", "more time", "enhancement", "refactor", "future", "add"],
            QuestionIntent.PROJECT_OVERVIEW: ["project", "system", "designed", "purpose", "built", "workflow", "architecture"],
            QuestionIntent.DATABASE: ["schema", "database", "index", "query", "relational", "table", "data"],
            QuestionIntent.PERFORMANCE: ["performance", "latency", "profil", "speed", "optim", "bottleneck", "efficient"],
            QuestionIntent.DEBUGGING: ["debug", "diagnos", "troubleshoot", "root cause", "log", "reproduce", "test"]
        }

        expected_terms = intent_expectations.get(intent, ["approach", "implement", "solution", "architecture"])
        matches = sum(1 for t in expected_terms if t in ans_lower)

        if matches >= 2:
            return "RELEVANT"
        elif matches == 1:
            return "PARTIALLY_RELEVANT"
        else:
            # Check general question keyword intersection
            q_keywords = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', q_lower) if w not in ["what", "when", "where", "which", "would", "your", "this", "about"]]
            q_matches = sum(1 for kw in q_keywords if kw in ans_lower)
            if q_matches >= 2:
                return "RELEVANT"
            elif q_matches >= 1:
                return "PARTIALLY_RELEVANT"
            return "IRRELEVANT"

    @classmethod
    def generate_diverse_grounded_answer(
        cls,
        question_text: str,
        skill: str,
        based_on: str,
        difficulty: str,
        resume: Optional[ExtractedResume],
        jd: Optional[JobDescriptionAnalysis] = None,
        session_id: str = "default",
        previous_answers: Optional[List[str]] = None
    ) -> Tuple[str, str, str, str]:
        """
        Generates a strictly question-specific, diverse, resume-grounded answer tailored to the question's intent.
        Returns: (generated_answer, detected_intent, answer_structure, relevance_verdict)
        """
        sess = MockInterviewSessionTracker.get_session(session_id)
        prior_answers = previous_answers or sess["answers"]
        prior_openings = sess["used_openings"]

        # 1. Detect Intent and Structure
        intent, structure = QuestionIntentClassifier.classify(question_text, based_on=based_on)

        # 2. Extract Project & Technology Details from Resume
        proj_title = "my project"
        proj_techs = [skill] if skill and skill != "Technical" else ["Python", "APIs"]
        proj_desc = ""

        if resume and resume.projects:
            # Match project mentioned in question or based_on
            matched_p = None
            for p in resume.projects:
                if p.title.lower() in question_text.lower() or p.title.lower() in based_on.lower():
                    matched_p = p
                    break
            if not matched_p:
                matched_p = resume.projects[0]

            proj_title = matched_p.title
            proj_techs = matched_p.technologies if matched_p.technologies else proj_techs
            proj_desc = matched_p.description or ""

        main_tech = skill if (skill and skill not in ["Technical", "General", "Mixed"]) else (proj_techs[0] if proj_techs else "the core stack")

        # 3. Formulate Question-Specific Content by Intent
        goal_str = "scalable workflow processing"
        if "inventory" in proj_title.lower() or "inventory" in proj_desc.lower():
            goal_str = "inventory tracking and automated stock level alerts"
        elif "traffic" in proj_title.lower() or "vehicle" in proj_desc.lower() or "traffic" in proj_desc.lower():
            goal_str = "real-time traffic density estimation and vehicle counting"
        elif "sentiment" in proj_title.lower() or "nlp" in proj_desc.lower():
            goal_str = "customer sentiment classification from live feedback streams"
        elif "portfolio" in proj_title.lower() or "web" in proj_desc.lower():
            goal_str = "interactive, responsive UI rendering and modular layout presentation"

        # Determine best opening template that hasn't been used yet in session
        openings = cls.OPENING_TEMPLATES.get(intent, cls.OPENING_TEMPLATES[QuestionIntent.TECHNICAL_DECISION])
        selected_opening_template = openings[0]
        for op in openings:
            if op not in prior_openings:
                selected_opening_template = op
                break

        # Generate Intent-Specific Body
        if intent == QuestionIntent.PROJECT_OVERVIEW:
            opening = selected_opening_template.format(title=proj_title, goal=goal_str, mechanism=f"ingesting requests and persisting validated entities via {main_tech}", tech=main_tech)
            body = (
                f"In this system, {main_tech} serves as the primary backbone for data transformation and business logic. "
                f"I structured the application into decoupled modules to isolate data validation from output handling. "
                f"This architecture allowed {proj_title} to operate reliably with clean data consistency and predictable execution."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.WHY_TECHNOLOGY:
            driver_str = f"low-latency request handling, reliable data consistency, and robust library support for {main_tech}"
            opening = selected_opening_template.format(title=proj_title, tech=main_tech, driver=driver_str)
            body = (
                f"We considered alternative approaches, but {main_tech} offered the cleanest integration with our schema definitions and workflow requirements. "
                f"The primary trade-off was managing memory overhead under concurrent access, which we mitigated by structuring connection pooling and defensive error boundaries. "
                f"This ensured stable throughput without introducing unnecessary third-party architectural dependencies."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.CHALLENGE:
            obstacle_str = f"processing latency increased during peak transaction batches in {proj_title}"
            opening = selected_opening_template.format(title=proj_title, obstacle=obstacle_str)
            body = (
                f"To diagnose the issue, I profiled execution paths with runtime analyzers and isolated that synchronous I/O operations were blocking worker threads. "
                f"I resolved this by refactoring blocking calls into asynchronous non-blocking handlers and optimizing our query filters. "
                f"This restored steady execution speed, and taught me the importance of proactive profiling before scaling."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.SCALABILITY:
            opening = selected_opening_template.format(title=proj_title)
            body = (
                f"First, I would inspect slow query logs and execution plans to ensure all high-frequency filter predicates use covering indexes. "
                f"Second, I would introduce connection pooling to prevent database connection exhaustion under bursty client traffic. "
                f"If read volume remains the primary bottleneck, I would evaluate caching frequently queried read paths and configuring read replicas. "
                f"Since my experience in {proj_title} utilized {main_tech}, I would roll out these optimizations based on measured production metrics rather than premature redesigns."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.IMPROVEMENT:
            limitation_str = f"the current synchronous background processing and reliance on single-node scheduling"
            opening = selected_opening_template.format(title=proj_title, limitation=limitation_str)
            body = (
                f"I would introduce asynchronous task processing with retries and dead-letter queues to handle compute-heavy operations without blocking HTTP requests. "
                f"Additionally, adding comprehensive telemetry and health-check monitoring would provide deeper visibility into runtime latency distributions. "
                f"This would increase the overall system resilience and fault tolerance."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.DATABASE:
            opening = selected_opening_template.format(title=proj_title)
            body = (
                f"In {proj_title}, we normalized entities to third normal form to eliminate data duplication, while applying composite indexes on frequently filtered foreign keys. "
                f"For transaction safety, we wrapped multi-table state updates in atomic ACID transactions to prevent partial writes. "
                f"This design provided strong consistency while maintaining sub-millisecond query seeks on indexed columns."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.PERFORMANCE:
            opening = selected_opening_template.format(title=proj_title)
            body = (
                f"By profiling resource consumption in {proj_title}, we identified that serialization overhead and unindexed lookups were causing latency spikes. "
                f"We resolved this by streamlining data validation schemas, batching database queries, and keeping memory allocations localized. "
                f"These optimizations significantly reduced response variability across high-concurrency test runs."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.DEBUGGING:
            opening = selected_opening_template.format(title=proj_title, problem=f"intermittent data inconsistency in {proj_title}")
            body = (
                f"I began by capturing reproduction logs and inspecting payload payloads at each boundary layer to isolate state mutations. "
                f"I identified that unhandled edge-case values were bypassing validation before persisting. "
                f"I fixed the issue by enforcing strict schema validators, added automated unit tests, and verified that no data corruption occurred."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.PROJECT_ROLE:
            opening = selected_opening_template.format(title=proj_title, tech=main_tech)
            body = (
                f"Specifically, I designed the REST API endpoints, created data transformation handlers, and implemented error handling mechanisms. "
                f"I collaborated on architectural reviews to keep component dependencies clean and maintainable. "
                f"My contributions ensured {proj_title} was delivered with full test coverage and reliable error recovery."
            )
            answer = f"{opening} {body}"

        elif intent == QuestionIntent.CONCEPTUAL:
            mech_str = f"modular abstractions, predictable state management, and optimized execution lifecycle"
            opening = selected_opening_template.format(tech=main_tech, mechanism=mech_str)
            body = (
                f"When working with {main_tech}, understanding the trade-offs between memory overhead, execution speed, and safety guarantees is essential. "
                f"In practice, this enables building maintainable applications that scale reliably while keeping runtime complexity low."
            )
            answer = f"{opening} {body}"

        else:
            # Technical Decision / Tradeoff
            opening = selected_opening_template.format(title=proj_title, tech=main_tech)
            body = (
                f"In {proj_title}, selecting {main_tech} gave us rapid prototyping capabilities and well-tested libraries, but required careful attention to concurrency and memory bounds. "
                f"We addressed this by profiling hot paths, adding structured validation, and strictly isolating compute tasks to maintain high stability."
            )
            answer = f"{opening} {body}"

        # 4. Anti-Repetition Guard: Check similarity with previous answers in session
        for prior_ans in prior_answers[-4:]:
            sim = cls.calculate_similarity(answer, prior_ans)
            if sim > 0.60:
                # Alter phrasing to ensure distinctiveness
                answer = f"From an engineering perspective on {question_text.lower().replace('?', '')}, {answer}"
                break

        # 5. Semantic Relevance Check
        relevance_verdict = cls.check_relevance(question_text, intent, answer)

        # 6. Record in Session Tracker
        MockInterviewSessionTracker.record_entry(
            session_id=session_id,
            question=question_text,
            answer=answer,
            intent=intent,
            opening=selected_opening_template,
            topic=main_tech
        )

        return answer, intent, structure, relevance_verdict
